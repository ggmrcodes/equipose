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

# slate-light palette (kept in sync with ui.py) — cool, architectural
TEXT = "#0C1013"        # near-black navy ink
SOFT = "#415A69"        # slate (secondary)
MUTE = "#6E8794"        # muted slate (tertiary)
LINE = "#DBE3E7"        # cool hairline for SVG strokes
PANEL = "#FFFFFF"       # white card fill (callout cards)
ACCENT = "#415A69"      # slate-blue emphasis tone
GOOD = "#2E7D52"        # sage (darkened for AA on light)
AMBER = "#9A6A12"       # ochre
CONCERN = "#B0432A"     # terracotta
GHOST = "#C3CDD3"       # cool light gray (undetected)
SEG = "#90A2AC"         # neutral slate segment
BODY = "#D2DBE0"        # light cool body silhouette (the rider mass under the skeleton)
WASH = 0.50             # opacity of the per-limb status tint over the body
OUTLINE = "#0C1013"     # near-black rim around the rider silhouette (drawn under the fill)
# horse (context, not measured) — muted slate tones
HORSE = "#C4D0D6"
HORSE_FAR = "#D2DBE0"   # far legs (depth)
HOOF = "#A7B6BD"
HORSE_DK = "#9DAEB6"    # subtle detail (mane, ears, saddle)

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


def _capsule(x1, y1, x2, y2, stroke, w, opacity=1.0):
    """A thick rounded stroke — one limb of the body silhouette (or its status wash)."""
    o = f' stroke-opacity="{opacity:g}"' if opacity != 1.0 else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{w}" stroke-linecap="round"{o}/>')


def _curved(a, ctrl, b, stroke, w, opacity=1.0):
    """A thick rounded quadratic-Bézier stroke — a limb that bows (e.g. a rounded back)."""
    o = f' stroke-opacity="{opacity:g}"' if opacity != 1.0 else ""
    return (f'<path d="M {a[0]:.1f} {a[1]:.1f} Q {ctrl[0]:.1f} {ctrl[1]:.1f} {b[0]:.1f} {b[1]:.1f}" '
            f'fill="none" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round"{o}/>')


def _txt(x, y, s, fill=SOFT, size=10.5, anchor="middle", weight=500):
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
            f'font-family="Mono, ui-monospace, monospace" font-weight="{weight}" '
            f'text-anchor="{anchor}">{s}</text>')


def _col(status: str) -> str:
    return (GOOD if status == "good" else AMBER if status == "watch"
            else CONCERN if status == "concern" else GHOST)


_SEV = {"concern": 3, "watch": 2, "good": 1, "none": 0}


def _worst(a: str, b: str) -> str:
    """The more severe of two statuses — so a trunk that both leans and rounds shows
    the worse of the two, never a falsely reassuring green."""
    return a if _SEV.get(a, 0) >= _SEV.get(b, 0) else b


def _inband_els(x: float, y: float, w: float, value: float, lo: float, hi: float,
                ideal: float, status: str, pad: float = 4.0) -> str:
    """Positioned in-band track primitives (band + ideal tick + status marker) drawn at
    (x, y) — shared by the standalone table track and the body-chart callout gauge."""
    x0, x1 = x + pad, x + w - pad
    span = x1 - x0

    def tx(v: float) -> float:
        t = (v - lo) / (hi - lo) if hi != lo else 0.5
        return x0 + span * max(0.0, min(1.0, t))

    ix, mx = tx(ideal), tx(value)
    return (f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" stroke="{LINE}" '
            f'stroke-width="3" stroke-linecap="round"/>'
            f'<line x1="{ix:.1f}" y1="{y - 3:.1f}" x2="{ix:.1f}" y2="{y + 3:.1f}" '
            f'stroke="{MUTE}" stroke-width="1"/>'
            f'<circle class="mk" cx="{mx:.1f}" cy="{y:.1f}" r="2.8" fill="{_col(status)}"/>')


