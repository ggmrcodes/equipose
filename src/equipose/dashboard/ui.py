"""equipose dashboard design system — "graphite instrument" (Apple HIG).

A warm-charcoal dark workspace styled on Apple's Human Interface Guidelines:
the system San Francisco font stack with JetBrains Mono for numerals, a single
warm-bone emphasis tone (no pink), and posture status (sage/amber/clay) as the
only functional color. A faint architectural goniometer field fills the negative
space. SF is OS-provided (offline); JetBrains Mono is self-hosted at app/static.

Each component has a pure ``*_html`` builder (testable) and a thin render
wrapper that pushes it through ``st.markdown``.
"""
from __future__ import annotations

from equipose.dashboard import glyphs

# ---- palette (slate-light, cool — "graphite instrument, on paper") ----------
BG = "#E7EDEF"          # cool light ground
PANEL = "#FFFFFF"       # white card / surface fill
PANEL_HI = "#EDF2F4"    # elevated fill (selected segment, hover)
LINE = "rgba(12,16,19,0.10)"  # hairline separator (cool ink, low alpha)
TEXT = "#0C1013"        # near-black navy ink
SOFT = "#415A69"        # slate (secondary label)
MUTE = "#6E8794"        # muted slate (tertiary label)
ACCENT = "#415A69"      # slate-blue — the one emphasis tone
ACCENT_PRESS = "#354B58"  # pressed slate
BTN_INK = "#FFFFFF"     # white ink text on slate-filled buttons
AMBER_PROV = "#9A6A12"  # flags provisional/needs-literature ranges (ochre)

# posture status (darkened for AA on the light surface; each has a distinct glyph
# so it never relies on color alone — colorblind-safe)
_STATUS = {
    "green": ("Good", "#2E7D52", "", "✓"),
    "yellow": ("Watch", "#9A6A12", "", "◐"),
    "red": ("Concern", "#B0432A", "", "▲"),
}

_FONT_FACES = """
@font-face{font-family:'JBMono';font-weight:400;font-style:normal;font-display:swap;
  src:url('app/static/fonts/JetBrainsMono-400.woff2') format('woff2');}
@font-face{font-family:'JBMono';font-weight:500;font-style:normal;font-display:swap;
  src:url('app/static/fonts/JetBrainsMono-500.woff2') format('woff2');}
"""

