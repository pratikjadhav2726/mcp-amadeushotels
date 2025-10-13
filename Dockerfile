# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Build arguments for environment variables
ARG AMADEUS_API_KEY
ARG AMADEUS_API_SECRET
ARG AMADEUS_BASE_URL=https://test.api.amadeus.com
ARG PORT=3000
ARG LOG_LEVEL=INFO

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    AMADEUS_API_KEY=${AMADEUS_API_KEY} \
    AMADEUS_API_SECRET=${AMADEUS_API_SECRET} \
    AMADEUS_BASE_URL=${AMADEUS_BASE_URL} \
    PORT=${PORT} \
    LOG_LEVEL=${LOG_LEVEL}

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy Python dependencies first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/
COPY run_server.py ./

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose the port that the app runs on
EXPOSE ${PORT}

# Set the default host to 0.0.0.0 for container deployment
ENV HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/mcp || exit 1

# Start the application with streamable HTTP transport
CMD ["uv", "run", "run_server.py", "--transport", "streamable-http"]