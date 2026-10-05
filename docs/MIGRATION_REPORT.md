# Public-repository migration report

Date: 2026-10-05. Preserved internal baseline: **3.2.1**. Public release: **3.3.0**,
under the repository name **ChronicleFrame**. The maintainer subsequently authorized
commit and publication. See [v3.3.0 release notes](releases/v3.3.0.md) for the public package.

The validation tables below record the local refactor checkpoint, before GitHub publication.
Online results are available through the repository's Actions page; no historical release
or Git history has been reconstructed.

## Scope and preservation

Created a separate public-ready checkout on `refactor/public-oss`. The supplied source had no
`.git` directory/history; the delivery repository was initialized on that branch without inventing
historical commits, authors, release dates or a remote. No Git configuration was read or disclosed.
At that checkpoint, the branch had no commit; source changes were reviewable in the local
index and files. No hosting, publishing, account login or paid generation was performed
during the refactor. The later publication adds present-day commits rather than invented history.

The original active Skill and film projects remain outside this new checkout. All 90 original
files, including six original bytecode files, were verified unchanged against the pre-refactor hash
manifest. The MIT license is byte-for-byte unchanged. Private research documents and source media
were never copied. Temporary tests, media and environments are outside the public source checkout.

Before restructuring, the original 41-method suite passed. Protected invariants were atomic JSON
and single-writer state, portable paths/containment, durable claims and receipts, input/candidate
hashes, transitive freshness, real human decisions bound to reviewed hashes, preserved authored
plans, exact non-destructive overlays, complete decode and preview/assembly provenance.
The changes package those implementations instead of replacing working rendering or state logic.

## Resulting architecture

Behavior lives under `src/historical_shortfilm_director/`: runtime storage/state, graph/compilers,
prompts, evidence overlays, assets/gates, QC, media, reviews, provider capabilities and profiles.
`hsd` and `historical-shortfilm-director` expose local operations. Existing scripts are thin wrappers
over the same package functions; there is no parallel runtime implementation. Child command
execution uses argument vectors and a package bootstrap, also preserving an uninstalled complete
Skill checkout. No shell interpolation or invented provider/browser API was added.

Generic operation uses `image`/`video` observed capabilities without a historical profile.
Flow browser/operator policy and legacy capability aliases remain conditional adapters. OpenAI
image tools remain an agent-tool workflow without assumed model selection. Capability snapshots
record supported conditioning, durations/reference limits, observation evidence and execution kind.
Actual external execution remains separate from local preparation and ingestion.

JNU policy is packaged declarative profile data, with frozen project configuration and an optional
`examples/jnu-gate/` demonstration. All six original JNU references and remaining institution-specific
application sections are retained there. Constraints and historical assertions are clearly labeled
as example material; there is no current competition-rule claim or bundled original source media.

## Old path → new path

Old script filenames remain compatibility entry points unless explicitly described below.
The machine-readable full map is [path-mapping.json](path-mapping.json).

