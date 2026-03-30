"""
CLI: python run_eval.py --baseline all

Triggers evaluation-service POST /run_eval and polls until complete.

Usage:
    python run_eval.py --dataset 2026_full --baseline openai_mod,gpt4o,llamaguard
    python run_eval.py --dataset harmbench --baseline all
    python run_eval.py --baseline all --output ./my_report.pdf
"""

import argparse
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Project-root sys.path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Install with: pip install httpx")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EVAL_SERVICE_URL = os.getenv("EVAL_SERVICE_URL", "http://localhost:8001")
ALL_BASELINES = ["openai_mod", "gpt4o_raw", "llamaguard"]
POLL_INTERVAL_SEC = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="EthicsGuard v0.4 - Evaluation CLI Runner"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="2026_full",
        help="Dataset to evaluate: 2026_full, harmbench, or absolute path to CSV.",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="all",
        help="Comma-separated baselines (openai_mod,gpt4o_raw,llamaguard) or 'all'.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save the PDF report. Default: ./eval_report_<id>.pdf",
    )
    parser.add_argument(
        "--service-url",
        type=str,
        default=None,
        help=f"Evaluation service URL. Default: {EVAL_SERVICE_URL}",
    )
    return parser.parse_args()


def resolve_baselines(baseline_str: str) -> list[str]:
    """Parse the --baseline argument into a list of targets."""
    if baseline_str.strip().lower() == "all":
        return ALL_BASELINES
    parts = [b.strip() for b in baseline_str.split(",") if b.strip()]
    # Normalize shorthand
    normalized = []
    for p in parts:
        if p == "gpt4o":
            normalized.append("gpt4o_raw")
        else:
            normalized.append(p)
    return normalized


def start_evaluation(client: httpx.Client, dataset: str, baselines: list[str]) -> dict:
    """POST /run_eval to start the evaluation."""
    resp = client.post(
        f"{EVAL_SERVICE_URL}/run_eval",
        json={"dataset": dataset, "baselines": baselines},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def poll_status(client: httpx.Client, eval_id: str) -> dict:
    """GET /eval_status/{eval_id} and return the status payload."""
    resp = client.get(
        f"{EVAL_SERVICE_URL}/eval_status/{eval_id}",
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def download_report(client: httpx.Client, eval_id: str, output_path: str) -> str:
    """GET /report/{eval_id} and save the PDF to disk."""
    resp = client.get(
        f"{EVAL_SERVICE_URL}/report/{eval_id}",
        timeout=60.0,
    )
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return os.path.abspath(output_path)


def print_results_summary(results: dict):
    """Pretty-print evaluation results to the terminal."""
    print("\n" + "=" * 68)
    print("  EthicsGuard v0.4 - Evaluation Results")
    print("=" * 68)
    header = f"{'Target':<18} {'ASR':>8} {'FPR':>8} {'FNR':>8} {'P95 (ms)':>10} {'Errors':>8}"
    print(header)
    print("-" * 68)
    for target, res in results.items():
        asr = res.get("asr", 0)
        fpr = res.get("fpr", 0)
        fnr = res.get("fnr", 0)
        p95 = res.get("latency_p95_ms", 0)
        errors = res.get("errors", 0)
        print(
            f"{target:<18} {asr:>7.1%} {fpr:>7.1%} {fnr:>7.1%} {p95:>9.0f} {errors:>8}"
        )
    print("=" * 68)


def main():
    args = parse_args()

    global EVAL_SERVICE_URL
    if args.service_url:
        EVAL_SERVICE_URL = args.service_url

    baselines = resolve_baselines(args.baseline)
    print(f"[EthicsGuard Eval] Dataset:   {args.dataset}")
    print(f"[EthicsGuard Eval] Baselines: {', '.join(baselines)}")
    print(f"[EthicsGuard Eval] Service:   {EVAL_SERVICE_URL}")
    print()

    client = httpx.Client()

    # 1. Start evaluation
    try:
        start_resp = start_evaluation(client, args.dataset, baselines)
    except httpx.ConnectError:
        print(
            f"ERROR: Could not connect to evaluation service at {EVAL_SERVICE_URL}.\n"
            "       Make sure the service is running (python -m services.evaluation_service.main)."
        )
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        print(f"ERROR: Service returned {exc.response.status_code}: {exc.response.text}")
        sys.exit(1)

    eval_id = start_resp["eval_id"]
    est_min = start_resp.get("estimated_minutes", "?")
    print(f"[EthicsGuard Eval] Job started: {eval_id}")
    print(f"[EthicsGuard Eval] Estimated time: ~{est_min} minutes")
    print()

    # 2. Poll until complete
    spinner = ["|", "/", "-", "\\"]
    spin_idx = 0
    while True:
        time.sleep(POLL_INTERVAL_SEC)
        try:
            status = poll_status(client, eval_id)
        except Exception as exc:
            print(f"\n  Warning: poll failed ({exc}), retrying...")
            continue

        job_status = status["status"]
        progress = status.get("progress", 0)
        sp = spinner[spin_idx % len(spinner)]
        spin_idx += 1

        sys.stdout.write(
            f"\r  {sp} Status: {job_status}  |  Progress: {progress:.0%}    "
        )
        sys.stdout.flush()

        if job_status == "complete":
            print()  # newline after spinner
            if status.get("results"):
                print_results_summary(status["results"])
            break
        elif job_status == "failed":
            print(f"\n\nERROR: Evaluation failed: {status.get('error', 'unknown')}")
            sys.exit(1)

    # 3. Download PDF report
    output_path = args.output or f"eval_report_{eval_id}.pdf"
    try:
        saved = download_report(client, eval_id, output_path)
        print(f"\n[EthicsGuard Eval] Report saved: {saved}")
    except httpx.HTTPStatusError as exc:
        print(f"\nWarning: Could not download report ({exc.response.status_code}).")
    except Exception as exc:
        print(f"\nWarning: Could not download report: {exc}")

    client.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
