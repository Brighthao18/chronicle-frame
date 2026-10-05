# Security

This runtime prepares local jobs and validates receipts/media. It does not manage provider
credentials or implement authenticated provider APIs. Treat profiles, plans and downloaded media
as untrusted inputs; preserve path containment, safe argument-vector subprocess calls, hash checks
and explicit state transitions. Never use shell interpolation to execute supplied project data.

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
