# Security Policy

## Supported Versions

Only the latest release in the `0.1.x` series receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.1.x (latest) | Yes |
| < 0.1.0 | No |

## Reporting a Vulnerability

**Please do not file public GitHub issues for security vulnerabilities.**

Report security issues by email to **security@placeholder-domain.example**
*(note: this is a placeholder address — replace with a real contact before publishing)*.

Include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce (proof-of-concept code is welcome).
- Any suggested mitigations you have in mind.

You will receive an acknowledgement within **48 hours** and a resolution or
status update within **90 days**. We follow a **90-day coordinated disclosure
clock**: if no fix is available after 90 days we will publish a mitigation advisory
and credit the reporter.

## PGP Key

*TBD — the maintainer will add a PGP public key here before the first public release.
Until then, encrypt sensitive reports with the recipient's personal key if available.*

## Scope

**In scope:**

- Code in this repository (`src/`, `tests/`, `web/`, `website/`, `scripts/`).
- The default configuration shipped with the project.
- The OAuth / credential handling in `tools/gmail.py`.
- The desktop bridge RPC surface in `desktop/bridge.py`.

**Out of scope:**

- Third-party LLM provider infrastructure (Anthropic, OpenAI, Google, Ollama).
- OS-level vulnerabilities or hardware vulnerabilities.
- Vulnerabilities in upstream dependencies that have not yet been fixed upstream.
- Issues that require physical access to the user's machine.

## Acknowledgements

*No reporters yet — this section will list contributors who responsibly disclosed
security issues once the project receives its first report.*
