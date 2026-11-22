# Operations

## Service health

Endpoints:

- `/api/health`: application and model metadata
- `/api/ready`: SQLite readiness

Use a reverse proxy or monitoring system to check readiness externally.

## Logs

Expected log sources:

- Uvicorn application output
- FaceSignUp systemd or container logs
- Reverse-proxy access and error logs

Never log:

- Raw camera frames
- Passwords
- Security answers
- Decrypted embeddings
- Decrypted profile photos
- Session tokens

## Backup

Use SQLite's online backup API:

```bash
python scripts/backup_database.py \
  --source data/facesignup.db \
  --output backups
```

Encrypt the backup and store it separately from the Fernet key.

Without the original Fernet key:

- Face templates cannot be decrypted.
- Profile thumbnails cannot be decrypted.
- Users must re-enroll if the key is lost.

Database backup alone is insufficient for a complete restoration.

## Restore

1. Stop the application.
2. Preserve the current database as an incident backup.
3. Place the restored database at `FACESIGNUP_DB`.
4. Set ownership to the application service account and mode `0600`.
5. Restore the matching `FACESIGNUP_EMBEDDING_KEY`.
6. Start the service.
7. Verify `/api/ready`, administrator login, face login, and recovery.

## Administrator password recovery

Passwords are not reversible. If the sole administrator password is lost:

1. Create an offline backup.
2. Stop the service.
3. Use a trusted maintenance environment with the same backend code to replace
   the administrator password hash with an Argon2id hash and set
   `must_change_password=1`.
4. Restrict database access during the operation.
5. Start the service and immediately change the temporary password.
6. Destroy any temporary secret and backup when no longer required.

Do not insert a plaintext password into the database.

## Session invalidation

To invalidate every user session:

```sql
DELETE FROM auth_sessions;
```

This is appropriate after suspected token compromise or a security incident.

## Updating dependencies

1. Run `npm audit --omit=dev`.
2. Run `pip-audit -r backend/requirements.txt`.
3. Update one dependency family at a time.
4. Run all tests and scan representative faces.
5. Rebuild frontend assets.
6. Verify MediaPipe WASM and model hashes.

## Rotating models

Embedding vectors are model-specific. Replacing SFace invalidates the
compatibility of existing embeddings. A safe migration requires:

- Keeping the old model until all users re-enroll, or
- Storing a model version and running compatible comparison paths, or
- Performing an explicit re-enrollment campaign.

## Resource monitoring

Alert on:

- `/api/ready` failure
- Repeated `401`, `403`, `422`, and `429`
- Face detection or embedding failures
- Lighting challenge failures
- Process memory close to its limit
- Database disk usage
- Reverse-proxy 5xx responses

## Incident checklist

- Is the service still running?
- Are authentication sessions or keys exposed?
- Is the database or key backup intact?
- Are other projects on the same host affected?
- Are logs sufficient without containing biometric data?
- Is legal/regulatory notification required?
- Has the compromised credential or key been rotated?

## Clean removal

Only remove paths known to belong to FaceSignUp. Validate the reverse-proxy
configuration before reloading it. Never delete a parent directory shared with
other projects.