CSS = f"""
<style>
{_FONT_FACES}
:root {{
  --bg:{BG}; --panel:{PANEL}; --panel-hi:{PANEL_HI}; --line:{LINE};
  --text:{TEXT}; --soft:{SOFT}; --mute:{MUTE};
  --accent:{ACCENT}; --accent-press:{ACCENT_PRESS}; --btn-ink:{BTN_INK};
  --font-ui:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",system-ui,sans-serif;
  --font-mono:ui-monospace,"SF Mono",Menlo,"JBMono",monospace;
  --radius:12px; --radius-sm:8px;
  --elev:0 1px 2px rgba(12,16,19,0.06), 0 10px 26px rgba(12,16,19,0.08);
}}

/* hide default Streamlit chrome (NOT the sidebar — we use it as a source list) */
header[data-testid="stHeader"] {{ background:transparent; height:0; }}
#MainMenu, footer {{ visibility:hidden; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none !important; }}

/* flat cool canvas */
.stApp {{ background:var(--bg); }}
.block-container {{ max-width:920px; padding-top:1.4rem; padding-bottom:5rem;
  position:relative; z-index:1; }}

/* ambient goniometer field (kept, neutral) */
.eq-field {{ position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; }}
.eq-field svg {{ width:100%; height:100%; display:block; }}

/* typography (San Francisco) */
html, body, .stApp, [class*="css"], input, textarea, button, select {{
  font-family:var(--font-ui); color:var(--text);
  -webkit-font-smoothing:antialiased; }}
h1,h2,h3,h4 {{ font-family:var(--font-ui); color:var(--text);
  letter-spacing:-0.021em; font-weight:700; }}
.eq-num {{ font-family:var(--font-mono); font-variant-numeric:tabular-nums; }}

/* ---- sidebar as macOS source list ---- */
section[data-testid="stSidebar"] {{ background:var(--panel);
  border-right:1px solid var(--line); width:232px !important; }}
section[data-testid="stSidebar"] > div {{ padding-top:2.4rem; }}
.eq-railhead {{ font-family:var(--font-mono); font-size:.66rem; letter-spacing:.14em;
  text-transform:uppercase; color:var(--mute); padding:0 .35rem .55rem; }}
.eq-srclist {{ display:flex; flex-direction:column; gap:.12rem; }}
.eq-srcrow {{ display:flex; align-items:center; gap:.6rem; padding:.5rem .55rem;
  border-radius:var(--radius-sm); color:var(--soft); font-size:.92rem; }}
.eq-srcrow.active {{ background:var(--panel-hi); color:var(--text); }}
.eq-srcdot {{ display:grid; place-items:center; width:1.5rem; height:1.5rem; border-radius:50%;
  background:rgba(12,16,19,0.05); color:var(--mute); font-family:var(--font-mono);
  font-size:.78rem; flex:0 0 auto; }}
.eq-srcrow.active .eq-srcdot {{ background:var(--accent); color:var(--btn-ink); }}
.eq-srcrow.done .eq-srcdot {{ background:rgba(46,125,82,0.15); color:#2E7D52; }}
.eq-srclabel {{ flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}

/* ---- toolbar header ---- */
.eq-head {{ display:flex; align-items:center; justify-content:space-between; gap:1rem;
  padding-bottom:.85rem; margin-bottom:1.1rem; border-bottom:1px solid var(--line); }}
.eq-brandrow {{ display:flex; align-items:center; gap:.1rem; }}
/* horse brand mark: black line-art PNG kept near-black so it reads as ink on the
   light surface. Served locally (app/static), no CDN. */
.eq-brandmark {{ width:26px; height:26px; margin-right:.5rem; vertical-align:-6px;
  filter:brightness(0) opacity(0.85); }}
.eq-word {{ font-size:1.18rem; font-weight:600; letter-spacing:-0.02em; }}
.eq-pchip {{ display:inline-flex; align-items:center; gap:.5rem; background:var(--panel);
  border:1px solid var(--line); border-radius:999px; padding:.3rem .75rem; font-size:.82rem; }}
.eq-pchip .k {{ color:var(--mute); font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; }}
.eq-pchip .v {{ font-family:var(--font-mono); color:var(--text); font-weight:500; }}

/* ---- Large Title section ---- */
.eq-eyebrow {{ font-family:var(--font-mono); font-size:.7rem; letter-spacing:.06em;
  color:var(--soft); margin:.2rem 0 .5rem; text-transform:none; }}
.eq-title {{ font-size:clamp(2rem, 1.5rem + 1.8vw, 2.7rem); font-weight:700;
  letter-spacing:-0.03em; line-height:1.05; margin:0 0 .4rem; }}
.eq-lead {{ color:var(--soft); font-size:1.02rem; margin:0 0 .2rem; max-width:62ch; line-height:1.5; }}

/* ---- buttons (macOS push-button) — cover regular, download AND form-submit ---- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
  border-radius:var(--radius-sm); border:1px solid var(--line); background:var(--panel-hi);
  color:var(--text); font-weight:500; padding:.5rem 1.05rem;
  transition:transform .06s ease, background .12s, border-color .12s; }}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{ background:#E3EAED; }}
.stButton > button:active, .stFormSubmitButton > button:active {{ transform:translateY(1px); }}
/* primary — incl. form-submit primary (Streamlit uses kind="primaryFormSubmit") so the
   dark bone-ink text applies and the label isn't washed out on the bone fill. */
button[kind="primary"], button[kind="primaryFormSubmit"],
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {{
  background:var(--accent); border-color:var(--accent); color:var(--btn-ink) !important; font-weight:600; }}
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {{
  background:var(--accent-press); border-color:var(--accent-press); }}
[data-testid="stWidgetLabel"] p {{ font-size:.82rem; color:var(--soft); font-weight:500; }}

/* inputs */
[data-baseweb="input"], [data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
  background:var(--panel) !important; border-radius:var(--radius-sm) !important; }}
[data-testid="stFileUploaderDropzone"] {{ background:var(--panel); border:1px dashed var(--line);
  border-radius:var(--radius); }}

/* ---- segmented control (radios) ---- */
div[role="radiogroup"] {{ gap:.2rem; background:var(--panel); padding:.22rem;
  border-radius:var(--radius-sm); border:1px solid var(--line); width:fit-content; }}
div[role="radiogroup"] > label {{ border:0; background:transparent; border-radius:6px;
  padding:.32rem .9rem; color:var(--soft); }}
div[role="radiogroup"] > label:has(input:checked) {{ background:var(--panel-hi); color:var(--text);
  box-shadow:0 1px 2px rgba(12,16,19,0.14); }}
div[role="radiogroup"] > label > div:first-child {{ display:none; }}

[data-testid="stDataFrame"] {{ border:1px solid var(--line); border-radius:var(--radius); }}

/* ---- inset grouped list (metrics) ---- */
.eq-group {{ background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
  overflow:hidden; }}
.eq-grow {{ display:flex; align-items:flex-start; justify-content:space-between; gap:1rem;
  padding:.8rem 1rem; border-bottom:1px solid var(--line); }}
.eq-grow:last-child {{ border-bottom:0; }}
.eq-gmain {{ display:flex; flex-wrap:wrap; align-items:center; gap:.5rem; }}
.eq-gname {{ font-weight:500; color:var(--text); }}
.eq-gsub {{ flex-basis:100%; color:var(--mute); font-size:.78rem; margin-top:.25rem;
  display:flex; gap:.5rem; align-items:center; }}
.eq-gtrail {{ display:flex; align-items:center; gap:.55rem; flex:0 0 auto; white-space:nowrap; }}
.eq-val {{ font-family:var(--font-mono); }}
.eq-val .u {{ color:var(--mute); font-size:.78rem; margin-left:.15rem; }}
.pct {{ color:var(--mute); font-size:.78rem; }}

/* ---- panels / surfaces ---- */
.eq-panel {{ background:var(--panel); border:1px solid var(--line); border-radius:var(--radius);
  padding:1.1rem 1.2rem; }}

/* ---- status chip ---- */
.eq-chip {{ display:inline-flex; align-items:center; gap:.4rem; font-size:.82rem; font-weight:600;
  white-space:nowrap; line-height:1.35; }}
.eq-chip .g {{ font-size:.82rem; line-height:1; }}
.eq-tier {{ display:inline-block; font-family:var(--font-mono); font-size:.62rem; letter-spacing:.06em;
  text-transform:uppercase; padding:.1rem .42rem; border-radius:5px; border:1px solid var(--line); color:var(--soft); }}
.eq-tier.best {{ color:var(--mute); border-style:dashed; }}

/* ---- score readout (flat, soft elevation) ---- */
.eq-score {{ display:flex; align-items:center; gap:1.3rem; background:var(--panel);
  border:1px solid var(--line); border-radius:16px; padding:1.3rem 1.5rem; box-shadow:var(--elev); }}
.eq-score .big {{ font-family:var(--font-mono); font-size:3.2rem; font-weight:500; line-height:.9;
  letter-spacing:-0.02em; color:var(--text); }}
.eq-score .den {{ color:var(--mute); font-size:1.05rem; font-family:var(--font-mono); }}
.eq-score .lbl {{ font-size:.82rem; letter-spacing:0; color:var(--soft); margin-bottom:.5rem; }}
.eq-score .eq-chip {{ font-size:1rem; }}
.eq-score .note {{ color:var(--soft); font-size:.9rem; margin-top:.5rem; }}
.eq-score .vr {{ width:1px; align-self:stretch; background:var(--line); }}
.eq-score .eq-dial {{ flex:0 0 auto; line-height:0; }}

/* ---- posture body-chart ---- */
.eq-postwrap {{ display:flex; gap:1.4rem; align-items:center; background:var(--panel);
  border:1px solid var(--line); border-radius:var(--radius); padding:1rem 1.3rem; }}
.eq-posture {{ flex:0 0 240px; line-height:0; }}
.eq-legendbox {{ display:flex; flex-direction:column; gap:.6rem; }}
.eq-leg {{ display:inline-flex; align-items:center; gap:.55rem; font-size:.82rem; color:var(--soft); }}
.eq-leg i {{ width:.72rem; height:.72rem; border-radius:50%; flex:0 0 auto; }}
.eq-leg .lab {{ font-family:var(--font-mono); font-size:.7rem; letter-spacing:.04em; }}
@media (max-width:680px) {{ .eq-postwrap {{ flex-direction:column; align-items:stretch; }}
  .eq-posture {{ flex:1 1 auto; }} }}

/* ---- score breakdown table (kept tabular) ---- */
.eq-table {{ width:100%; border-collapse:collapse; font-size:.9rem; }}
.eq-table thead th {{ text-align:left; font-family:var(--font-mono); font-size:.62rem; letter-spacing:.08em;
  text-transform:uppercase; color:var(--soft); font-weight:500; padding:.2rem .6rem .55rem; border-bottom:1px solid var(--line); }}
.eq-table thead th.num, .eq-table td.num {{ text-align:right; }}
.eq-table tbody td {{ padding:.62rem .6rem; border-bottom:1px solid var(--line); vertical-align:middle; }}
.eq-table tbody tr:last-child td {{ border-bottom:none; }}
.eq-table .mname {{ font-weight:500; color:var(--text); }}
.eq-table .val {{ font-family:var(--font-mono); }}
.eq-skip {{ font-family:var(--font-mono); font-size:.62rem; letter-spacing:.05em; text-transform:uppercase;
  color:var(--mute); margin-left:.5rem; }}
.eq-prov {{ font-family:var(--font-mono); font-size:.58rem; letter-spacing:.06em; text-transform:uppercase;
  color:{AMBER_PROV}; border:1px solid {AMBER_PROV}55; border-radius:5px; padding:.04rem .3rem; margin-left:.4rem;
  vertical-align:middle; cursor:help; }}
.eq-conf {{ display:inline-flex; align-items:center; gap:.5rem; }}
.eq-bar {{ width:52px; height:5px; border-radius:3px; background:rgba(12,16,19,0.08); overflow:hidden; }}
.eq-bar > i {{ display:block; height:100%; background:var(--accent); }}

/* ---- review overview ---- */
.eq-overview {{ display:flex; flex-wrap:wrap; gap:.7rem; }}
.eq-stat {{ flex:1 1 120px; background:var(--panel); border:1px solid var(--line);
  border-radius:var(--radius); padding:.7rem .85rem; }}
.eq-stat .k {{ font-family:var(--font-mono); font-size:.62rem; letter-spacing:.08em;
  text-transform:uppercase; color:var(--mute); margin-bottom:.35rem; }}
.eq-stat .v {{ font-size:1.4rem; font-weight:600; color:var(--text); display:flex;
  align-items:center; gap:.45rem; }}

.eq-disc {{ color:var(--mute); font-size:.8rem; border-left:2px solid var(--line); padding-left:.7rem; line-height:1.5; }}
.eq-foot {{ color:var(--mute); font-size:.74rem; margin-top:2.4rem; padding-top:1rem; border-top:1px solid var(--line); }}
</style>
"""


