# Deploying the equipose demo

**This is a DEMO deployment for synthetic / consented images only.** Hosting inverts the
app's local-only privacy model: uploads are processed on a server. Do **not** put real,
unconsented patient photos on a hosted instance. The hosted app shows a demo-mode privacy
warning (via `EQUIPOSE_HOSTED`) instead of the local "no data leaves this machine" claim.

## Streamlit Community Cloud (recommended for a public demo)

Prereqs: the repo is on GitHub, and you have a Streamlit Community Cloud account.

1. Push this branch to GitHub.
2. On https://share.streamlit.io → **New app** → pick the repo/branch.
3. **Main file path:** `src/equipose/dashboard/app.py`
4. **Advanced settings:**
   - **Python version: 3.11** (mediapipe has no 3.13 wheels; `.python-version` also pins this).
   - **Secrets / env:** add `EQUIPOSE_HOSTED = "1"` (flips on the demo privacy footer and
     makes the pose backend mediapipe-only).
5. Deploy.

What happens on first boot:
- `requirements.txt` (`-e .`) installs equipose + its pinned deps. **mediapipe pulls
  in non-headless `opencv-contrib-python`**, whose `import cv2` needs `libGL.so.1` **and**
  `libgthread-2.0.so.0`, so `packages.txt` installs **`libgl1`** + **`libglib2.0-0t64`**.
  Note the **`t64`** suffix: Cloud's base is Debian **trixie**, where the plain
  `libglib2.0-0` resolves to an old bullseye build (`libffi7`/`libpcre3` unmet) and
  breaks apt — `libglib2.0-0t64` is the trixie-native package that provides
  `libgthread-2.0.so.0`.
- **After changing `packages.txt`, Reboot the app** (Manage → Reboot) — Cloud often
  skips re-running apt on a plain push.
- The app **downloads the models on first run** (`equipose.deploy.ensure_models` — the
  ~9 MB pose model + ~250 KB segmenter, from Google's public MediaPipe storage), because
  `models/` is gitignored. Expect a slower first cold start; a spinner shows while it fetches.
- **MoveNet is not fetched** — the demo is mediapipe-only.

## Notes / gotchas

- **Cold starts are slow-ish** (mediapipe import + the one-time model download).
- **Community Cloud memory is tight.** If it OOMs, use **Hugging Face Spaces** (Streamlit
  SDK, more RAM) or a container host (Fly/Render) — same `EQUIPOSE_HOSTED=1` + main file.
- **Scores are placeholder/uncalibrated.** Keep the "research build, not a diagnostic
  device" framing prominent for anyone you show it to.
- **Fonts** are served locally via `enableStaticServing` (already in `.streamlit/config.toml`);
  no CDN.

## Local run (unchanged)

```bash
./.venv/bin/streamlit run src/equipose/dashboard/app.py
```
No `EQUIPOSE_HOSTED` → the true local-only footer, both backends, and (already-present)
models — no network.
