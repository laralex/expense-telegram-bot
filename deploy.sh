#!/usr/bin/env bash
# deploy.sh — Deploy expense-tracker-bot to a VPS
# Assumes: repo already cloned, script run from repo root
# Usage: bash deploy.sh

set -euo pipefail

DEPLOY_DIR="/opt/expense-tracker-bot"
SERVICE_NAME="expense-tracker"
SERVICE_FILE="receipt-tracker.service"
VENV="$DEPLOY_DIR/.venv"

FILES=(bot.py cbr.py parser.py storage.py categories.yaml requirements.txt "$SERVICE_FILE")

echo "==> Pulling latest from main"
git pull origin main

echo "==> Stopping existing service (if running)"
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || true

echo "==> Creating $DEPLOY_DIR"
sudo mkdir -p "$DEPLOY_DIR"

echo "==> Copying files"
for f in "${FILES[@]}"; do
    sudo cp -f "$f" "$DEPLOY_DIR/"
done

echo "==> Creating virtual environment"
sudo python3 -m venv "$VENV"

echo "==> Installing dependencies"
sudo "$VENV/bin/pip" install --quiet -r "$DEPLOY_DIR/requirements.txt"

echo "==> Verifying installed packages satisfy requirements"
sudo "$VENV/bin/pip" check

echo "==> Updating service ExecStart to use venv python"
sudo sed -i "s|^ExecStart=.*|ExecStart=$VENV/bin/python bot.py|" "$DEPLOY_DIR/$SERVICE_FILE"

if [ ! -f "$DEPLOY_DIR/.env" ]; then
    echo "==> Creating .env from example (fill in BOT_TOKEN and OWNER_ID)"
    sudo cp .env.example "$DEPLOY_DIR/.env"
    sudo chmod 600 "$DEPLOY_DIR/.env"
    echo ""
    echo "  !! Edit $DEPLOY_DIR/.env before starting the service:"
    echo "       sudo nano $DEPLOY_DIR/.env"
    echo ""
    read -r -p "Press Enter once .env is ready, or Ctrl-C to abort..."
else
    echo "==> .env already exists — skipping"
fi

echo "==> Installing and enabling systemd service"
sudo cp -f "$DEPLOY_DIR/$SERVICE_FILE" "/etc/systemd/system/$SERVICE_NAME.service"
sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"

echo ""
echo "==> Status"
sudo systemctl status "$SERVICE_NAME" --no-pager
echo ""
echo "Done. Useful commands:"
echo "  sudo systemctl restart $SERVICE_NAME    # after code updates"
echo "  sudo journalctl -u $SERVICE_NAME -f     # live logs"
