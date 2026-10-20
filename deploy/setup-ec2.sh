#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this setup script with sudo: sudo bash deploy/setup-ec2.sh" >&2
  exit 1
fi

APP_NAME="horse-tinder"
APP_DIR="/opt/${APP_NAME}"
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_USER="${SUDO_USER:-ubuntu}"

if ! id "$APP_USER" >/dev/null 2>&1; then
  echo "Application user '$APP_USER' does not exist." >&2
  exit 1
fi

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip nginx rsync
install -d -o "$APP_USER" -g "$APP_USER" "$APP_DIR" "$APP_DIR/instance"
install -m 0644 "$DEPLOY_DIR/horse-tinder.service" /etc/systemd/system/horse-tinder.service

# Keep a stable signing secret across restarts and repeated setup runs.
if [[ ! -s /etc/horse-tinder.env ]]; then
  python3 -c 'import secrets; from pathlib import Path; Path("/etc/horse-tinder.env").write_text("SECRET_KEY=" + secrets.token_urlsafe(48) + "\n")'
fi
chown root:"$APP_USER" /etc/horse-tinder.env
chmod 0640 /etc/horse-tinder.env

cat > /etc/nginx/sites-available/horse-tinder <<'NGINX'
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

rm -f /etc/nginx/sites-enabled/default
ln -sfn /etc/nginx/sites-available/horse-tinder /etc/nginx/sites-enabled/horse-tinder
systemctl daemon-reload
systemctl enable nginx horse-tinder.service
systemctl restart nginx

echo "EC2 setup complete. Deploy the app from your laptop with deploy/deploy.sh."
