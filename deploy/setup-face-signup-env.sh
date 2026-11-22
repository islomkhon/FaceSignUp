#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/var/www/facesignup"
ENV_FILE="${ROOT_DIR}/.env"
DOMAIN="${DOMAIN:-}"

if [[ -z "${DOMAIN}" ]]; then
  echo "DOMAIN must be set, for example: DOMAIN=faces.example.com $0"
  exit 2
fi

if [[ -e "${ENV_FILE}" ]]; then
  echo "Refusing to overwrite existing ${ENV_FILE}"
  exit 40
fi

install -d -m 0700 -o facesignup -g facesignup "${ROOT_DIR}/data"
install -d -m 0750 -o facesignup -g facesignup /var/log/facesignup

embedding_key="$(openssl rand -base64 32 | tr '+/' '-_' | tr -d '\n')"
umask 077
cat > "${ENV_FILE}.tmp" <<EOF
FACESIGNUP_ENV=production
FACESIGNUP_ALLOWED_HOSTS=${DOMAIN}
FACESIGNUP_ALLOWED_ORIGINS=https://${DOMAIN}
FACESIGNUP_COOKIE_SECURE=true
FACESIGNUP_ALLOW_MOVEMENT_FALLBACK=false
FACESIGNUP_MAX_FRAME_BYTES=2097152
FACESIGNUP_MAX_REQUEST_BYTES=524288
FACESIGNUP_DB=/var/www/facesignup/data/facesignup.db
FACESIGNUP_EMBEDDING_KEY=${embedding_key}
EOF
mv "${ENV_FILE}.tmp" "${ENV_FILE}"
chown root:facesignup "${ENV_FILE}"
chmod 0640 "${ENV_FILE}"
echo "Created ${ENV_FILE}"
