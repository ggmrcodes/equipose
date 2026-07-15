# equipose UI Revamp — "Graphite Instrument" (Apple-language)

**Date:** 2026-06-24
**Status:** Approved (design) — pending spec review → implementation plan
**Supersedes:** the "Warm night clinic" dusty-rose accent direction

## Problem

The current dashboard ("warm night clinic") is well-built but reads two ways the
user rejects:

1. The **dusty-rose / pink accent** (`#E08A9B`) looks unprofessional for an
   instrument-grade clinical/research tool.
2. The **layout and font selection look "obviously AI-generated"** — the
   accent-caps eyebrow → giant title hero, pills on everything, bordered
   card-in-card stacks, a radial accent glow + gradient score card, and a
   trendy display+body font pairing (Bricolage Grotesque + Hanken Grotesk).

## Goal

A **clean, minimal, professional** dashboard that does not read as AI-generated,
using **Apple's Human Interface Guidelines as the design reference**. Keep the
warm-charcoal dark base and the goniometer identity; remove the pink; replace the
designer font pairing with San Francisco; restructure the layout to Apple
patterns.

## Decisions (locked with the user)

| Axis | Decision |
|---|---|
| Theme base | **Keep warm-charcoal DARK** (`#17120F`) — not light, not cold blue-black |
| Accent | **Monochrome** — pink removed entirely; emphasis carried by **warm bone `#FBF5EF`** |
| Color budget | The *only* hue in the app is functional posture **status** (sage/amber/clay) |
| Design reference | **Apple HIG** (San Francisco type, Large Title, inset grouped lists, segmented control, source-list sidebar, soft elevation, 8-pt grid) |
| Scope | **Recolor + rework components** (palette + CSS + component layouts + flow chrome) |
| Fonts | **System San Francisco stack** (OS-provided, offline). JetBrains Mono kept as self-hosted mono fallback. |

## Type system

- **UI / titles:** `-apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif`.
  SF Pro Display is selected automatically by the OS at large sizes.
- **Numerals / units / data / eyebrow-mono:** `ui-monospace, "SF Mono", Menlo, "JetBrains Mono", monospace`
  with `font-variant-numeric: tabular-nums`.
- **Offline:** San Francisco is provided by macOS — no network, satisfies the
  privacy/offline constraint. **Tradeoff:** SF cannot be redistributed, so
  non-Apple machines fall back to Segoe UI / `system-ui`. Accepted because the
  user is on macOS and wants the authentic Apple feel. (If pixel-identical
  cross-platform rendering becomes required, swap in self-hosted Inter — less
  authentically Apple.)
- **Removed:** Bricolage Grotesque, Hanken Grotesk. Self-hosted `Hanken-*` /
  `Bricolage-*` woff2 faces are no longer referenced (font files may stay on
  disk; the `@font-face` rules for them are removed).

## Color & material

```
--bg        #17120F   warm near-black charcoal           (kept)
--panel     #1E1814   grouped-list fill (subtle)
--panel-hi  #251E19   elevated fill (selected segment, hover)
--line      rgba(242,233,226,0.10)   hairline separators (warm white, low alpha)
--text      #F2E9E2   warm off-white                     (kept)
--soft      #B8A99E   secondary label                    (kept)
--mute      #8A7A6E   tertiary label                     (kept)
--accent    #FBF5EF   warm bone — emphasis / primary actions / active / focus
--accent-press  #ECE3DA   pressed bone
```

- **Removed:** `--accent` rose family, `--accent-bg` rose tint, the `.stApp`
  radial rose glow, and the `.eq-score` rose gradient. Replace glow/gradients
  with flat surfaces + a soft, large-radius, low-alpha shadow for elevation.
- **Status (unchanged, the only color):** good `#86CFA0` ✓ "Good" /
  watch `#E8BE78` ◐ "Watch" / concern `#EC8A74` ▲ "Concern". Rendered as
  SF-Symbol-style filled circles + glyph + text label (stays WCAG AA and
  colorblind-safe — status is never color alone).
- **Provisional/needs-literature** amber tag retained.

## Layout & structure (Apple patterns)

1. **Unified toolbar** (top): small `equipose` wordmark left, patient identity
   right, single hairline divider underneath. Replaces the large branded header
   block. No accent-caps eyebrow.
2. **Steps as a source-list sidebar** (Patient · Capture · Read): use Streamlit's
   native sidebar styled as a macOS vibrancy source list (numbered/▸ rows, active
   row = bone). Replaces the floating fixed custom rail (`.eq-railv`) and the
   horizontal pill stepper (`.eq-steps`). Native sidebar collapses gracefully on
   narrow screens.
3. **Large Title per step**: big, bold, **left-aligned** SF title (e.g. "Read")
   + quiet secondary subtitle. Replaces eyebrow → centered hero.
4. **Inset grouped sections**: a small gray section header *above* a single
   subtly-filled rounded container with hairline row separators (System Settings
   pattern). Group by space + one container, not by bordering every element.
5. **8-pt spacing grid**; Apple continuous-radius geometry (~8–12px), not pills.

## Component mapping

| Component | Now | After (Apple) |
|---|---|---|
| Score readout | gradient card, rose dial | flat panel, large SF tabular number, **thin bone-stroke dial** |
| Metrics table | ruled HTML `<table>` | **inset grouped list** — name leading, value + status trailing, hairline separators |
| View toggle (front/side) | radio "segmented pills" | real macOS **segmented control** (selected = elevated bone-tinted segment, soft shadow) |
| Buttons | rose primary | macOS push-button geometry; **primary = bone fill / dark text**, secondary = bordered gray; "Continue" bottom-right |
| Stepper | pills + floating rail | source-list sidebar (see Layout #2) |
| Status chip | pill (kept) | pill kept — this is the legit use of a pill |
| Goniometer field | faint rose-tinted SVG | **kept**, redrawn as faint precise technical-drawing layer (neutral), low alpha |
| Trend chart (Altair) | rose line/points | bone line/points; in-range band stays sage |
| Confidence bar | rose fill | bone fill |

## Files touched

- `.streamlit/config.toml` — `primaryColor` → bone; remove rose; keep dark base.
- `src/equipose/dashboard/ui.py` — palette constants, `@font-face` cleanup, full
  CSS rework (toolbar, sidebar source list, Large Title, inset grouped list,
  segmented control, button geometry, remove glow/gradients), and the
  table→grouped-list and score-readout component changes.
- `src/equipose/dashboard/glyphs.py` — recolor SVG strokes to bone; thinner
  SF-style score dial; neutralize the background goniometer field tint.
- `src/equipose/dashboard/flow.py`, `flow_review.py` — render the toolbar and the
  sidebar step list; adopt Large Title + grouped sections; segmented control for
  view toggle.
- `.impeccable.md`, `CLAUDE.md` — update the design-context source of truth to the
  new direction (so future design skills read the right system).

## Accessibility / constraints (unchanged guarantees)

- WCAG AA contrast on the dark surfaces (bone-on-charcoal and text-on-charcoal
  both pass; verify the bone-fill button's dark text passes AA).
- Status never color-alone: glyph + text label retained.
- Local-only, no runtime network calls (system fonts are OS-local; no CDN).

## Out of scope

- No change to the analysis pipeline, scoring math, schemas, or data model.
- No new metrics or features — visual/structural revamp only.
- Font *files* are not deleted from disk (only their `@font-face` references are
  removed); cleanup of unused woff2 can be a later chore.

## Open questions

None. (Fonts: system SF stack confirmed; layout reworks in sections above
confirmed.)
