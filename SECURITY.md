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
  validated in `src/asset_manager/validation.py` before use.
- No secrets or credentials are stored by this project.
- Dependencies are pinned via `requirements-dev.lock.txt` and audited with
  `pip-audit` in CI.