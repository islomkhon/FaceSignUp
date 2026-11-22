# Privacy Notes

This document describes the default implementation and is not legal advice.

## Data categories

### Account data

- Display name or nickname
- Role
- Creation time
- Password hash
- Recovery question
- Recovery-answer hash
- Consent and Terms versions/timestamps

### Biometric and image data

- Encrypted numerical face embedding
- Encrypted 256x256 profile thumbnail
- Per-scan consistency and quality measurements

Raw camera frames are processed in memory and are not intentionally persisted.

### Security data

- Hashed session tokens
- Temporary in-memory face, candidate, and enrollment tokens
- Rate-limit counters

## Purposes

- Account registration
- Face sign-in
- Same-person consistency checks
- Password fallback
- Password recovery
- Administrator account management
- Abuse prevention and security monitoring
- Legal and consent record keeping

## Access

- A successful face scan returns candidate display names.
- Profile thumbnails require an authenticated administrator.
- Recovery questions are returned through the recovery flow.
- Face embeddings and photo blobs are never returned by public APIs.

## Retention

Persistent account and biometric data remains until:

- The user deletes the account, or
- Deletion is performed under an authorized support process, or
- Law requires a different retention period.

Temporary scan and candidate tokens expire automatically. Auth sessions expire
after 12 hours unless invalidated earlier.

## Deletion

Self-service account deletion removes:

- User record
- Face template
- Profile thumbnail
- Recovery question and answer hash
- Authentication sessions

Backups may retain encrypted copies until their normal expiry. Operators should
document backup retention and deletion procedures.

## Children

The current checkbox does not establish guardian consent or verify age. A
separate age-assurance and guardian-consent process is required where children
may register.

## International requirements

Biometric-data rules vary. Before public deployment:

- Identify the legal basis and operator identity.
- Provide a localized privacy notice.
- Provide a non-face alternative where required.
- Document retention, processors, transfers, and user rights.
- Complete a privacy impact assessment.
- Obtain qualified local legal review.

## Logs and analytics

The default app does not use remote analytics. Do not add analytics that capture
camera contents, names, embeddings, passwords, answers, or session cookies.
