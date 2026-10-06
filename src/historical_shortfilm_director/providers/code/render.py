"""Render code jobs locally: authored program -> frames -> FFmpeg -> verified candidate.

The runtime performs this operation itself, so the receipt it records is an observation of
work it did rather than a statement copied from an external tool. Rendering happens before
any claim: a broken program costs no attempt and leaves no runtime state. Only a decoded,
verified output is claimed, receipted and ingested, through the same runtime functions every
provider uses. Review and acceptance stay explicit; a render never approves itself.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

from historical_shortfilm_director import __version__
from historical_shortfilm_director.providers.code import EXECUTION, frame_count, render_settings
from historical_shortfilm_director.providers.code.scene import SceneRenderer, validate_scene
import historical_shortfilm_director.runtime.engine as runtime
from historical_shortfilm_director.runtime.common import (
    digest,
    ffmpeg,
    load,
    local,
    media_check,
    now,
    relative,
    save,
    sha,
)

RENDERS = "work/code_renders"
PREVIEWS = "work/code_previews"
RECEIPT_SCHEMA = "hsd-code-render/1"
PROGRAM_SCHEMA = "hsd-code-program/1"
ENCODER = [
    "-c:v",
    "libx264",
    "-preset",
    "medium",
    "-crf",
    "18",
    "-pix_fmt",
    "yuv420p",
    "-colorspace",
    "bt709",
    "-color_primaries",
    "bt709",
    "-color_trc",
    "bt709",
    "-color_range",
    "tv",
    "-movflags",
    "+faststart",
]
_TOOLCHAINS = {}


def render_policy(root):
    """The project's opt-ins for code rendering; Python programs stay off unless enabled."""
    policy = load(Path(root) / "00_execution_policy.json", {}).get("code_render") or {}
    timeout = policy.get("timeout_s", 600)
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not 1 <= timeout <= 86400
    ):
        raise ValueError("code_render.timeout_s must be 1..86400 seconds")
    return {"python_programs": policy.get("python_programs") is True, "timeout_s": float(timeout)}


def job_context(root, k):
    """A code job, its verified inputs and its exact render format."""
    current = runtime.jobs(root)
    if k not in current:
        raise ValueError("Unknown job: " + k)
    job = current[k]
    if job["provider"] != "code":
        raise ValueError(f"{k} is a {job['provider']} job; only code jobs render locally")
    refs, errors = runtime.inputs(root, job)
    if errors:
        raise ValueError(f"{k} inputs are not ready: " + ", ".join(errors))
    settings = render_settings(
        {"render": {key: job[key] for key in ("width", "height", "fps") if key in job}}
    )
    duration = float(job["duration_s"])
    use_in = float(job.get("use_in_s") or 0)
    use_out = float(job.get("use_out_s") or duration)
    if not 0 <= use_in < use_out <= duration + 1e-6:
        raise ValueError(f"{k}: edit range {use_in}-{use_out} s is outside the {duration} s clip")
    settings.update(
        duration_s=duration,
        frames=frame_count(duration, settings["fps"]),
        use_in_s=use_in,
        use_out_s=use_out,
    )
    assets = {r["asset_id"]: local(root, r["path"]) for r in refs}
    return job, refs, assets, settings


def read_program(root, program, inputs, settings, policy):
    """Load a scene (data) or an opt-in Python program, bound to its exact bytes."""
    path = local(root, program)
    if not path.is_file():
        raise ValueError("Render program missing: " + str(program))
    data = path.read_bytes()
    item = {"path": path, "bytes": data, "sha256": hashlib.sha256(data).hexdigest()}
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            scene = json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Scene is not valid UTF-8 JSON: {error}")
        normalized = validate_scene(scene, settings["duration_s"], inputs)
        return {**item, "kind": "scene", "scene": normalized, "suffix": ".scene.json"}
    if suffix == ".py":
        if not policy["python_programs"]:
            raise ValueError(
                "Python render programs are disabled. Review the program, then set"
                " code_render.python_programs to true in 00_execution_policy.json,"
                " or author an hsd-scene/1 JSON scene instead"
            )
        return {**item, "kind": "python", "suffix": ".py"}
    raise ValueError("A render program is an hsd-scene/1 .json scene or an opt-in .py program")


