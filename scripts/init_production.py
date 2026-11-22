from __future__ import annotations

import argparse
import re
from pathlib import Path

from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_PATTERN = re.compile(r"^[A-Za-z0-9.-]+$")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / ".env")
    args = parser.parse_args()

    domain = args.domain.strip().lower()
    if not DOMAIN_PATTERN.fullmatch(domain):
        raise SystemExit("Use a hostname such as faces.example.com, without a scheme.")
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {args.output}")

    key = Fernet.generate_key().decode("ascii")
    content = "\n".join(
        [
            f"DOMAIN={domain}",
            "FACESIGNUP_ENV=production",
            f"FACESIGNUP_ALLOWED_HOSTS={domain}",
            f"FACESIGNUP_ALLOWED_ORIGINS=https://{domain}",
            "FACESIGNUP_COOKIE_SECURE=true",
            "FACESIGNUP_ALLOW_MOVEMENT_FALLBACK=false",
            "FACESIGNUP_MAX_FRAME_BYTES=2097152",
            "FACESIGNUP_MAX_REQUEST_BYTES=524288",
            f"FACESIGNUP_EMBEDDING_KEY={key}",
            "",
        ]
    )
    args.output.write_text(content, encoding="utf-8")
    try:
        args.output.chmod(0o600)
    except OSError:
        pass
    print(
        f"Created {args.output}. Store this file in a secret manager and never commit it."
    )


if __name__ == "__main__":
    main()
