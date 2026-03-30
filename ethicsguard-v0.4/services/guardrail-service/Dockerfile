FROM python:3.11-slim

WORKDIR /app

# Install build tools for native extensions (annoy, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends g++ && rm -rf /var/lib/apt/lists/*

# Copy shared and core modules first (common layer)
COPY shared/ /app/shared/
COPY core/ /app/core/

# Copy service-specific code
COPY services/guardrail-service/ /app/services/guardrail_service/
RUN touch /app/services/__init__.py /app/services/guardrail_service/__init__.py

# Install dependencies
COPY services/guardrail-service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create data directories
RUN mkdir -p /data /app/results /app/logs

# Set PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8000

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "services.guardrail_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