def program_environment(workdir):
    """A minimal environment: no inherited credentials, caches or config directories."""
    kept = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT")
    temp = workdir / "tmp"
    temp.mkdir(exist_ok=True)
    return {
        **{name: os.environ[name] for name in kept if name in os.environ},
        "HOME": str(workdir),
        "USERPROFILE": str(workdir),
        "TMPDIR": str(temp),
        "TEMP": str(temp),
        "TMP": str(temp),
        "MPLCONFIGDIR": str(workdir / "mpl"),
        "XDG_CACHE_HOME": str(workdir / "cache"),
    }


def python_frames(root, workdir, program_file, settings, refs, indices, policy):
    """Run an opt-in program that writes exactly the requested PNG frames."""
    from PIL import Image

    frames_dir = workdir / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir()
    context = {
        "schema": PROGRAM_SCHEMA,
        "width": settings["width"],
        "height": settings["height"],
        "fps": settings["fps"],
        "duration_s": settings["duration_s"],
        "frame_count": settings["frames"],
        "frame_indices": indices,
        "frames_dir": str(frames_dir),
        "inputs": {
            r["asset_id"]: {"path": str(local(root, r["path"])), "sha256": r["sha256"]}
            for r in refs
        },
        "seed": 0,
    }
    save(workdir / "context.json", context)
    log = workdir / "program.log"
    command = [sys.executable, "-I", "-X", "utf8", str(program_file), str(workdir / "context.json")]
    with log.open("wb") as handle:
        try:
            completed = subprocess.run(
                command,
                cwd=workdir,
                env=program_environment(workdir),
                stdin=subprocess.DEVNULL,
                stdout=handle,
                stderr=subprocess.STDOUT,
                timeout=policy["timeout_s"],
            )
        except subprocess.TimeoutExpired:
            raise ValueError(
                f"Program exceeded code_render.timeout_s ({policy['timeout_s']:g} s);"
                f" see {relative(root, log)}"
            )
    if completed.returncode:
        raise ValueError(
            f"Program exited with status {completed.returncode}; see {relative(root, log)}"
        )
    expected = {f"{index:06d}.png" for index in indices}
    found = {path.name for path in frames_dir.iterdir()}
    if found != expected:
        missing = sorted(expected - found)[:5]
        extra = sorted(found - expected)[:5]
        raise ValueError(
            f"Program frames do not match the request; missing {missing}, extra {extra}"
        )

    def frame_at(index):
        with Image.open(frames_dir / f"{index:06d}.png") as image:
            image.load()
            if image.size != (settings["width"], settings["height"]):
                raise ValueError(f"Frame {index} is {image.size}, not the job's format")
            return image.convert("RGB")

    return frame_at, {"fonts": [], "warnings": []}


def frame_source(root, workdir, program, program_file, settings, refs, assets, indices, policy):
    """A frame(index) callable plus a details dict filled in while frames are drawn."""
    if program["kind"] == "python":
        return python_frames(root, workdir, program_file, settings, refs, indices, policy)
    renderer = SceneRenderer(
        program["scene"],
        settings["width"],
        settings["height"],
        settings["fps"],
        settings["frames"],
        assets,
    )
    details = {"fonts": renderer.fonts, "warnings": []}

    def frame_at(index):
        frame = renderer.frame(index)
        details["warnings"] = renderer.warnings()
        return frame

    return frame_at, details


def toolchain(root):
    """Observed local renderer versions; no absolute paths enter receipts."""
    import PIL
    from PIL import features

    executable = ffmpeg(root)
    if executable not in _TOOLCHAINS:

        def ask(*flags):
            try:
                return subprocess.run(
                    [executable, "-hide_banner", *flags],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=True,
                    timeout=60,
                ).stdout
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                raise RuntimeError(f"FFmpeg probe failed: {error}")

        _TOOLCHAINS[executable] = {
            "ffmpeg": (ask("-version").splitlines() or ["unknown"])[0].strip(),
            "libx264": " libx264 " in ask("-encoders"),
        }
    return {
        "runtime": __version__,
        "python": platform.python_version(),
        "pillow": PIL.__version__,
        "freetype": features.version("freetype2"),
        **_TOOLCHAINS[executable],
    }