def _md(html: str) -> None:
    import streamlit as st

    st.markdown(html, unsafe_allow_html=True)


def inject_theme() -> None:
    _md(CSS)
    _md(f'<div class="eq-field" aria-hidden="true">{glyphs.background_field_svg()}</div>')


# ---- header ---------------------------------------------------------------
def header_html(patient: str | None = None) -> str:
    chip = ""
    if patient:
        chip = (f'<span class="eq-pchip"><span class="k">Patient</span>'
                f'<span class="v">{patient}</span></span>')
    return (f'<div class="eq-head"><div class="eq-brandrow">'
            f'<img class="eq-brandmark" src="app/static/horse.png" alt="equipose" />'
            f'<span class="eq-word">equipose</span></div>{chip}</div>')


def app_header(patient: str | None = None) -> None:
    _md(header_html(patient))


# ---- stepper --------------------------------------------------------------
def stepper_html(steps: list[str], active: int) -> str:
    rows = []
    for i, label in enumerate(steps):
        state = "active" if i == active else ("done" if i < active else "")
        mark = "✓" if i < active else str(i + 1)
        rows.append(f'<div class="eq-srcrow {state}"><span class="eq-srcdot">{mark}</span>'
                    f'<span class="eq-srclabel">{label}</span></div>')
    return f'<nav class="eq-srclist">{"".join(rows)}</nav>'


