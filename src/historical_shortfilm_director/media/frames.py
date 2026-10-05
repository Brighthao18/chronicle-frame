"""Extract timestamped candidate/trim/boundary evidence without claiming semantic approval."""

import argparse
from pathlib import Path
import cv2
from historical_shortfilm_director.runtime.common import local, media_check, save, sha, relative


def extract(root, video, times):
    p = local(root, video)
    meta = media_check(p, root)
    dst = local(root, "reviews/frames") / sha(p)[:16]
    dst.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(p))
    items = []
    try:
        for t in sorted(set(float(x) for x in times)):
            if not 0 <= t < meta["duration_s"]:
                raise ValueError("Sample time outside clip")
            idx = min(round(t * meta["fps"]), round(meta["duration_s"] * meta["fps"]) - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, fr = cap.read()
            if not ok:
                raise ValueError("Unable to decode requested sample")
            out = dst / f"frame_{idx:07d}.png"
            encoded = cv2.imencode(".png", fr)[1]
            if not out.exists():
                encoded.tofile(str(out))
            items.append(
                {"time_s": idx / meta["fps"], "path": relative(root, out), "sha256": sha(out)}
            )
    finally:
        cap.release()
    save(
        dst / "manifest.json",
        {"video": relative(root, p), "video_sha256": meta["sha256"], "samples": items},
    )
    return items


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("project_dir")
    p.add_argument("video")
    p.add_argument(
        "--times",
        required=True,
        help="Seconds separated by commas; include selected trim boundaries",
    )
    a = p.parse_args()
    print(extract(Path(a.project_dir).resolve(), a.video, a.times.split(",")))