def inband_track_svg(value: float, lo: float, hi: float, ideal: float, status: str,
                     w: float = 68.0, h: float = 12.0) -> str:
    """A thin band track showing where ``value`` sits in [lo,hi] — clamped to the edges
    when out of band — with a subtle ideal tick and a status-colored value marker."""
    return (f'<svg width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}" fill="none" '
            f'style="vertical-align:middle">'
            f'{_inband_els(0.0, h / 2.0, w, value, lo, hi, ideal, status)}</svg>')


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


def _horse_svg() -> str:
    """A muted horse silhouette — riding context for the sagittal body-chart, drawn
    behind the rider (who sits in the saddle). Faces right; the caller mirrors it for
    left. Carries no status color: it is context, never a measured value."""
    body = ("M 150 192 C 164 176 181 165 196 158 C 207 160 214 169 213 179 "
            "C 212 187 205 189 198 188 C 191 187 185 185 181 181 "
            "C 175 187 170 197 166 210 C 163 222 159 232 156 240 "
            "C 146 240 126 246 104 250 C 88 253 74 251 66 245 "
            "C 58 239 53 230 51 220 C 50 212 51 204 55 200 "
            "Q 80 204 104 201 Q 130 198 150 192 Z")
    tail = (f'<path d="M 54 202 C 40 214 33 232 32 252 C 39 244 46 240 52 238 '
            f'C 48 226 49 214 58 206 Z" fill="{HORSE}"/>')
    ears = (f'<path d="M 190 162 Q 187 150 192 148 Q 196 152 196 160 Z" fill="{HORSE_DK}"/>'
            f'<path d="M 197 161 Q 197 149 203 149 Q 205 154 203 163 Z" fill="{HORSE_DK}"/>')
    mane = (f'<path d="M 150 192 C 160 178 176 167 192 159" fill="none" stroke="{HORSE_DK}" '
            f'stroke-width="4" stroke-linecap="round" opacity="0.8"/>')

    def leg(pts, w, color):
        d = "M " + " L ".join(f"{x} {y}" for x, y in pts)
        hx, hy = pts[-1]
        return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" '
                f'stroke-linecap="round" stroke-linejoin="round"/>'
                f'<ellipse cx="{hx}" cy="{hy + 3}" rx="{w / 2 + 1.2:.1f}" ry="3.4" fill="{HOOF}"/>')

    far = (leg([(150, 234), (150, 266), (152, 296)], 8, HORSE_FAR)
           + leg([(88, 244), (82, 268), (86, 296)], 9, HORSE_FAR))
    near = (leg([(158, 234), (158, 267), (161, 298)], 10, HORSE)
            + leg([(70, 242), (63, 269), (69, 298)], 11, HORSE))
    eye = f'<ellipse cx="199" cy="176" rx="2.6" ry="3" fill="{MUTE}"/>'
    nostril = f'<circle cx="209" cy="181" r="1.4" fill="{MUTE}"/>'
    saddle = f'<path d="M 92 194 Q 116 186 148 197 L 149 205 Q 116 198 92 204 Z" fill="{HORSE_DK}"/>'
    return (f'<g opacity="0.96">{far}{tail}<path d="{body}" fill="{HORSE}"/>{mane}{ears}'
            f'{near}{eye}{nostril}{saddle}</g>')


