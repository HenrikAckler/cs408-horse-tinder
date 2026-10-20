#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 -h <EC2 public IP or hostname> -i <SSH private key>"
}

HOST=""
IDENTITY=""
while getopts ":h:i:" option; do
  case "$option" in
    h) HOST="$OPTARG" ;;
    i) IDENTITY="$OPTARG" ;;
    *) usage >&2; exit 2 ;;
  esac
done

if [[ -z "$HOST" || -z "$IDENTITY" ]]; then
  usage >&2
  exit 2
fi
if [[ ! -f "$IDENTITY" ]]; then
  echo "SSH key not found: $IDENTITY" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH=(ssh -i "$IDENTITY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new)
RSYNC_RSH="ssh -i '$IDENTITY' -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

"${SSH[@]}" "ubuntu@${HOST}" 'mkdir -p ~/horse-tinder-bootstrap'
scp -i "$IDENTITY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
  -r "$ROOT_DIR/deploy" "ubuntu@${HOST}:horse-tinder-bootstrap/"

# Bootstrap a fresh instance automatically. On an existing server, refresh the
# service unit without repeating the OS package installation.
"${SSH[@]}" "ubuntu@${HOST}" 'set -euo pipefail
if ! command -v nginx >/dev/null 2>&1 \
  || ! command -v rsync >/dev/null 2>&1 \
  || [[ ! -s /etc/horse-tinder.env ]] \
  || [[ ! -f /etc/systemd/system/horse-tinder.service ]] \
  || [[ ! -e /etc/nginx/sites-enabled/horse-tinder ]]; then
  sudo bash ~/horse-tinder-bootstrap/deploy/setup-ec2.sh
fi
sudo install -m 0644 ~/horse-tinder-bootstrap/deploy/horse-tinder.service /etc/systemd/system/horse-tinder.service
sudo systemctl daemon-reload'

"${SSH[@]}" "ubuntu@${HOST}" 'mkdir -p ~/horse-tinder-upload'
rsync -az --delete \
  --exclude '.git/' --exclude '.venv/' --exclude '__pycache__/' --exclude '*.pyc' \
  --exclude 'instance/' --exclude '.env*' --exclude '.flaskenv' --exclude '.netrc' \
  --exclude '.npmrc' --exclude '.pypirc' --exclude '.aws/' --exclude '.ssh/' \
  --exclude 'credentials' --exclude 'credentials.*' --exclude 'secrets/' \
  --exclude '*.pem' --exclude '*.key' --exclude '*.p12' --exclude '*.pfx' \
  --exclude '*.ppk' --exclude '*.jks' --exclude '*.keystore' \
  -e "$RSYNC_RSH" "$ROOT_DIR/" "ubuntu@${HOST}:horse-tinder-upload/"

"${SSH[@]}" "ubuntu@${HOST}" 'sudo rsync -a --delete --exclude instance/ --exclude .venv/ ~/horse-tinder-upload/ /opt/horse-tinder/ && sudo chown -R ubuntu:ubuntu /opt/horse-tinder && cd /opt/horse-tinder && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && set -a && . /etc/horse-tinder.env && set +a && .venv/bin/python -c "from app import initialize_database; initialize_database()" && sudo systemctl restart horse-tinder.service'

echo "Checking deployed app at http://${HOST}/api/health ..."
for attempt in {1..12}; do
  if curl --fail --silent "http://${HOST}/api/health" >/dev/null; then
    echo "Deployment succeeded: http://${HOST}/"
    exit 0
  fi
  sleep 5
done
echo "Deployment did not become healthy. Check: ssh -i '$IDENTITY' ubuntu@${HOST} 'sudo systemctl status horse-tinder'" >&2
exit 1
