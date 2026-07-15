"""Digital-goniometer overlay for the photo path.

One shared geometry source (`build_overlay_spec`) emits drawable primitives in
image-pixel space; two thin renderers consume it: `overlay_svg` for the crisp
on-screen overlay (JetBrains Mono labels, exact alignment via viewBox) and
`overlay_raster` for the face-blurred PNG download. Degrees only (v1).

No Streamlit here. `overlay_svg` is pure string; `overlay_raster` needs cv2.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from equipose.angles_side import pick_side
from equipose.dashboard import glyphs
from equipose.schemas import Landmark

SEG = "#9A8678"          # muted warm bone
LAYERS = ("skeleton", "reference", "arcs", "labels")

Point = tuple[float, float]


# ---- primitives -----------------------------------------------------------
@dataclass
class Bone:
    p1: Point
    p2: Point
    color: str
    width: float


@dataclass
class Joint:
    p: Point
    color: str
    r: float


@dataclass
class Ref:
    p1: Point
    p2: Point
    color: str
    width: float


@dataclass
class Arc:
    cx: float
    cy: float
    r: float
    start: float   # degrees (cv2/atan2 convention, clockwise, y-down)
    delta: float   # signed sweep, the short way
    color: str
    width: float


@dataclass
class Label:
    x: float
    y: float
    text: str
    color: str
    size: float


@dataclass
class OverlaySpec:
    bones: list[Bone] = field(default_factory=list)
    joints: list[Joint] = field(default_factory=list)
    refs: list[Ref] = field(default_factory=list)
    arcs: list[Arc] = field(default_factory=list)
    labels: list[Label] = field(default_factory=list)


# ---- math helpers ---------------------------------------------------------
def _ang(frm: Point, to: Point) -> float:
    return math.degrees(math.atan2(to[1] - frm[1], to[0] - frm[0]))


def _short(start: float, end: float) -> float:
    """Signed shortest sweep from start to end, in (-180, 180]."""
    return ((end - start + 180) % 360) - 180


def _mid(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _metric_status(m, scoring=None) -> str:
    """good | watch | concern | none. Graded to match the score when ``scoring`` is
    given (near-edge -> watch); binary in-range fallback otherwise."""
    if m.pct_in_range is None:
        return "none"
    if scoring is None:
        return "good" if m.pct_in_range >= 0.5 else "concern"
    from equipose.scoring import metric_band
    return {"green": "good", "yellow": "watch", "red": "concern", "none": "none"}[metric_band(m, scoring)]


def _col(status: str) -> str:
    return (glyphs.GOOD if status == "good" else glyphs.AMBER if status == "watch"
            else glyphs.CONCERN if status == "concern" else glyphs.GHOST)


# ---- edge topology --------------------------------------------------------
_FRONT_EDGES = [
    ("nose", "left_eye"), ("nose", "right_eye"), ("left_eye", "left_ear"),
    ("right_eye", "right_ear"), ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"), ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"), ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"), ("right_knee", "right_ankle"),
]


def _side_edges(s: str):
    return [(f"{s}_ear", f"{s}_shoulder"), (f"{s}_shoulder", f"{s}_hip"),
            (f"{s}_hip", f"{s}_knee"), (f"{s}_knee", f"{s}_ankle"),
            (f"{s}_shoulder", f"{s}_elbow"), (f"{s}_elbow", f"{s}_wrist")]


# Below this confidence a landmark's POSITION is too unreliable to place at all.
_GHOST_FLOOR = 0.08
_FRONT_MARKERS = ("nose", "left_eye", "right_eye", "left_ear", "right_ear",
                  "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
                  "left_wrist", "right_wrist", "left_hip", "right_hip",
                  "left_knee", "right_knee", "left_ankle", "right_ankle")


# ---- spec builder ---------------------------------------------------------
def build_overlay_spec(landmarks: list[Landmark], view: str, metrics, layers,
                       w: int, h: int, vis_threshold: float = 0.3, scoring=None) -> OverlaySpec:
    raw = {lm.name: lm for lm in landmarks}
    P = {n: (lm.x_px, lm.y_px) for n, lm in raw.items() if lm.confidence >= _GHOST_FLOOR}
    Pc = {n: (lm.x_px, lm.y_px) for n, lm in raw.items() if lm.confidence >= vis_threshold}
    conf_ok = set(Pc)  # landmarks confident enough for arcs/reference anchors
    mret = {m.name: m for m in metrics}
    spec = OverlaySpec()

    bone_w = max(2.0, w / 320)
    joint_r = max(3.0, w / 180)
    arc_r = min(max(w * 0.058, 24.0), 72.0)
    arc_w = max(2.5, w / 260)
    ref_w = max(1.0, w / 800)
    fs = min(max(w * 0.021, 12.0), 22.0)

    # Pick the camera-facing side from ALL landmarks, exactly as compute_side does,
    # so the overlay and the metric values always refer to the SAME side.
    side = pick_side(raw) if view == "side" else None
    edges = _side_edges(side) if view == "side" else _FRONT_EDGES
    markers = (("nose", f"{side}_ear", f"{side}_shoulder", f"{side}_elbow",
                f"{side}_wrist", f"{side}_hip", f"{side}_knee", f"{side}_ankle")
               if view == "side" else _FRONT_MARKERS)

    # --- skeleton: show every detected marker; ghost the low-confidence ones ---
    if "skeleton" in layers:
        for a, b in edges:
            if a in P and b in P:
                faint = a not in conf_ok or b not in conf_ok
                spec.bones.append(Bone(P[a], P[b], glyphs.GHOST if faint else SEG, bone_w))
        for n in markers:
            if n in P:
                spec.joints.append(Joint(P[n], SEG if n in conf_ok else glyphs.GHOST, joint_r))

    def metric(name):
        return mret.get(name)

    def _ms(m):  # graded status (matches the score) when scoring is provided
        return _metric_status(m, scoring)

    def drawable(name):
        m = metric(name)
        return m is not None and _ms(m) != "none" and m.mean is not None

    arcs_spec = []  # (vertex, start, delta, status, value) — confident joints only

    def add_joint_angle(name, vname, aname, bname):
        if drawable(name) and all(k in Pc for k in (vname, aname, bname)):
            v = Pc[vname]
            r1, r2 = _ang(v, Pc[aname]), _ang(v, Pc[bname])
            arcs_spec.append((v, r1, _short(r1, r2), _ms(metric(name)), metric(name).mean))

    def add_tilt_h(name, vname, oname):
        if drawable(name) and vname in Pc and oname in Pc:
            v, o = Pc[vname], Pc[oname]
            r1 = _ang(v, o)
            r2 = 0.0 if o[0] >= v[0] else 180.0
            arcs_spec.append((v, r2, _short(r2, r1), _ms(metric(name)), metric(name).mean))

    def add_tilt_v(name, vname, upname):
        if drawable(name) and vname in Pc and upname in Pc:
            v, up = Pc[vname], Pc[upname]
            r1 = _ang(v, up)
            arcs_spec.append((v, -90.0, _short(-90.0, r1), _ms(metric(name)), metric(name).mean))

    if view == "front":
        add_tilt_h("head_tilt", "right_ear", "left_ear")
        add_tilt_h("shoulder_tilt", "right_shoulder", "left_shoulder")
        add_tilt_h("pelvic_obliquity", "right_hip", "left_hip")
        if drawable("trunk_lateral_lean") and all(k in Pc for k in
                                                  ("left_shoulder", "right_shoulder", "left_hip", "right_hip")):
            sh = _mid(Pc["left_shoulder"], Pc["right_shoulder"])
            hp = _mid(Pc["left_hip"], Pc["right_hip"])
            r1 = _ang(hp, sh)
            arcs_spec.append((hp, -90.0, _short(-90.0, r1),
                              _ms(metric("trunk_lateral_lean")), metric("trunk_lateral_lean").mean))
    else:
        s = side
        add_tilt_v("forward_trunk_lean", f"{s}_hip", f"{s}_shoulder")
        add_joint_angle("neck_forward_angle", f"{s}_shoulder", f"{s}_ear", f"{s}_hip")
        add_joint_angle("hip_flexion", f"{s}_hip", f"{s}_shoulder", f"{s}_knee")
        add_joint_angle("knee_angle", f"{s}_knee", f"{s}_hip", f"{s}_ankle")

    for v, start, delta, status, value in arcs_spec:
        color = _col(status)
        if "arcs" in layers:
            spec.arcs.append(Arc(v[0], v[1], arc_r, start, delta, color, arc_w))
            spec.joints.append(Joint(v, color, joint_r * 1.15))  # colored vertex on top
        if "labels" in layers:
            bis = math.radians(start + delta / 2)
            lx = v[0] + (arc_r + fs * 1.1) * math.cos(bis)
            ly = v[1] + (arc_r + fs * 1.1) * math.sin(bis)
            spec.labels.append(Label(lx, ly, f"{abs(value):.0f}°", color, fs))

    # --- reference lines (anchored on confident joints, spanning the figure) ---
    if "reference" in layers and P:
        xs = [p[0] for p in P.values()]
        ys = [p[1] for p in P.values()]
        y0, y1 = min(ys) - 12, max(ys) + 12
        x0, x1 = min(xs) - 12, max(xs) + 12
        if view == "front":
            if "left_hip" in Pc and "right_hip" in Pc:
                hx = _mid(Pc["left_hip"], Pc["right_hip"])[0]
                spec.refs.append(Ref((hx, y0), (hx, y1), glyphs.SOFT, ref_w))
            if "left_shoulder" in Pc and "right_shoulder" in Pc:
                sy = _mid(Pc["left_shoulder"], Pc["right_shoulder"])[1]
                spec.refs.append(Ref((x0, sy), (x1, sy), glyphs.SOFT, ref_w))
            if "left_hip" in Pc and "right_hip" in Pc:
                hy = _mid(Pc["left_hip"], Pc["right_hip"])[1]
                spec.refs.append(Ref((x0, hy), (x1, hy), glyphs.SOFT, ref_w))
            # midline deviation: connector nose -> shoulder/hip axis + ratio label
            if drawable("midline_deviation") and all(k in Pc for k in
                                                     ("nose", "left_shoulder", "right_shoulder", "left_hip", "right_hip")):
                sh = _mid(Pc["left_shoulder"], Pc["right_shoulder"])
                hp = _mid(Pc["left_hip"], Pc["right_hip"])
                proj = _project(Pc["nose"], sh, hp)
                spec.refs.append(Ref(Pc["nose"], proj, _col(_ms(metric("midline_deviation"))), ref_w * 2))
                if "labels" in layers:
                    mp = _mid(Pc["nose"], proj)
                    spec.labels.append(Label(mp[0], mp[1] - fs, f"{metric('midline_deviation').mean:.2f}w",
                                             _col(_ms(metric("midline_deviation"))), fs))
        else:
            if f"{side}_shoulder" in Pc:
                sx = Pc[f"{side}_shoulder"][0]
                spec.refs.append(Ref((sx, y0), (sx, y1), glyphs.SOFT, ref_w))
            if f"{side}_hip" in Pc:
                hy = Pc[f"{side}_hip"][1]
                spec.refs.append(Ref((x0, hy), (x1, hy), glyphs.SOFT, ref_w))

    return spec


def _project(p: Point, a: Point, b: Point) -> Point:
    """Perpendicular projection of p onto line a-b."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return a
    t = ((p[0] - ax) * dx + (p[1] - ay) * dy) / denom
    return (ax + t * dx, ay + t * dy)