def stepper(steps: list[str], active: int) -> None:
    _md(stepper_html(steps, active))


# ---- section --------------------------------------------------------------
def section_html(title: str, eyebrow: str = "", lead: str = "") -> str:
    html = f'<div class="eq-eyebrow">{eyebrow}</div>' if eyebrow else ""
    html += f'<div class="eq-title">{title}</div>'
    if lead:
        html += f'<div class="eq-lead">{lead}</div>'
    return html


def section(title: str, eyebrow: str = "", lead: str = "") -> None:
    _md(section_html(title, eyebrow, lead))


# ---- status ---------------------------------------------------------------
def status_chip(band: str) -> str:
    label, fg, _bg, glyph = _STATUS.get(band, ("n/a", SOFT, "", "·"))
    return (f'<span class="eq-chip" style="color:{fg};">'
            f'<span class="g">{glyph}</span>{label}</span>')


def status_chip_neutral(label: str) -> str:
    return (f'<span class="eq-chip" style="color:{SOFT};">'
            f'<span class="g" style="color:{MUTE};">·</span>{label}</span>')


# ---- score readout --------------------------------------------------------
_NOTE = {
    "green": "Posture held within range for this reading.",
    "yellow": "Some drift worth keeping an eye on.",
    "red": "Notable deviation in this reading.",
}


