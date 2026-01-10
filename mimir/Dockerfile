# Build argument for multi-architecture support
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Add labels
LABEL \
    io.hass.name="Mímir" \
    io.hass.description="Intelligent Home Assistant agent with Nordic wisdom" \
    io.hass.version="0.1.6" \
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
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /opt/mimir

# Copy requirements first for better caching
COPY requirements.txt /opt/mimir/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code as a package
COPY app/ /opt/mimir/app/

# Copy S6 overlay service configuration
COPY rootfs/ /

# Make service scripts executable
RUN chmod a+x /etc/s6-overlay/s6-rc.d/mimir/run \
    && chmod a+x /etc/s6-overlay/s6-rc.d/mimir/finish

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
