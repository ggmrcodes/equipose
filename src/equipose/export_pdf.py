"""Patient progress report (PDF).

A light, printable clinical artifact built with reportlab + matplotlib. Pure:
all data is passed in (no DB), so it is unit-testable and returns PDF bytes for
a Streamlit download. No child images -> de-identified by construction (patient
code only). See docs/superpowers/specs/2026-06-21-pdf-export-design.md.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Optional

from equipose.config import ThresholdConfig
from equipose.schemas import PatientRecord

# light, printable palette (deep dusty-rose accent; status tuned for white)
INK = "#1F2933"
SLATE = "#52606D"
MUTE = "#7B8794"
LINE = "#CBD5E1"
ACCENT = "#B6446A"           # deep dusty rose, readable on white
GOOD = "#15803D"
AMBER = "#B45309"
CONCERN = "#B42318"
_BAND_HEX = {"green": GOOD, "yellow": AMBER, "red": CONCERN}
_BAND_LABEL = {"green": "Good", "yellow": "Watch", "red": "Concern"}


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _in_range(v: float, lo: float, hi: float) -> bool:
    return lo <= v <= hi


def _pretty(name: str) -> str:
    return name.replace("_", " ")


# ---- plain-language summary ------------------------------------------------
def _summary(patient: PatientRecord, view: str, sessions: list[dict],
             series: dict, thresholds: ThresholdConfig) -> str:
    code = patient.patient_id
    n = len(sessions)
    if n == 1:
        d = sessions[0]["captured_at"][:10]
        return (f"A single {view} reading on {d}. Trends appear after the next visit. "
                f"These are provisional, screening-only measures, not a diagnosis.")

    d0, d1 = sessions[0]["captured_at"][:10], sessions[-1]["captured_at"][:10]
    s0, s1 = sessions[0]["overall_score"], sessions[-1]["overall_score"]
    delta = s1 - s0
    direction = "improved" if delta > 5 else "declined" if delta < -5 else "held steady"

    moved_in = []
    for name, hist in series.items():
        if len(hist) < 2 or name not in thresholds.metrics:
            continue
        lo, hi = thresholds.acceptable_range(name)
        if not _in_range(hist[0][1], lo, hi) and _in_range(hist[-1][1], lo, hi):
            moved_in.append(_pretty(name))

    parts = [f"Across {n} {view} readings ({d0} to {d1}), {code}'s overall posture "
             f"score moved from {s0:.0f} to {s1:.0f} ({direction})."]
    if moved_in:
        names = ", ".join(moved_in[:3])
        more = f", and {len(moved_in) - 3} more" if len(moved_in) > 3 else ""
        parts.append(f"{len(moved_in)} measure(s) moved into their acceptable range, "
                     f"including {names}{more}.")
    parts.append("These are provisional, screening-only measures (2D estimates), not a diagnosis.")
    return " ".join(parts)


# ---- matplotlib charts (light) --------------------------------------------
def _fig_png(fig) -> bytes:
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return buf.getvalue()


def _style_axes(ax):
    ax.set_facecolor("white")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(LINE)
    ax.tick_params(colors=SLATE, labelsize=8)
    ax.grid(True, color=LINE, linewidth=0.6, linestyle=(0, (2, 3)), alpha=0.7)


def _date_ticks(ax, xs):
    """Tick only at the actual reading dates, short-formatted, no overlap."""
    import matplotlib.dates as mdates

    ax.set_xticks(xs)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    if len(xs) > 6:
        for lbl in ax.get_xticklabels():
            lbl.set_rotation(30)
            lbl.set_ha("right")


def _overall_chart_png(sessions: list[dict]) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt

    xs = [_dt(s["captured_at"]) for s in sessions]
    ys = [s["overall_score"] for s in sessions]
    fig, ax = plt.subplots(figsize=(6.6, 2.2))
    _style_axes(ax)
    ax.plot(xs, ys, color=ACCENT, linewidth=2.2, marker="o", markersize=5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("score / 100", color=SLATE, fontsize=8)
    _date_ticks(ax, xs)
    fig.tight_layout()
    return _fig_png(fig)


def _metrics_grid_png(names: list[str], series: dict, thresholds: ThresholdConfig) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = [n for n in names if series.get(n)]
    if not metrics:
        return b""
    ncol = 2
    nrow = (len(metrics) + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(6.6, 1.7 * nrow), squeeze=False)
    for i, name in enumerate(metrics):
        ax = axes[i // ncol][i % ncol]
        _style_axes(ax)
        hist = series[name]
        xs = [_dt(t) for t, _ in hist]
        ys = [v for _, v in hist]
        if name in thresholds.metrics:
            lo, hi = thresholds.acceptable_range(name)
            ax.axhspan(lo, hi, color=GOOD, alpha=0.12)
        ax.plot(xs, ys, color=ACCENT, linewidth=1.8, marker="o", markersize=4)
        ax.set_title(_pretty(name), color=INK, fontsize=9, loc="left")
        _date_ticks(ax, xs)
        ax.tick_params(labelbottom=(i // ncol == nrow - 1))
    # hide any unused cells
    for j in range(len(metrics), nrow * ncol):
        axes[j // ncol][j % ncol].axis("off")
    fig.tight_layout()
    return _fig_png(fig)


# ---- PDF assembly ---------------------------------------------------------
def build_progress_pdf(patient: PatientRecord, view: str, sessions: list[dict],
                       series: dict, thresholds: ThresholdConfig,
                       generated_at: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (HRFlowable, Image, Paragraph, SimpleDocTemplate,
                                    Spacer, Table, TableStyle)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.8 * inch,
                            bottomMargin=0.7 * inch, leftMargin=0.9 * inch,
                            rightMargin=0.9 * inch, title="equipose progress report")
    H = ParagraphStyle("H", fontName="Helvetica-Bold", fontSize=20, textColor=colors.HexColor(INK),
                       spaceAfter=2, leading=23)
    sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=9.5, textColor=colors.HexColor(SLATE),
                         spaceAfter=2)
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=10.5, textColor=colors.HexColor(INK),
                          leading=15, alignment=TA_LEFT)
    h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, textColor=colors.HexColor(ACCENT),
                        spaceBefore=14, spaceAfter=6)
    foot = ParagraphStyle("foot", fontName="Helvetica", fontSize=8, textColor=colors.HexColor(MUTE),
                          leading=11)

    d0 = sessions[0]["captured_at"][:10]
    d1 = sessions[-1]["captured_at"][:10]
    span = d0 if d0 == d1 else f"{d0} to {d1}"
    latest = sessions[-1]

    story = []
    story.append(Paragraph('equi<font color="%s">pose</font>  Posture Progress Report' % ACCENT, H))
    story.append(Paragraph(
        f'Patient <b>{patient.patient_id}</b> &nbsp;|&nbsp; age {patient.age_years} &nbsp;|&nbsp; '
        f'GMFCS {patient.gmfcs_level} &nbsp;|&nbsp; {view} view &nbsp;|&nbsp; {span} &nbsp;|&nbsp; '
        f'generated {generated_at[:10]}', sub))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.4, color=colors.HexColor(ACCENT)))
    story.append(Spacer(1, 8))

    story.append(Paragraph(_summary(patient, view, sessions, series, thresholds), body))

    # overview line
    band_txt = (f'<font color="{_BAND_HEX[latest["band"]]}"><b>{latest["overall_score"]:.0f}/100 '
                f'({_BAND_LABEL[latest["band"]]})</b></font>')
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f'Readings: <b>{len(sessions)}</b> &nbsp;&nbsp; Latest score: {band_txt}', body))

    story.append(Paragraph("Overall score", h2))
    story.append(Image(BytesIO(_overall_chart_png(sessions)), width=6.6 * inch, height=2.2 * inch))

    grid = _metrics_grid_png(list(series.keys()), series, thresholds)
    if grid:
        nrow = (len([n for n in series if series.get(n)]) + 1) // 2
        story.append(Paragraph("By metric (acceptable range shaded)", h2))
        story.append(Image(BytesIO(grid), width=6.6 * inch, height=1.7 * nrow * inch))

    story.append(Paragraph("History", h2))
    rows = [["Date", "Type", "Score", "Status"]]
    for s in reversed(sessions):
        rows.append([s["captured_at"][:16].replace("T", " "),
                     "Photo" if s.get("kind") == "snapshot" else "Video",
                     f'{s["overall_score"]:.0f}', _BAND_LABEL.get(s["band"], s["band"])])
    table = Table(rows, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(INK)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(LINE)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F3EF")]),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(INK)),
    ]))
    story.append(table)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor(LINE)))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Acceptable ranges are provisional, pending pilot calibration; values are 2D projective "
        "approximations. equipose is a screening and tracking aid, not a diagnostic device. "
        "Generated locally; no data left this machine.", foot))

    doc.build(story)
    return buf.getvalue()
