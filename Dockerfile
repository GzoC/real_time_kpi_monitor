# Dockerfile (Simplified)
ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base

# Set up a non-root user 'appuser'
ARG UID=10001
RUN useradd -m -s /bin/bash -u ${UID} appuser
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Install OS dependencies needed for typical Python projects (e.g., for psycopg2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory and environment variables
ENV APP_HOME=/app
WORKDIR ${APP_HOME}
ENV PYTHONNOUSERSITE=True
ENV PYTHONDONTWRITEBYTECODE=True

# Switch to non-root user before copying files or installing dependencies
USER appuser

# Copy requirements first to leverage Docker cache
COPY --chown=appuser:appuser requirements.txt .

# Install project dependencies (for the non-root user)
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of the application code
# Ensure paths in docker-compose.yml volumes match where code is copied if different from WORKDIR subdirs
COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./scripts ./scripts
# If .env file is used and needs to be IN the image (not recommended for secrets, use volume mount)
# COPY --chown=appuser:appuser .env .

# Expose port for FastAPI/uvicorn (optional, as docker-compose handles mapping)
EXPOSE 8000 

# Default command (can be overridden in docker-compose, e.g., sleep infinity)
# CMD ["sleep", "infinity"] # Or a command to run your main application if it's a server
