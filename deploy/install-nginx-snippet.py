from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


CONFIG = Path(
    os.environ.get(
        "NGINX_SITE_CONFIG",
        "/etc/nginx/sites-available/facesignup.conf",
    )
)
SNIPPET_SOURCE = Path("/tmp/facesignup-config/nginx-facesignup.conf")
SNIPPET_TARGET = Path("/etc/nginx/snippets/facesignup.conf")
INCLUDE_LINE = "    include /etc/nginx/snippets/facesignup.conf;"
MARKER = os.environ.get("NGINX_ACCESS_LOG_LINE", "")


def main() -> None:
    if not SNIPPET_SOURCE.exists():
        raise SystemExit(f"Missing snippet source: {SNIPPET_SOURCE}")

    SNIPPET_TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SNIPPET_SOURCE, SNIPPET_TARGET)
    SNIPPET_TARGET.chmod(0o644)

    original = CONFIG.read_text(encoding="utf-8")
    if INCLUDE_LINE in original:
        print("FaceSignUp Nginx include is already present.")
        return
    if not MARKER:
        raise SystemExit("NGINX_ACCESS_LOG_LINE must identify the include location.")
    if original.count(MARKER) != 1:
        raise SystemExit("Expected Nginx insertion marker was not found exactly once.")

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
    backup = CONFIG.with_name(f"{CONFIG.name}.facesignup-{timestamp}.bak")
    shutil.copy2(CONFIG, backup)

    updated = original.replace(MARKER, f"{INCLUDE_LINE}\n\n{MARKER}")
    temporary = CONFIG.with_suffix(".facesignup.tmp")
    temporary.write_text(updated, encoding="utf-8")
    shutil.copymode(CONFIG, temporary)
    temporary.replace(CONFIG)
    validation = subprocess.run(
        ["nginx", "-t"],
        check=False,
        capture_output=True,
        text=True,
    )
    if validation.returncode != 0:
        shutil.copy2(backup, CONFIG)
        raise SystemExit(
            "Nginx validation failed; configuration was restored.\n"
            f"{validation.stdout}{validation.stderr}"
        )
    print(f"Installed FaceSignUp Nginx include; backup: {backup}")


if __name__ == "__main__":
    main()