| Old path or behavior | New implementation or retained location |
|---|---|
| `CHANGELOG.md` | `CHANGELOG.md (public release changes) + docs/legacy/CHANGELOG.md (retained internal notes)` |
| `references/FLOW_AUTOMATION.md` | `references/providers/FLOW_AUTOMATION.md` |
| `references/FLOW_CINEMATIC_PROMPTING.md` | `references/providers/FLOW_CINEMATIC_PROMPTING.md` |
| `references/FLOW_NATIVE_SCREENWRITING_AND_PROMPTING.md` | `references/providers/FLOW_NATIVE_SCREENWRITING_AND_PROMPTING.md` |
| `references/FLOW_SHOT_ENDPOINT_SYSTEM.md` | `references/providers/FLOW_SHOT_ENDPOINT_SYSTEM.md` |
| `references/IMAGE25_AUTOMATION.md` | `references/providers/IMAGE25_AUTOMATION.md` |
| `references/JNU_120_PROFILE.md` | `examples/jnu-gate/references/JNU_120_PROFILE.md` |
| `references/JNU_GATE_FLOW_PLAYBOOK.md` | `examples/jnu-gate/references/JNU_GATE_FLOW_PLAYBOOK.md` |
| `references/JNU_GATE_GENERATION_PLAYBOOK.md` | `examples/jnu-gate/references/JNU_GATE_GENERATION_PLAYBOOK.md` |
| `references/JNU_GATE_PROJECT_MODE.md` | `examples/jnu-gate/references/JNU_GATE_PROJECT_MODE.md` |
| `references/JNU_GATE_V2_PRODUCTION_BASELINE.md` | `examples/jnu-gate/references/JNU_GATE_V2_PRODUCTION_BASELINE.md` |
| `references/JNU_GATE_VISUAL_REDESIGN_EXAMPLE.md` | `examples/jnu-gate/references/JNU_GATE_VISUAL_REDESIGN_EXAMPLE.md` |
| `scripts/apply_locked_overlays.py` | `src/historical_shortfilm_director/evidence/apply_overlays.py` |
| `scripts/approve_gate.py` | `src/historical_shortfilm_director/gates.py` |
| `scripts/assemble_direct.py` | `src/historical_shortfilm_director/media/assembly.py` |
| `scripts/auto_qc_media.py` | `src/historical_shortfilm_director/qc/media.py` |
| `scripts/build_animatic.py` | `src/historical_shortfilm_director/media/animatic.py` |
| `scripts/build_review_board.py` | `src/historical_shortfilm_director/reviews/board.py` |
| `scripts/build_review_packet.py` | `src/historical_shortfilm_director/reviews/packet.py` |
| `scripts/check_dependencies.py` | `src/historical_shortfilm_director/dependencies.py` |
| `scripts/compile_ass_subtitles.py` | `src/historical_shortfilm_director/media/subtitles.py` |
| `scripts/compile_chain_prompts.py` | `src/historical_shortfilm_director/prompts/chain.py` |
| `scripts/compile_direct_assembly.py` | `src/historical_shortfilm_director/production/assembly_plan.py` |
| `scripts/compile_flow_jobs.py` | `src/historical_shortfilm_director/production/video_jobs.py` |
| `scripts/compile_flow_operator_pack.py` | `src/historical_shortfilm_director/providers/flow/operator_pack.py` |
| `scripts/compile_flow_prompts.py` | `src/historical_shortfilm_director/prompts/video.py` |
| `scripts/compile_generation_plan.py` | `src/historical_shortfilm_director/production/generation_plan.py` |
| `scripts/compile_image25_jobs.py` | `src/historical_shortfilm_director/production/image_jobs.py` |
| `scripts/compile_scene_graph.py` | `src/historical_shortfilm_director/production/graph.py` |
| `scripts/extract_review_frames.py` | `src/historical_shortfilm_director/media/frames.py` |
| `scripts/init_project.py` | `src/historical_shortfilm_director/project.py` |
| `scripts/init_project.py::GATE_FILES` | `src/historical_shortfilm_director/profiles/builtin/jnu_gate/profile.json` |
| `scripts/lint_flow_prompts.py` | `src/historical_shortfilm_director/qc/video_prompts.py` |
| `scripts/lint_generation_prompts.py` | `src/historical_shortfilm_director/qc/generation_prompts.py` |
| `scripts/mix_final_master.py` | `src/historical_shortfilm_director/media/finishing.py` |
| `scripts/pipeline_controller.py` | `src/historical_shortfilm_director/runtime/controller.py` |
| `scripts/prepare_production.py` | `src/historical_shortfilm_director/production/prepare.py` |
| `scripts/production_common.py` | `src/historical_shortfilm_director/runtime/common.py` |
| `scripts/production_common.py::ffmpeg/media_check` | `src/historical_shortfilm_director/media/inspection.py` |
| `scripts/production_common.py::gate_status/gate_covers` | `src/historical_shortfilm_director/runtime/gate_records.py` |
| `scripts/production_common.py::register` | `src/historical_shortfilm_director/runtime/asset_registry.py` |
| `scripts/production_common.py::storage/hash/path/lock` | `src/historical_shortfilm_director/runtime/storage.py` |
| `scripts/production_runtime.py` | `src/historical_shortfilm_director/runtime/engine.py` |
| `scripts/production_runtime.py::capability` | `src/historical_shortfilm_director/providers/capabilities.py` |
| `scripts/qc_project.py` | `src/historical_shortfilm_director/qc/readiness.py` |
| `scripts/qc_project.py::flow_*_warnings` | `src/historical_shortfilm_director/providers/flow/qc.py` |
| `scripts/register_asset.py` | `src/historical_shortfilm_director/assets.py` |
| `scripts/render_deterministic_shots.py` | `src/historical_shortfilm_director/media/deterministic.py` |
| `scripts/review_flow_endpoints.py` | `src/historical_shortfilm_director/qc/endpoints.py` |
| `scripts/review_flow_script.py` | `src/historical_shortfilm_director/qc/screenplay.py` |
| `scripts/review_join_contracts.py` | `src/historical_shortfilm_director/qc/joins.py` |
| `scripts/seal_evidence.py` | `src/historical_shortfilm_director/evidence/overlays.py` |
| `scripts/self_test_v31.py` | `retained entry point + tests/unit/test_runtime_regressions.py + tests/integration/test_runtime_media.py` |
| `scripts/self_test_v32.py` | `retained entry point + tests/unit/test_graph_regressions.py + tests/integration/test_animatic_media.py` |
| `scripts/upgrade_project_v110.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v110.py` |
| `scripts/upgrade_project_v13.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v13.py` |
| `scripts/upgrade_project_v14.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v14.py` |
| `scripts/upgrade_project_v14.py::GATE_NEW` | `src/historical_shortfilm_director/profiles/builtin/jnu_gate/legacy-v14-templates.json` |
| `scripts/upgrade_project_v15.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v15.py` |
| `scripts/upgrade_project_v16.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v16.py` |
| `scripts/upgrade_project_v17.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v17.py` |
| `scripts/upgrade_project_v18.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v18.py` |
| `scripts/upgrade_project_v19.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v19.py` |
| `scripts/upgrade_project_v20.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v20.py` |
| `scripts/upgrade_project_v30.py` | `src/historical_shortfilm_director/migrations/legacy/upgrade_project_v30.py` |
| `scripts/validate_skill.py` | `src/historical_shortfilm_director/validation.py` |

