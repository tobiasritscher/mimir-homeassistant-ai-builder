#!/usr/bin/with-contenv bashio

set -e

# Configuration
CONFIG_PATH=/data/options.json

# Read configuration using bashio
LLM_PROVIDER=$(bashio::config 'llm_provider')
LLM_API_KEY=$(bashio::config 'llm_api_key')
LLM_MODEL=$(bashio::config 'llm_model')
LLM_BASE_URL=$(bashio::config 'llm_base_url')
TELEGRAM_OWNER_ID=$(bashio::config 'telegram_owner_id')
OPERATING_MODE=$(bashio::config 'operating_mode')
DEBUG=$(bashio::config 'debug')

# Export as environment variables
export MIMIR_LLM_PROVIDER="${LLM_PROVIDER}"
export MIMIR_LLM_API_KEY="${LLM_API_KEY}"
export MIMIR_LLM_MODEL="${LLM_MODEL}"
export MIMIR_LLM_BASE_URL="${LLM_BASE_URL}"
export MIMIR_TELEGRAM_OWNER_ID="${TELEGRAM_OWNER_ID}"
export MIMIR_OPERATING_MODE="${OPERATING_MODE}"
export MIMIR_DEBUG="${DEBUG}"

# Supervisor token is automatically available
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

# Set log level based on debug setting
if bashio::config.true 'debug'; then
    export LOG_LEVEL="DEBUG"
    bashio::log.info "Debug mode enabled"
else
    export LOG_LEVEL="INFO"
fi

bashio::log.info "Starting Mímir - Intelligent Home Assistant Agent"
bashio::log.info "LLM Provider: ${LLM_PROVIDER}"
bashio::log.info "Operating Mode: ${OPERATING_MODE}"

# Create data directories
mkdir -p /data/mimir

# Run the application
exec python3 /app/main.py
