"""Database connection management for Mímir."""

from __future__ import annotations

import aiosqlite

from ..utils.logging import get_logger

logger = get_logger(__name__)

# SQL schema for audit tables
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    source TEXT NOT NULL,
    user_id TEXT,
    session_id TEXT,
    message_type TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS tool_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_log_id INTEGER,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    tool_name TEXT NOT NULL,
    parameters TEXT NOT NULL,
    result TEXT,
    duration_ms INTEGER,
    success INTEGER NOT NULL,
    error_message TEXT,
    FOREIGN KEY (audit_log_id) REFERENCES audit_logs(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_source ON audit_logs(source);
CREATE INDEX IF NOT EXISTS idx_audit_message_type ON audit_logs(message_type);
CREATE INDEX IF NOT EXISTS idx_tool_name ON tool_executions(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_timestamp ON tool_executions(timestamp);

-- Long-term memory storage
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT,
    user_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
"""


class Database:
    """Async database connection manager using aiosqlite."""

    def __init__(self, db_path: str = "/data/mimir.db") -> None:
        """Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file.
        """
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connection is not None

    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        logger.info("Initializing database at %s", self._db_path)

        self._connection = await aiosqlite.connect(self._db_path)
        self._connection.row_factory = aiosqlite.Row

        # Create tables if they don't exist
        await self._connection.executescript(SCHEMA_SQL)
        await self._connection.commit()

        logger.info("Database initialized successfully")

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    async def execute(
        self,
        sql: str,
        parameters: tuple[object, ...] | None = None,
    ) -> aiosqlite.Cursor:
        """Execute a SQL query.

        Args:
            sql: SQL query string.
            parameters: Query parameters.

        Returns:
            Cursor with query results.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        if parameters:
            return await self._connection.execute(sql, parameters)
        return await self._connection.execute(sql)

    async def execute_many(
        self,
        sql: str,
        parameters: list[tuple[object, ...]],
    ) -> None:
        """Execute a SQL query with multiple parameter sets.

        Args:
            sql: SQL query string.
            parameters: List of parameter tuples.
        """
        if not self._connection:
            raise RuntimeError("Database not initialized")

        await self._connection.executemany(sql, parameters)

    async def fetch_one(
        self,
        sql: str,
        parameters: tuple[object, ...] | None = None,
    ) -> aiosqlite.Row | None:
        """Fetch a single row from a query.

        Args:
            sql: SQL query string.
            parameters: Query parameters.

        Returns:
            Single row or None.
        """
        cursor = await self.execute(sql, parameters)
        return await cursor.fetchone()

    async def fetch_all(
        self,
        sql: str,
        parameters: tuple[object, ...] | None = None,
    ) -> list[aiosqlite.Row]:
        """Fetch all rows from a query.

        Args:
            sql: SQL query string.
            parameters: Query parameters.

        Returns:
            List of rows.
        """
        cursor = await self.execute(sql, parameters)
        return list(await cursor.fetchall())

    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._connection:
            await self._connection.commit()

    async def get_last_insert_id(self) -> int:
        """Get the last inserted row ID.

        Returns:
            The rowid of the last inserted row.
        """
        row = await self.fetch_one("SELECT last_insert_rowid()")
        return row[0] if row else 0
