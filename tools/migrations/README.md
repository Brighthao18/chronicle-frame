# Retained migration support

Implementations live in the installed package's `migrations/legacy` namespace. Thin wrappers
remain at both `tools/migrations/legacy/upgrade_project_v*.py` and the old `scripts/` paths.
`hsd migrate <revision> <project>` offers dry-run entry points; add `--apply` to make the
existing non-destructive additions. Specialized legacy flags remain on the direct wrapper.

| Additive milestone | Retained helper |
|---|---|
| 1.2 or earlier → 1.3 planning assets | `upgrade_project_v13.py` |
| 1.3 → 1.4 creative/optional profile | `upgrade_project_v14.py` |
| 1.4 → 1.5 chaining | `upgrade_project_v15.py` |
| 1.5 → 1.6 chaining refinement | `upgrade_project_v16.py` |
| 1.6 → 1.7 reachability | `upgrade_project_v17.py` |
| 1.7 → 1.8 scene planning | `upgrade_project_v18.py` |
| 1.8 → 1.9 prompt planning | `upgrade_project_v19.py` |
| 1.9 → 1.10 per-unit endpoints | `upgrade_project_v110.py` |
| 1.10 → 2.0 join/assembly plans | `upgrade_project_v20.py` |
| 2.0 → 3.0 source-first controls | `upgrade_project_v30.py` |

These milestones describe internal file-layout additions, not fabricated public releases or
a universal inference engine for arbitrary old workspaces. Take a recoverable copy, inspect the
dry run and use the needed milestones in order. No helper deletes source media or adopts a
legacy generated asset automatically. Authored files and active runtime requests must be preserved.

Current readers retain graph schema `3.2` and state/queue schema `3.1`; some additive control and
registry files still use `3.0` and the original generation manifest uses `1.2`. These are distinct
wire schemas, not package release numbers. `VERSION` and Skill metadata define the current runtime.
There is no destructive automatic downgrade or unsupported blanket schema upgrade.
