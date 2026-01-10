#!/bin/bash
set -e

CONFIG_PATH=/data/options.json

echo "=========================================="
echo "Mímir - Intelligent Home Assistant Agent"
echo "=========================================="

# Read configuration using jq
if [ -f "$CONFIG_PATH" ]; then
    export MIMIR_LLM_PROVIDER=$(jq -r '.llm_provider // "anthropic"' "$CONFIG_PATH")
    export MIMIR_LLM_API_KEY=$(jq -r '.llm_api_key // ""' "$CONFIG_PATH")
    export MIMIR_LLM_MODEL=$(jq -r '.llm_model // "claude-sonnet-4-20250514"' "$CONFIG_PATH")
    export MIMIR_LLM_BASE_URL=$(jq -r '.llm_base_url // ""' "$CONFIG_PATH")
    export MIMIR_TELEGRAM_OWNER_ID=$(jq -r '.telegram_owner_id // 0' "$CONFIG_PATH")
    export MIMIR_OPERATING_MODE=$(jq -r '.operating_mode // "normal"' "$CONFIG_PATH")
    export MIMIR_DEBUG=$(jq -r '.debug // false' "$CONFIG_PATH")
else
    echo "Warning: Config file not found at $CONFIG_PATH"
fi

if [ "$MIMIR_DEBUG" = "true" ]; then
    export LOG_LEVEL="DEBUG"
    echo "Debug mode enabled"
else
    export LOG_LEVEL="INFO"
fi

echo "LLM Provider: ${MIMIR_LLM_PROVIDER}"
echo "LLM Model: ${MIMIR_LLM_MODEL}"
echo "Operating Mode: ${MIMIR_OPERATING_MODE}"
echo "Telegram Owner ID: ${MIMIR_TELEGRAM_OWNER_ID}"
echo "SUPERVISOR_TOKEN: ${SUPERVISOR_TOKEN:+[SET]}"
echo "SUPERVISOR_TOKEN: ${SUPERVISOR_TOKEN:-[NOT SET]}"

mkdir -p /data/mimir

echo "Starting Python application..."
cd /opt/mimir
exec python3 -m app.main
