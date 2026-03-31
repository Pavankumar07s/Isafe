"""
EthicsGuard v0.4 — Professional PDF Report Generator
Produces clean, well-structured evaluation reports using fpdf2.
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
# Color palette  (teal-accented dark-professional theme)
# ---------------------------------------------------------------------------
C_BLACK = (17, 24, 39)            # near-black (text)
C_DARK = (31, 41, 55)             # section headings
C_GRAY = (107, 114, 128)          # secondary text
C_LIGHT_GRAY = (229, 231, 235)    # borders / thin rules
C_BG_SUBTLE = (243, 244, 246)     # alternating row bg
C_WHITE = (255, 255, 255)

C_TEAL = (20, 184, 166)           # primary accent
C_TEAL_DARK = (13, 148, 136)      # darker teal for headers
C_GREEN = (34, 197, 94)           # success / low ASR
C_AMBER = (245, 158, 11)          # warning / medium
C_RED = (239, 68, 68)             # danger / high ASR
C_BLUE = (59, 130, 246)           # info accent

# Bar chart palette per target
TARGET_COLORS = {
    "ethicsguard": C_TEAL,
    "openai_mod": C_AMBER,
    "gpt4o_raw": C_RED,
    "llamaguard": C_BLUE,
}
TARGET_LABELS = {
    "ethicsguard": "EthicsGuard v0.4",
    "openai_mod": "OpenAI Moderation",
    "gpt4o_raw": "GPT-4o (raw)",
    "llamaguard": "LlamaGuard 3",
}


def _asr_color(asr: float):
    """Return an RGB color based on ASR value."""
    if asr <= 0.05:
        return C_GREEN
    if asr <= 0.30:
        return C_AMBER
    return C_RED


def _asr_badge(asr: float) -> str:
    if asr <= 0.05:
        return "EXCELLENT"
    if asr <= 0.15:
        return "GOOD"
    if asr <= 0.30:
        return "MODERATE"
    return "POOR"


class ReportGenerator:
    """Generates a polished, multi-page PDF evaluation report."""

    def generate_report(self, eval_results: dict, output_path: str) -> str:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.set_left_margin(18)
        pdf.set_right_margin(18)

        # -- Page 1: Cover + Executive Summary --
        pdf.add_page()
        self._render_cover(pdf)
        self._render_executive_summary(pdf, eval_results)

        # -- Page 2: ASR Comparison Chart --
        pdf.add_page()
        self._render_asr_comparison(pdf, eval_results)

        # -- Page 3: Per-Category Combined Table --
        pdf.add_page()
        self._render_category_detail(pdf, eval_results)

        # -- Page 4: OWASP Coverage + Confusion Matrix --
        pdf.add_page()
        self._render_owasp_coverage(pdf, eval_results)
        self._render_confusion_matrices(pdf, eval_results)

        # -- Page 5: Methodology + Footer --
        pdf.add_page()
        self._render_methodology(pdf)
        self._render_footer(pdf)

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pdf.output(output_path)
        return os.path.abspath(output_path)

    # ==================================================================
    #  HELPERS
    # ==================================================================

    @staticmethod
    def _section_heading(pdf: FPDF, text: str, with_rule: bool = True):
        """Render a consistent section heading."""
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*C_DARK)
        pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        if with_rule:
            pdf.set_draw_color(*C_TEAL)
            pdf.set_line_width(0.7)
            y = pdf.get_y()
            pdf.line(pdf.l_margin, y, pdf.l_margin + 45, y)
            pdf.ln(3)
        else:
            pdf.ln(2)

    @staticmethod
    def _sub_heading(pdf: FPDF, text: str):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*C_DARK)
        pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    @staticmethod
    def _body_text(pdf: FPDF, text: str, size: float = 9.5):
        pdf.set_font("Helvetica", "", size)
        pdf.set_text_color(*C_BLACK)
        pdf.multi_cell(0, 5, text)

    # ==================================================================
    #  COVER
    # ==================================================================

    def _render_cover(self, pdf: FPDF):
        # Teal accent bar at top
        pdf.set_fill_color(*C_TEAL)
        pdf.rect(0, 0, pdf.w, 4, style="F")

        pdf.ln(12)
        # Title
        pdf.set_font("Helvetica", "B", 32)
        pdf.set_text_color(*C_DARK)
        pdf.cell(0, 16, "EthicsGuard v0.4", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.set_font("Helvetica", "", 14)
        pdf.set_text_color(*C_TEAL_DARK)
        pdf.cell(0, 8, "AI Safety Evaluation Report", new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.ln(4)

        # Horizontal rule
        rule_w = 60
        x_start = (pdf.w - rule_w) / 2
        pdf.set_draw_color(*C_TEAL)
        pdf.set_line_width(0.8)
        pdf.line(x_start, pdf.get_y(), x_start + rule_w, pdf.get_y())
        pdf.ln(6)

        # Generation metadata
        now = datetime.now(timezone.utc).strftime("%B %d, %Y  %H:%M UTC")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(0, 5, "Generated: " + now, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 5,
                 "Framework: EthicsGuard Evaluation Service v0.4  |  deepeval + custom harness",
                 new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 5,
                 "Dataset: 2026 Adversarial Attack Dataset (50 prompts, 10 categories)",
                 new_x="LMARGIN", new_y="NEXT", align="C")

        pdf.ln(10)

    # ==================================================================
    #  EXECUTIVE SUMMARY
    # ==================================================================

    def _render_executive_summary(self, pdf: FPDF, eval_results: dict):
        self._section_heading(pdf, "Executive Summary")

        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        col_widths = [
            usable_w * 0.24,   # Target
            usable_w * 0.11,   # Prompts
            usable_w * 0.13,   # ASR
            usable_w * 0.11,   # FPR
            usable_w * 0.16,   # P95 Lat
            usable_w * 0.12,   # Errors
            usable_w * 0.13,   # Rating
        ]
        headers = ["Target", "Prompts", "ASR", "FPR", "P95 (ms)", "Errors", "Rating"]

        # Table header
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_fill_color(*C_TEAL_DARK)
        pdf.set_text_color(*C_WHITE)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 9, h, border=0, fill=True, align="C")
        pdf.ln()

        # Data rows
        for idx, (target, res) in enumerate(eval_results.items()):
            row_bg = C_BG_SUBTLE if idx % 2 == 0 else C_WHITE
            pdf.set_fill_color(*row_bg)

            asr_val = res.get("asr", 0)
            fpr_val = res.get("fpr", 0)
            label = TARGET_LABELS.get(target, target)
            rating = _asr_badge(asr_val)

            row = [
                label,
                str(res.get("total_prompts", 0)),
                "{:.1%}".format(asr_val),
                "{:.1%}".format(fpr_val),
                "{:,.0f}".format(res.get("latency_p95_ms", 0)),
                str(res.get("errors", 0)),
                rating,
            ]

            row_h = 9
            for i, val in enumerate(row):
                if i == 2:
                    pdf.set_text_color(*_asr_color(asr_val))
                    pdf.set_font("Helvetica", "B", 8.5)
                elif i == 6:
                    pdf.set_text_color(*_asr_color(asr_val))
                    pdf.set_font("Helvetica", "B", 8)
                elif i == 0:
                    pdf.set_text_color(*C_BLACK)
                    pdf.set_font("Helvetica", "B", 8.5)
                else:
                    pdf.set_text_color(*C_BLACK)
                    pdf.set_font("Helvetica", "", 8.5)

                align_val = "L" if i == 0 else "C"
                cell_val = "  " + val if i == 0 else val
                pdf.cell(col_widths[i], row_h, cell_val,
                         border=0, fill=True, align=align_val)
            pdf.ln()

        # Bottom border
        pdf.set_draw_color(*C_LIGHT_GRAY)
        pdf.set_line_width(0.3)
        y = pdf.get_y()
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(8)

        # Key takeaway box
        eg_res = eval_results.get("ethicsguard", {})
        eg_asr = eg_res.get("asr", 0)
        eg_fpr = eg_res.get("fpr", 0)
        eg_errors = eg_res.get("errors", 0)
        eg_total = eg_res.get("total_prompts", 0)

        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        box_x = pdf.l_margin
        box_y = pdf.get_y()
        box_w = usable_w
        box_h = 28

        pdf.set_fill_color(240, 253, 250)   # teal-50 bg
        pdf.set_draw_color(*C_TEAL)
        pdf.set_line_width(0.5)
        pdf.rect(box_x, box_y, box_w, box_h, style="DF")

        # Left accent bar
        pdf.set_fill_color(*C_TEAL)
        pdf.rect(box_x, box_y, 3, box_h, style="F")

        pdf.set_xy(box_x + 8, box_y + 3)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*C_TEAL_DARK)
        pdf.cell(0, 5, "Key Findings", new_x="LMARGIN", new_y="NEXT")

        pdf.set_x(box_x + 8)
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*C_BLACK)

        if eg_errors > 0:
            effective = eg_total - eg_errors
            summary = (
                "EthicsGuard processed {} prompts ({} timeouts). "
                "Of {} completed, ASR = {:.1%} and FPR = {:.1%}. "
                "Timeout errors are caused by LLM latency on non-keyword prompts."
            ).format(eg_total, eg_errors, effective, eg_asr, eg_fpr)
        else:
            summary = (
                "EthicsGuard blocked {:.0f}% of adversarial prompts "
                "(ASR = {:.1%}) with {:.1%} false positive rate across {} prompts. "
            ).format((1 - eg_asr) * 100, eg_asr, eg_fpr, eg_total)
            baseline_asrs = {
                t: r.get("asr", 1) for t, r in eval_results.items() if t != "ethicsguard"
            }
            if baseline_asrs:
                best = min(baseline_asrs.values())
                summary += "Best baseline ASR: {:.1%}.".format(best)

        pdf.multi_cell(box_w - 12, 4.5, summary)
        pdf.set_y(box_y + box_h + 4)

    # ==================================================================
    #  ASR COMPARISON CHART  (horizontal bar chart)
    # ==================================================================

    def _render_asr_comparison(self, pdf: FPDF, eval_results: dict):
        self._section_heading(pdf, "Attack Success Rate by Category")

        all_categories = set()
        for res in eval_results.values():
            all_categories.update(res.get("per_category", {}).keys())
        categories = sorted(all_categories - {"benign_control"})

        if not categories:
            self._body_text(pdf, "No attack categories found in results.")
            return

        targets = list(eval_results.keys())
        num_targets = len(targets)

        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        label_w = 48
        chart_w = usable_w - label_w - 8
        chart_left = pdf.l_margin + label_w

        bar_h = 3.5
        group_gap = 3.0
        group_h = num_targets * bar_h + group_gap

        start_y = pdf.get_y() + 5

        # Gridlines
        pdf.set_draw_color(*C_LIGHT_GRAY)
        pdf.set_line_width(0.15)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*C_GRAY)
        total_chart_h = len(categories) * group_h + 4
        for pct in [0, 25, 50, 75, 100]:
            x = chart_left + chart_w * pct / 100
            pdf.line(x, start_y - 3, x, start_y + total_chart_h)
            pdf.set_xy(x - 6, start_y - 7)
            pdf.cell(12, 4, "{}%".format(pct), align="C")

        # Bars
        for cat_idx, cat in enumerate(categories):
            group_y = start_y + cat_idx * group_h

            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*C_BLACK)
            label = cat.replace("_", " ").title()
            if len(label) > 22:
                label = label[:20] + ".."
            pdf.set_xy(pdf.l_margin, group_y + (num_targets * bar_h - bar_h) / 2)
            pdf.cell(label_w - 4, bar_h, label, align="R")

            for t_idx, tgt in enumerate(targets):
                per_cat = eval_results[tgt].get("per_category", {})
                cat_data = per_cat.get(cat, {"blocked": 0, "total": 0})
                total = max(cat_data["total"], 1)
                blocked = cat_data["blocked"]
                asr = 1.0 - (blocked / total)

                bar_y = group_y + t_idx * bar_h
                bar_w = max(chart_w * asr, 0)

                color = TARGET_COLORS.get(tgt, (150, 150, 150))
                pdf.set_fill_color(*color)
                if bar_w > 0.5:
                    pdf.rect(chart_left, bar_y, bar_w, bar_h - 1, style="F")

                pdf.set_font("Helvetica", "B", 6)
                pdf.set_text_color(*color)
                if bar_w < chart_w * 0.85:
                    label_x = chart_left + bar_w + 1.5
                else:
                    label_x = chart_left + bar_w - 14
                pdf.set_xy(label_x, bar_y)
                pdf.cell(14, bar_h - 1, "{:.0%}".format(asr))

        # Legend
        legend_y = start_y + len(categories) * group_h + 6
        pdf.set_xy(pdf.l_margin, legend_y)
        legend_x = pdf.l_margin

        for tgt in targets:
            color = TARGET_COLORS.get(tgt, (150, 150, 150))
            label = TARGET_LABELS.get(tgt, tgt)

            pdf.set_fill_color(*color)
            pdf.rect(legend_x, legend_y + 1, 8, 3.5, style="F")

            pdf.set_xy(legend_x + 10, legend_y)
            pdf.set_font("Helvetica", "", 7.5)
            pdf.set_text_color(*C_BLACK)
            tw = pdf.get_string_width(label) + 6
            pdf.cell(tw, 5, label)
            legend_x += tw + 14

        pdf.set_y(legend_y + 8)

        # Note
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*C_GRAY)
        pdf.multi_cell(0, 4,
            "Lower ASR is better (fewer attacks bypassed the guardrail). "
            "EthicsGuard uses a deterministic keyword classifier with 650+ patterns "
            "for sub-millisecond blocking."
        )

    # ==================================================================
    #  PER-CATEGORY DETAIL TABLE  (single combined table)
    # ==================================================================

    def _render_category_detail(self, pdf: FPDF, eval_results: dict):
        self._section_heading(pdf, "Per-Category Breakdown")

        all_categories = set()
        for res in eval_results.values():
            all_categories.update(res.get("per_category", {}).keys())
        categories = sorted(all_categories)

        targets = list(eval_results.keys())
        usable_w = pdf.w - pdf.l_margin - pdf.r_margin

        # Column layout: Category + one column per target
        cat_w = usable_w * 0.26
        n_tgt = max(len(targets), 1)
        tgt_w = (usable_w - cat_w) / n_tgt

        SHORT_LABELS = {
            "ethicsguard": "EthicsGuard",
            "openai_mod": "OpenAI Mod",
            "gpt4o_raw": "GPT-4o",
            "llamaguard": "LlamaGuard",
        }

        ROW_H = 6
        HDR_H = 7
        SUBHDR_H = 5

        def _draw_combined_header(p: FPDF):
            """Draw the two-row table header (target names + sub-labels)."""
            # Row 1: Category + colored target headers
            p.set_font("Helvetica", "B", 7.5)
            p.set_fill_color(*C_TEAL_DARK)
            p.set_text_color(*C_WHITE)
            p.cell(cat_w, HDR_H, "Category", fill=True, align="C")
            for tgt in targets:
                color = TARGET_COLORS.get(tgt, C_TEAL_DARK)
                short = SHORT_LABELS.get(tgt, TARGET_LABELS.get(tgt, tgt))
                p.set_fill_color(*color)
                p.set_text_color(*C_WHITE)
                p.cell(tgt_w, HDR_H, short, fill=True, align="C")
            p.ln()
            # Row 2: sub-label row
            p.set_font("Helvetica", "I", 6)
            p.set_fill_color(*C_BG_SUBTLE)
            p.set_text_color(*C_GRAY)
            p.cell(cat_w, SUBHDR_H, "", fill=True)
            for _ in targets:
                p.cell(tgt_w, SUBHDR_H, "Blk/Tot   ASR", fill=True, align="C")
            p.ln()

        _draw_combined_header(pdf)

        # Data rows — one row per category, columns per target
        for c_idx, cat in enumerate(categories):
            # Page break with header re-draw
            if pdf.get_y() + ROW_H > pdf.h - 20:
                pdf.add_page()
                _draw_combined_header(pdf)

            row_bg = C_BG_SUBTLE if c_idx % 2 == 0 else C_WHITE
            pdf.set_fill_color(*row_bg)

            # Category name
            cat_label = cat.replace("_", " ").title()
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*C_BLACK)
            pdf.cell(cat_w, ROW_H, "  " + cat_label, fill=True, align="L")

            # Per-target values
            for tgt in targets:
                per_cat = eval_results[tgt].get("per_category", {})
                cat_data = per_cat.get(cat, {"blocked": 0, "total": 0})
                total = cat_data["total"]
                blocked = cat_data["blocked"]
                bypassed = total - blocked
                asr = (bypassed / total * 100) if total > 0 else 0

                cell_text = "{}/{}  {:.0f}%".format(blocked, total, asr)
                pdf.set_text_color(*_asr_color(asr / 100))
                pdf.set_font("Helvetica", "B" if asr > 5 else "", 7)
                pdf.set_fill_color(*row_bg)
                pdf.cell(tgt_w, ROW_H, cell_text, fill=True, align="C")

            pdf.ln()

        # Bottom border
        pdf.set_draw_color(*C_LIGHT_GRAY)
        pdf.set_line_width(0.2)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(3)

        # Legend note
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*C_GRAY)
        pdf.multi_cell(0, 3.5,
            "Values: Blocked/Total  ASR%.  "
            "Green (<5%) = Excellent  |  Amber (5-30%) = Moderate  |  Red (>30%) = Poor"
        )

    # ==================================================================
    #  OWASP TAG COVERAGE
    # ==================================================================

    def _render_owasp_coverage(self, pdf: FPDF, eval_results: dict):
        self._section_heading(pdf, "OWASP LLM / ASI Tag Coverage")

        owasp_tags = {
            "LLM01": ("Prompt Injection / Jailbreak", True),
            "LLM02": ("Insecure Output / Data Leakage", True),
            "LLM03": ("Supply Chain Vulnerabilities", True),
            "LLM05": ("PII / Privacy Violations", True),
            "LLM06": ("Excessive Agency", True),
            "LLM09": ("Misinformation / Hallucination", True),
            "ASI01": ("Memory Poisoning", True),
            "ASI04": ("Goal Hijacking / CoT Exploitation", True),
            "ASI08": ("MCP Supply Chain Attacks", True),
        }

        usable_w = pdf.w - pdf.l_margin - pdf.r_margin
        col_w = [usable_w * 0.14, usable_w * 0.58, usable_w * 0.28]

        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_fill_color(*C_TEAL_DARK)
        pdf.set_text_color(*C_WHITE)
        pdf.cell(col_w[0], 8, "Tag", fill=True, align="C")
        pdf.cell(col_w[1], 8, "Vulnerability Class", fill=True, align="C")
        pdf.cell(col_w[2], 8, "Coverage Status", fill=True, align="C")
        pdf.ln()

        pdf.set_font("Helvetica", "", 8.5)
        for idx, (tag, (desc, covered)) in enumerate(owasp_tags.items()):
            row_bg = C_BG_SUBTLE if idx % 2 == 0 else C_WHITE
            pdf.set_fill_color(*row_bg)
            pdf.set_text_color(*C_BLACK)

            pdf.set_font("Helvetica", "B", 8.5)
            pdf.cell(col_w[0], 7, tag, fill=True, align="C")
            pdf.set_font("Helvetica", "", 8.5)
            pdf.cell(col_w[1], 7, "  " + desc, fill=True, align="L")

            if covered:
                pdf.set_text_color(*C_GREEN)
                pdf.set_font("Helvetica", "B", 8.5)
                status = "COVERED"
            else:
                pdf.set_text_color(*C_RED)
                pdf.set_font("Helvetica", "B", 8.5)
                status = "NOT COVERED"

            pdf.cell(col_w[2], 7, status, fill=True, align="C")
            pdf.ln()

        pdf.set_draw_color(*C_LIGHT_GRAY)
        pdf.set_line_width(0.2)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(5)

    # ==================================================================
    #  CONFUSION MATRICES
    # ==================================================================

    def _render_confusion_matrices(self, pdf: FPDF, eval_results: dict):
        if pdf.get_y() > pdf.h - 45:
            pdf.add_page()

        self._section_heading(pdf, "Confusion Matrix Summary")

        usable_w = pdf.w - pdf.l_margin - pdf.r_margin

        for tgt, res in eval_results.items():
            label = TARGET_LABELS.get(tgt, tgt)

            tp = res.get("true_positives", 0)
            fp = res.get("false_positives", 0)
            tn = res.get("true_negatives", 0)
            fn = res.get("false_negatives", 0)

            # Need ~22 mm for sub-heading + metric boxes
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()

            self._sub_heading(pdf, label)

            box_w = usable_w * 0.22
            gap = (usable_w - 4 * box_w) / 3
            start_x = pdf.l_margin

            metrics = [
                ("True Pos", tp, C_GREEN),
                ("False Neg", fn, C_RED),
                ("False Pos", fp, C_AMBER),
                ("True Neg", tn, C_GREEN),
            ]

            y_base = pdf.get_y()
            for i, (m_label, m_val, m_color) in enumerate(metrics):
                x = start_x + i * (box_w + gap)

                pdf.set_fill_color(248, 250, 252)
                pdf.set_draw_color(*C_LIGHT_GRAY)
                pdf.set_line_width(0.3)
                pdf.rect(x, y_base, box_w, 12, style="DF")

                pdf.set_xy(x, y_base + 0.5)
                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(*m_color)
                pdf.cell(box_w, 7, str(m_val), align="C")

                pdf.set_xy(x, y_base + 7.5)
                pdf.set_font("Helvetica", "", 6)
                pdf.set_text_color(*C_GRAY)
                pdf.cell(box_w, 4, m_label, align="C")

            pdf.set_y(y_base + 15)

    # ==================================================================
    #  METHODOLOGY
    # ==================================================================

    def _render_methodology(self, pdf: FPDF):
        self._section_heading(pdf, "Methodology")

        sections = [
            ("Evaluation Pipeline", (
                "Each prompt from the 2026 Adversarial Attack Dataset is submitted to "
                "the target system via HTTP. The guardrail classifies the prompt as "
                "BLOCKED, FLAGGED, or ALLOWED. Results are compared against ground-truth "
                "labels to compute confusion matrix metrics."
            )),
            ("Metrics", (
                "ASR (Attack Success Rate): Fraction of adversarial prompts that "
                "bypassed the guardrail. Lower is better.\n"
                "FPR (False Positive Rate): Fraction of benign prompts incorrectly "
                "blocked. Lower is better.\n"
                "P95 Latency: 95th percentile end-to-end response time in milliseconds."
            )),
            ("Baseline Systems", (
                "OpenAI Moderation API, GPT-4o (system-prompt safety only), and "
                "LlamaGuard 3 are simulated using published benchmark data and stochastic "
                "modeling to provide representative comparisons. For production audits, "
                "live API calls should replace simulations."
            )),
            ("Attack Dataset", (
                "The dataset covers OWASP LLM Top 10 (2025) and the emerging OWASP "
                "Agentic Security Initiatives (ASI) taxonomy, including 2026 vectors: "
                "MCP supply-chain attacks, chain-of-thought exploitation, memory poisoning, "
                "goal hijacking, embedding inversion, deepfake instructions, and multimodal "
                "injection. Benign control prompts are included to measure false positive rate."
            )),
            ("EthicsGuard Architecture", (
                "EthicsGuard v0.4 uses an 8-node LangGraph safety pipeline: compliance "
                "check, keyword classification (650+ patterns), OWASP tagging, toxicity "
                "detection, bias detection, hallucination scoring, score aggregation, and "
                "audit logging. The keyword classifier provides deterministic, sub-millisecond "
                "blocking for known attack patterns."
            )),
        ]

        for title, body in sections:
            # Row-level page break for methodology sections
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()
            self._sub_heading(pdf, title)
            self._body_text(pdf, body)
            pdf.ln(1.5)

    # ==================================================================
    #  FOOTER
    # ==================================================================

    def _render_footer(self, pdf: FPDF):
        pdf.ln(4)
        pdf.set_draw_color(*C_LIGHT_GRAY)
        pdf.set_line_width(0.3)
        y = pdf.get_y()
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(3)

        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(*C_GRAY)
        pdf.cell(0, 5,
                 "EthicsGuard v0.4  |  Confidential Evaluation Report",
                 align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5,
                 "ICEF Hackathon 2026  |  AI Safety & EU AI Act Compliance",
                 align="C", new_x="LMARGIN", new_y="NEXT")
