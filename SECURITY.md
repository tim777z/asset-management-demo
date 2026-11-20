# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
privately to the maintainers rather than opening a public issue.

- Email: security@precogsecurity.com
- Include a description, reproduction steps, and the affected version/commit.
- You can expect an acknowledgement within 72 hours and a fix or mitigation
  plan within 14 days for confirmed issues.

Please do not publicly disclose the issue until a fix has been released.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Security Notes

- This project reads untrusted CSV and command-line input; all such input is
  validated in `src/asset_manager/validation.py` before use (symbol allowlist,
  numeric parsing via `decimal.Decimal`, row caps). CSV input is treated as
  untrusted; avoid opening unreviewed files.
- No secrets or credentials are stored by this project. Do not commit real
  portfolio data containing sensitive identifiers to public forks. `.env` and
  `.env.*` are gitignored and excluded from the Docker build context; only
  `.env.example` is tracked.
- Symbols are matched against the full string, so trailing newlines or Unicode
  line separators cannot forge an extra row in an exported CSV. Free-text fields
  also reject DEL (0x7F) and U+2028/U+2029 in addition to C0 controls.
- Numeric parsing rejects magnitudes that overflow the float range rather than
  silently returning `inf`, and unexpected CLI exceptions are logged as
  structured JSON with a non-zero exit status instead of raw tracebacks.
- Dependencies are pinned via `requirements-dev.lock.txt` and audited with
  `pip-audit` in CI. Runtime has zero third-party dependencies by design.
- **Project scope:** this is a Python library/CLI (not infrastructure-as-code).
  Security reviews should focus on input validation, dependency hygiene, and
  safe file handling.