"""Declarative `hsd-scene/1` programs: exact layers moved by keyframes, never synthesized.

A scene is JSON data, typically authored by Claude Code from a job's render brief. Validation
is strict and reports every problem with its JSON path, so an author can repair a scene in one
pass. Rendering needs only Pillow: image, text and rectangle layers are translated, scaled,
rotated and faded. No source pixel is repainted, warped, recoloured or invented.
"""

from __future__ import annotations

import math
import re

SCHEMA = "hsd-scene/1"
MAX_LAYERS = 64
MAX_KEYS = 1000
MAX_TEXT = 1000
MAX_NOTES = 2000
MAX_FONT_PX = 2048
PAD = 4
SPRITE_DEFAULTS = {
    "x": 0.5,
    "y": 0.5,
    "ax": 0.5,
    "ay": 0.5,
    "scale": 1.0,
    "rotation": 0.0,
    "opacity": 1.0,
}
RECT_DEFAULTS = {"x": 0.0, "y": 0.0, "w": 1.0, "h": 1.0, "opacity": 1.0}
RANGES = {
    "x": (-10.0, 10.0),
    "y": (-10.0, 10.0),
    "ax": (-10.0, 10.0),
    "ay": (-10.0, 10.0),
    "w": (0.0, 10.0),
    "h": (0.0, 10.0),
    "scale": (0.01, 100.0),
    "rotation": (-3600.0, 3600.0),
    "opacity": (0.0, 1.0),
}
EASES = {"linear", "in", "out", "in_out", "hold"}
FITS = {"cover", "contain", "width", "height", "none"}
ALIGNS = {"left", "center", "right"}
TOP_FIELDS = {"schema", "background", "layers", "notes"}
COMMON_FIELDS = {"id", "type", "start_s", "end_s", "keys", "notes"}
LAYER_FIELDS = {
    "image": {"asset", "fit"},
    "text": {"text", "font", "size", "color", "align", "line_spacing"},
    "rect": {"color", "outline"},
}
COLOR = re.compile(r"#([0-9A-Fa-f]{6})([0-9A-Fa-f]{2})?")
LAYER_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")

FORMAT_REFERENCE = """\
A scene is one JSON object, `{"schema": "hsd-scene/1", "background": "#000000",
"layers": [...], "notes": "..."}`. Layers draw bottom to top. Width, height, fps and
duration come from the job, never from the scene. Coordinates are fractions of the frame:
x grows right, y grows down, (0, 0) is the top-left corner. Frame i is shown at t = i / fps.

Every layer may set `id`, `notes`, `start_s` and `end_s` (visible while
start_s <= t < end_s; default the whole clip) and `keys`, a list of keyframes with strictly
increasing `t` (seconds). A key sets any animatable property of its layer plus an optional
`ease` (linear, in, out, in_out or hold) for the segment that arrives at it. A property
holds its first keyed value before its first key and its last value after its last key.
An animatable property may also be written on the layer itself as a constant; it applies
whenever no key sets that property. Anything else keeps its default.

- `image`: `asset` (a listed input ID) and `fit` (cover [default], contain, width, height,
  none) sizing the image to the frame at scale 1. Animate x, y, ax, ay, scale, rotation,
  opacity. The image point at fractions (ax, ay) of its own width and height is placed at
  frame point (x, y), scaled by `scale` and rotated clockwise by `rotation` degrees.
  Defaults: x = y = ax = ay = 0.5, scale = 1, rotation = 0, opacity = 1.
- `text`: `text` (exact wording; newlines allowed), `size` (fraction of frame height,
  default 0.05), `color` (#RRGGBB or #RRGGBBAA, default #FFFFFF), `font` (a listed font
  asset ID; default: Pillow's bundled scalable font), `align` (left [default], center,
  right; multi-line alignment) and `line_spacing` (default 1.2). Animates like an image.
- `rect`: `color` (default #000000) and optional `outline` (stroke width as a fraction of
  frame height; omit for a filled box). Animate x, y, w, h (top-left corner and size, as
  frame fractions; default the full frame) and opacity.

Example: a 4 s slow push toward a detail with a fading caption.
{"schema": "hsd-scene/1", "layers": [
  {"type": "image", "asset": "SRC_GATE", "keys": [
    {"t": 0, "scale": 1.0, "ax": 0.5, "ay": 0.5},
    {"t": 4, "scale": 1.15, "ax": 0.58, "ay": 0.44, "ease": "in_out"}]},
  {"type": "text", "text": "Main gate", "size": 0.045, "ax": 0, "keys": [
    {"t": 0.5, "x": 0.06, "y": 0.88, "opacity": 0},
    {"t": 1.3, "opacity": 1, "ease": "out"}]}]}
"""


