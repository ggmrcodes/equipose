"""Signature SVG art for equipose — the domain-specific visual identity.

These are functional, on-theme visuals, not decoration:
  - logo_mark_svg: a plumb line + angle (the posture-measurement motif)
  - score_dial_svg: a goniometer-style arc gauge (the goniometer is the tool
    physios use to measure joint angles)
  - posture_chart_svg: a body-chart that maps the measured angles onto a figure,
    tilting segments by the real values and coloring joints by status

Pure string builders (no Streamlit, no I/O) so they are unit-testable. Palette
is duplicated locally to avoid an import cycle with ui.py.
"""
from __future__ import annotations

import math

# warm-night palette (kept in sync with ui.py) — monochrome graphite
TEXT = "#F2E9E2"
SOFT = "#B8A99E"
MUTE = "#8A7A6E"
LINE = "#332A24"        # solid warm hairline for SVG strokes
PANEL = "#1E1814"
ACCENT = "#FBF5EF"      # warm bone (replaces rose)
GOOD = "#86CFA0"
AMBER = "#E8BE78"
CONCERN = "#EC8A74"
GHOST = "#5A4D43"
SEG = "#7C6B5E"

_BAND = {"green": GOOD, "yellow": AMBER, "red": CONCERN}


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _rot(px, py, cx, cy, deg):
    r = math.radians(deg)
    s, c = math.sin(r), math.cos(r)
    dx, dy = px - cx, py - cy
    return (cx + dx * c - dy * s, cy + dx * s + dy * c)


def _pol(cx, cy, r, deg):
    t = math.radians(deg)
    return (cx + r * math.cos(t), cy + r * math.sin(t))


def _arc(cx, cy, r, a0, a1):
    x0, y0 = _pol(cx, cy, r, a0)
    x1, y1 = _pol(cx, cy, r, a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M {x0:.2f} {y0:.2f} A {r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}"


def _line(x1, y1, x2, y2, stroke, w=5.0, extra=""):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{w}" stroke-linecap="round" {extra}/>')


def _dot(x, y, fill, r=4.6):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}"/>'


def _txt(x, y, s, fill=SOFT, size=10.5, anchor="middle", weight=500):
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
            f'font-family="Mono, ui-monospace, monospace" font-weight="{weight}" '
            f'text-anchor="{anchor}">{s}</text>')


def _col(status: str) -> str:
    return (GOOD if status == "good" else AMBER if status == "watch"
            else CONCERN if status == "concern" else GHOST)


# ---- logo mark ------------------------------------------------------------
def logo_mark_svg(size: int = 26) -> str:
    """A plumb line meeting an angled line — the posture / goniometer motif."""
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 28 28" fill="none" '
        f'style="vertical-align:-5px;margin-right:.5rem">'
        f'<path d="M7 4 A 16 16 0 0 1 20 11" stroke="{ACCENT}" stroke-width="1.6" '
        f'fill="none" stroke-linecap="round" opacity="0.9"/>'
        f'<line x1="7" y1="3" x2="7" y2="21" stroke="{SOFT}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<line x1="7" y1="4" x2="22" y2="20" stroke="{ACCENT}" stroke-width="1.8" stroke-linecap="round"/>'
        f'<circle cx="7" cy="23.2" r="2.1" fill="{SOFT}"/>'
        f'<circle cx="7" cy="4" r="1.5" fill="{ACCENT}"/>'
        f'</svg>'
    )


# ---- score dial (goniometer gauge) ----------------------------------------
def score_dial_svg(score: float, band: str, size: int = 138) -> str:
    cx = cy = 66.0
    r = 50.0
    start, sweep = 135.0, 270.0
    p = _clamp(score, 0, 100) / 100.0
    color = _BAND.get(band, ACCENT)

    parts = [f'<svg width="{size}" height="{size}" viewBox="0 0 132 132" fill="none">']
    parts.append(f'<path d="{_arc(cx, cy, r, start, start + sweep)}" stroke="{LINE}" '
                 f'stroke-width="5" fill="none" stroke-linecap="round"/>')
    if p > 0.004:
        parts.append(f'<path d="{_arc(cx, cy, r, start, start + sweep * p)}" stroke="{color}" '
                     f'stroke-width="5" fill="none" stroke-linecap="round"/>')
    for i in range(11):
        a = start + sweep * i / 10
        x1, y1 = _pol(cx, cy, r - 10, a)
        x2, y2 = _pol(cx, cy, r - 6, a)
        parts.append(_line(x1, y1, x2, y2, MUTE, 1.1))
    parts.append(_txt(cx, cy + 7, f"{score:.0f}", fill=TEXT, size=30, weight=600))
    parts.append(_txt(cx, cy + 24, "/ 100", fill=MUTE, size=11))
    parts.append("</svg>")
    return "".join(parts)


