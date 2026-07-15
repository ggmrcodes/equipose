"""Hosted-mode flag + model-provisioning logic (no network)."""
from equipose import deploy


def test_is_hosted_reads_env(monkeypatch):
    monkeypatch.delenv("EQUIPOSE_HOSTED", raising=False)
    assert deploy.is_hosted() is False
    for truthy in ("1", "true", "TRUE", "yes"):
        monkeypatch.setenv("EQUIPOSE_HOSTED", truthy)
        assert deploy.is_hosted() is True
    for falsy in ("0", "false", "no", ""):
        monkeypatch.setenv("EQUIPOSE_HOSTED", falsy)
        assert deploy.is_hosted() is False


def test_missing_models_reports_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(deploy, "_MODELS_DIR", tmp_path)
    assert set(deploy.missing_models()) == set(deploy._REQUIRED)
    (tmp_path / "pose_landmarker_full.task").write_bytes(b"x")
    assert deploy.missing_models() == ["selfie_segmenter.tflite"]
    (tmp_path / "selfie_segmenter.tflite").write_bytes(b"y")
    assert deploy.missing_models() == []
