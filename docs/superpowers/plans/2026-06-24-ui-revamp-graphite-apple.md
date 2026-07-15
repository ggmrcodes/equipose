# equipose UI Revamp — "Graphite Instrument" (Apple-language) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dusty-rose "warm night clinic" theme with a monochrome warm-charcoal "graphite instrument" theme that follows Apple's Human Interface Guidelines, removing the AI-generated look.

**Architecture:** The design system lives in three places — `.streamlit/config.toml` (Streamlit theme), `src/equipose/dashboard/ui.py` (palette constants + one injected `CSS` f-string + pure `*_html` builders), and `src/equipose/dashboard/glyphs.py` (pure SVG builders). The flow renders builders through Streamlit in `flow.py`/`flow_review.py`. We swap the accent to bone, replace designer fonts with the system San Francisco stack, restyle components to Apple patterns (toolbar, source-list sidebar, Large Title, inset grouped lists, segmented control), and update the existing tests that hard-code the old design.

**Tech Stack:** Python 3.11, Streamlit ≥1.36 (installed 1.58), Altair, pytest. CSS injected via `st.markdown(unsafe_allow_html=True)`. No build step.

## Global Constraints

- Keep the warm-charcoal DARK base `#17120F`. Not light, not cold blue-black.
- The ONLY hue in the app is functional posture status: good `#86CFA0` ✓, watch `#E8BE78` ◐, concern `#EC8A74` ▲. Status is never color-alone (glyph + text label retained).
- Accent / emphasis = warm bone `#FBF5EF`. No pink anywhere.
- Fonts: system San Francisco stack `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif`; numerals `ui-monospace, "SF Mono", Menlo, "JetBrains Mono", monospace`. JetBrains Mono stays self-hosted as the only vendored face.
- No runtime network calls: `ui.CSS` must contain no `http://` / `https://`. System fonts are OS-local (allowed); the only `@font-face` URLs are the local `app/static/fonts/JetBrainsMono-*.woff2`.
- WCAG AA contrast on dark. Bone-fill buttons use dark ink text `#17120F`.
- Public Python API of `ui.py` is unchanged (same function names/signatures): `inject_theme, app_header, header_html, stepper, stepper_html, section, section_html, status_chip, status_chip_neutral, score_readout, score_readout_html, metrics_table, metrics_table_html, posture_panel, score_breakdown(_html), trend_chart, disclaimer, footer, review_overview(_html), review_history(_html)`. Only their output/styling changes.
- Verification gate is `./.venv/bin/pytest` (no linter is configured in this repo). Run from the equipose dir: `/Users/macbook/Desktop/2026_WORK/equipose`.
- Commits: do NOT commit unless the human approves in-turn. equipose is currently untracked inside the Desktop-wide git repo; resolve repo ownership before any commit. The "Step 5: Commit" steps below are written for when commit is approved; if not approved, do the `git add` dry-run/skip and move on.

---

## File Structure

- `.streamlit/config.toml` — Streamlit theme tokens (`primaryColor` → bone).
- `src/equipose/dashboard/ui.py` — palette constants, the `CSS` f-string (full Apple rework), and three builder changes (`header_html`, `stepper_html`, `metrics_table_html`).
- `src/equipose/dashboard/glyphs.py` — palette constants (ACCENT → bone), thinner score dial.
- `src/equipose/dashboard/flow.py` — render the step source-list into `st.sidebar`.
- `.impeccable.md`, `CLAUDE.md` — design-context source of truth updated.
- `tests/test_dashboard_smoke.py`, `tests/test_glyphs.py` — rewrite assertions that hard-code the old design; add structure tests for the new builders.

---

## Task 1: Foundation recolor — palette tokens + config

**Files:**
- Modify: `.streamlit/config.toml`
- Modify: `src/equipose/dashboard/ui.py:16-27` (palette constants)
- Modify: `src/equipose/dashboard/glyphs.py:17-28` (palette constants)
- Test: `tests/test_dashboard_smoke.py`, `tests/test_glyphs.py`