def score_readout_html(score: float, band: str, kind: str = "Session") -> str:
    note = _NOTE.get(band, "")
    return (f'<div class="eq-score">'
            f'<div class="eq-dial">{glyphs.score_dial_svg(score, band)}</div>'
            f'<div class="vr"></div>'
            f'<div><div class="lbl">{kind} posture status</div>{status_chip(band)}'
            f'<div class="note">{note}</div></div></div>')


def score_readout(score: float, band: str, kind: str = "Session") -> None:
    _md(score_readout_html(score, band, kind))


_MONO_FF = 'ui-monospace,"SF Mono",monospace'


def position_scale_html(score: float, band: str, scoring, baseline=None) -> str:
    """The 0-100 score as a position on a concern->watch->good scale (cutoffs from
    ``scoring``), marking this reading (bone line + status dot) and — when present —
    the child's own baseline (dashed). Muted zones; no fabricated 'average users'."""
    ymin, gmin = scoring.yellow_min, scoring.green_min
    W, x0 = 620.0, 24.0
    x1 = W - x0
    span, y = x1 - x0, 20.0

    def px(pct):
        return x0 + span * max(0.0, min(100.0, pct)) / 100.0

    p = [f'<svg width="100%" viewBox="0 0 {W:g} 74" fill="none" style="max-width:{W:g}px">']
    for a, b, c in ((0, ymin, glyphs.CONCERN), (ymin, gmin, glyphs.AMBER), (gmin, 100, glyphs.GOOD)):
        p.append(f'<rect x="{px(a):.1f}" y="{y:g}" width="{px(b) - px(a):.1f}" height="10" fill="{c}" opacity="0.20"/>')
    p.append(f'<rect x="{x0:g}" y="{y:g}" width="{span:g}" height="10" rx="5" fill="none" stroke="{glyphs.LINE}" stroke-width="1"/>')
    for t in (ymin, gmin):
        p.append(f'<line x1="{px(t):.1f}" y1="{y - 3:g}" x2="{px(t):.1f}" y2="{y + 13:g}" stroke="{MUTE}" stroke-width="1"/>')
        p.append(f'<text x="{px(t):.1f}" y="{y + 27:g}" fill="{MUTE}" font-size="9" text-anchor="middle" font-family="{_MONO_FF}">{t:g}</text>')
    if baseline is not None:
        bx = px(baseline)
        p.append(f'<line x1="{bx:.1f}" y1="{y - 6:g}" x2="{bx:.1f}" y2="{y + 16:g}" stroke="{SOFT}" stroke-width="1.5" stroke-dasharray="2 2"/>')
        p.append(f'<text x="{bx:.1f}" y="{y - 9:g}" fill="{SOFT}" font-size="9.5" text-anchor="middle">baseline {baseline:.0f}</text>')
    sx = px(score)
    dot = _STATUS.get(band, ("", SOFT, "", ""))[1]
    p.append(f'<line x1="{sx:.1f}" y1="{y - 14:g}" x2="{sx:.1f}" y2="{y + 18:g}" stroke="{ACCENT}" stroke-width="2"/>')
    p.append(f'<circle cx="{sx:.1f}" cy="{y + 5:g}" r="5" fill="{dot}" stroke="{BG}" stroke-width="1.5"/>')
    p.append(f'<text x="{sx:.1f}" y="{y - 19:g}" fill="{TEXT}" font-size="12" text-anchor="middle" font-family="{_MONO_FF}" font-weight="600">{score:.0f}</text>')
    p.append(f'<text x="{x0:g}" y="{y + 45:g}" fill="{MUTE}" font-size="11">needs attention</text>')
    p.append(f'<text x="{x1:g}" y="{y + 45:g}" fill="{MUTE}" font-size="11" text-anchor="end">in range</text>')
    p.append('</svg>')
    return "".join(p)


