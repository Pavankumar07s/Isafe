FROM python:3.11-slim

WORKDIR /app

# Copy shared and core modules first (common layer)
COPY shared/ /app/shared/
COPY core/ /app/core/

# Copy service-specific code
COPY services/evaluation-service/ /app/services/evaluation_service/
COPY evaluation/ /app/evaluation/
RUN touch /app/services/__init__.py /app/services/evaluation_service/__init__.py

# Install dependencies
COPY services/evaluation-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create data directories
RUN mkdir -p /data /app/results /app/logs

# Set PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8002

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
    CMD python -c "import httpx; httpx.get('http://localhost:8002/health').raise_for_status()"

CMD ["uvicorn", "services.evaluation_service.main:app", "--host", "0.0.0.0", "--port", "8002"]