## Removed files and justification

- Six source `scripts/__pycache__/*.pyc` files were excluded from the public copy. They are generated
  interpreter caches, not source behavior; the original files were left intact.
- Original JNU/provider reference paths were relocated, not discarded. Git/source maps identify
  their new paths; no copyrighted media was bundled.
- Private contributor identity, seven private-report attribution occurrences, one stale deadline
  and one submission destination were removed/reworded after classification. Source design ideas
  are retained as internal project decisions, not fabricated public citations.
- The old short README was replaced by complete English/Chinese documentation. Original internal
  change notes moved to `docs/legacy/CHANGELOG.md`, with an explicit non-release-history disclaimer.
- Build products, bytecode and tool caches produced during validation are removed from the source
  checkout before packaging and are ignored. No functioning legacy implementation or upgrader was
  destructively dropped. Wheel/source distributions are separate delivery artifacts.

## Compatibility and intentional changes

Retained: all 41 original assertions, old script commands/import bridges, ten dry-run/apply migration
helpers, generic/Flow CLI initialization flags, `jnu_gate` and `jnu120` profile entry names, numbered
project artifacts, `IMG25_`/`FLOW_` IDs, legacy image routes, pending plan readiness, source overlays,
gate prerequisites and hash-bound acceptance. Pristine original initialization templates remain
recognized by graph ownership checks; authored plan edits still block silent replacement.

Changes contributors should review:

- Reusable Python imports now use the installed package namespace. A single copied script needs
  the rest of the Skill/package bundle; direct old script paths remain supported in a full checkout.
- New generic image jobs have no automatically selected vendor/model. Missing current capabilities
  block execution rather than claiming unavailable model selection.
- Generic video jobs use the neutral `video` capability/output-budget slot and explicit observed
  conditioning. Existing Flow jobs keep their legacy slot and hash semantics.
- The old `jnu120` initialization name resolves to the canonical gate profile and gains its templates.
  New custom profile JSON is frozen as `00_profile.json`; project metadata stores a portable name.
- Legacy v1.4 title-based institution inference is replaced by an explicit profile or its retained
  `--gate-mode` flag. No institution name or archival asset ID is embedded in generic runtime/QC.
- Current `skill_pipeline_version` output uses canonical `VERSION`; legacy milestone filenames and
  distinct wire schema numbers are retained intentionally. See [migration support](../tools/migrations/README.md).
- Full Skill installation needs the source/documentation bundle. A wheel installs the Python runtime
  and bundled profiles/templates, not a separate agent discovery installation.

No destructive downgrade or unsupported blanket project conversion is claimed. Legacy additive
migrations support the documented 1.3–3.0 milestones; readers retain graph 3.2 and state/queue 3.1,
with original control/registry 3.0 and generation-manifest 1.2 wire formats.

## Actual validation

Local host: Windows, Python 3.12. No failed check remains.

