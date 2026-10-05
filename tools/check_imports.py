"""Import the complete standard-library runtime surface without media dependencies."""

import importlib

MODULES = [
    "cli",
    "commands",
    "project",
    "profiles",
    "validation",
    "dependencies",
    "runtime.storage",
    "runtime.common",
    "runtime.engine",
    "runtime.controller",
    "runtime.gate_records",
    "runtime.asset_registry",
    "providers.capabilities",
    "providers.code",
    "providers.code.scene",
    "providers.code.render",
    "providers.code.brief",
    "providers.code.claude",
    "providers.code.command",
    "production.graph",
    "production.prepare",
    "production.image_jobs",
    "production.video_jobs",
    "production.generation_plan",
    "production.assembly_plan",
    "prompts.video",
    "prompts.chain",
    "qc.project",
    "qc.readiness",
    "qc.endpoints",
    "qc.joins",
    "qc.screenplay",
    "qc.video_prompts",
    "qc.generation_prompts",
    "media.inspection",
    "media.assembly",
    "media.animatic",
    "media.deterministic",
    "media.finishing",
    "media.subtitles",
]

for module in MODULES:
    importlib.import_module("historical_shortfilm_director." + module)
print(f"PASS: imported {len(MODULES)} core modules without executing a provider")