**Interfaces:**
- Produces: `ui.BG, ui.PANEL, ui.PANEL_HI, ui.LINE, ui.TEXT, ui.SOFT, ui.MUTE, ui.ACCENT, ui.ACCENT_PRESS, ui.BTN_INK` (str hex); `glyphs.ACCENT` (bone). Status constants unchanged.

- [ ] **Step 1: Write the failing test** — add to `tests/test_dashboard_smoke.py`:

```python
def test_palette_is_monochrome_bone_no_rose():
    from equipose.dashboard import ui, glyphs

    # accent is warm bone, the old dusty-rose is gone everywhere
    assert ui.ACCENT.upper() == "#FBF5EF"
    assert glyphs.ACCENT.upper() == "#FBF5EF"
    for mod in (ui, glyphs):
        for name in dir(mod):
            val = getattr(mod, name)
            if isinstance(val, str):
                assert "e08a9b" not in val.lower(), f"rose leak in {mod.__name__}.{name}"
                assert "eca1b0" not in val.lower(), f"rose-hover leak in {mod.__name__}.{name}"
    # warm-charcoal base kept
    assert ui.BG.upper() == "#17120F"
    # bone buttons use dark ink text for AA contrast
    assert ui.BTN_INK.upper() == "#17120F"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_dashboard_smoke.py::test_palette_is_monochrome_bone_no_rose -v`
Expected: FAIL (`ui.ACCENT` is `#E08A9B`; `ui.BTN_INK` does not exist).

- [ ] **Step 3: Implement — ui.py palette** — replace `ui.py:16-27` with:

```python
# ---- palette (warm dark, monochrome — "graphite instrument") ---------------
BG = "#17120F"          # warm near-black charcoal (kept)
PANEL = "#1E1814"       # grouped-list / surface fill
PANEL_HI = "#251E19"    # elevated fill (selected segment, hover)
LINE = "rgba(242,233,226,0.10)"  # hairline separator (warm white, low alpha)
TEXT = "#F2E9E2"        # warm off-white
SOFT = "#B8A99E"        # warm taupe-gray (secondary label)
MUTE = "#8A7A6E"        # warm muted (tertiary label)
ACCENT = "#FBF5EF"      # warm bone — the one emphasis tone (replaces rose)
ACCENT_PRESS = "#ECE3DA"  # pressed bone
BTN_INK = "#17120F"     # dark ink text on bone-filled buttons
AMBER_PROV = "#E8BE78"  # flags provisional/needs-literature ranges
```

Note: `ACCENT_BG` (the old rose tint) is removed; any remaining `ACCENT_BG` reference in the CSS is handled in Task 5.

- [ ] **Step 4: Implement — glyphs.py palette** — replace `glyphs.py:17-28` with:

```python
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
```

- [ ] **Step 5: Implement — config.toml** — set the accent to bone. Replace the `primaryColor` line in `.streamlit/config.toml`:

```toml
primaryColor = "#FBF5EF"             # warm bone — the one emphasis tone
```