def probe(root):
    """Record an observed `code` capability for this project's local renderer."""
    root = Path(root).resolve()
    problems = []
    try:
        chain = toolchain(root)
    except (RuntimeError, OSError, ImportError) as error:
        chain = {}
        problems.append(str(error))
    if chain and not chain["libx264"]:
        problems.append("FFmpeg has no libx264 encoder")
    if importlib.util.find_spec("cv2") is None or importlib.util.find_spec("numpy") is None:
        problems.append("Install the media extras (OpenCV, NumPy) to verify rendered video")
    observation = {
        "available": not problems,
        "observed_at": now(),
        "evidence": (
            f"Local probe by hsd {__version__}: "
            + (f"{chain['ffmpeg']}; Pillow {chain['pillow']}" if chain else "no toolchain")
            + ("; " + "; ".join(problems) if problems else "; libx264 and OpenCV present")
        ),
        "execution": EXECUTION,
        "toolchain": chain,
        "renderers": ["scene", "python"],
        "problems": problems,
    }
    path = root / "00_capability_snapshot.json"
    snapshot = load(path, {})
    snapshot["code"] = observation
    save(path, snapshot)
    return observation


def encode(root, frames, settings, output, log_path):
    """Pipe RGB frames to FFmpeg as raw video; argument vectors only, never a shell."""
    command = [
        ffmpeg(root),
        "-hide_banner",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-video_size",
        f"{settings['width']}x{settings['height']}",
        "-framerate",
        format(settings["fps"], "g"),
        "-i",
        "pipe:0",
        "-an",
        "-vf",
        "scale=out_color_matrix=bt709:out_range=tv",
        *ENCODER,
        "-n",
        str(output),
    ]
    with log_path.open("wb") as log:
        process = subprocess.Popen(
            command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log
        )
        try:
            for frame in frames:
                process.stdin.write(frame.tobytes())
        except BrokenPipeError:
            pass  # FFmpeg exited early; its status and log explain why.
        except BaseException:
            process.kill()
            process.wait()
            output.unlink(missing_ok=True)
            raise
        finally:
            if not process.stdin.closed:
                try:
                    process.stdin.close()
                except BrokenPipeError:
                    pass
        status = process.wait()
    if status:
        output.unlink(missing_ok=True)
        tail = log_path.read_text(encoding="utf-8", errors="replace")[-800:]
        raise RuntimeError(f"FFmpeg encoding failed ({status}): {tail}")
    # A portable record of the encode: no executable or output paths.
    return ["ffmpeg", *command[1:-1], output.name]


def sample_marks(settings):
    """Frames an agent should look at: the clip ends, the edit range and fill-in samples."""
    count, fps = settings["frames"], settings["fps"]
    marks = {}

    def mark(index, label):
        marks.setdefault(min(count - 1, max(0, index)), label)

    mark(0, "first")
    mark(round(settings["use_in_s"] * fps), "edit in")
    mark(round((settings["use_in_s"] + settings["use_out_s"]) / 2 * fps), "edit mid")
    mark(round(settings["use_out_s"] * fps) - 1, "edit out")
    mark(count - 1, "last")
    for step in range(1, 5):
        if len(marks) >= 6:
            break
        mark(round(step * (count - 1) / 5), "")
    return marks


