# Administrator Guide

## First login

1. Open `/admin` on the same host as FaceSignUp.
2. Sign in with the bootstrap administrator credentials documented in the
   repository.
3. Change the bootstrap password immediately.
4. User-management access remains locked until the password change completes.

Password changes invalidate existing sessions and create a fresh session.

## User management

The account list shows:

- Display name
- Role
- Face-enrollment state
- Profile-photo availability
- Password-change requirement
- Creation date

## Profile photos

Profile photos are small encrypted enrollment thumbnails.

- Only authenticated administrators can request them.
- Responses are marked `no-store`.
- Select the avatar or **View photo** to open the larger viewer.
- Close with the close button, Escape, or a click outside the image.

Existing accounts created before profile-photo support show initials instead.

## Roles

### User

Can use the scanner, password fallback, recovery, and self-deletion.

### Admin

Can additionally access administrator APIs and user management.

Safety rules:

- An administrator cannot change their own role.
- The final administrator cannot be demoted.
- The final administrator cannot be deleted.
- Administrators cannot delete themselves through user management; use the
  current account's self-deletion flow.

## Delete a user

Deletion is permanent and cascades to:

- Face templates
- Profile thumbnail
- Recovery question and answer hash
- Authentication sessions

Confirm the selected account before deleting it.

## Administrator password recovery

The app does not expose a public administrator-recovery question. Because
passwords are one-way hashes, a lost administrator password cannot be decoded.
Use the offline maintenance procedure in [Operations](OPERATIONS.md).

## Security checklist

- Use a unique password of at least 10 characters.
- Never share administrator sessions.
- Use HTTPS.
- Sign out on shared computers.
- Review unexpected role changes.
- Keep encrypted database backups.
- Do not export user photos or biometric data unless legally authorized.
