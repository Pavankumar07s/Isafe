#!/bin/bash
# =============================================================================
# EthicsGuard v0.4 — Local Development Launcher
# Starts all 4 services with Ollama (mistral:7b)
# =============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

# Common environment
export PYTHONPATH="$PROJECT_ROOT"
export OPENAI_API_KEY="ollama"
export OPENAI_API_BASE="http://localhost:11434/v1"
export OPENAI_MODEL="mistral:7b"
export COMPLIANCE_MODE="STANDARD"
export INTERNAL_API_SECRET="test-secret-for-development-32chars"
export ENABLE_PROMETHEUS="true"
export AUDIT_DB_PATH="$PROJECT_ROOT/data/ethicsguard_audit.db"
export GUARDRAIL_BASE_URL="http://localhost:8000"
export GUARDRAIL_SERVICE_URL="http://localhost:8000"
export GUARDRAIL_URL="http://localhost:8000"
export REDTEAM_URL="http://localhost:8001"
export EVAL_URL="http://localhost:8002"

# Create data dirs
mkdir -p "$PROJECT_ROOT/data" "$PROJECT_ROOT/reports"

echo "🛡️  EthicsGuard v0.4 — Starting all services..."
echo "   Using Ollama (mistral:7b) at http://localhost:11434"
echo ""

# Kill any existing services
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
sleep 1

# 1. Guardrail Service (port 8000)
echo "🚀 Starting guardrail-service on :8000..."
cd "$PROJECT_ROOT/services/guardrail-service"
PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/services/guardrail-service" \
  python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info &
GUARDRAIL_PID=$!
sleep 2

# 2. Red Team Service (port 8001)
echo "🚀 Starting redteam-service on :8001..."
cd "$PROJECT_ROOT/services/redteam-service"
PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/services/redteam-service" \
  python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info &
REDTEAM_PID=$!
sleep 2

# 3. Evaluation Service (port 8002)
echo "🚀 Starting evaluation-service on :8002..."
cd "$PROJECT_ROOT/services/evaluation-service"
PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/services/evaluation-service" \
  python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 --log-level info &
EVAL_PID=$!
sleep 2

# 4. Dashboard Service (port 8501)
echo "🚀 Starting dashboard-service on :8501..."
cd "$PROJECT_ROOT/services/dashboard-service"
PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/services/dashboard-service" \
  python3 -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true &
DASHBOARD_PID=$!
sleep 2

echo ""
echo "✅ All services started!"
echo ""
echo "   🛡️  Guardrail API:  http://localhost:8000  (PID: $GUARDRAIL_PID)"
echo "   🔴 Red Team API:   http://localhost:8001  (PID: $REDTEAM_PID)"
echo "   📊 Evaluation API: http://localhost:8002  (PID: $EVAL_PID)"
echo "   🖥️  Dashboard:      http://localhost:8501  (PID: $DASHBOARD_PID)"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for any child to exit
trap "echo ''; echo 'Stopping all services...'; kill $GUARDRAIL_PID $REDTEAM_PID $EVAL_PID $DASHBOARD_PID 2>/dev/null; exit 0" INT TERM
wait
