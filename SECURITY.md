# Security Policy

## Supported status

FaceSignUp is an MVP. Security fixes are applied to the current main branch.

## Reporting

Do not open a public issue for a vulnerability. Use GitHub's private
**Security advisories** feature:

1. Open the repository's **Security** tab.
2. Select **Advisories**.
3. Choose **Report a vulnerability**.

Include the affected commit, impact, reproduction steps, and any suggested
mitigation. Do not upload real biometric data or production secrets.

## Scope

Examples of in-scope issues:

- Authentication or authorization bypass
- Session or temporary-token flaws
- Cross-site request or WebSocket origin bypass
- SQL injection or unsafe deserialization
- Recovery-flow account takeover
- Exposure of decrypted biometric data
- Profile-photo access by non-administrators
- Model or frontend integrity bypass

Known limitations listed in [Security](docs/SECURITY.md) are still useful to
report if a practical exploit or stronger mitigation exists.

## Safe research

- Use only accounts and systems you own or are authorized to test.
- Do not access, modify, retain, or disclose another person's data.
- Avoid denial-of-service testing against public production systems.
- Give the maintainer reasonable time to investigate and patch.