# ---- posture body-chart ---------------------------------------------------
def _g(data, name):
    return data.get(name, ("none", None))


def _posture_side(data, face_left: bool = False) -> str:
    # Base geometry faces RIGHT (knee/foot/head sit right of the trunk axis).
    H0 = (98.0, 196.0)
    S0 = (98.0, 104.0)
    E0 = (104.0, 62.0)
    HEAD0 = (105.0, 46.0)
    K0 = (150.0, 206.0)
    A0 = (150.0, 266.0)
    FT0 = (172.0, 270.0)

    trunk_s, trunk_v = _g(data, "forward_trunk_lean")
    neck_s, neck_v = _g(data, "neck_forward_angle")
    hip_s, _ = _g(data, "hip_flexion")
    knee_s, _ = _g(data, "knee_angle")

    lean = _clamp(abs(trunk_v), 0, 22) if (trunk_s != "none" and trunk_v is not None) else 0
    neckd = _clamp(abs(180 - neck_v), 0, 24) if (neck_s != "none" and neck_v is not None) else 0

    S = _rot(*S0, *H0, lean)
    E = _rot(*_rot(*E0, *H0, lean), *S, neckd)
    HEAD = _rot(*_rot(*HEAD0, *H0, lean), *S, neckd)

    # Reflect the whole figure about the viewBox centre (x=120) so it faces the
    # same way as the subject in the photo. Geometry and label sides mirror; the
    # glyph text stays upright (we reflect points, never wrap in a scale(-1) group).
    def mx(x: float) -> float:
        return 240.0 - x if face_left else x

    def mp(pt):
        return (mx(pt[0]), pt[1])

    H, S, E, HEAD, K, A, FT = mp(H0), mp(S), mp(E), mp(HEAD), mp(K0), mp(A0), mp(FT0)

    p = []
    # segments
    p.append(_line(*H, *S, _col(trunk_s)))                 # trunk
    p.append(_line(*S, *E, _col(neck_s)))                  # neck
    p.append(_line(*H, *K, _col(hip_s)))                   # thigh
    p.append(_line(*K, *A, _col(knee_s)))                  # shank
    p.append(_line(*A, *FT, SEG, 4))                       # foot
    # head
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="13" fill="{PANEL}" '
             f'stroke="{_col(neck_s)}" stroke-width="2.6"/>')
    # joints
    p.append(_dot(*E, _col(neck_s)))
    p.append(_dot(*S, _col(trunk_s)))
    p.append(_dot(*H, _col(hip_s)))
    p.append(_dot(*K, _col(knee_s)))
    p.append(_dot(*A, SEG))
    # labels: trunk on the posterior side, neck ahead of the face; sides swap with
    # facing so text never overlaps the figure.
    if trunk_s != "none" and trunk_v is not None:
        mid_x, mid_y = (S[0] + H[0]) / 2, (S[1] + H[1]) / 2
        off, anc = (16, "start") if face_left else (-16, "end")
        p.append(_txt(mid_x + off, mid_y, f"{abs(trunk_v):.0f}°", fill=SOFT, anchor=anc))
    if neck_s != "none" and neck_v is not None:
        off, anc = (-14, "end") if face_left else (14, "start")
        p.append(_txt(E[0] + off, E[1] - 2, f"{neck_v:.0f}°", fill=SOFT, anchor=anc))
    return "".join(p)