def position_scale(score: float, band: str, scoring, baseline=None) -> None:
    _md(f'<div class="eq-eyebrow">Overall posture position</div>'
        f'<div class="eq-panel" style="padding:.8rem 1.2rem;">{position_scale_html(score, band, scoring, baseline)}</div>')


def reading_why(metrics, scoring) -> str:
    """One plain-language line naming the joint(s) pulling the score down — so the
    verdict reads without parsing the table."""
    from equipose.scoring import metric_band
    concern, watch = [], []
    for m in metrics:
        if m.pct_in_range is None or m.mean is None:
            continue
        band = metric_band(m, scoring)
        name = _pretty(m.name).lower()
        if band == "red":
            concern.append(name)
        elif band == "yellow":
            watch.append(name)
    issues = concern + watch
    if not issues:
        return "Every measured joint is within range for this reading."
    if len(issues) == 1:
        return f"{issues[0].capitalize()} is driving the score."
    return f"{issues[0].capitalize()} and {issues[1]} are pulling the score down."


def reading_hero_html(score: float, band: str, why: str, scoring, baseline=None,
                      kind: str = "Snapshot") -> str:
    """Answer-first summary: score dial + status + plain-language 'why' + the position
    scale, in one card at the top of the Reading screen."""
    return (f'<div class="eq-score">'
            f'<div class="eq-dial">{glyphs.score_dial_svg(score, band)}</div>'
            f'<div class="vr"></div>'
            f'<div style="flex:0 0 auto;max-width:26ch"><div class="lbl">{kind} posture status</div>'
            f'{status_chip(band)}<div class="note">{why}</div></div>'
            f'<div style="flex:1;min-width:240px">{position_scale_html(score, band, scoring, baseline)}</div>'
            f'</div>')


def reading_hero(score: float, band: str, why: str, scoring, baseline=None,
                 kind: str = "Snapshot") -> None:
    _md(reading_hero_html(score, band, why, scoring, baseline, kind))


# ---- metrics table --------------------------------------------------------
# short, readable unit tags for the value cell (raw config units like
# "frac_trunk" would read awkwardly; "deg" stays "deg").
_UNIT_DISP = {"deg": "deg", "frac_shoulder_w": "w", "frac_back": "%", "score": ""}


def _pretty(name: str) -> str:
    return name.replace("_", " ")


def metrics_table_html(metrics, thresholds=None, scoring=None) -> str:
    show_ref = thresholds is not None
    rows = ""
    for m in metrics:
        tier_cls = "best" if m.reliability == "best_effort" else ""
        tier_txt = "best-effort" if m.reliability == "best_effort" else "primary"
        tier = f'<span class="eq-tier {tier_cls}">{tier_txt}</span>'

        if m.mean is None:
            val = f'<span class="eq-val" style="color:{MUTE};">n/a</span>'
        else:
            if m.unit == "frac_back":     # bow as a % of back length (not a raw fraction)
                val = f'<span class="eq-val eq-num">{m.mean * 100:.0f}<span class="u">%</span></span>'
            else:
                unit_disp = _UNIT_DISP.get(m.unit, m.unit)
                val = f'<span class="eq-val eq-num">{m.mean:.2f}<span class="u">{unit_disp}</span></span>'

        status = metric_status(m, scoring)   # good | watch | concern | none
        if status == "none":
            stat = status_chip_neutral("Not detected")
        else:
            band = {"good": "green", "watch": "yellow", "concern": "red"}[status]
            pct = (f' <span class="pct eq-num">{m.pct_in_range * 100:.0f}%</span>'
                   if m.n_total_frames > 1 else "")
            stat = f'{status_chip(band)}{pct}'

        sub_bits = []
        mt = thresholds.metrics.get(m.name) if show_ref else None
        if show_ref:
            rng = thresholds.format_range(m.name)
            basis = thresholds.basis(m.name).replace('"', "'")
            prov = ' · needs-lit' if basis.startswith("PLACEHOLDER") else ""
            sub_bits.append(f'<span title="{basis}">range {rng}{prov}</span>')
        # in-band track: where the value sits in its band (status-colored) — replaces
        # the old confidence mini-bar; the confidence stays as a number.
        if mt is not None and m.mean is not None and status != "none":
            lo, hi = mt.acceptable
            sub_bits.append(glyphs.inband_track_svg(m.mean, lo, hi, mt.ideal, status))
        sub_bits.append(f'<span class="eq-num" style="color:{MUTE};">conf {m.confidence:.2f}</span>')
        sub = f'<div class="eq-gsub">{" · ".join(sub_bits)}</div>'

        rows += (f'<div class="eq-grow"><div class="eq-gmain">'
                 f'<span class="eq-gname">{_pretty(m.name)}</span> {tier}{sub}</div>'
                 f'<div class="eq-gtrail">{val}{stat}</div></div>')
    return f'<div class="eq-group">{rows}</div>'


