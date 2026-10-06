# Offline Claude Code video example

Two `CODE` units animate one original, document-like synthetic sheet: a push toward a red
square that ends in an outline, then a graphic-reset wipe with a caption. Their scenes in
`programs/` are what Claude Code writes from `hsd code brief`. The fixture carries no
historical claim. Initialization and preparation need only Python; previews need Pillow
(the `media` extras). Rendering also needs FFmpeg and OpenCV.

Run from the repository after installation:

```sh
python examples/claude-code-video/create_demo.py work/code-demo
hsd validate work/code-demo
hsd prepare work/code-demo
hsd next work/code-demo
hsd code brief work/code-demo FLOW_U1
hsd code preview work/code-demo FLOW_U1 --program programs/U1.scene.json
hsd code preview work/code-demo FLOW_U2 --program programs/U2.scene.json
```

`next` lists both jobs as provider `code`, held by `G2_VISUAL`, `CAPABILITY_UNAVAILABLE`
and `EXECUTION_SCOPE_MISSING`. That is intended: this example never fabricates a human
decision or an authorization. `brief` prints the contract, format, input and rules an author
works from. Each `preview` writes full-resolution stills and `contact.png` under
`work/code-demo/work/code_previews/` and records nothing.

To render in a real project, an actual G2 decision is recorded with `scripts/approve_gate.py`,
the user's authorization reference and a `code_output_limit` go into
`00_execution_policy.json`, and `hsd code probe` observes the local renderer. Then
`hsd code render <project> FLOW_U1 --program programs/U1.scene.json` produces a candidate,
a contact sheet and a review template for an explicit review. See
[Claude Code video](../../references/providers/CLAUDE_CODE_VIDEO.md).
