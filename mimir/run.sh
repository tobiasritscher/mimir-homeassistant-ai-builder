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

# Debug: Check all possible token sources
echo ""
echo "=== Token Debug ==="
if [ -n "$SUPERVISOR_TOKEN" ]; then
    echo "SUPERVISOR_TOKEN env: [SET - ${#SUPERVISOR_TOKEN} chars]"
else
    echo "SUPERVISOR_TOKEN env: [NOT SET]"
fi

if [ -n "$HASSIO_TOKEN" ]; then
    echo "HASSIO_TOKEN env: [SET - ${#HASSIO_TOKEN} chars]"
    export SUPERVISOR_TOKEN="$HASSIO_TOKEN"
else
    echo "HASSIO_TOKEN env: [NOT SET]"
fi

# Check S6 environment files
if [ -f /run/s6/container_environment/SUPERVISOR_TOKEN ]; then
    echo "S6 file exists: /run/s6/container_environment/SUPERVISOR_TOKEN"
    export SUPERVISOR_TOKEN=$(cat /run/s6/container_environment/SUPERVISOR_TOKEN)
    echo "Loaded from S6 file"
elif [ -f /var/run/s6/container_environment/SUPERVISOR_TOKEN ]; then
    echo "S6 file exists: /var/run/s6/container_environment/SUPERVISOR_TOKEN"
    export SUPERVISOR_TOKEN=$(cat /var/run/s6/container_environment/SUPERVISOR_TOKEN)
    echo "Loaded from S6 file (var)"
fi

# List all environment variables containing TOKEN or HASSIO
echo ""
echo "=== Related env vars ==="
env | grep -iE "(token|hassio|supervisor)" || echo "No matching env vars found"
echo "========================"
echo ""

mkdir -p /data/mimir

echo "Starting Python application..."
cd /opt/mimir
exec python3 -m app.main