def metrics_table(metrics, thresholds=None, scoring=None) -> None:
    _md(metrics_table_html(metrics, thresholds, scoring))


# ---- posture body-chart ---------------------------------------------------
_BAND_WORD = {"green": "good", "yellow": "watch", "red": "concern", "none": "none"}


def metric_status(m, scoring=None) -> str:
    """good | watch | concern | none.

    With ``scoring``, graded to match the overall score (a value inside its range
    but near the edge reads ``watch``); without it, the binary in-range fallback."""
    if m.pct_in_range is None:
        return "none"
    if scoring is None:
        return "good" if m.pct_in_range >= 0.5 else "concern"
    from equipose.scoring import metric_band
    return _BAND_WORD[metric_band(m, scoring)]


def _legend_html() -> str:
    items = [("Good", glyphs.GOOD), ("Watch", glyphs.AMBER),
             ("Concern", glyphs.CONCERN), ("Not detected", glyphs.GHOST)]
    rows = "".join(f'<span class="eq-leg"><i style="background:{c}"></i>'
                   f'<span class="lab">{label}</span></span>' for label, c in items)
    return f'<div class="eq-legendbox">{rows}</div>'


def posture_panel(view: str, metrics, face_left: bool = False, scoring=None, thresholds=None) -> None:
    data = {m.name: (metric_status(m, scoring), m.mean) for m in metrics}
    plane = "Sagittal" if view == "side" else "Coronal"
    _md(f'<div class="eq-eyebrow">Body-chart · {plane}</div>'
        f'<div class="eq-panel">{glyphs.posture_chart_svg(view, data, face_left, thresholds)}</div>')


# ---- score breakdown ------------------------------------------------------
def score_breakdown_html(entries, overall: float) -> str:
    """Explain the overall score: each metric's weight, sub-score, contribution."""
    rows = ""
    for e in entries:
        if e.counted:
            sub = f'<span class="val eq-num">{e.sub_score:.0f}</span>'
            contrib = f'<span class="val eq-num">{e.contribution:.0f}</span>'
            note = ""
        else:
            sub = f'<span class="val" style="color:{MUTE};">—</span>'
            contrib = f'<span class="val" style="color:{MUTE};">—</span>'
            note = f'<span class="eq-skip">{e.reason}</span>'
        rows += (f'<tr><td class="mname">{_pretty(e.name)}{note}</td>'
                 f'<td class="num val eq-num">×{e.weight:g}</td>'
                 f'<td class="num">{sub}</td><td class="num">{contrib}</td></tr>')
    counted = [e for e in entries if e.counted]
    if counted:
        counted_w = sum(e.weight for e in counted)
        wmean = sum(e.contribution for e in counted) / counted_w
        worst = min(counted, key=lambda e: e.sub_score)
        foot = (f'<div class="eq-disc" style="margin-top:.6rem;">Sub-score grades how close each '
                f'joint is to ideal (100 = ideal, ~60 at the edge of the acceptable range). '
                f'Overall = halfway between the weighted average ({wmean:.0f}) and the worst joint '
                f'({_pretty(worst.name)} at {worst.sub_score:.0f}) = <b>{overall:.0f}</b>, so one '
                f'poor joint is not averaged away. Skipped metrics do not affect the score.</div>')
    else:
        foot = (f'<div class="eq-disc" style="margin-top:.6rem;">Overall = <b>{overall:.0f}</b> — '
                f'no metrics were reliable enough to count for this reading.</div>')
    return (f'<table class="eq-table"><thead><tr><th>Metric</th>'
            f'<th class="num">Weight</th><th class="num">Sub-score</th>'
            f'<th class="num">Contribution</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>{foot}')


