"""Minimal CLI: analyze one video and print the SessionReport as JSON.

    equipose --video front.mp4 --view front --patient P001 \
             --bbox 655,180,905,690 --backend mediapipe
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from equipose.pipeline import analyze_session
from equipose.pose_backend import get_backend


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="equipose", description="Hippotherapy posture analysis")
    ap.add_argument("--video", required=True)
    ap.add_argument("--view", required=True, choices=["front", "side"])
    ap.add_argument("--patient", required=True)
    ap.add_argument("--bbox", required=True, help="left,top,right,bottom of the child on frame 1")
    ap.add_argument("--backend", default="mediapipe", choices=["mediapipe", "movenet"])
    ap.add_argument("--session-id", default="session-001")
    ap.add_argument("--captured-at", default="1970-01-01T00:00:00")
    ap.add_argument("--qc", action="store_true")
    args = ap.parse_args(argv)

    bbox = tuple(int(x) for x in args.bbox.split(","))
    if len(bbox) != 4:
        ap.error("--bbox must be left,top,right,bottom")

    report = analyze_session(
        args.video, args.view, args.patient, bbox,  # type: ignore[arg-type]
        session_id=args.session_id, captured_at=args.captured_at,
        backend=get_backend(args.backend), qc=args.qc,
    )
    json.dump(report.model_dump(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