def _posture_side(data, face_left: bool = False, trunk_ideal: float = 2.5) -> str:
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

    # back rounding (kyphosis): bow the trunk posteriorly by the measured amount so the
    # rider's back visibly rounds. Posterior = the trunk-perpendicular pointing away from
    # the knee (the front) — correct for either facing.
    br_s, br_v = _g(data, "back_roundness")
    # the trunk carries BOTH lean and rounding — color it by the worse of the two so a
    # rounded (concern) back never reads as a reassuring green from a good lean
    trunk_seg_s = _worst(trunk_s, br_s)
    trunk_ctrl, trunk_ref = None, None
    if br_s != "none" and br_v is not None:
        bow = _clamp(br_v, 0.0, 0.26)
        vx, vy = S[0] - H[0], S[1] - H[1]
        tl = math.hypot(vx, vy) or 1.0
        nx, ny = -vy / tl, vx / tl                       # trunk-perpendicular (unit)
        midx, midy = (H[0] + S[0]) / 2, (H[1] + S[1]) / 2
        if nx * (K[0] - midx) + ny * (K[1] - midy) > 0:  # points toward the knee (front)
            nx, ny = -nx, -ny                            # -> flip to posterior (back)
        depth = bow * tl
        trunk_ctrl = (midx + nx * 2 * depth, midy + ny * 2 * depth)  # quad ctrl -> apex ~ depth
        if depth > 4:                                    # visible rounding -> show 'straight' ref
            trunk_ref = (nx, ny)

    # limbs of the seated side profile: (a, b, status, body_width, curve_ctrl or None)
    limbs = [
        (H, S, trunk_seg_s, 26, trunk_ctrl),   # trunk (bows + colored by lean/rounding)
        (S, E, neck_s, 14, None),          # neck
        (H, K, hip_s, 24, None),           # thigh
        (K, A, knee_s, 20, None),          # shank
        (A, FT, "none", 10, None),         # foot (neutral)
    ]

    def draw(a, b, stroke, w, opacity=1.0, ctrl=None):
        return _curved(a, ctrl, b, stroke, w, opacity) if ctrl else _capsule(*a, *b, stroke, w, opacity)

    # horse (context) sits behind the rider; mirror it to match a left-facing rider
    horse = _horse_svg()
    if face_left:
        horse = f'<g transform="translate(240,0) scale(-1,1)">{horse}</g>'
    p = [horse]
    OUT = 2.2  # outline thickness added to each side of the silhouette
    # layer 0 — near-black outline: each part drawn wider under the fill so the dark
    # shows only as a crisp rim around the merged rider silhouette
    for a, b, _st, bw, ctrl in limbs:
        p.append(draw(a, b, OUTLINE, bw + 2 * OUT, 1.0, ctrl))
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="{15 + OUT:g}" fill="{OUTLINE}"/>')
    # layer 1 — gray body silhouette (recognizable seated mass)
    for a, b, _st, bw, ctrl in limbs:
        p.append(draw(a, b, BODY, bw, 1.0, ctrl))
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="15" fill="{BODY}"/>')
    # layer 2 — faint per-limb status wash (the body carries a soft status tint)
    for a, b, st, bw, ctrl in limbs:
        if st != "none":
            p.append(draw(a, b, _col(st), bw, WASH, ctrl))
    if neck_s != "none":
        p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="15" '
                 f'fill="{_col(neck_s)}" fill-opacity="{WASH:g}"/>')
    # layer 3 — colored skeleton centerline + joints + head ring
    p.append(draw(H, S, _col(trunk_seg_s), 4, 1.0, trunk_ctrl))  # trunk (bows + combined color)
    p.append(_line(*S, *E, _col(neck_s), 4))               # neck
    p.append(_line(*H, *K, _col(hip_s), 4))                # thigh
    p.append(_line(*K, *A, _col(knee_s), 4))               # shank
    p.append(_line(*A, *FT, SEG, 3))                       # foot
    if trunk_ref is not None:
        # dashed straight spine — 'where straight should be'. A light halo lets it pop on
        # the colored trunk; the curved skeleton diverges from it so the rounding reads.
        rnx, rny = trunk_ref
        p.append(_line(*H, *S, "#FFFFFF", 5.0, 'stroke-dasharray="5 4" opacity="0.7"'))
        p.append(_line(*H, *S, TEXT, 2.6, 'stroke-dasharray="5 4"'))
        for pt in (H, S):  # end ticks bracketing the reference
            p.append(_line(pt[0] - 7 * rnx, pt[1] - 7 * rny, pt[0] + 7 * rnx, pt[1] + 7 * rny,
                           TEXT, 2.2))

    # trunk-lean angle arc at the hip: a goniometer arc from the ideal-lean ray to the
    # actual trunk, with a dashed 'ideal' ray so the small angle reads. Only when notable.
    if trunk_s in ("watch", "concern") and trunk_v is not None:
        ideal_S = mp(_rot(*S0, *H0, _clamp(abs(trunk_ideal), 0, 22)))
        a_id = math.degrees(math.atan2(ideal_S[1] - H[1], ideal_S[0] - H[0]))
        a_ac = math.degrees(math.atan2(S[1] - H[1], S[0] - H[0]))
        tlen = math.hypot(S[0] - H[0], S[1] - H[1]) * 0.82
        ex, ey = _pol(H[0], H[1], tlen, a_id)                 # dashed ideal-lean ray
        p.append(_line(H[0], H[1], ex, ey, "#FFFFFF", 4.0, 'stroke-dasharray="5 4" opacity="0.7"'))
        p.append(_line(H[0], H[1], ex, ey, MUTE, 2.0, 'stroke-dasharray="5 4"'))
        r = 40.0                                              # goniometer arc (ideal -> actual)
        delta = ((a_ac - a_id + 180) % 360) - 180
        x0, y0 = _pol(H[0], H[1], r, a_id)
        x1, y1 = _pol(H[0], H[1], r, a_ac)
        arc = (f'A {r:g} {r:g} 0 {1 if abs(delta) > 180 else 0} '
               f'{1 if delta >= 0 else 0} {x1:.1f} {y1:.1f}')
        p.append(f'<path d="M {x0:.1f} {y0:.1f} {arc}" stroke="#FFFFFF" stroke-width="5" '
                 f'fill="none" stroke-linecap="round" opacity="0.7"/>')
        p.append(f'<path d="M {x0:.1f} {y0:.1f} {arc}" stroke="{_col(trunk_s)}" stroke-width="3" '
                 f'fill="none" stroke-linecap="round"/>')
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="15" fill="none" '
             f'stroke="{_col(neck_s)}" stroke-width="2.4"/>')
    p.append(_dot(*E, _col(neck_s)))
    p.append(_dot(*S, _col(trunk_seg_s)))
    p.append(_dot(*H, _col(hip_s)))
    p.append(_dot(*K, _col(knee_s)))
    p.append(_dot(*A, SEG))
    # joint anchors for the per-joint callouts (labels moved off the figure).
    # back_roundness is a trunk/back measure (not a joint angle) — anchor it on the
    # upper-mid back so it gets a callout alongside the joints.
    joints = {
        "forward_trunk_lean": ((S[0] + H[0]) / 2, (S[1] + H[1]) / 2),
        "neck_forward_angle": S,
        "back_roundness": (0.6 * S[0] + 0.4 * H[0], 0.6 * S[1] + 0.4 * H[1]),
        "hip_flexion": H,
        "knee_angle": K,
    }
    return "".join(p), joints


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

    # regions of the front body: (a, b, status, body_width)
    body = [
        (Sc2, Pc, tr_s, 30),     # torso
        (SL, SR, sh_s, 16),      # shoulders (breadth)
        (HL, HR, pel_s, 18),     # pelvis (breadth)
        (Sc2, HEAD, hd_s, 14),   # neck
    ]

    p = []
    # plumb reference (behind the body — reads as true-vertical above/below the figure)
    p.append(_line(120, 40, 120, 250, LINE, 1.4, 'stroke-dasharray="2 4"'))
    OUT = 2.2  # outline thickness added to each side of the silhouette
    # layer 0 — near-black outline (drawn wider under the fill; rims the silhouette)
    for a, b, _st, bw in body:
        p.append(_capsule(*a, *b, OUTLINE, bw + 2 * OUT))
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="{16 + OUT:g}" fill="{OUTLINE}"/>')
    # layer 1 — gray body silhouette
    for a, b, _st, bw in body:
        p.append(_capsule(*a, *b, BODY, bw))
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="16" fill="{BODY}"/>')
    # layer 2 — faint per-region status wash
    for a, b, st, bw in body:
        if st != "none":
            p.append(_capsule(*a, *b, _col(st), bw, WASH))
    if hd_s != "none":
        p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="16" '
                 f'fill="{_col(hd_s)}" fill-opacity="{WASH:g}"/>')
    # layer 3 — colored skeleton: spine, shoulder line, hip line
    p.append(_line(*Sc2, *Pc, _col(tr_s), 4))
    p.append(_line(*SL, *SR, _col(sh_s), 4))
    p.append(_line(*HL, *HR, _col(pel_s), 4))
    # head with a downward nose tick that leans with head tilt (reads as orientation,
    # not a prohibition sign)
    p.append(f'<circle cx="{HEAD[0]:.1f}" cy="{HEAD[1]:.1f}" r="16" fill="none" '
             f'stroke="{_col(hd_s)}" stroke-width="2.4"/>')
    chin = (HEAD[0], HEAD[1] + 16)
    tip = _rot(HEAD[0], HEAD[1] + 29, *HEAD, hdt)
    p.append(_line(*chin, *tip, _col(hd_s), 2.6))
    p.append(_dot(*tip, _col(hd_s), 2.8))
    # joints
    p.append(_dot(*SL, _col(sh_s)))
    p.append(_dot(*SR, _col(sh_s)))
    p.append(_dot(*HL, _col(pel_s)))
    p.append(_dot(*HR, _col(pel_s)))
    p.append(_dot(*Pc, SEG, 3.4))
    joints = {
        "head_tilt": HEAD,
        "shoulder_tilt": SR,          # right shoulder
        "trunk_lateral_lean": Sc2,    # upper spine
        "pelvic_obliquity": HR,       # right hip
    }
    return "".join(p), joints


