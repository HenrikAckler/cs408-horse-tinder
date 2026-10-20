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

"${SSH[@]}" "ubuntu@${HOST}" 'mkdir -p ~/horse-tinder-upload'
rsync -az --delete \
  --exclude '.git/' --exclude '.venv/' --exclude '__pycache__/' --exclude '*.pyc' \
  --exclude 'instance/' --exclude '.env' --exclude '*.pem' \
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