class SceneError(ValueError):
    """Every problem found in one scene, each prefixed by its JSON path."""

    def __init__(self, problems):
        self.problems = list(problems)
        shown = self.problems[:25]
        more = len(self.problems) - len(shown)
        super().__init__(
            "Invalid scene: " + "; ".join(shown) + (f"; and {more} more" if more else "")
        )


def color(value, path, problems, opaque=False):
    match = COLOR.fullmatch(value) if isinstance(value, str) else None
    if not match or (opaque and match.group(2)):
        problems.append(f"{path}: must be {'#RRGGBB' if opaque else '#RRGGBB or #RRGGBBAA'}")
        return (0, 0, 0, 255)
    rgb = match.group(1)
    alpha = int(match.group(2), 16) if match.group(2) else 255
    return (int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16), alpha)


def number(value, path, problems, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        problems.append(f"{path}: must be a finite number")
        return None
    if not low <= value <= high:
        problems.append(f"{path}: must be in {low:g}..{high:g}")
        return None
    return float(value)


def notes(value, path, problems):
    if value is not None and (not isinstance(value, str) or len(value) > MAX_NOTES):
        problems.append(f"{path}: must be text of at most {MAX_NOTES} characters")


def validate_scene(scene, duration_s, inputs):
    """Normalize a scene for a clip of `duration_s` that may read only `inputs` asset IDs."""
    problems = []
    if not isinstance(scene, dict):
        raise SceneError(["scene: must be a JSON object"])
    extra = set(scene) - TOP_FIELDS
    if extra:
        problems.append(f"scene: unknown fields {sorted(extra)}")
    if scene.get("schema") != SCHEMA:
        problems.append(f"schema: must be {SCHEMA!r}")
    notes(scene.get("notes"), "notes", problems)
    background = color(scene.get("background", "#000000"), "background", problems, opaque=True)
    layers = scene.get("layers")
    if not isinstance(layers, list) or not layers:
        problems.append("layers: must be a non-empty list")
        layers = []
    elif len(layers) > MAX_LAYERS:
        problems.append(f"layers: at most {MAX_LAYERS} layers")
    allowed = set(inputs)
    seen = set()
    normalized = []
    for index, layer in enumerate(layers):
        path = f"layers[{index}]"
        if not isinstance(layer, dict):
            problems.append(f"{path}: must be an object")
            continue
        kind = layer.get("type")
        if kind not in LAYER_FIELDS:
            problems.append(f"{path}.type: must be one of {sorted(LAYER_FIELDS)}")
            continue
        defaults = RECT_DEFAULTS if kind == "rect" else SPRITE_DEFAULTS
        extra = set(layer) - COMMON_FIELDS - LAYER_FIELDS[kind] - set(defaults)
        if extra:
            problems.append(f"{path}: unknown fields {sorted(extra)} for a {kind} layer")
        constants = {
            name: number(layer[name], f"{path}.{name}", problems, *RANGES[name])
            for name in defaults
            if name in layer
        }
        layer_id = layer.get("id", f"layer{index}")
        if not isinstance(layer_id, str) or not LAYER_ID.fullmatch(layer_id):
            problems.append(f"{path}.id: must be 1-64 letters, digits, '_' or '-'")
        elif layer_id in seen:
            problems.append(f"{path}.id: duplicate layer id {layer_id!r}")
        seen.add(layer_id)
        notes(layer.get("notes"), f"{path}.notes", problems)
        start = number(layer.get("start_s", 0), f"{path}.start_s", problems, 0, duration_s)
        end = number(layer.get("end_s", duration_s), f"{path}.end_s", problems, 0, duration_s)
        if start is not None and end is not None and not start < end:
            problems.append(f"{path}: start_s must be before end_s")
        keys = layer.get("keys", [])
        if not isinstance(keys, list) or len(keys) > MAX_KEYS:
            problems.append(f"{path}.keys: must be a list of at most {MAX_KEYS} keys")
            keys = []
        clean_keys = []
        previous = None
        for key_index, key in enumerate(keys):
            key_path = f"{path}.keys[{key_index}]"
            if not isinstance(key, dict):
                problems.append(f"{key_path}: must be an object")
                continue
            extra = set(key) - {"t", "ease"} - set(defaults)
            if extra:
                problems.append(
                    f"{key_path}: unknown fields {sorted(extra)}; {kind} layers animate"
                    f" {sorted(defaults)}"
                )
            t = number(key.get("t"), f"{key_path}.t", problems, 0, duration_s)
            if t is not None and previous is not None and t <= previous:
                problems.append(f"{key_path}.t: must be greater than the previous key's t")
            previous = t if t is not None else previous
            ease = key.get("ease", "linear")
            if ease not in EASES:
                problems.append(f"{key_path}.ease: must be one of {sorted(EASES)}")
            values = {
                name: number(key[name], f"{key_path}.{name}", problems, *RANGES[name])
                for name in defaults
                if name in key
            }
            if not values:
                problems.append(f"{key_path}: sets no animatable property")
            clean_keys.append({"t": t, "ease": ease, **values})
        item = {
            "index": index,
            "id": layer_id,
            "type": kind,
            "start_s": start,
            "end_s": end,
            "keys": clean_keys,
            "constants": constants,
            "notes": layer.get("notes"),
        }
        if kind == "image":
            asset = layer.get("asset")
            if not isinstance(asset, str) or asset not in allowed:
                problems.append(f"{path}.asset: must be one of this job's inputs {sorted(allowed)}")
            fit = layer.get("fit", "cover")
            if fit not in FITS:
                problems.append(f"{path}.fit: must be one of {sorted(FITS)}")
            item.update(asset=asset, fit=fit)
        elif kind == "text":
            text = layer.get("text")
            if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
                problems.append(f"{path}.text: must be 1-{MAX_TEXT} characters of exact wording")
            font = layer.get("font")
            if font is not None and (not isinstance(font, str) or font not in allowed):
                problems.append(f"{path}.font: must be one of this job's inputs {sorted(allowed)}")
            align = layer.get("align", "left")
            if align not in ALIGNS:
                problems.append(f"{path}.align: must be one of {sorted(ALIGNS)}")
            item.update(
                text=text,
                font=font,
                size=number(layer.get("size", 0.05), f"{path}.size", problems, 0.005, 1.0),
                color=color(layer.get("color", "#FFFFFF"), f"{path}.color", problems),
                align=align,
                line_spacing=number(
                    layer.get("line_spacing", 1.2), f"{path}.line_spacing", problems, 0.5, 3.0
                ),
            )
        else:
            outline = layer.get("outline")
            item.update(
                color=color(layer.get("color", "#000000"), f"{path}.color", problems),
                outline=None
                if outline is None
                else number(outline, f"{path}.outline", problems, 0.0005, 0.5),
            )
        normalized.append(item)
    if problems:
        raise SceneError(problems)
    return {"schema": SCHEMA, "background": background, "layers": normalized}


def ease(kind, u):
    if kind == "hold":
        return 0.0 if u < 1 else 1.0
    if kind == "in":
        return u**3
    if kind == "out":
        return 1 - (1 - u) ** 3
    if kind == "in_out":
        return 4 * u**3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
    return u


def tracks(layer):
    defaults = RECT_DEFAULTS if layer["type"] == "rect" else SPRITE_DEFAULTS
    return {
        name: [(key["t"], key[name], key["ease"]) for key in layer["keys"] if name in key]
        for name in defaults
    }


def value_at(track, t, default):
    if not track:
        return default
    if t <= track[0][0]:
        return track[0][1]
    for (t0, v0, _), (t1, v1, kind) in zip(track, track[1:]):
        if t < t1:
            return v0 + (v1 - v0) * ease(kind, (t - t0) / (t1 - t0))
    return track[-1][1]


def state_at(layer, t):
    """Every animatable property of a validated layer at time `t`."""
    defaults = RECT_DEFAULTS if layer["type"] == "rect" else SPRITE_DEFAULTS
    layer_tracks = layer.get("tracks") or tracks(layer)
    return {
        name: value_at(layer_tracks[name], t, layer["constants"].get(name, default))
        for name, default in defaults.items()
    }


def eight_bit(image):
    """Scale 16-bit greyscale scans to 8 bits instead of clipping them to white."""
    if image.mode in {"I;16", "I;16B", "I;16L", "I"}:
        return image.convert("I").point(lambda value: value * (1 / 256)).convert("L")
    return image


class SceneRenderer:
    """Render frames of one validated scene; `assets` maps input IDs to verified paths."""

    def __init__(self, scene, width, height, fps, frames, assets):
        from PIL import Image

        self.Image = Image
        self.width = width
        self.height = height
        self.fps = float(fps)
        self.frames = frames
        self.background = scene["background"][:3] + (255,)
        self.fonts = []
        self.cover_gaps = []
        self.layers = [self._prepare(layer, assets) for layer in scene["layers"]]
        self.unseen = [
            layer["id"]
            for layer in self.layers
            if not any(self._visible(layer, i) for i in range(frames))
        ]

    def _visible(self, layer, index):
        t = index / self.fps
        return layer["start_s"] <= t < layer["end_s"]

    def _peak_scale(self, layer):
        constant = layer["constants"].get("scale", 1.0)
        values = [
            value_at(layer["tracks"]["scale"], i / self.fps, constant)
            for i in range(self.frames)
            if self._visible(layer, i)
        ]
        return max(values, default=constant)

    def _prepare(self, layer, assets):
        from PIL import ImageOps

        layer = {**layer, "tracks": tracks(layer), "cache": None}
        if layer["type"] == "rect":
            return layer
        peak = self._peak_scale(layer)
        if layer["type"] == "image":
            with self.Image.open(assets[layer["asset"]]) as opened:
                opened.load()
                source = eight_bit(ImageOps.exif_transpose(opened)).convert("RGBA")
            sw, sh = source.size
            fit = {
                "cover": max(self.width / sw, self.height / sh),
                "contain": min(self.width / sw, self.height / sh),
                "width": self.width / sw,
                "height": self.height / sh,
                "none": 1.0,
            }[layer["fit"]]
        else:
            source, fit = self._text_sprite(layer, assets, peak)
            sw, sh = source.size
        # Downscale once to the largest size ever shown; a box-filtered pyramid covers zooms.
        largest = fit * peak
        if largest < 1:
            size = (max(1, round(sw * largest)), max(1, round(sh * largest)))
            source = source.resize(size, self.Image.Resampling.LANCZOS)
        layer.update(source_size=(sw, sh), fit_scale=fit, levels=[self._level_entry(source)])
        return layer

    def _level_entry(self, image):
        """A pyramid level, premultiplied once and framed by transparent pixels.

        Premultiplying avoids Pillow re-converting a large source on every frame; the
        transparent frame gives antialiased edges and keeps every sampling box in bounds.
        """
        premultiplied = image.convert("RGBa")
        padded = self.Image.new("RGBa", (image.width + 2 * PAD, image.height + 2 * PAD))
        padded.paste(premultiplied, (PAD, PAD))
        return {"image": padded, "plain": image}

    def _text_sprite(self, layer, assets, peak):
        from PIL import ImageDraw, ImageFont, features

        px = layer["size"] * self.height
        raster = min(MAX_FONT_PX, max(1.0, px * peak))
        if layer["font"]:
            font = ImageFont.truetype(str(assets[layer["font"]]), round(raster))
            source = {"asset": layer["font"]}
        else:
            try:
                font = ImageFont.load_default(size=round(raster))
            except TypeError:
                font = None
            if not isinstance(font, ImageFont.FreeTypeFont):
                raise ValueError(
                    f"Layer {layer['id']}: no scalable default font; register a font asset"
                )
            import PIL

            source = {"default": "Pillow " + PIL.__version__}
        source["freetype"] = features.version("freetype2")
        self.fonts.append({"layer": layer["id"], **source})
        spacing = max(0, round((layer["line_spacing"] - 1.0) * round(raster)))
        probe = ImageDraw.Draw(self.Image.new("L", (1, 1)))
        box = probe.multiline_textbbox(
            (0, 0), layer["text"], font=font, spacing=spacing, align=layer["align"]
        )
        pad = 2
        # Centred multi-line boxes have fractional offsets; round the canvas outward.
        size = (math.ceil(box[2] - box[0]) + 2 * pad, math.ceil(box[3] - box[1]) + 2 * pad)
        mask = self.Image.new("L", size, 0)
        ImageDraw.Draw(mask).multiline_text(
            (pad - box[0], pad - box[1]),
            layer["text"],
            font=font,
            fill=255,
            spacing=spacing,
            align=layer["align"],
        )
        red, green, blue, alpha = layer["color"]
        sprite = self.Image.new("RGBA", size, (red, green, blue, 0))
        sprite.putalpha(mask if alpha == 255 else mask.point(lut(alpha / 255)))
        # At scale 1 the glyphs are shown at `px`, whatever size they were rasterized at.
        return sprite, px / round(raster)

    def _level(self, layer, scale):
        """The coarsest pyramid level still at least as detailed as the displayed size."""
        levels = layer["levels"]
        sw = layer["source_size"][0]
        while True:
            plain = levels[-1]["plain"]
            if plain.width < 4 or plain.height < 4 or plain.width / 2 / sw < scale:
                break
            levels.append(self._level_entry(plain.reduce(2)))
        for level in reversed(levels):
            if level["plain"].width / sw >= scale:
                return level
        return levels[0]

    def _sprite(self, layer, state, cover):
        sw, sh = layer["source_size"]
        scale = layer["fit_scale"] * state["scale"]
        level = self._level(layer, scale)
        padded = level["image"]
        dx, dy = level["plain"].width / sw, level["plain"].height / sh
        theta = math.radians(state["rotation"])
        cos, sin = math.cos(theta), math.sin(theta)
        px, py = state["x"] * self.width, state["y"] * self.height
        ax, ay = state["ax"] * sw, state["ay"] * sh
        # Inverse map: output pixel -> source coordinates -> padded pyramid-level coordinates.
        a, b = dx * cos / scale, dx * sin / scale
        d, e = -dy * sin / scale, dy * cos / scale
        c = dx * ax - a * px - b * py + PAD
        f = dy * ay - d * px - e * py + PAD
        # Output bounds of the padded level: the edge band stays antialiased and in bounds.
        det = a * e - b * d
        corners = [
            ((e * (u - c) - b * (v - f)) / det, (a * (v - f) - d * (u - c)) / det)
            for u, v in ((0, 0), (padded.width, 0), (0, padded.height), padded.size)
        ]
        x0 = max(0, math.ceil(min(point[0] for point in corners)))
        y0 = max(0, math.ceil(min(point[1] for point in corners)))
        x1 = min(self.width, math.floor(max(point[0] for point in corners)))
        y1 = min(self.height, math.floor(max(point[1] for point in corners)))
        if x1 <= x0 or y1 <= y0:
            return None
        if abs(sin) < 1e-12 and cos > 0:
            # Unrotated moves (nearly all Ken Burns work) take Pillow's filtered resize path.
            box = (
                min(max(0.0, a * x0 + c), padded.width),
                min(max(0.0, e * y0 + f), padded.height),
                min(max(0.0, a * x1 + c), padded.width),
                min(max(0.0, e * y1 + f), padded.height),
            )
            region = padded.resize((x1 - x0, y1 - y0), self.Image.Resampling.BICUBIC, box=box)
        else:
            region = padded.transform(
                (x1 - x0, y1 - y0),
                self.Image.Transform.AFFINE,
                (a, b, c + a * x0 + b * y0, d, e, f + d * x0 + e * y0),
                resample=self.Image.Resampling.BICUBIC,
            )
        region = region.convert("RGBA")
        # Geometric coverage ignores opacity: a fade is intended, an uncovered edge is not.
        covered = (
            region.getchannel("A").point(lambda value: 255 if value >= 128 else 0)
            if cover
            else None
        )
        if state["opacity"] < 1:
            region.putalpha(region.getchannel("A").point(lut(state["opacity"])))
        return region, (x0, y0), covered

    def _rect(self, layer, state):
        ux0, uy0 = round(state["x"] * self.width), round(state["y"] * self.height)
        ux1 = round((state["x"] + state["w"]) * self.width)
        uy1 = round((state["y"] + state["h"]) * self.height)
        x0, y0 = max(0, ux0), max(0, uy0)
        x1, y1 = min(self.width, ux1), min(self.height, uy1)
        red, green, blue, alpha = layer["color"]
        fill = (red, green, blue, round(alpha * state["opacity"]))
        if x1 <= x0 or y1 <= y0 or fill[3] == 0:
            return None
        if layer["outline"] is None:
            return self.Image.new("RGBA", (x1 - x0, y1 - y0), fill), (x0, y0), None
        from PIL import ImageDraw

        region = self.Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        ImageDraw.Draw(region).rectangle(
            (ux0 - x0, uy0 - y0, ux1 - x0 - 1, uy1 - y0 - 1),
            outline=fill,
            width=max(1, round(layer["outline"] * self.height)),
        )
        return region, (x0, y0), None

    def frame(self, index):
        """One RGB frame; frame `index` is shown at t = index / fps."""
        t = index / self.fps
        canvas = self.Image.new("RGBA", (self.width, self.height), self.background)
        coverage = None
        for layer in self.layers:
            if not self._visible(layer, index):
                continue
            state = state_at(layer, t)
            cover = layer["type"] == "image" and layer["fit"] == "cover"
            signature = tuple(sorted(state.items()))
            if layer["cache"] and layer["cache"][0] == signature:
                drawn = layer["cache"][1]
            else:
                drawn = (
                    self._rect(layer, state)
                    if layer["type"] == "rect"
                    else self._sprite(layer, state, cover)
                )
                layer["cache"] = (signature, drawn)
            if cover and coverage is None:
                coverage = self.Image.new("L", (self.width, self.height), 0)
            if drawn:
                region, (x0, y0), covered = drawn
                if covered is not None:
                    box = (x0, y0, x0 + region.width, y0 + region.height)
                    coverage.paste(255, box, covered)
                canvas.alpha_composite(region, dest=(x0, y0))
        if coverage is not None and self.width > 2 and self.height > 2:
            inner = coverage.crop((1, 1, self.width - 1, self.height - 1))
            if inner.getextrema()[0] < 255:
                self.cover_gaps.append(index)
        return canvas.convert("RGB")

    def warnings(self):
        found = []
        if self.cover_gaps:
            found.append(
                f"cover-fit layers leave the background visible in {len(self.cover_gaps)} frame(s),"
                f" first at frame {self.cover_gaps[0]}"
            )
        if self.unseen:
            found.append("layers never visible: " + ", ".join(self.unseen))
        return found


def lut(factor):
    return [round(value * factor) for value in range(256)]
