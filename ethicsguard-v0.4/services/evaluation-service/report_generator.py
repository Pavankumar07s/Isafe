"""
EthicsGuard v0.4 - PDF Report Generator
Produces professional evaluation reports using fpdf2.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fpdf import FPDF


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLOR_PRIMARY = (33, 37, 41)       # near-black
COLOR_ACCENT = (0, 123, 255)       # blue
COLOR_SUCCESS = (40, 167, 69)      # green
COLOR_DANGER = (220, 53, 69)       # red
COLOR_WARNING = (255, 193, 7)      # amber
COLOR_LIGHT_BG = (248, 249, 250)   # light gray
COLOR_WHITE = (255, 255, 255)
COLOR_TABLE_HEADER = (52, 58, 64)  # dark gray

# Bar chart colors per target
TARGET_COLORS = {
    "ethicsguard": (0, 123, 255),
    "openai_mod": (255, 193, 7),
    "gpt4o_raw": (220, 53, 69),
    "llamaguard": (40, 167, 69),
}


class ReportGenerator:
    """Generates a PDF evaluation report from eval results."""

    def generate_report(self, eval_results: dict, output_path: str) -> str:
        """
        Generate a professional PDF report.

        Parameters
        ----------
        eval_results : dict
            Mapping of target_name -> result dict (as returned by
            EvalResult.to_dict()).
        output_path : str
            Filesystem path where the PDF will be written.

        Returns
        -------
        str
            The absolute path to the generated PDF.
        """
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.set_left_margin(15)
        pdf.set_right_margin(15)
        pdf.add_page()

        self._render_title(pdf)
        self._render_generation_info(pdf)
        self._render_executive_summary(pdf, eval_results)
        self._render_asr_bar_chart(pdf, eval_results)
        self._render_owasp_coverage(pdf, eval_results)
        self._render_methodology(pdf)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pdf.output(output_path)
        return os.path.abspath(output_path)

    # ------------------------------------------------------------------
    # Title page
    # ------------------------------------------------------------------
    @staticmethod
    def _render_title(pdf: FPDF):
        pdf.set_font("Helvetica", "B", 26)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 18, "EthicsGuard v0.4", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 14)
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.cell(
            0, 10, "Evaluation Report", new_x="LMARGIN", new_y="NEXT", align="C"
        )
        pdf.ln(6)
        # Horizontal rule
        pdf.set_draw_color(*COLOR_ACCENT)
        pdf.set_line_width(0.8)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(8)

    @staticmethod
    def _render_generation_info(pdf: FPDF):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, f"Generated: {now}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(
            0,
            5,
            "Framework: EthicsGuard Evaluation Service v0.4 | deepeval + custom harness",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(6)

    # ------------------------------------------------------------------
    # Executive summary table
    # ------------------------------------------------------------------
    def _render_executive_summary(self, pdf: FPDF, eval_results: dict):
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        col_widths = [40, 28, 26, 26, 32, 28]
        headers = ["Target", "Prompts", "ASR", "FPR", "P95 Lat (ms)", "Errors"]

        # Header row
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*COLOR_TABLE_HEADER)
        pdf.set_text_color(*COLOR_WHITE)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 9, h, border=1, fill=True, align="C")
        pdf.ln()

        # Data rows
        pdf.set_font("Helvetica", "", 9)
        for idx, (target, res) in enumerate(eval_results.items()):
            if idx % 2 == 0:
                pdf.set_fill_color(*COLOR_LIGHT_BG)
            else:
                pdf.set_fill_color(*COLOR_WHITE)
            pdf.set_text_color(*COLOR_PRIMARY)

            asr_val = res.get("asr", 0)
            fpr_val = res.get("fpr", 0)

            row = [
                target,
                str(res.get("total_prompts", 0)),
                f"{asr_val:.1%}",
                f"{fpr_val:.1%}",
                f"{res.get('latency_p95_ms', 0):.0f}",
                str(res.get("errors", 0)),
            ]
            for i, val in enumerate(row):
                pdf.cell(
                    col_widths[i], 8, val, border=1, fill=True, align="C"
                )
            pdf.ln()
        pdf.ln(10)

    # ------------------------------------------------------------------
    # Per-category ASR bar chart (drawn with fpdf2 rectangles)
    # ------------------------------------------------------------------
    def _render_asr_bar_chart(self, pdf: FPDF, eval_results: dict):
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(
            0,
            10,
            "Per-Category Attack Success Rate (ASR)",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        # Gather all categories across targets
        all_categories = set()
        for res in eval_results.values():
            per_cat = res.get("per_category", {})
            all_categories.update(per_cat.keys())
        categories = sorted(all_categories - {"benign_control"})

        if not categories:
            pdf.set_font("Helvetica", "I", 10)
            pdf.cell(0, 8, "No attack categories found.", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)
            return

        targets = list(eval_results.keys())
        num_targets = len(targets)

        chart_left = pdf.l_margin + 50  # space for labels
        chart_width = pdf.w - pdf.l_margin - pdf.r_margin - 55
        row_height = 10
        bar_height = max(5, row_height / max(num_targets, 1))
        group_height = row_height * max(num_targets, 1) + 6

        # Check if we need a new page
        needed = len(categories) * group_height + 40
        if pdf.get_y() + needed > pdf.h - 40:
            pdf.add_page()

        start_y = pdf.get_y()

        for cat_idx, cat in enumerate(categories):
            group_y = start_y + cat_idx * group_height

            # Category label
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.set_xy(pdf.l_margin, group_y)
            pdf.cell(48, group_height - 2, cat.replace("_", " ").title(), align="R")

            for t_idx, tgt in enumerate(targets):
                per_cat = eval_results[tgt].get("per_category", {})
                cat_data = per_cat.get(cat, {"blocked": 0, "total": 1})
                total = cat_data["total"] if cat_data["total"] > 0 else 1
                blocked = cat_data["blocked"]
                asr = 1.0 - (blocked / total)  # unblocked fraction = ASR

                bar_y = group_y + t_idx * bar_height
                bar_w = max(chart_width * asr, 0)

                color = TARGET_COLORS.get(tgt, (150, 150, 150))
                pdf.set_fill_color(*color)
                pdf.rect(chart_left, bar_y, bar_w, bar_height - 1, style="F")

                # ASR % label
                pdf.set_font("Helvetica", "", 7)
                pdf.set_xy(chart_left + bar_w + 2, bar_y)
                pdf.cell(18, bar_height - 1, f"{asr:.0%}")

        # Legend
        legend_y = start_y + len(categories) * group_height + 8
        if legend_y > pdf.h - 40:
            pdf.add_page()
            legend_y = pdf.get_y()

        pdf.set_xy(pdf.l_margin, legend_y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 6, "Legend:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for tgt in targets:
            color = TARGET_COLORS.get(tgt, (150, 150, 150))
            pdf.set_fill_color(*color)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.rect(x, y + 1.5, 10, 4, style="F")
            pdf.set_xy(x + 13, y)
            pdf.cell(0, 6, tgt, new_x="LMARGIN", new_y="NEXT")

        pdf.set_y(legend_y + len(targets) * 6 + 10)

    # ------------------------------------------------------------------
    # OWASP tag coverage
    # ------------------------------------------------------------------
    def _render_owasp_coverage(self, pdf: FPDF, eval_results: dict):
        if pdf.get_y() > pdf.h - 70:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 12, "OWASP LLM/ASI Tag Coverage", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        owasp_tags = {
            "LLM01": "Prompt Injection / Jailbreak",
            "LLM02": "Insecure Output / Data Leakage",
            "LLM03": "Supply Chain Vulnerabilities",
            "LLM06": "Excessive Agency",
            "LLM09": "Misinformation",
            "ASI01": "Memory Poisoning",
            "ASI04": "Goal Hijacking / CoT Exploitation",
            "ASI08": "MCP Supply Chain",
        }

        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(*COLOR_TABLE_HEADER)
        pdf.set_text_color(*COLOR_WHITE)
        pdf.cell(28, 9, "Tag", border=1, fill=True, align="C")
        pdf.cell(90, 9, "Description", border=1, fill=True, align="C")
        pdf.cell(32, 9, "Status", border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for tag, desc in owasp_tags.items():
            pdf.set_text_color(*COLOR_PRIMARY)
            pdf.set_fill_color(*COLOR_LIGHT_BG)
            pdf.cell(28, 8, tag, border=1, fill=True, align="C")
            pdf.cell(90, 8, desc, border=1, fill=True)
            pdf.set_text_color(*COLOR_SUCCESS)
            pdf.cell(32, 8, "Covered", border=1, fill=True, align="C")
            pdf.ln()

        pdf.ln(10)

    # ------------------------------------------------------------------
    # Methodology section
    # ------------------------------------------------------------------
    @staticmethod
    def _render_methodology(pdf: FPDF):
        if pdf.get_y() > pdf.h - 90:
            pdf.add_page()

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*COLOR_PRIMARY)
        pdf.cell(0, 12, "Methodology", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*COLOR_PRIMARY)

        methodology_text = (
            "This evaluation was conducted using the EthicsGuard v0.4 evaluation "
            "harness. Each prompt from the attack dataset is submitted to the target "
            "system, and the response is classified as blocked or allowed. Results "
            "are compared against ground-truth labels to compute confusion matrix "
            "metrics.\n\n"
            "Metrics computed:\n"
            "  - ASR (Attack Success Rate): Fraction of adversarial prompts that "
            "bypassed the guardrail.\n"
            "  - FPR (False Positive Rate): Fraction of benign prompts incorrectly "
            "blocked.\n"
            "  - FNR (False Negative Rate): Equivalent to ASR for attack prompts.\n"
            "  - P95 Latency: 95th percentile end-to-end response time.\n\n"
            "Baseline systems (OpenAI Moderation, GPT-4o raw, LlamaGuard 3) are "
            "simulated using published benchmark data and stochastic modeling to "
            "provide representative comparisons. For production audits, live API "
            "calls should be used.\n\n"
            "The attack dataset covers OWASP LLM Top 10 (2025) and the emerging "
            "OWASP Agentic Security Initiatives (ASI) taxonomy, including novel "
            "2026 vectors such as MCP supply-chain attacks, chain-of-thought "
            "exploitation, and memory poisoning.\n\n"
            "deepeval framework metrics (HarmfulnessMetric, BiasMetric, "
            "ToxicityMetric) are optionally run as a secondary analysis pass."
        )

        pdf.multi_cell(0, 5.5, methodology_text)
        pdf.ln(8)

        # Footer
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(
            0,
            5,
            "EthicsGuard v0.4 | Confidential Evaluation Report",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )
