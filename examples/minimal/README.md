# Offline synthetic example

These original geometric fixtures carry no historical claims. The example needs no account,
network access or paid generation. Initialization and preparation need only Python; rendering
needs the `media` extras and an external FFmpeg executable.

Run from the repository after installation:

```sh
python examples/minimal/create_demo.py work/demo
hsd validate work/demo
hsd prepare work/demo
hsd status work/demo
hsd next work/demo
hsd qc work/demo
hsd animatic work/demo
hsd qc work/demo --media
```

`prepare` creates the production graph receipt, local plans and an empty generation queue.
`animatic` exports a three-second still-based preview with a padded silent audio track.
Its receipt and HTML review page sit beside the MP4 under the project `previews/` directory.
Every human gate remains `PENDING`; this example never fabricates a human decision.
The preview receipt records an intermediate assembly manifest under `work/animatic/`.
Use that project's relative manifest path with `hsd assemble --manifest` for an optional
straight-cut assembly exercise. This creates a picture-only local output, not an approved final film.

`SOURCE_VERIFIED` in this example means the synthetic input file is integrity-checked.
It does not classify the fixture as a historical source. Keep `origin` and `historical_status`
with the asset when using its record elsewhere.