def _posture_front(data) -> str:
    Pc = (120.0, 196.0)
    Sc = (120.0, 104.0)
    SL0, SR0 = (84.0, 108.0), (156.0, 108.0)
    HL0, HR0 = (92.0, 196.0), (148.0, 196.0)
    HEAD0 = (120.0, 58.0)

    sh_s, sh_v = _g(data, "shoulder_tilt")
    pel_s, pel_v = _g(data, "pelvic_obliquity")
    tr_s, tr_v = _g(data, "trunk_lateral_lean")
    hd_s, hd_v = _g(data, "head_tilt")

    lean = _clamp(tr_v, -18, 18) if (tr_s != "none" and tr_v is not None) else 0
    sht = _clamp(sh_v, -16, 16) if (sh_s != "none" and sh_v is not None) else 0
    pel = _clamp(pel_v, -16, 16) if (pel_s != "none" and pel_v is not None) else 0
    hdt = _clamp(hd_v, -18, 18) if (hd_s != "none" and hd_v is not None) else 0

    Sc2 = _rot(*Sc, *Pc, lean)
    HEAD = _rot(*HEAD0, *Pc, lean)
    SL = _rot(*_rot(*SL0, *Pc, lean), *Sc2, sht)
    SR = _rot(*_rot(*SR0, *Pc, lean), *Sc2, sht)
    HL = _rot(*HL0, *Pc, pel)
    HR = _rot(*HR0, *Pc, pel)

    p = []
    # plumb reference
    p.append(_line(120, 40, 120, 250, LINE, 1.4, 'stroke-dasharray="2 4"'))
    # spine, shoulder line, hip line
    p.append(_line(*Sc2, *Pc, _col(tr_s)))
    p.append(_line(*SL, *SR, _col(sh_s)))
    p.append(_line(*HL, *HR, _col(pel_s)))
    # head with a downward nose tick that leans with head tilt (reads as orientation,
    # not a prohibition sign)
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="14" fill="{PANEL}" '
             f'stroke="{_col(hd_s)}" stroke-width="2.6"/>')
    chin = (HEAD[0], HEAD[1] + 14)
    tip = _rot(HEAD[0], HEAD[1] + 27, *HEAD, hdt)
    p.append(_line(*chin, *tip, _col(hd_s), 2.6))
    p.append(_dot(*tip, _col(hd_s), 2.8))
    # joints
    p.append(_dot(*SL, _col(sh_s)))
    p.append(_dot(*SR, _col(sh_s)))
    p.append(_dot(*HL, _col(pel_s)))
    p.append(_dot(*HR, _col(pel_s)))
    p.append(_dot(*Pc, SEG, 3.4))
    # labels
    if sh_s != "none" and sh_v is not None:
        p.append(_txt(SR[0] + 16, SR[1], f"{abs(sh_v):.0f}°", fill=SOFT, anchor="start"))
    if pel_s != "none" and pel_v is not None:
        p.append(_txt(HR[0] + 16, HR[1] + 4, f"{abs(pel_v):.0f}°", fill=SOFT, anchor="start"))
    return "".join(p)


def posture_chart_svg(view: str, data: dict, face_left: bool = False) -> str:
    """data: {metric_name: (status, value_or_None)} with status in good|concern|none.

    ``face_left`` mirrors the sagittal schematic so it faces the same way as the
    subject in the photo (ignored for the front/coronal view)."""
    inner = _posture_front(data) if view == "front" else _posture_side(data, face_left)
    return (f'<svg viewBox="0 0 240 300" width="100%" height="300" '
            f'preserveAspectRatio="xMidYMid meet" fill="none">{inner}</svg>')


# ---- ambient background field (architectural goniometer) -------------------
def background_field_svg() -> str:
    """A giant, faint protractor + plumb grid that turns the empty canvas into a
    measurement-instrument field. The small score dial echoes this at full scale.
    Ultra-low opacity so it reads as atmosphere, never clutter."""
    cx, cy, r = 720.0, 560.0, 520.0
    p = [f'<svg viewBox="0 0 1440 1100" width="100%" height="100%" '
         f'preserveAspectRatio="xMidYMid slice" fill="none">']
    p.append(f'<g stroke="{SOFT}" opacity="0.06">')
    for rr in (r, r - 72, r - 144):
        p.append(f'<path d="{_arc(cx, cy, rr, 135, 405)}" stroke-width="1.1" fill="none"/>')
    n = 45
    for i in range(n + 1):
        a = 135 + 270 * i / n
        major = (i % 5 == 0)
        x1, y1 = _pol(cx, cy, r, a)
        x2, y2 = _pol(cx, cy, r - (24 if major else 12), a)
        p.append(_line(x1, y1, x2, y2, SOFT, 1.4 if major else 0.9))
    p.append("</g>")
    # plumb verticals in the side margins
    p.append(f'<g stroke="{SOFT}" opacity="0.045" stroke-dasharray="2 8">')
    for x in (150, 372, 1068, 1290):
        p.append(f'<line x1="{x}" y1="0" x2="{x}" y2="1100" stroke-width="1"/>')
    p.append("</g></svg>")
    return "".join(p)