(Leave `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`, `[server]`, `[browser]` unchanged.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_dashboard_smoke.py::test_palette_is_monochrome_bone_no_rose tests/test_glyphs.py -v`
Expected: the new test PASSES. `test_glyphs.py` still passes (it references the `glyphs.ACCENT` constant, not the literal hex). If `test_glyphs.py::test_logo_mark_is_svg` fails, it is because `header`/logo CSS in later tasks — not here; it should pass now.

- [ ] **Step 7: Commit** (only if commit approved — see Global Constraints)

```bash
git add .streamlit/config.toml src/equipose/dashboard/ui.py src/equipose/dashboard/glyphs.py tests/test_dashboard_smoke.py
git commit -m "feat(ui): swap rose accent for monochrome bone palette"
```

---

## Task 2: Type system — San Francisco stack, drop designer fonts

**Files:**
- Modify: `src/equipose/dashboard/ui.py` (`_FONT_FACES` `ui.py:37-52`, typography rules in `CSS`)
- Test: `tests/test_dashboard_smoke.py`

**Interfaces:**
- Produces: `ui.CSS` contains the SF system stack and CSS vars `--font-ui`, `--font-mono`; contains no `Bricolage`/`Hanken` `@font-face`; keeps the two `JetBrainsMono` faces; contains no `http`/`https`; contains `app/static/fonts/`.

- [ ] **Step 1: Rewrite the failing tests** — in `tests/test_dashboard_smoke.py`, replace `test_typography_uses_new_families_not_plex` and `test_fonts_are_vendored_for_offline_use` with:

```python
def test_typography_uses_system_san_francisco_stack():
    from equipose.dashboard import ui

    # San Francisco via the system stack (OS-provided, no files shipped)
    assert "-apple-system" in ui.CSS and "BlinkMacSystemFont" in ui.CSS
    assert "SF Pro Text" in ui.CSS
    assert "ui-monospace" in ui.CSS and "SF Mono" in ui.CSS
    # designer pairing fully removed from the stylesheet
    assert "Bricolage" not in ui.CSS and "Hanken" not in ui.CSS
    assert "Plex" not in ui.CSS
    # JetBrains Mono kept as the only vendored fallback face
    assert "JetBrainsMono-400.woff2" in ui.CSS


def test_only_jetbrains_mono_is_vendored_referenced():
    """The one self-hosted face is JetBrains Mono, served locally (offline)."""
    from equipose.dashboard import ui

    assert ui.CSS.count("@font-face") == 2          # JetBrainsMono 400 + 500 only
    assert "app/static/fonts/JetBrainsMono" in ui.CSS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/pytest tests/test_dashboard_smoke.py::test_typography_uses_system_san_francisco_stack tests/test_dashboard_smoke.py::test_only_jetbrains_mono_is_vendored_referenced -v`
Expected: FAIL (CSS still has Bricolage/Hanken `@font-face` and no `-apple-system`).

- [ ] **Step 3: Implement — `_FONT_FACES`** — replace `ui.py:37-52` with only the mono faces:

```python
_FONT_FACES = """
@font-face{font-family:'JBMono';font-weight:400;font-style:normal;font-display:swap;
  src:url('app/static/fonts/JetBrainsMono-400.woff2') format('woff2');}
@font-face{font-family:'JBMono';font-weight:500;font-style:normal;font-display:swap;
  src:url('app/static/fonts/JetBrainsMono-500.woff2') format('woff2');}
"""
```

- [ ] **Step 4: Implement — typography vars + rules** — this is folded into the full CSS rewrite in Task 5, but the two rules the tests need are: add to `:root` —

```css
--font-ui:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",system-ui,sans-serif;
--font-mono:ui-monospace,"SF Mono",Menlo,"JBMono",monospace;
```

and the global typography block becomes:

```css
html, body, .stApp, [class*="css"], input, textarea, button, select {
  font-family:var(--font-ui); color:var(--text);
}
h1,h2,h3,h4 { font-family:var(--font-ui); color:var(--text);
  letter-spacing:-0.021em; font-weight:700; }
.eq-num { font-family:var(--font-mono); font-variant-numeric:tabular-nums; }
```

(Replace every other `'Brico'`, `'Hanken'`, `'Mono'` font-family reference in the CSS with `var(--font-ui)` or `var(--font-mono)` accordingly — done wholesale in Task 5.)

- [ ] **Step 5: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_dashboard_smoke.py -k "typography or vendored or external_url" -v`
Expected: PASS (including the unchanged `test_theme_css_has_no_external_url`).

- [ ] **Step 6: Commit** (if approved)

```bash
git add src/equipose/dashboard/ui.py tests/test_dashboard_smoke.py
git commit -m "feat(ui): adopt system San Francisco font stack, drop designer fonts"
```

---

## Task 3: Builder markup — toolbar, source-list stepper, grouped metrics list

**Files:**
- Modify: `src/equipose/dashboard/ui.py` (`header_html` `:251-259`, `stepper_html` `:267-279`, `metrics_table_html` `:337-378`)
- Test: `tests/test_dashboard_smoke.py`

**Interfaces:**
- Produces:
  - `header_html(patient=None) -> str` → `<div class="eq-head">…<span class="eq-word">equipose</span>… [eq-pchip]</div>`, no rose `<b>`, no sub-tagline.
  - `stepper_html(steps, active) -> str` → `<nav class="eq-srclist"><div class="eq-srcrow {active|done|}"><span class="eq-srcdot">…</span><span class="eq-srclabel">…</span></div>…</nav>`.
  - `metrics_table_html(metrics, thresholds=None) -> str` → `<div class="eq-group">` of `<div class="eq-grow">` rows (no `<table>`).

- [ ] **Step 1: Rewrite/extend the failing tests** — in `tests/test_dashboard_smoke.py`, replace `test_stepper_marks_active_and_done_in_both_layouts` with the source-list version and add toolbar + grouped-list tests:

```python
def test_stepper_is_apple_source_list():
    from equipose.dashboard import ui

    html = ui.stepper_html(["Patient", "Capture", "Read"], active=1)
    assert "eq-srclist" in html
    assert "eq-srcrow active" in html        # current step
    assert "eq-srcrow done" in html          # completed step
    assert "✓" in html                       # done rows show a check
    assert "Read" in html
    # old pill/rail markup is gone
    assert "eq-railv" not in html and "eq-steps" not in html


def test_toolbar_has_wordmark_and_patient_no_rose():
    from equipose.dashboard import ui

    html = ui.header_html("P001")
    assert "eq-head" in html and "equipose" in html
    assert "P001" in html and "eq-pchip" in html
    assert "<b>" not in html                  # no rose-emphasized 'pose'


def test_metrics_render_as_inset_grouped_list():
    from types import SimpleNamespace
    from equipose.dashboard import ui

    m = SimpleNamespace(name="forward_trunk_lean", unit="°", mean=4.2,
                        reliability="primary", pct_in_range=0.9,
                        n_total_frames=10, confidence=0.82)
    html = ui.metrics_table_html([m])
    assert "eq-group" in html and "eq-grow" in html
    assert "<table" not in html               # not a ruled table anymore
    assert "forward trunk lean" in html and "4.2" in html
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./.venv/bin/pytest tests/test_dashboard_smoke.py -k "source_list or toolbar or grouped_list" -v`
Expected: FAIL (old `eq-railv`/`eq-step`/`<table>` markup still emitted).

- [ ] **Step 3: Implement — `header_html`** — replace `ui.py:251-259`:

```python
def header_html(patient: str | None = None) -> str:
    chip = ""
    if patient:
        chip = (f'<span class="eq-pchip"><span class="k">Patient</span>'
                f'<span class="v">{patient}</span></span>')
    return (f'<div class="eq-head"><div class="eq-brandrow">{glyphs.logo_mark_svg()}'
            f'<span class="eq-word">equipose</span></div>{chip}</div>')
```

- [ ] **Step 4: Implement — `stepper_html`** — replace `ui.py:267-279`:

```python
def stepper_html(steps: list[str], active: int) -> str:
    rows = []
    for i, label in enumerate(steps):
        state = "active" if i == active else ("done" if i < active else "")
        mark = "✓" if i < active else str(i + 1)
        rows.append(f'<div class="eq-srcrow {state}"><span class="eq-srcdot">{mark}</span>'
                    f'<span class="eq-srclabel">{label}</span></div>')
    return f'<nav class="eq-srclist">{"".join(rows)}</nav>'
```

- [ ] **Step 5: Implement — `metrics_table_html`** — replace `ui.py:337-378` with a grouped-list builder. Keeps tier, value, range, status, and confidence, but as Apple list rows (primary line + secondary sub-line):

```python
def metrics_table_html(metrics, thresholds=None) -> str:
    show_ref = thresholds is not None
    rows = ""
    for m in metrics:
        tier_cls = "best" if m.reliability == "best_effort" else ""
        tier_txt = "best-effort" if m.reliability == "best_effort" else "primary"
        tier = f'<span class="eq-tier {tier_cls}">{tier_txt}</span>'

        if m.mean is None:
            val = f'<span class="eq-val" style="color:{MUTE};">n/a</span>'
        else:
            val = f'<span class="eq-val eq-num">{m.mean:.2f}<span class="u">{m.unit}</span></span>'

        if m.pct_in_range is None:
            stat = status_chip_neutral("Not detected")
        else:
            good = m.pct_in_range >= 0.5
            _, fg, bg, glyph = _STATUS["green"] if good else _STATUS["red"]
            label = "In range" if good else "Out of range"
            pct = (f' <span class="pct eq-num">{m.pct_in_range * 100:.0f}%</span>'
                   if m.n_total_frames > 1 else "")
            stat = (f'<span class="eq-chip" style="color:{fg};background:{bg};">'
                    f'<span class="g">{glyph}</span>{label}</span>{pct}')

        sub_bits = []
        if show_ref:
            rng = thresholds.format_range(m.name)
            basis = thresholds.basis(m.name).replace('"', "'")
            prov = ' · needs-lit' if basis.startswith("PLACEHOLDER") else ""
            sub_bits.append(f'<span title="{basis}">range {rng}{prov}</span>')
        cw = max(2, min(100, int(round(m.confidence * 100))))
        sub_bits.append(f'<span class="eq-conf"><span class="eq-bar">'
                        f'<i style="width:{cw}%"></i></span>'
                        f'<span class="eq-num">conf {m.confidence:.2f}</span></span>')
        sub = f'<div class="eq-gsub">{" · ".join(sub_bits)}</div>'

        rows += (f'<div class="eq-grow"><div class="eq-gmain">'
                 f'<span class="eq-gname">{_pretty(m.name)}</span> {tier}{sub}</div>'
                 f'<div class="eq-gtrail">{val}{stat}</div></div>')
    return f'<div class="eq-group">{rows}</div>'
```

(`_pretty`, `_STATUS`, `status_chip_neutral` are unchanged and already defined above this function.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_dashboard_smoke.py -v`
Expected: PASS (all smoke tests; the `callable(...)` checks still hold — function names unchanged).

- [ ] **Step 7: Commit** (if approved)

```bash
git add src/equipose/dashboard/ui.py tests/test_dashboard_smoke.py
git commit -m "feat(ui): toolbar wordmark, source-list stepper, inset grouped metrics"
```

---

## Task 4: Flow wiring — steps into the sidebar source list

**Files:**
- Modify: `src/equipose/dashboard/flow.py:60-77` (`render`)
- Test: `tests/test_dashboard_smoke.py` (existing `test_dashboard_imports_and_callables` must still pass)

**Interfaces:**
- Consumes: `ui.stepper(STEPS, step)` (Task 3 output).
- Produces: in capture mode the step source list renders inside `st.sidebar`; `flow.render` signature unchanged.

- [ ] **Step 1: Implement — render stepper in the sidebar** — replace `flow.py:60-77` (`render`) with:

```python
def render(store: Store) -> None:
    import streamlit as st

    _init()
    ui.app_header(st.session_state.eq_patient)
    _mode_toggle()

    if st.session_state.eq_mode == "review":
        flow_review.render(store)
    else:
        step = st.session_state.eq_step
        with st.sidebar:
            st.markdown('<div class="eq-railhead">STEPS</div>', unsafe_allow_html=True)
            ui.stepper(STEPS, step)
        if step == 0:
            _step_patient(store)
        elif step == 1:
            _step_capture(store)
        else:
            _step_read(store)

    ui.footer("equipose · local-only, no data leaves this machine · faces are blurred in any export.")
```

- [ ] **Step 2: Run the smoke + full suite to verify nothing broke**

Run: `./.venv/bin/pytest -q`
Expected: PASS (import graph intact; `flow.STEPS == ["Patient","Capture","Read"]`).

- [ ] **Step 3: Commit** (if approved)

```bash
git add src/equipose/dashboard/flow.py
git commit -m "feat(ui): render guided steps as a macOS-style sidebar source list"
```

---

## Task 5: The Apple stylesheet — full CSS rework

**Files:**
- Modify: `src/equipose/dashboard/ui.py` (`CSS` f-string `:54-236`)
- Test: `tests/test_dashboard_smoke.py` (no external url; the visual result is verified in Task 8)

**Interfaces:**
- Consumes: palette vars (Task 1), font vars (Task 2), builder classes `eq-head/eq-word/eq-pchip`, `eq-srclist/eq-srcrow/eq-srcdot/eq-srclabel/eq-railhead`, `eq-group/eq-grow/eq-gmain/eq-gname/eq-gsub/eq-gtrail/eq-val`, `eq-eyebrow/eq-title/eq-lead`, `eq-score`, `eq-chip`, `eq-tier`, `eq-conf/eq-bar`.

- [ ] **Step 1: Replace the `CSS` f-string** in `ui.py` (the block currently spanning `:54-236`) with the following. It un-hides and styles the sidebar, removes the rose glow + gradients, adds the source list, inset groups, segmented control, and Apple button geometry:

```python
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
  --elev:0 1px 2px rgba(0,0,0,0.35), 0 8px 24px rgba(0,0,0,0.22);
}}

