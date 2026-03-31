#!/bin/bash
# =============================================================================
# EthicsGuard v0.4 — Railway Production Starter
# Runs all 4 services in a single container
# =============================================================================

set -euo pipefail

# Railway provides PORT env var — Streamlit uses it
STREAMLIT_PORT="${PORT:-8501}"

# Map GROQ_API_KEY to OPENAI_API_KEY for OpenAI-compatible usage
export OPENAI_API_KEY="${GROQ_API_KEY:-${OPENAI_API_KEY:-}}"
export OPENAI_API_BASE="${OPENAI_API_BASE:-https://api.groq.com/openai/v1}"
export OPENAI_MODEL="${OPENAI_MODEL:-qwen/qwen3-32b}"
export COMPLIANCE_MODE="${COMPLIANCE_MODE:-STANDARD}"
export INTERNAL_API_SECRET="${INTERNAL_API_SECRET:-railway-prod-secret-32chars}"
export ENABLE_PROMETHEUS="${ENABLE_PROMETHEUS:-true}"
export AUDIT_DB_PATH="${AUDIT_DB_PATH:-/app/data/ethicsguard_audit.db}"
export GUARDRAIL_BASE_URL="http://localhost:8000"
export GUARDRAIL_SERVICE_URL="http://localhost:8000"
export GUARDRAIL_URL="http://localhost:8000"
export REDTEAM_URL="http://localhost:8001"
export EVAL_URL="http://localhost:8002"
export PYTHONPATH="/app"

mkdir -p /app/data /app/reports

echo "[EthicsGuard] Starting all services (Railway mode)..."

# 1. Guardrail Service (port 8000 — internal)
cd /app/services/guardrail-service
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level warning &
PID_GUARD=$!
sleep 2

# 2. Red Team Service (port 8001 — internal)
cd /app/services/redteam-service
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --log-level warning &
PID_RED=$!
sleep 1

# 3. Evaluation Service (port 8002 — internal)
cd /app/services/evaluation-service
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --log-level warning &
PID_EVAL=$!
sleep 1

# 4. Dashboard (Streamlit — exposed on Railway PORT)
cd /app/services/dashboard-service
echo "[EthicsGuard] Dashboard on port $STREAMLIT_PORT"
python -m streamlit run app.py \
  --server.port="$STREAMLIT_PORT" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false &
PID_DASH=$!

echo "[EthicsGuard] All services started."
echo "  Guardrail:  PID $PID_GUARD (:8000)"
echo "  Red Team:   PID $PID_RED   (:8001)"
echo "  Evaluation: PID $PID_EVAL  (:8002)"
echo "  Dashboard:  PID $PID_DASH  (:$STREAMLIT_PORT)"

# Handle graceful shutdown
trap "kill $PID_GUARD $PID_RED $PID_EVAL $PID_DASH 2>/dev/null; exit 0" SIGTERM SIGINT

# Wait for any process to exit
wait -n $PID_GUARD $PID_RED $PID_EVAL $PID_DASH
EXIT_CODE=$?
echo "[EthicsGuard] A service exited with code $EXIT_CODE — shutting down."
kill $PID_GUARD $PID_RED $PID_EVAL $PID_DASH 2>/dev/null
exit $EXIT_CODE
