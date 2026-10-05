# Changelog

## Unreleased

Claude Code video: code-rendered units authored as programs and rendered locally.

- Add the `CODE` unit mode, an optional film-wide `render` format and provider `code` jobs that
  compile with a code render contract instead of a Flow prompt.
- Add the `hsd-scene/1` declarative scene format (image, text and rectangle layers with eased
  keyframes) and a deterministic Pillow compositor that only moves, scales, rotates and fades
  verified inputs, reports every validation problem by JSON path and warns about uncovered frames.
- Add `hsd code probe|brief|preview|render|author`. Renders are verified before any claim, so a
  broken program costs no attempt; valid renders are receipted as `local-render` with program,
  input, output and toolchain hashes, a contact sheet and a review template.
- Allow opt-in Python render programs, run in isolated mode with a minimal environment.
- Add budgeted headless Claude Code authoring (`claude -p`, file tools only, observed CLI flags,
  per-session reservation, optional USD cap and an explicit input-sharing data boundary).
- Assemble each job from its own approved output, fixing neutral `video` projects whose accepted
  clips live in `generated/video_approved/`.
- Add the offline `examples/claude-code-video` project, fast and real-media tests and the
  [Claude Code video guide](references/providers/CLAUDE_CODE_VIDEO.md). No live Claude Code
  session was run by the tests; they use an offline stand-in for the CLI.

## 3.3.0 — 2026-10-05

First public ChronicleFrame release, preserving the internal 3.2.1 production baseline.

- Preserve the tested production behavior behind a proper Python package and local CLI.
- Extract optional historical profiles and provider workflows from generic runtime policy.
- Retain script commands and every original behavioral assertion; separate real-media tests.
- Add offline examples, package metadata, bilingual documentation, governance and no-paid-API CI.
- Remove private identity, private design-report references, cached submission logistics and bytecode.
- Introduce the ChronicleFrame repository identity, original banner and project links; retain
  the existing package, Skill, CLI and compatibility names.

See [the migration report](docs/MIGRATION_REPORT.md) for actual verification and limitations.
[Legacy internal change notes](docs/legacy/CHANGELOG.md) are retained for migration context.
