# Troubleshooting

## Camera does not start

- Use HTTPS or localhost.
- Grant camera permission in the browser and operating system.
- Close applications that hold exclusive camera access.
- Confirm `navigator.mediaDevices.getUserMedia` exists.
- Check browser console for MediaPipe or WebSocket errors.

## "Starting the camera" lasts too long

- Confirm MediaPipe WASM and `face_landmarker.task` are present.
- Run `npm run localize:mediapipe`.
- Check that the reverse proxy supports WebSocket upgrades.
- Confirm the frontend and API use the same hostname.

## Screen-light check fails

- Disable movement-only fallback in production.
- Remove other bright lights and glare.
- Turn screen brightness up.
- Keep the entire face in view.
- Test with a case that does not block the front camera.
- Try a different browser/device if the camera applies strong white balance or
  exposure compensation.

## Registration says the enrollment expired

Possibilities:

- More than 15 minutes passed after the face scan.
- The page was reloaded, losing the in-memory ticket.
- The backend restarted.
- The request client address changed.
- The ticket was already consumed.

Rescan and submit the form within the enrollment window.

## Old action name or old UI appears

The HTML and API responses are `no-store`, but an already running browser bundle
does not update itself. Close/reopen the scanner or hard-refresh.

Deployments should remove obsolete hashed assets after copying a new build.

## "Keep only one face in the frame"

- Ensure only one person is visible.
- Remove posters or reflected faces.
- Improve lighting.
- Keep the camera stable.

## Face is not detected

- Move closer.
- Center the face.
- Remove heavy backlight.
- Avoid covering the face.
- Confirm the face-control overlay is visible.

## Password recovery question is missing

- Confirm the exact account name.
- Check whether the account was created before custom questions were required.
- Older accounts with two questions use the first question.
- Rate limits may temporarily block repeated lookups.

## Administrator cannot access user management

- Confirm the account role is `admin`.
- Confirm the bootstrap password was changed.
- Sign in again because password changes invalidate existing sessions.
- Check that the browser cookie is allowed and the site is using the expected
  hostname.

## Production readiness fails

Run the script with production environment variables loaded:

```bash
set -a
. ./.env
set +a
python scripts/check_production.py
```

Common failures:

- Development environment selected
- HTTP origin or insecure cookie
- Movement-only fallback enabled
- Invalid/missing Fernet key
- Default administrator password
- Missing or modified model
- Missing consent metadata

## Database is locked

- Keep writes short.
- Do not run multiple application processes against one SQLite file.
- Check for long-running external queries.
- Inspect free disk space and WAL files.

## Nginx returns 502

- Check `systemctl status facesignup`.
- Check the configured backend port.
- Inspect application error logs.
- Validate Nginx with `nginx -t`.
- Confirm the service is bound to `127.0.0.1`, not a public interface.

## Translation key appears literally

- Run `npm run check:locales`.
- Rebuild the frontend.
- Remove stale hashed assets.
- Hard-refresh the browser.
- Confirm the action or message key exists in every locale.