# ---- SVG renderer ---------------------------------------------------------
def _arc_path(cx, cy, r, start, delta):
    a0 = math.radians(start)
    a1 = math.radians(start + delta)
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    large = 1 if abs(delta) > 180 else 0
    sweep = 1 if delta >= 0 else 0
    return f"M {x0:.2f} {y0:.2f} A {r:.2f} {r:.2f} 0 {large} {sweep} {x1:.2f} {y1:.2f}"


def overlay_svg(spec: OverlaySpec, w: int, h: int, image_data_uri: str) -> str:
    p = [f'<div class="eq-goni" style="position:relative;width:100%;line-height:0;">',
         f'<img src="{image_data_uri}" alt="" '
         f'style="display:block;width:100%;height:auto;border-radius:14px;"/>',
         f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid meet" '
         f'style="position:absolute;inset:0;width:100%;height:100%;">']
    for r in spec.refs:
        p.append(f'<line x1="{r.p1[0]:.1f}" y1="{r.p1[1]:.1f}" x2="{r.p2[0]:.1f}" y2="{r.p2[1]:.1f}" '
                 f'stroke="{r.color}" stroke-width="{r.width:.1f}" stroke-dasharray="5 7" opacity="0.55"/>')
    for b in spec.bones:
        p.append(f'<line x1="{b.p1[0]:.1f}" y1="{b.p1[1]:.1f}" x2="{b.p2[0]:.1f}" y2="{b.p2[1]:.1f}" '
                 f'stroke="{b.color}" stroke-width="{b.width:.1f}" stroke-linecap="round" opacity="0.55"/>')
    for a in spec.arcs:
        d = _arc_path(a.cx, a.cy, a.r, a.start, a.delta)
        p.append(f'<path d="{d}" stroke="rgba(20,16,12,0.6)" stroke-width="{a.width + 3:.1f}" '
                 f'fill="none" stroke-linecap="round"/>')  # dark halo for legibility
        p.append(f'<path d="{d}" stroke="{a.color}" stroke-width="{a.width:.1f}" '
                 f'fill="none" stroke-linecap="round"/>')
    for j in spec.joints:
        p.append(f'<circle cx="{j.p[0]:.1f}" cy="{j.p[1]:.1f}" r="{j.r:.1f}" fill="{j.color}"/>')
    for lb in spec.labels:
        tw = len(lb.text) * lb.size * 0.62 + lb.size * 0.7
        th = lb.size * 1.5
        p.append(f'<g><rect x="{lb.x - tw/2:.1f}" y="{lb.y - th*0.72:.1f}" width="{tw:.1f}" height="{th:.1f}" '
                 f'rx="{th*0.28:.1f}" fill="rgba(20,16,12,0.66)"/>'
                 f'<text x="{lb.x:.1f}" y="{lb.y + lb.size*0.34:.1f}" fill="{lb.color}" '
                 f'font-family="Mono, ui-monospace, monospace" font-size="{lb.size:.1f}" '
                 f'font-weight="500" text-anchor="middle">{lb.text}</text></g>')
    p.append("</svg></div>")
    return "".join(p)