def contact_sheet(samples, settings, path):
    """One PNG an agent can read to review motion: labelled thumbnails in time order."""
    from PIL import Image, ImageDraw, ImageFont

    width = min(480, settings["width"])
    height = max(2, round(settings["height"] * width / settings["width"]))
    label, gap, columns = 22, 8, 3
    rows = -(-len(samples) // columns)
    sheet = Image.new(
        "RGB",
        (columns * width + (columns + 1) * gap, rows * (height + label) + (rows + 1) * gap),
        (24, 26, 30),
    )
    try:
        font = ImageFont.load_default(size=14)
    except TypeError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(sheet)
    for number, (index, name, frame) in enumerate(samples):
        x = gap + (number % columns) * (width + gap)
        y = gap + (number // columns) * (height + label + gap)
        sheet.paste(frame.resize((width, height), Image.Resampling.LANCZOS), (x, y))
        caption = f"#{index}  {index / settings['fps']:.2f} s" + (f"  {name}" if name else "")
        draw.text((x, y + height + 4), caption, fill=(232, 232, 232), font=font)
    sheet.save(path)
    return path


def preview(root, k, program, times=None):
    """Full-resolution stills and a contact sheet; no attempt, receipt or approval."""
    root = Path(root).resolve()
    job, refs, assets, settings = job_context(root, k)
    policy = render_policy(root)
    item = read_program(root, program, {r["asset_id"] for r in refs}, settings, policy)
    if times:
        indices = []
        for value in times:
            t = float(value)
            if not 0 <= t <= settings["duration_s"]:
                raise ValueError(
                    f"Preview time {t} s is outside the {settings['duration_s']} s clip"
                )
            indices.append(min(settings["frames"] - 1, round(t * settings["fps"])))
        marks = {index: "" for index in sorted(set(indices))}
    else:
        marks = dict(sorted(sample_marks(settings).items()))
    key = digest(
        {"program": item["sha256"], "inputs": refs, "format": settings, "frames": list(marks)}
    )
    workdir = local(root, PREVIEWS) / k / key[:16]
    workdir.mkdir(parents=True, exist_ok=True)
    program_file = workdir / ("program" + item["suffix"])
    program_file.write_bytes(item["bytes"])
    frame_at, details = frame_source(
        root, workdir, item, program_file, settings, refs, assets, list(marks), policy
    )
    stills = []
    samples = []
    for index, name in marks.items():
        frame = frame_at(index)
        still = workdir / f"frame_{index:06d}.png"
        frame.save(still)
        stills.append(
            {"index": index, "time_s": index / settings["fps"], "path": relative(root, still)}
        )
        samples.append((index, name, frame))
    sheet = contact_sheet(samples, settings, workdir / "contact.png")
    return {
        "status": "PREVIEW_ONLY",
        "job_id": k,
        "program_sha256": item["sha256"],
        "format": settings,
        "stills": stills,
        "contact_sheet": relative(root, sheet),
        "warnings": details["warnings"],
        "note": "Preview stills only: no attempt, receipt, candidate or approval was recorded.",
    }


def render(root, k, program, author=None):
    """Render one attempt and ingest it as a candidate awaiting explicit review."""
    root = Path(root).resolve()
    job, refs, assets, settings = job_context(root, k)
    policy = render_policy(root)
    execution = runtime.state(root)
    entry = execution["jobs"].get(k, {})
    fingerprint, _, upstream = runtime.fingerprint(root, job, execution)
    active = entry.get("active_attempt") if entry.get("status") == "ACTIVE" else None
    if active:
        attempt = entry["attempts"][-1]
        if attempt.get("receipt"):
            raise ValueError(
                f"Attempt {active} already has a receipt ({attempt['receipt'].get('handle')});"
                " ingest that output with `hsd runtime ... ingest` or reconcile the attempt"
            )
        if attempt.get("input_hash") != fingerprint or upstream:
            raise ValueError(
                f"Active claim {active} was made for different inputs; reconcile it as"
                " NOT_SUBMITTED, then render again"
            )
    else:
        blockers = runtime.readiness(root, k, job, execution)
        if blockers:
            raise ValueError(f"{k} is not ready to render: " + "; ".join(blockers))
    item = read_program(root, program, {r["asset_id"] for r in refs}, settings, policy)
    render_id = uuid.uuid4().hex
    bundle = local(root, RENDERS) / render_id
    bundle.mkdir(parents=True)
    program_file = bundle / ("program" + item["suffix"])
    program_file.write_bytes(item["bytes"])
    output = bundle / "output.mp4"
    record = {
        "schema": RECEIPT_SCHEMA,
        "render_id": render_id,
        "job_id": k,
        "unit": job.get("unit"),
        "started_at": now(),
        "program": {
            "kind": item["kind"],
            "source": relative(root, item["path"]),
            "path": relative(root, program_file),
            "sha256": item["sha256"],
        },
        "author": author if isinstance(author, dict) else {"declared": author},
        "inputs": refs,
        "input_hash": fingerprint,
        "format": settings,
    }
    try:
        chain = toolchain(root)
        marks = sample_marks(settings)
        kept = {}
        indices = list(range(settings["frames"]))
        frame_at, details = frame_source(
            root, bundle, item, program_file, settings, refs, assets, indices, policy
        )

        def stream():
            for index in indices:
                frame = frame_at(index)
                if index in marks:
                    kept[index] = frame
                yield frame

        encoder = encode(root, stream(), settings, output, bundle / "ffmpeg.log")
        if item["kind"] == "python":
            shutil.rmtree(bundle / "frames")
        meta = media_check(output, root)
        if (
            (meta["width"], meta["height"]) != (settings["width"], settings["height"])
            or abs(meta["fps"] - settings["fps"]) > 0.01
            or round(meta["duration_s"] * meta["fps"]) != settings["frames"]
        ):
            raise ValueError("Encoded output does not match the job's format: " + str(meta))
        sheet = contact_sheet(
            [(index, marks[index], kept[index]) for index in sorted(kept)],
            settings,
            bundle / "contact.png",
        )
    except Exception as error:
        output.unlink(missing_ok=True)
        save(bundle / "render.json", {**record, "status": "FAILED", "error": str(error)})
        raise
    record.update(
        status="RENDERED",
        rendered_at=now(),
        output={key: meta[key] for key in ("sha256", "bytes", "width", "height", "fps")}
        | {"frames": settings["frames"]},
        toolchain=chain,
        encoder=encoder,
        fonts=details["fonts"],
        warnings=details["warnings"],
        contact_sheet={"path": relative(root, sheet), "sha256": sha(sheet), "frames": sorted(kept)},
    )
    save(bundle / "render.json", record)
    try:
        token = active or runtime.claim(root, k, expected_input_hash=fingerprint)["token"]
        runtime.receipt(
            root,
            k,
            token,
            {
                "handle": "local-render:" + render_id,
                "evidence": relative(root, bundle / "render.json"),
                "actual_model": None,
                "actual_mode": job["mode"],
                "render_receipt_sha256": sha(bundle / "render.json"),
                "program_sha256": item["sha256"],
                "output_sha256": meta["sha256"],
                "toolchain": chain,
            },
        )
        candidate = runtime.ingest(root, k, token, output)
    except Exception as error:
        save(bundle / "commit_error.json", {"error": str(error), "time": now()})
        raise
    output.unlink(missing_ok=True)  # the ingested candidate is now the canonical copy
    checks = runtime.CHECKS + ["motion_camera", "join"]
    template = local(root, "work/reviews") / f"{token}.template.json"
    save(
        template,
        {
            "sha256": candidate["sha256"],
            "reviewer": "",
            "evidence": [relative(root, sheet), candidate["path"]],
            "checks": {check: "UNCERTAIN" for check in checks},
            "score": 0,
            "notes": "",
            "failure_code": None,
        },
    )
    return {
        "status": "REVIEW_REQUIRED",
        "job_id": k,
        "token": token,
        "render_id": render_id,
        "candidate": candidate,
        "contact_sheet": relative(root, sheet),
        "render_receipt": relative(root, bundle / "render.json"),
        "review_template": relative(root, template),
        "warnings": details["warnings"],
        "next": (
            "Inspect the contact sheet and candidate against the contract, replace every"
            " UNCERTAIN check with your actual judgment, then run `hsd runtime <project>"
            f" review {k} <review.json>` and `accept`."
        ),
    }
