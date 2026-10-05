# Contributing

Keep tested behavior and historical integrity ahead of architectural changes. Start from a
dedicated branch, identify the protected invariants and tests, and retain compatibility entry
points until an equivalent replacement is exercised. Do not reconstruct private Git history.

## Development setup

Use Python 3.10+ in an isolated virtual environment. From the checkout:

```sh
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m ruff format --check .
hsd validate --skill .
```

Fast tests use synthetic inputs and need no account or FFmpeg. The test/development extras include
Pillow and NumPy for lossless pixel checks; OpenCV remains in the media extra. Install `.[dev,media]` and an
external FFmpeg for `python -m pytest -m slow`. Real media tests are separate from PR checks.
Legacy suites `scripts/self_test_v31.py` and `scripts/self_test_v32.py` remain during migration;
their real-media dependencies are optional and their assertions map to the normal test layout.
Neither suite calls a live provider. Local artifacts belong under ignored `work/` or outside
the repository. Never commit bytecode, generated media, account state or credentials.

Future live tests must be explicitly marked `live`, require `--live` and disclose possible paid
credits. Default test selection and CI exclude them. Do not add such a test merely to assert
that a provider is available. Record actual authorized executions separately from synthetic tests.

## Add a profile

A profile is JSON data, not executable Python. See the bundled
[`jnu_gate` profile](src/historical_shortfilm_director/profiles/builtin/jnu_gate/profile.json).
Fields: `name`, optional `aliases`/`description`, `templates`, `constraints`, `metadata`, `routing`,
`qc` and `initialization_files`. Templates map project-relative filenames to text; initialization
files map safe relative paths to JSON values. Unknown fields, unsafe paths and nonportable names
must fail before creating files. Core code asks the profile for policy rather than inspecting its name.

Use `hsd init --profile <profile.json> --title <title> --dir <empty-dir>` for a local profile.
The configuration is frozen as `00_profile.json` so a project travels without its original
configuration path. New bundled profiles go under `profiles/builtin/<name>/` in the package;
include fixtures checking installation, constraints, routes, path containment and generic operation
with the profile absent. Keep historical assertions in an explicitly labeled example with sources,
rights and unresolved claims. No private source media or temporary submission logistics.

## Add provider capability support

Read [provider model](references/PROVIDER_MODEL.md). Describe capabilities and a real execution
kind; never infer a model, selector, entitlement, duration or API. Capability snapshots require
observed time and evidence. New neutral video snapshots declare conditioning flags explicitly.
The runtime should remain usable without any provider.

If a provider needs agent/browser/operator handoff, document precisely that limitation. Place
provider policy and operational references under `providers` and `references/providers`. Keep
vendor decisions out of generic graph/state/QC. Test missing and stale observations, unsupported
conditioning, reference/duration bounds and receipt mismatches with deterministic synthetic data.

## Add a migration

Retained migrations are under `src/historical_shortfilm_director/migrations/legacy/`, with thin
entry points under `tools/migrations/legacy/` and `scripts/`. Read [migration support](tools/migrations/README.md).
New migrations need an explicit source/target schema, dry-run mode, backup/preservation policy
and idempotency checks. Preserve evidence, authored plans, accepted asset hashes and active
requests; changing a schema must never silently resubmit a potentially paid operation.
Do not delete an upgrader without documenting an intentional support drop or equivalent path.

## Historical-integrity reports

Use the historical-integrity issue template. Provide the isolated claim, current allowed wording,
source citation, distinction between fact/inference/reconstruction and affected example/logic.
Conflicting evidence is useful. Do not post private research, participant data or copyrighted scans
without redistribution permission. A successful technical test never proves historical truth.

## Generation/runtime reports and pull requests

Use synthetic reproduction data, the command and local version, expected/actual state transitions,
redacted receipt structure and relevant hash changes. Separate offline results from actual live
generation. Never include credentials, cookies, private URLs or full account/session state.
For vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of posting a public exploit.

A PR should explain the trigger, resulting behavior, tests and meaningful limitations. Keep the
MIT license and legitimate source attribution. Use the existing PR template. Version remains
defined by `VERSION`; package metadata, Skill metadata and current runtime reports must agree.
