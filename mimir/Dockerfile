# Build argument for multi-architecture support
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Add labels
LABEL \
    io.hass.name="Mímir" \
    io.hass.description="Intelligent Home Assistant agent with Nordic wisdom" \
    io.hass.version="0.1.3" \
    io.hass.type="addon" \
    io.hass.arch="amd64|aarch64|armv7"

# Install system dependencies
RUN apk add --no-cache \
    git \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    jq \
    bash \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/

# Copy startup script
COPY run.sh /
RUN chmod a+x /run.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run the application
CMD ["/run.sh"]
