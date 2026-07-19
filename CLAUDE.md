# equipose

AI vision posture monitoring for pediatric hippotherapy (cerebral palsy). Python /
Streamlit. See `README.md` for architecture and `docs/` for the measurement math,
camera protocol, and privacy notes.

## Design Context

> Source of truth: `.impeccable.md` (read by impeccable design skills).

### Users
Pediatric physiotherapists and clinical researchers running CP hippotherapy
sessions (children, GMFCS III, ages 7–10). Laptop use, often in a bright arena or
clinic. They register a patient, analyze front/side video or a single photo, read
posture angles + a snapshot score, and track progress over a 3–6 month program.
Time-pressured domain experts handling pediatric medical data. They value speed,
legibility, and trustworthy numbers over delight.

### Brand Personality
Precise, trustworthy, instrument-grade. Factual, restrained, no fluff. The
interface should inspire confidence that the numbers are real and the tool is
serious — calm focus, never playful or noisy.

### Aesthetic Direction
**"Graphite instrument, on paper"** — a warm-**light** clinical workspace styled on
Apple's Human Interface Guidelines (moved off the original dark theme; a clinician
read the dark UI as "dev-like"). Cool paper ground (bg `#E7EDEF`) + **white cards**
(`#FFFFFF`) + near-black navy ink (`#0C1013`) + a **single slate-blue emphasis tone**
(`#415A69`) — graphite is now the ink, paper the ground. Type: the **system San
Francisco stack** (`-apple-system`, `BlinkMacSystemFont`, `"SF Pro Text"`) with **SF
Mono / JetBrains Mono** for numerals — SF is OS-provided/offline, JetBrains Mono
self-hosted (`static/fonts/`, served at `app/static/`, no CDN). Apple patterns: a
unified toolbar, the guided flow (Patient -> Capture -> Read) as a **source-list
sidebar**, left-aligned **Large Title** + subtitle, **inset grouped lists** with
hairline separators, real **segmented controls**, soft elevation, 8-pt spacing (no
pills). The Reading screen is **answer-first**: a summary hero (score dial + status +
plain-language "why" + position scale) leads, then the big annotated photo, then the
body-chart, then the breakdown. A faint neutral **goniometer field** fills the
negative space; the score dial echoes it as a thin arc. The **body-chart** shows an
outlined rider (measured, status-colored) on a muted **horse** silhouette (context,
never measured). Posture status (good=sage / watch=amber / concern=clay, darkened for
AA on light) is the only color and carries a label + glyph. Anti-references: AI-slop
(accent-caps eyebrows, pills-on-everything, card-in-card, radial glows/gradients,
trendy display fonts, neon glow, emoji-as-UI), cheap neon blue-black, cream/beige
"vibe-coded" palettes, glassmorphism, toy aesthetics.

### Design Principles
1. Calm and clinical — cool paper + white cards, reassuring progress-forward tone.
2. One emphasis tone (slate-blue), used sparingly (actions + emphasis only).
3. Status is never color alone — good/watch/concern carry a label + distinct glyph (✓/◐/▲).
4. Numerals are monospaced (SF Mono / JetBrains Mono); prose is San Francisco.
5. One continuous flow, not pages — patient stays in context across steps.
6. Honest restraint — placeholder thresholds; never imply false precision via dazzle.

### Constraints
Streamlit: light theme via `.streamlit/config.toml` (`base = "light"`) + scoped CSS
injection (`ui.py`); system San Francisco (OS-provided, offline) with only JetBrains
Mono self-hosted via `enableStaticServing` (`static/fonts/`, served at `app/static/`,
no external CDN). Flow via `st.session_state`. WCAG AA contrast on the light surface;
status not color-encoded alone; local-only, no runtime network calls.
