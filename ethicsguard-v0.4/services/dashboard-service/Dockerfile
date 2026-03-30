FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy shared and core modules first (common layer)
COPY shared/ /app/shared/
COPY core/ /app/core/

# Copy service-specific code
COPY services/dashboard-service/ /app/services/dashboard_service/
RUN touch /app/services/__init__.py /app/services/dashboard_service/__init__.py

# Install dependencies
COPY services/dashboard-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create data directories
RUN mkdir -p /data /app/results /app/logs

# Set PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8501

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "services/dashboard_service/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