_UI_FF = '-apple-system,system-ui,sans-serif'
_MONO_FF = 'ui-monospace,"SF Mono",monospace'
_SHORT = {
    "forward_trunk_lean": "Trunk lean", "neck_forward_angle": "Neck",
    "hip_flexion": "Hip", "knee_angle": "Knee", "back_roundness": "Back rounding",
    "head_tilt": "Head", "shoulder_tilt": "Shoulder",
    "pelvic_obliquity": "Pelvis", "trunk_lateral_lean": "Trunk lean",
}


def _fmt_val(v: float, unit: str) -> str:
    if unit == "deg":
        return f"{v:.0f}°"
    if unit == "frac_back":          # bow as a % of back length — legible for clinicians
        return f"{v * 100:.0f}%"
    if unit and unit.startswith("frac"):
        return f"{v:.2f}"
    return f"{v:g}"


def _callouts_svg(specs, col_x: float = 300.0, col_w: float = 250.0,
                  card_h: float = 60.0, gap: float = 68.0, top: float = 44.0) -> str:
    """specs: (jx, jy, name, value_text, status, gauge) with joint coords in the outer
    viewBox and gauge = (value, lo, hi, ideal) or None. A right-hand column of cards
    ordered by joint height, each linked by a leader line; a card carries the joint name,
    the you/ideal readout, and an in-band gauge showing where the value sits in range."""
    out, y = [], top
    for jx, jy, name, val, status, gauge in sorted(specs, key=lambda s: s[1]):
        cy = max(jy, y)
        col = _col(status)
        ty0 = cy - card_h / 2.0
        out.append(f'<line x1="{jx:.1f}" y1="{jy:.1f}" x2="{col_x - 10:.1f}" y2="{cy:.1f}" '
                   f'stroke="{LINE}" stroke-width="1.4"/>')
        out.append(f'<rect x="{col_x:g}" y="{ty0:.1f}" width="{col_w:g}" '
                   f'height="{card_h:g}" rx="10" fill="{PANEL}" stroke="{LINE}"/>')
        out.append(f'<circle cx="{col_x + 18:g}" cy="{ty0 + 22:.1f}" r="5" fill="{col}"/>')
        out.append(f'<text x="{col_x + 34:g}" y="{ty0 + 26:.1f}" fill="{TEXT}" font-size="13" '
                   f'font-family="{_UI_FF}" font-weight="600">{name}</text>')
        out.append(f'<text x="{col_x + 34:g}" y="{ty0 + 44:.1f}" fill="{SOFT}" font-size="12" '
                   f'font-family="{_MONO_FF}">{val}</text>')
        if gauge is not None:
            gv, glo, ghi, gid, gunit = gauge
            gx, gy = col_x + 62.0, ty0 + 54.0
            gw = col_w - 62.0 - 40.0                 # leave room for the range endpoints
            out.append(_inband_els(gx, gy, gw, gv, glo, ghi, gid, status))
            elo = f"{glo * 100:.0f}%" if gunit == "frac_back" else f"{glo:g}"
            ehi = f"{ghi * 100:.0f}%" if gunit == "frac_back" else f"{ghi:g}"
            out.append(f'<text x="{gx - 6:.1f}" y="{gy + 3.4:.1f}" fill="{MUTE}" font-size="9" '
                       f'font-family="{_MONO_FF}" text-anchor="end">{elo}</text>')
            out.append(f'<text x="{gx + gw + 6:.1f}" y="{gy + 3.4:.1f}" fill="{MUTE}" font-size="9" '
                       f'font-family="{_MONO_FF}">{ehi}</text>')
        y = cy + gap
    return "".join(out)


