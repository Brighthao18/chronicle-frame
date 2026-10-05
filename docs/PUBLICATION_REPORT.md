# ChronicleFrame publication validation

Date: 2026-10-05. Version: **3.3.0**. Repository:
[Brighthao18/chronicle-frame](https://github.com/Brighthao18/chronicle-frame).

The maintainer authorized commit and public GitHub publication after the preservation-first
refactor. ChronicleFrame is the public identity; the Skill/distribution name,
`historical_shortfilm_director` imports, `hsd` CLI and legacy entry points are retained.
The original active Skill and film projects are outside this public checkout and unchanged.

## Observed validation

The tested runtime/package commit is `043c810777cd22f61c982245ca77c5830abc0caa`.
Subsequent publication documentation records these results; it does not change production logic.

| Check | Result | Evidence |
| --- | --- | --- |
| Windows Python 3.10 / 3.12 / 3.13 | PASS | [Public matrix run](https://github.com/Brighthao18/chronicle-frame/actions/runs/37298784798) |
| Ubuntu Python 3.10 / 3.12 / 3.13 | PASS | [Public matrix run](https://github.com/Brighthao18/chronicle-frame/actions/runs/37298784798) |
| Fresh dependency-free wheel installation | PASS | `wheel` job in the same run |
| Ubuntu real-media, retained suite and offline example | PASS | [Media run](https://github.com/Brighthao18/chronicle-frame/actions/runs/37298788454) |
| Isolated local developer install, without OpenCV | 54 PASS | Only `.[dev]`; two optional media modules skipped during collection |
| Full local media suite | 6 PASS | Real FFmpeg encoding and decoded-media checks |
| Retained legacy suite | 41 PASS | Original behavior preserved; overlaps with the replacement tests |
| Public clone and README commands | PASS | Fresh environment, Skill/project checks and three-second offline preview |
| English/Chinese README rendering | PASS | Banner, links, tables and legible Mermaid architecture checked on GitHub |
| Original source preservation | 90 unchanged hashes | Rechecked against the pre-refactor manifest; MIT unchanged |
| Privacy/static tree and index review | PASS | [Security scan ledger](security-scan.json); no tracked caches |

The CI runs listed above were explicitly dispatched. Their corresponding push and pull-request
triggers are also configured. No paid provider is used by either workflow.

## Corrections made before release

- The public repository name differs from the preserved Skill name. Installation instructions
  and CI now check out `historical-shortfilm-director`, satisfying the existing directory/name
  validation rather than weakening it.
- Exact-pixel tests import NumPy. The development/test extras now declare it alongside Pillow;
  OpenCV stays in the media extra and the core retains zero third-party dependencies.
- CI uses UTF-8 consistently on both operating systems.
- The architecture diagram uses three readable stages instead of a very wide single row.

## Distribution and boundaries

The GitHub release includes a complete source ZIP, a runtime wheel, a Python source distribution
and SHA-256 checksums. Source bundles contain the original SVG banner and bilingual documentation.
Git history starts with actual present-day publication commits; earlier history was not reconstructed.
Git configuration was not read or disclosed. The pattern scan covers the current tree/index,
not an exhaustive Git-history or vulnerability audit.

GitHub private vulnerability reporting is enabled. The repository is public, uses MIT licensing
and defaults to `main`. No PyPI publication, live generation, provider-account validation or
creative-quality verification is claimed. Generated media is not historical evidence; the
synthetic example leaves all human gates pending.

[Migration report](MIGRATION_REPORT.md) · [Release notes](releases/v3.3.0.md)