| Check | Actual result |
|---|---|
| Original pre-refactor self-test | 41 passed |
| Retained packaged self-test | 41 passed |
| Default fast pytest suite | 54 passed; 6 slow tests deselected |
| Actual local encoding integration | 6 passed; 54 fast tests deselected |
| Core install, wheel in fresh environment | Passed with no package dependencies installed |
| Installed generic and JNU profile initialization | Both passed from the wheel outside the checkout |
| Skill structural validation | Built-in bundle validator and creator validator passed |
| Python compilation/core imports | Passed; 34 standard-library runtime modules imported |
| Python 3.10 syntax parsing | Passed for 141 source/helper/test files; not a Python 3.10 execution claim |
| Lint and formatting | Ruff checks passed |
| Workflow/issue YAML and package JSON | Parsed successfully |
| Minimal example | Initialized, validated, prepared, inspected and encoded |
| Synthetic preview and assembly | Three-second still preview, full decode, receipt and picture assembly passed |
| Documented command checks | 21 exercised forms; runtime/final-mix mechanics additionally covered by preserved tests |
| Original source/filename preservation | 90 original file hashes unchanged |
| Paid/live providers | NOT RUN; no generation account or provider call used |
| GitHub Actions online execution | NOT RUN; configuration and corresponding local checks only |

The replacement suites preserve all 41 methods in [test-coverage-mapping.json](test-coverage-mapping.json):
35 fast and six real-media tests. New public-runtime tests add CLI/profile/capability/migration checks.
Synthetic receipts and approved test fixtures are explicitly marked as fixtures; they do not prove
real tool execution, historical truth or actual human approval. The minimal demonstration leaves
every human gate pending and has no historical claims.

## Security/privacy classification

The baseline static tree scan found the following ten locations, each classified before cleanup.
Values are intentionally omitted from this public report.

| Original location | Category | Disposition |
|---|---|---|
| `CHANGELOG.md:127` | private_report | Removed private attribution; described as internal design decisions |
| `CHANGELOG.md:200` | private_report | Removed private attribution; described as internal design decisions |
| `references/JNU_120_PROFILE.md:19` | stale_submission_logistics | Removed cached deadline; example constraints labeled as illustrative |
| `references/JNU_120_PROFILE.md:20` | email | Removed stale submission destination from the example |
| `references/SHORTFORM_CREATIVE_SYSTEM.md:3` | private_report | Removed private attribution; described as internal design decisions |
| `references/SOURCES.md:48` | private_report | Removed private attribution; described as internal design decisions |
| `references/SOURCES.md:61` | private_report | Removed private attribution; described as internal design decisions |
| `references/SOURCES.md:77` | private_report | Removed private attribution; described as internal design decisions |
| `references/SOURCES.md:82` | private_report | Removed private attribution; described as internal design decisions |
| `SKILL.md:6` | private_identity | Replaced with neutral contributor metadata |

One additional possessive restoration-reference sentence was made project-neutral in the labeled
historical example; its source/restoration distinction was retained. Institutional names, archival
IDs and historical design constraints are safe optional example material, never core defaults.
All report/source phrasing was independently searched for private identity, personal paths and email.

The final pattern scan finds no embedded API key/password/session cookie/OAuth value, account-state
artifact, personal path, email, private report attribution or temporary submission authorization.
Runtime attempt IDs, receipt fields, blank execution-scope schemas, synthetic fixtures and security
instructions are benign domain terminology. The scan records these separately rather than treating
every occurrence of “token” as an account secret. Public third-party attribution and official
documentation links were retained and checked; no private research citation was invented.

Git index checks exclude tracked bytecode/cache files. This is a best-effort static tree/index scan,
not a universal secret/vulnerability guarantee. **Git history was not scanned:** the input had no
history and the delivery branch had no commits at the local refactor checkpoint. No
history-clean claim is made by this static scan.
See [security-scan.json](security-scan.json) for the actual final tree/index summary.

## Remaining limitations and release recommendation

- Real cloud generation, authenticated browser behavior and provider quality remain untested.
  The runtime truthfully prepares/records handoffs; no direct integrations are promised.
- Python 3.10/3.13 and Ubuntu execution are configured in CI but were not run on this local host.
  Syntax checks and local Python 3.12 tests are distinguished from online matrix execution;
  consult Actions for the current public CI result.
- Legacy numbered artifacts, route aliases and historical migration names remain for preservation.
  Some old manual prompt-planning helpers retain configurable 3-reference/10-second legacy planning
  defaults; they do not establish provider capabilities or bypass observed dispatch checks.
- Historical assertions and redistribution rights in the advanced example require source-specific
  review before real production. No original historical source image is redistributed.
- Local technical PASS is not semantic/historical acceptance or a final-film completion state.
- Public repository and issue channels use the actual ChronicleFrame GitHub repository.
  No PyPI publication, private contact address or public community activity is fabricated.

The recommended **3.3.0** release was adopted after publication was authorized: the new
package/CLI/profile surface is additive while legacy commands, wire formats and production
behavior remain supported. `VERSION`, package metadata and Skill metadata agree at 3.3.0.
The original active Skill remains at 3.2.1. No backdated release or fictitious commit is created.
