"""Headless smoke test: dashboard modules import and expose their callables.

Does NOT start a Streamlit server; it verifies the module graph and the pure
HTML builders so import-time breakage and markup regressions are caught in CI.
"""


def test_dashboard_imports_and_callables():
    import streamlit  # noqa: F401  (ensure the dep is present)

    from equipose.dashboard import app, flow, flow_review, roi_select, ui

    assert callable(app.main)
    assert callable(app.get_store)
    assert callable(flow.render)
    assert flow.STEPS == ["Patient", "Capture", "Read"]
    assert callable(flow_review.render)
    assert callable(roi_select.select_bbox)
    assert callable(roi_select.select_bbox_image)
    for fn in ("review_overview_html", "review_history_html", "trend_chart"):
        assert callable(getattr(ui, fn))
    for fn in ("inject_theme", "app_header", "header_html", "stepper", "stepper_html",
               "section", "section_html", "status_chip", "score_readout",
               "score_readout_html", "metrics_table", "metrics_table_html",
               "trend_chart", "disclaimer", "footer"):
        assert callable(getattr(ui, fn))


def test_status_chip_renders_label_and_glyph_not_color_only():
    from equipose.dashboard import ui

    # each status carries a text label + a distinct glyph (colorblind-safe)
    g, y, r = ui.status_chip("green"), ui.status_chip("yellow"), ui.status_chip("red")
    assert "Good" in g and "✓" in g
    assert "Watch" in y and "◐" in y
    assert "Concern" in r and "▲" in r
    # distinct status hues present (palette-agnostic — reads the current status colors)
    assert ui._STATUS["green"][1] in g and ui._STATUS["red"][1] in r


def test_typography_uses_system_san_francisco_stack():
    from equipose.dashboard import ui

    assert "-apple-system" in ui.CSS and "BlinkMacSystemFont" in ui.CSS
    assert "SF Pro Text" in ui.CSS
    assert "ui-monospace" in ui.CSS and "SF Mono" in ui.CSS
    assert "Bricolage" not in ui.CSS and "Hanken" not in ui.CSS
    assert "Plex" not in ui.CSS
    assert "JetBrainsMono-400.woff2" in ui.CSS


def test_only_jetbrains_mono_is_vendored_referenced():
    from equipose.dashboard import ui

    assert ui.CSS.count("@font-face") == 2          # JetBrainsMono 400 + 500 only
    assert "app/static/fonts/JetBrainsMono" in ui.CSS


def test_css_body_has_no_rose_or_glow():
    from equipose.dashboard import ui

    assert "224,138,155" not in ui.CSS              # old rose radial glow removed
    assert "e08a9b" not in ui.CSS.lower() and "eca1b0" not in ui.CSS.lower()


def test_theme_css_has_no_external_url():
    """The injected CSS must not pull fonts/assets over the network at runtime."""
    from equipose.dashboard import ui

    assert "http://" not in ui.CSS and "https://" not in ui.CSS
    assert "app/static/fonts/" in ui.CSS  # locally served fonts only


def test_review_overview_and_history_builders():
    from equipose.dashboard import ui

    sessions = [
        {"captured_at": "2026-01-01T10:00:00", "overall_score": 60.0, "band": "yellow",
         "view": "front", "kind": "snapshot"},
        {"captured_at": "2026-03-01T10:00:00", "overall_score": 85.0, "band": "green",
         "view": "front", "kind": "session"},
    ]
    ov = ui.review_overview_html(sessions)
    assert "Readings" in ov and "▲" in ov  # improved 60 -> 85 shows an up arrow
    hist = ui.review_history_html(sessions)
    assert "Photo" in hist and "Video" in hist and "Score" in hist


def test_trend_chart_with_band_builds():
    import pandas as pd

    from equipose.dashboard import ui

    df = pd.DataFrame({"t": pd.to_datetime(["2026-01-01", "2026-02-01"]), "v": [3.0, 7.0]})
    chart = ui.trend_chart(df, "t", "v", "deg", band=(-5.0, 5.0))
    assert chart is not None  # layered chart (band + line + points) builds without error


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


def test_position_scale_marks_score_zones_and_baseline():
    from equipose.config import load_scoring
    from equipose.dashboard import ui

    sc = load_scoring()  # yellow_min 60, green_min 80
    html = ui.position_scale_html(77, "yellow", sc, baseline=62)
    assert "77" in html and "baseline" in html
    assert ">60<" in html and ">80<" in html          # zone cutoff ticks
    assert "baseline" not in ui.position_scale_html(90, "green", sc)   # no prior session


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



def test_background_field_is_subtle_svg():
    from equipose.dashboard import glyphs

    s = glyphs.background_field_svg()
    assert s.startswith("<svg") and "opacity=\"0.06\"" in s  # faint, not loud


def test_palette_is_slate_light_no_rose():
    from equipose.dashboard import ui, glyphs

    # accent is slate-blue (the one emphasis tone); the old dusty-rose is gone everywhere
    assert ui.ACCENT.upper() == "#415A69"
    assert glyphs.ACCENT.upper() == "#415A69"
    for mod in (ui, glyphs):
        for name in dir(mod):
            val = getattr(mod, name)
            if isinstance(val, str):
                assert "e08a9b" not in val.lower(), f"rose leak in {mod.__name__}.{name}"
                assert "eca1b0" not in val.lower(), f"rose-hover leak in {mod.__name__}.{name}"
    # cool light ground + navy ink; slate buttons use white ink text for AA contrast
    assert ui.BG.upper() == "#E7EDEF"
    assert ui.TEXT.upper() == "#0C1013"
    assert ui.BTN_INK.upper() == "#FFFFFF"
