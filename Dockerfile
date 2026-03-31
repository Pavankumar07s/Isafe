# =============================================================================
# EthicsGuard v0.4 — Unified Dockerfile (all 4 services in one container)
# Optimised for Railway / cloud free-tier deployment
# =============================================================================
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends g++ curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY ethicsguard-v0.4/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY ethicsguard-v0.4/ /app/

# Create data directories
RUN mkdir -p /app/data /app/reports /app/logs

# Set PYTHONPATH so all services can find shared/ and core/
ENV PYTHONPATH=/app

# Railway sets PORT dynamically; default to 8501 for Streamlit
ENV PORT=8501

# Expose the main port (Streamlit dashboard)
EXPOSE ${PORT}

# Production entrypoint — starts all 4 services
RUN chmod +x /app/start_railway.sh
CMD ["/app/start_railway.sh"]
