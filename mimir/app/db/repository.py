"""Audit repository for Mímir."""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..utils.logging import get_logger

if TYPE_CHECKING:
    from .connection import Database

logger = get_logger(__name__)


@dataclass
class AuditLogEntry:
    """Represents an audit log entry."""

    id: int
    timestamp: str
    source: str
    user_id: str | None
    session_id: str | None
    message_type: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    tool_executions: list[ToolExecutionEntry] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: Any) -> AuditLogEntry:
        """Create from database row."""
        metadata = {}
        if row["metadata"]:
            with contextlib.suppress(json.JSONDecodeError):
                metadata = json.loads(row["metadata"])

        return cls(
            id=row["id"],
            timestamp=row["timestamp"],
            source=row["source"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            message_type=row["message_type"],
            content=row["content"],
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "source": self.source,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "message_type": self.message_type,
            "content": self.content,
            "metadata": self.metadata,
            "tool_executions": [t.to_dict() for t in self.tool_executions],
        }


@dataclass
class ToolExecutionEntry:
    """Represents a tool execution record."""

    id: int
    audit_log_id: int | None
    timestamp: str
    tool_name: str
    parameters: dict[str, Any]
    result: str | None
    duration_ms: int | None
    success: bool
    error_message: str | None = None

    @classmethod
    def from_row(cls, row: Any) -> ToolExecutionEntry:
        """Create from database row."""
        parameters = {}
        if row["parameters"]:
            with contextlib.suppress(json.JSONDecodeError):
                parameters = json.loads(row["parameters"])

        return cls(
            id=row["id"],
            audit_log_id=row["audit_log_id"],
            timestamp=row["timestamp"],
            tool_name=row["tool_name"],
            parameters=parameters,
            result=row["result"],
            duration_ms=row["duration_ms"],
            success=bool(row["success"]),
            error_message=row["error_message"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "audit_log_id": self.audit_log_id,
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
        }


class AuditRepository:
    """Repository for audit log operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the repository.

        Args:
            db: Database connection instance.
        """
        self._db = db

    async def log_message(
        self,
        source: str,
        message_type: str,
        content: str,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Log a message to the audit log.

        Args:
            source: Source of the message ('telegram', 'web', 'system').
            message_type: Type of message ('user', 'assistant', 'tool', 'error').
            content: The message content.
            user_id: Optional user identifier.
            session_id: Optional session identifier.
            metadata: Optional additional metadata.

        Returns:
            The ID of the created audit log entry.
        """
        metadata_json = json.dumps(metadata) if metadata else None

        await self._db.execute(
            """
            INSERT INTO audit_logs (source, user_id, session_id, message_type, content, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (source, user_id, session_id, message_type, content, metadata_json),
        )
        await self._db.commit()

        log_id = await self._db.get_last_insert_id()
        logger.debug("Logged message: id=%d, type=%s, source=%s", log_id, message_type, source)
        return log_id

    async def log_tool_execution(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: str | None,
        duration_ms: int,
        success: bool,
        audit_log_id: int | None = None,
        error_message: str | None = None,
    ) -> int:
        """Log a tool execution.

        Args:
            tool_name: Name of the tool.
            parameters: Tool parameters.
            result: Tool execution result.
            duration_ms: Execution duration in milliseconds.
            success: Whether execution succeeded.
            audit_log_id: Optional link to parent audit log entry.
            error_message: Optional error message if failed.

        Returns:
            The ID of the created tool execution entry.
        """
        params_json = json.dumps(parameters)

        await self._db.execute(
            """
            INSERT INTO tool_executions
            (audit_log_id, tool_name, parameters, result, duration_ms, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_log_id,
                tool_name,
                params_json,
                result,
                duration_ms,
                int(success),
                error_message,
            ),
        )
        await self._db.commit()

        exec_id = await self._db.get_last_insert_id()
        logger.debug(
            "Logged tool execution: id=%d, tool=%s, success=%s",
            exec_id,
            tool_name,
            success,
        )
        return exec_id

    async def get_recent_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        source: str | None = None,
        message_type: str | None = None,
    ) -> list[AuditLogEntry]:
        """Get recent audit logs.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.
            source: Optional filter by source.
            message_type: Optional filter by message type.

        Returns:
            List of audit log entries.
        """
        conditions = []
        params: list[object] = []

        if source:
            conditions.append("source = ?")
            params.append(source)

        if message_type:
            conditions.append("message_type = ?")
            params.append(message_type)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        params.extend([limit, offset])

        rows = await self._db.fetch_all(
            f"""
            SELECT * FROM audit_logs
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params),
        )

        return [AuditLogEntry.from_row(row) for row in rows]

    async def get_log_by_id(self, log_id: int) -> AuditLogEntry | None:
        """Get a single audit log entry by ID.

        Args:
            log_id: The audit log ID.

        Returns:
            The audit log entry or None.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM audit_logs WHERE id = ?",
            (log_id,),
        )

        if not row:
            return None

        entry = AuditLogEntry.from_row(row)

        # Get associated tool executions
        tool_rows = await self._db.fetch_all(
            "SELECT * FROM tool_executions WHERE audit_log_id = ? ORDER BY timestamp",
            (log_id,),
        )
        entry.tool_executions = [ToolExecutionEntry.from_row(r) for r in tool_rows]

        return entry

    async def search_logs(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        """Search audit logs by content.

        Args:
            query: Search query string.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of matching audit log entries.
        """
        search_pattern = f"%{query}%"

        rows = await self._db.fetch_all(
            """
            SELECT * FROM audit_logs
            WHERE content LIKE ?
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """,
            (search_pattern, limit, offset),
        )

        return [AuditLogEntry.from_row(row) for row in rows]

    async def get_tool_executions(
        self,
        limit: int = 50,
        offset: int = 0,
        tool_name: str | None = None,
        success_only: bool | None = None,
    ) -> list[ToolExecutionEntry]:
        """Get tool execution records.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.
            tool_name: Optional filter by tool name.
            success_only: Optional filter by success status.

        Returns:
            List of tool execution entries.
        """
        conditions = []
        params: list[object] = []

        if tool_name:
            conditions.append("tool_name = ?")
            params.append(tool_name)

        if success_only is not None:
            conditions.append("success = ?")
            params.append(int(success_only))

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        params.extend([limit, offset])

        rows = await self._db.fetch_all(
            f"""
            SELECT * FROM tool_executions
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params),
        )

        return [ToolExecutionEntry.from_row(row) for row in rows]

    async def get_log_count(
        self,
        source: str | None = None,
        message_type: str | None = None,
    ) -> int:
        """Get total count of audit logs.

        Args:
            source: Optional filter by source.
            message_type: Optional filter by message type.

        Returns:
            Total count of matching logs.
        """
        conditions = []
        params: list[object] = []

        if source:
            conditions.append("source = ?")
            params.append(source)

        if message_type:
            conditions.append("message_type = ?")
            params.append(message_type)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        row = await self._db.fetch_one(
            f"SELECT COUNT(*) as count FROM audit_logs {where_clause}",
            tuple(params) if params else None,
        )

        return row["count"] if row else 0

    async def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete audit logs older than specified days.

        Args:
            days: Number of days to keep logs.

        Returns:
            Number of deleted rows.
        """
        # First delete tool executions for old logs
        await self._db.execute(
            """
            DELETE FROM tool_executions
            WHERE audit_log_id IN (
                SELECT id FROM audit_logs
                WHERE timestamp < datetime('now', ?)
            )
            """,
            (f"-{days} days",),
        )

        # Then delete old logs
        cursor = await self._db.execute(
            "DELETE FROM audit_logs WHERE timestamp < datetime('now', ?)",
            (f"-{days} days",),
        )
        await self._db.commit()

        deleted = cursor.rowcount
        if deleted > 0:
            logger.info("Cleaned up %d old audit log entries", deleted)

        return deleted