/* hide default Streamlit chrome (NOT the sidebar — we use it as a source list) */
header[data-testid="stHeader"] {{ background:transparent; height:0; }}
#MainMenu, footer {{ visibility:hidden; }}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display:none !important; }}

/* flat warm canvas — no rose glow */
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
  background:rgba(242,233,226,0.08); color:var(--mute); font-family:var(--font-mono);
  font-size:.78rem; flex:0 0 auto; }}
.eq-srcrow.active .eq-srcdot {{ background:var(--accent); color:var(--btn-ink); }}
.eq-srcrow.done .eq-srcdot {{ background:rgba(134,207,160,0.18); color:#86CFA0; }}

/* ---- toolbar header ---- */
.eq-head {{ display:flex; align-items:center; justify-content:space-between; gap:1rem;
  padding-bottom:.85rem; margin-bottom:1.1rem; border-bottom:1px solid var(--line); }}
.eq-brandrow {{ display:flex; align-items:center; gap:.1rem; }}
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

/* ---- buttons (macOS push-button) ---- */
.stButton > button, .stDownloadButton > button {{
  border-radius:var(--radius-sm); border:1px solid var(--line); background:var(--panel-hi);
  color:var(--text); font-weight:500; padding:.5rem 1.05rem;
  transition:transform .06s ease, background .12s, border-color .12s; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ background:#2E251F; }}
.stButton > button:active {{ transform:translateY(1px); }}
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {{
  background:var(--accent); border-color:var(--accent); color:var(--btn-ink); font-weight:600; }}
.stButton > button[kind="primary"]:hover {{ background:var(--accent-press); border-color:var(--accent-press); }}
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
  box-shadow:0 1px 2px rgba(0,0,0,0.3); }}
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
.eq-chip {{ display:inline-flex; align-items:center; gap:.42rem; font-size:.78rem; font-weight:600;
  padding:.2rem .62rem; border-radius:999px; white-space:nowrap; line-height:1.35; }}
.eq-chip .g {{ font-size:.78rem; line-height:1; }}
.eq-tier {{ display:inline-block; font-family:var(--font-mono); font-size:.62rem; letter-spacing:.06em;
  text-transform:uppercase; padding:.1rem .42rem; border-radius:5px; border:1px solid var(--line); color:var(--soft); }}
.eq-tier.best {{ color:var(--mute); border-style:dashed; }}

/* ---- score readout (flat, soft elevation) ---- */
.eq-score {{ display:flex; align-items:center; gap:1.3rem; background:var(--panel);
  border:1px solid var(--line); border-radius:16px; padding:1.3rem 1.5rem; box-shadow:var(--elev); }}
.eq-score .big {{ font-family:var(--font-mono); font-size:3.2rem; font-weight:500; line-height:.9;
  letter-spacing:-0.02em; color:var(--text); }}
.eq-score .den {{ color:var(--mute); font-size:1.05rem; font-family:var(--font-mono); }}
.eq-score .lbl {{ font-family:var(--font-mono); font-size:.66rem; letter-spacing:.1em;
  text-transform:uppercase; color:var(--soft); margin-bottom:.45rem; }}
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
.eq-bar {{ width:52px; height:5px; border-radius:3px; background:rgba(242,233,226,0.12); overflow:hidden; }}
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
```

- [ ] **Step 2: Confirm no-network invariant still holds**

Run: `./.venv/bin/pytest tests/test_dashboard_smoke.py::test_theme_css_has_no_external_url -v`
Expected: PASS (`app/static/fonts/` present via JetBrains Mono; no `http`/`https`).

- [ ] **Step 3: Run the full suite**

Run: `./.venv/bin/pytest -q`
Expected: PASS.

- [ ] **Step 4: Commit** (if approved)

```bash
git add src/equipose/dashboard/ui.py
git commit -m "feat(ui): Apple-language stylesheet — source list, grouped lists, segmented controls, flat surfaces"
```

---

## Task 6: Score dial — thinner, precise, status-colored arc

**Files:**
- Modify: `src/equipose/dashboard/glyphs.py:92-117` (`score_dial_svg`)
- Test: `tests/test_glyphs.py`

**Interfaces:**
- Consumes: `glyphs` palette (Task 1).
- Produces: `score_dial_svg(score, band, size=138) -> str` — track + ticks in neutral, value arc in band color (the one allowed color), thinner strokes; still renders `>NN<` and `/ 100`.

- [ ] **Step 1: Update the test** — in `tests/test_glyphs.py`, extend `test_score_dial_renders_number_and_band_color` to assert the lighter stroke weight:

```python
def test_score_dial_renders_number_and_band_color():
    s = glyphs.score_dial_svg(56, "red")
    assert "<svg" in s and ">56<" in s
    assert glyphs.CONCERN in s            # value arc colored by band (status)
    assert "/ 100" in s
    assert 'stroke-width="5"' in s        # thinner, Apple-precise arc
    z = glyphs.score_dial_svg(0, "red")
    assert ">0<" in z
```

- [ ] **Step 2: Run test to verify it fails**

Run: `./.venv/bin/pytest tests/test_glyphs.py::test_score_dial_renders_number_and_band_color -v`
Expected: FAIL (current stroke-width is `7`).

- [ ] **Step 3: Implement** — replace `glyphs.py:92-117` (`score_dial_svg`):

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./.venv/bin/pytest tests/test_glyphs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit** (if approved)

```bash
git add src/equipose/dashboard/glyphs.py tests/test_glyphs.py
git commit -m "feat(ui): thinner precise score dial"
```

---

## Task 7: Update the design-context source of truth

**Files:**
- Modify: `.impeccable.md` (Aesthetic Direction + Palette/Type/Constraints)
- Modify: `CLAUDE.md` (Aesthetic Direction + Design Principles + Constraints)

**Interfaces:** none (docs only).

- [ ] **Step 1: Update `.impeccable.md`** — change the Aesthetic Direction from "Warm night clinic / dusty-rose" to:

> **"Graphite instrument"** — a warm-charcoal DARK workspace styled on Apple's
> Human Interface Guidelines. Monochrome: the accent is **warm bone `#FBF5EF`**
> (no pink). The only hue is functional posture status (sage/amber/clay). Type is
> the **system San Francisco stack** (`-apple-system`…); numerals use SF Mono /
> JetBrains Mono. Apple patterns: unified toolbar, **source-list sidebar** for the
> Patient→Capture→Read steps, left-aligned **Large Title** + subtitle, **inset
> grouped lists** with hairline separators, real **segmented controls**, soft
> low-alpha elevation, 8-pt spacing. The faint goniometer field is kept as the
> neutral negative-space identity. Anti-references: AI-slop (accent-caps eyebrows,
> pills-on-everything, card-in-card, radial glows/gradients, trendy display fonts),
> cold blue-black dark mode, glassmorphism, emoji-as-UI.

Update the Palette bullet (bone, not rose), the Type bullet (San Francisco system stack; JetBrains Mono only vendored face), and the Constraints (fonts are OS-provided system fonts; only JetBrains Mono self-hosted at `app/static/fonts/`).

- [ ] **Step 2: Update `CLAUDE.md`** — mirror the same Aesthetic Direction / Design Principles / Constraints edits so the checked-in project instructions match. Principle 4 becomes "Numerals are monospaced (SF Mono / JetBrains Mono)". Principle 2 becomes "One emphasis tone (warm bone), used sparingly".

- [ ] **Step 3: Commit** (if approved)

```bash
git add .impeccable.md CLAUDE.md
git commit -m "docs: update design context to graphite-instrument (Apple) direction"
```

---

## Task 8: Visual QA against Apple HIG + full green suite

**Files:** none (verification + any small CSS follow-ups in `ui.py`).

- [ ] **Step 1: Full test suite green**

Run: `./.venv/bin/pytest -q`
Expected: PASS (entire suite).

- [ ] **Step 2: Launch the app on a clean port**

Run: `./.venv/bin/streamlit run src/equipose/dashboard/app.py --server.port 8600 --server.headless true`
(If the browser cannot reach localhost, first resolve ephemeral-port exhaustion — see the prior debugging note; the server itself is fine.)

- [ ] **Step 3: Screenshot each step and review against HIG** — use the `/browse` skill (per user routing) or the `verify`/`run` skill to capture: (a) Patient step with the sidebar source list, (b) Capture step with segmented controls + uploader, (c) Read step with score readout + posture chart + grouped metrics list, (d) Review mode trend chart. For each, check:
  - No pink anywhere; emphasis is bone; status is the only hue.
  - Title is a left-aligned Large Title; the eyebrow is a quiet gray overline, not accent caps.
  - Metrics read as an inset grouped list (hairline separators), not a ruled table.
  - Front/side + photo/video render as segmented controls.
  - Sidebar reads as a source list; active row is bone, done row shows a sage check.
  - Buttons: primary is bone-filled with dark text and passes AA; secondary is subtle.
  - No radial glow / gradients; surfaces are flat with soft elevation on the score card.
  - Numerals are monospaced and tabular; body is San Francisco.

- [ ] **Step 4: Fix any visual issues** found in Step 3 by editing the `CSS` in `ui.py` only (no structural/builder changes). Re-screenshot until each checklist item passes.

- [ ] **Step 5: Final commit** (if approved)

```bash
git add src/equipose/dashboard/ui.py
git commit -m "polish(ui): visual QA pass against Apple HIG"
```

---

## Self-Review

**Spec coverage:**
- Keep dark base → Task 1 (BG kept). ✓
- Bone accent, no rose → Tasks 1, 5 (palette + CSS) + `test_palette_is_monochrome_bone_no_rose`. ✓
- Status the only color → unchanged `_STATUS`; verified in Task 8. ✓
- System SF fonts, drop designer fonts → Task 2 + tests. ✓
- Toolbar / source-list sidebar / Large Title / inset grouped list / segmented control / soft elevation → Tasks 3, 4, 5. ✓
- Score dial thinner bone/status → Task 6. ✓
- Trend line + confidence bar bone → automatic via `ACCENT` token (Task 1) + `.eq-bar` CSS (Task 5). ✓
- Goniometer field kept, neutral → already uses `SOFT`; unchanged (Task 1 keeps SOFT). ✓
- Remove rose glow / gradients → Task 5 (`.stApp`, `.eq-score`). ✓
- `.impeccable.md` + `CLAUDE.md` updated → Task 7. ✓
- Offline / no network → preserved; `test_theme_css_has_no_external_url` + `test_only_jetbrains_mono_is_vendored_referenced`. ✓
- AA contrast → `BTN_INK` on bone (Task 1); checked in Task 8. ✓

**Placeholder scan:** No TBD/TODO; every code/test/CSS step contains the actual content. Task 8 Step 4 is iterative-by-design (visual polish) but bounded by an explicit checklist.

**Type consistency:** Builder class names emitted in Task 3 (`eq-srclist/eq-srcrow/eq-srcdot/eq-srclabel`, `eq-group/eq-grow/eq-gmain/eq-gname/eq-gsub/eq-gtrail/eq-val`, `eq-railhead`) all have matching CSS rules in Task 5. Font family token `'JBMono'` defined in `_FONT_FACES` (Task 2) matches `--font-mono` reference (Task 5). `ACCENT_PRESS`/`BTN_INK` defined in Task 1 are referenced in Task 5. `score_dial_svg` signature unchanged. No dangling references.

**Out of scope (unchanged):** analysis pipeline, scoring math, schemas, data model, metric set; font woff2 files remain on disk (only `@font-face` refs to Bricolage/Hanken removed).
