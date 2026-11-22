# Contributing

## Before opening a pull request

- Discuss large behavior or data-model changes in an issue.
- Keep biometric and authentication decisions on the backend.
- Preserve the non-face sign-in alternative.
- Preserve accessible, localized feedback.
- Never commit secrets, real face data, databases, logs, or local environments.

## Development checks

```powershell
npm test
npm run check:locales
$env:VITE_BASE = "/"
npm run build
.\.venv\Scripts\python.exe -m ruff check backend scripts
.\.venv\Scripts\python.exe -m ruff format --check backend scripts
```

Add regression tests for:

- Token expiry and client binding
- Authentication and recovery
- Administrator authorization
- Biometric encryption
- Localization changes
- WebSocket state transitions

## Pull requests

Describe:

- User-visible change
- Security impact
- Data migration impact
- Tests performed
- Screenshots for UI changes

Do not include sensitive personal data in screenshots.

## Commit style

Use concise imperative commit subjects, for example:

```text
Add candidate-token expiry checks
Fix recovery question localization
Harden production request limits
```

## Security reports

Follow [SECURITY.md](SECURITY.md). Do not disclose vulnerabilities in a public
issue or pull request.
