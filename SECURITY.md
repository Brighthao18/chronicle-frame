# Security

This runtime prepares local jobs and validates receipts/media. It does not manage provider
credentials or implement authenticated provider APIs. Treat profiles, plans and downloaded media
as untrusted inputs; preserve path containment, safe argument-vector subprocess calls, hash checks
and explicit state transitions. Never use shell interpolation to execute supplied project data.

Code-rendered video keeps that boundary. `hsd-scene/1` scenes are data and are rendered without
executing anything they contain. Python render programs are code: they run only after a project
sets `code_render.python_programs` to `true`, in isolated interpreter mode, in a scratch directory,
with a minimal environment (no inherited credentials) and a time limit. That is not a sandbox; the
program has the user's file-system permissions, so review it first and never enable it for an
untrusted project. `hsd code author` resolves the Claude Code CLI from `HSD_CLAUDE` or `PATH`, never
from project files, refuses to run nested inside a Claude Code session, and restricts each session
to file tools in its own work directory. Its brief is sent to the model; input images are shared
only when `claude_code_share_inputs` is `true`.

## Reporting code vulnerabilities

Use [GitHub private vulnerability reporting](https://github.com/Brighthao18/chronicle-frame/security/advisories/new)
when enabled. If the channel is unavailable, request a verified private contact through a public
issue without including exploit details, private data or credentials. No private report address
or response SLA is invented here.

Provide affected version, a minimal synthetic reproduction, impact and proposed mitigation if known.
Do not attach API keys, passwords, session cookies, OAuth values, tokens, private URLs, browser
storage, raw provider-account data or copyrighted media. Redact command paths and receipt handles.
The repository scanner is a best-effort static review, not proof that every secret or vulnerability
is absent. Git-history cleanliness requires a separate actual history scan.

## Provider-account incidents

Compromised provider accounts, billing, entitlements and provider service incidents belong with
that provider's official support/security process. Revoke or rotate exposed credentials through the
provider; never submit them here. Report a separate code issue only if this runtime contributed to
the exposure, using a redacted reproduction.

## Scope and support

The current release version is defined by `VERSION`; releases are distributed through GitHub.
No long-term support policy is established. Local integrity/semantic workflow issues are also welcome, but historical
disagreement alone is not a code security vulnerability; use the historical-integrity issue template.