def _legend_svg(y: float) -> str:
    x, out = 20.0, []
    for lab, c in (("Good", GOOD), ("Watch", AMBER), ("Concern", CONCERN), ("Not detected", GHOST)):
        out.append(f'<circle cx="{x:.1f}" cy="{y:g}" r="5" fill="{c}"/>'
                   f'<text x="{x + 12:.1f}" y="{y + 4:g}" fill="{SOFT}" font-size="12" '
                   f'font-family="{_UI_FF}">{lab}</text>')
        x += len(lab) * 7.0 + 46
    return "".join(out)


def posture_chart_svg(view: str, data: dict, face_left: bool = False, thresholds=None) -> str:
    """Enlarged figure (left) + per-joint 'you · ideal' callouts (right) + a compact
    legend. ``data``: {metric_name: (status, value_or_None)}. ``face_left`` mirrors the
    sagittal figure; ``thresholds`` supplies the ideal target + unit (callouts show
    value-only without it)."""
    if view == "front":
        fig, joints = _posture_front(data)
    else:
        _mt = thresholds.metrics.get("forward_trunk_lean") if thresholds else None
        fig, joints = _posture_side(data, face_left, _mt.ideal if _mt else 2.5)
    sc, ty = 1.15, 6.0
    tx = -24.0 if view == "side" else -70.0   # side shifts right to fit the horse silhouette

    specs = []
    for name, (jx0, jy0) in joints.items():
        status, val = _g(data, name)
        if status == "none" or val is None:
            continue
        mt = thresholds.metrics.get(name) if (thresholds and name in thresholds.metrics) else None
        unit = mt.unit if mt else "deg"
        # back rounding reads as 'N% rounded' (a % of back length) rather than a raw fraction
        txt = f"{val * 100:.0f}% rounded" if name == "back_roundness" else f"you {_fmt_val(val, unit)}"
        gauge = None
        if mt is not None:
            txt += f" · ideal {_fmt_val(mt.ideal, unit)}"
            lo, hi = mt.acceptable
            gauge = (val, lo, hi, mt.ideal, unit)
        specs.append((tx + sc * jx0, ty + sc * jy0, _SHORT.get(name, name), txt, status, gauge))

    # side view carries up to 5 callouts (incl. back rounding); front carries 4
    vh = 480 if view == "side" else 430
    return (f'<svg viewBox="0 0 600 {vh}" width="100%" preserveAspectRatio="xMidYMid meet" fill="none">'
            f'<g transform="translate({tx:g},{ty:g}) scale({sc:g})">{fig}</g>'
            f'{_callouts_svg(specs)}{_legend_svg(vh - 24)}</svg>')


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