def score_breakdown(metrics, scoring, overall: float) -> None:
    from equipose.scoring import score_breakdown as _bd

    _md(score_breakdown_html(_bd(metrics, scoring), overall))


# ---- misc -----------------------------------------------------------------
def disclaimer(text: str) -> None:
    _md(f'<div class="eq-disc">{text}</div>')


def footer(text: str) -> None:
    _md(f'<div class="eq-foot">{text}</div>')


def trend_chart(df, x: str, y: str, y_title: str, height: int = 250, band=None):
    """Dark, warm Altair line+point chart. ``band=(lo, hi)`` shades the
    acceptable range as a faint in-range zone behind the line."""
    import altair as alt
    import pandas as pd

    axis = dict(labelColor=SOFT, titleColor=SOFT, tickColor=LINE, domainColor=LINE)
    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:T", title=None, axis=alt.Axis(format="%b %d", grid=False, **axis)),
        y=alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(gridColor=LINE, gridDash=[2, 3], **axis)),
    )
    layers = []
    if band is not None:
        lo, hi = band
        bdf = pd.DataFrame({"lo": [lo], "hi": [hi]})
        layers.append(alt.Chart(bdf).mark_rect(opacity=0.12, color=glyphs.GOOD)
                      .encode(y=alt.Y("lo:Q"), y2="hi:Q"))
    layers.append(base.mark_line(color=ACCENT, strokeWidth=2.4, interpolate="monotone"))
    layers.append(base.mark_point(color=ACCENT, filled=True, size=64, opacity=1))
    return alt.layer(*layers).properties(height=height).configure_view(strokeWidth=0).configure(
        background=PANEL, font="-apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif")


# ---- review (patient progress) --------------------------------------------
def review_overview_html(sessions) -> str:
    """sessions: list of session dicts (one view), ordered oldest -> newest."""
    n = len(sessions)
    first, last = sessions[0], sessions[-1]
    d0, d1 = first["captured_at"][:10], last["captured_at"][:10]
    span = d0 if d0 == d1 else f"{d0} to {d1}"
    photos = sum(1 for s in sessions if s.get("kind") == "snapshot")
    videos = n - photos
    if n >= 2:
        delta = last["overall_score"] - first["overall_score"]
        arrow, col = (("▲", glyphs.GOOD) if delta > 0.5 else
                      ("▼", glyphs.CONCERN) if delta < -0.5 else ("·", MUTE))
        trend = f'<span class="eq-num" style="color:{col};">{arrow} {abs(delta):.0f}</span>'
    else:
        trend = f'<span style="color:{MUTE};">n/a</span>'

    def stat(label, val):
        return f'<div class="eq-stat"><div class="k">{label}</div><div class="v">{val}</div></div>'

    return ('<div class="eq-overview">'
            + stat("Readings", f'<span class="eq-num">{n}</span>')
            + stat("Span", f'<span style="font-size:.92rem;">{span}</span>')
            + stat("Latest score", f'<span class="eq-num">{last["overall_score"]:.0f}</span> '
                   + status_chip(last["band"]))
            + stat("Trend", trend)
            + stat("Photo / Video", f'<span class="eq-num">{photos}</span> / <span class="eq-num">{videos}</span>')
            + '</div>')


def review_overview(sessions) -> None:
    _md(review_overview_html(sessions))


def review_history_html(sessions) -> str:
    rows = ""
    for s in reversed(sessions):  # newest first
        date = s["captured_at"][:16].replace("T", " ")
        typ = "Photo" if s.get("kind") == "snapshot" else "Video"
        rows += (f'<tr><td class="mname">{date}</td><td>{typ}</td><td>{s["view"]}</td>'
                 f'<td class="num val eq-num">{s["overall_score"]:.0f}</td>'
                 f'<td>{status_chip(s["band"])}</td></tr>')
    return (f'<table class="eq-table"><thead><tr><th>Date</th><th>Type</th><th>View</th>'
            f'<th class="num">Score</th><th>Status</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


def review_history(sessions) -> None:
    _md(review_history_html(sessions))