# ---- raster renderer ------------------------------------------------------
def _bgr(hex_color: str) -> tuple[int, int, int]:
    hx = hex_color.lstrip("#")
    r, g, b = int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)
    return (b, g, r)


def overlay_raster(img_bgr, spec: OverlaySpec):
    import cv2

    out = img_bgr.copy()
    for r in spec.refs:
        cv2.line(out, (int(r.p1[0]), int(r.p1[1])), (int(r.p2[0]), int(r.p2[1])),
                 _bgr(r.color), max(1, int(r.width)), cv2.LINE_AA)
    for b in spec.bones:
        cv2.line(out, (int(b.p1[0]), int(b.p1[1])), (int(b.p2[0]), int(b.p2[1])),
                 _bgr(b.color), max(1, int(b.width)), cv2.LINE_AA)
    for a in spec.arcs:
        a0 = int(a.start)
        a1 = int(a.start + a.delta)
        lo, hi = min(a0, a1), max(a0, a1)
        cv2.ellipse(out, (int(a.cx), int(a.cy)), (int(a.r), int(a.r)), 0,
                    lo, hi, (16, 12, 20), max(2, int(a.width)) + 3, cv2.LINE_AA)  # dark halo
        cv2.ellipse(out, (int(a.cx), int(a.cy)), (int(a.r), int(a.r)), 0,
                    lo, hi, _bgr(a.color), max(2, int(a.width)), cv2.LINE_AA)
    for j in spec.joints:
        cv2.circle(out, (int(j.p[0]), int(j.p[1])), max(2, int(j.r)), _bgr(j.color), -1, cv2.LINE_AA)
    for lb in spec.labels:
        scale = lb.size / 26.0
        (tw, th), _ = cv2.getTextSize(lb.text, cv2.FONT_HERSHEY_DUPLEX, scale, 1)
        x, y = int(lb.x - tw / 2), int(lb.y)
        cv2.rectangle(out, (x - 5, y - th - 5), (x + tw + 5, y + 6), (18, 16, 20), -1)
        cv2.putText(out, lb.text, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, _bgr(lb.color), 1, cv2.LINE_AA)
    return out
