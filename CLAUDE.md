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
**"Graphite instrument"** — a warm-charcoal DARK workspace styled on Apple's
Human Interface Guidelines. Warm-charcoal neutrals (bg `#17120F`, panel
`#1E1814`) + warm off-white text + a **single warm-bone emphasis tone**
(`#FBF5EF`, no pink). Type: the **system San Francisco stack** (`-apple-system`,
`BlinkMacSystemFont`, `"SF Pro Text"`) with **SF Mono / JetBrains Mono** for
numerals — SF is OS-provided/offline, JetBrains Mono self-hosted (`static/fonts/`,
served at `app/static/`, no CDN). Apple patterns: a unified toolbar, the guided
flow (Patient -> Capture -> Read) as a **source-list sidebar**, left-aligned
**Large Title** + subtitle, **inset grouped lists** with hairline separators, real
**segmented controls**, soft elevation, 8-pt spacing (no pills). A faint neutral
**goniometer field** fills the negative space; the score dial echoes it as a thin
arc. Posture status (good=sage / watch=amber / concern=clay) is the only color and
carries a label + glyph. Anti-references: AI-slop (accent-caps eyebrows,
pills-on-everything, card-in-card, radial glows/gradients, trendy display fonts,
neon glow, emoji-as-UI), cold blue-black dark mode, glassmorphism, toy aesthetics.

### Design Principles
1. Warm, not cold — warm-charcoal dark, reassuring progress-forward tone.
2. One emphasis tone (warm bone), used sparingly (actions + emphasis only).
3. Status is never color alone — good/watch/concern carry a label + distinct glyph (✓/◐/▲).
4. Numerals are monospaced (SF Mono / JetBrains Mono); prose is San Francisco.
5. One continuous flow, not pages — patient stays in context across steps.
6. Honest restraint — placeholder thresholds; never imply false precision via dazzle.

### Constraints
Streamlit: dark theme via `.streamlit/config.toml` + scoped CSS injection (`ui.py`);
system San Francisco (OS-provided, offline) with only JetBrains Mono self-hosted
via `enableStaticServing` (`static/fonts/`, served at `app/static/`, no external
CDN). Flow via `st.session_state`. WCAG AA contrast on dark; status not
color-encoded alone; local-only, no runtime network calls.
