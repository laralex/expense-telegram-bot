#!/usr/bin/env bash
# backup.sh — Back up runtime data from the deployed expense-tracker-bot
# Copies data/ (SQLite database) and .env from the deploy directory into a
# timestamped zip archive under ./backup/. Prints the full path on stdout.
#
# Usage: bash backup.sh

set -euo pipefail

DEPLOY_DIR="/opt/expense-tracker-bot"
BACKUP_ROOT="./backup"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TMPDIR="$(mktemp -d)"
STAGE="$TMPDIR/expense-tracker-backup-$TIMESTAMP"

trap 'rm -rf "$TMPDIR"' EXIT

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Error: deploy directory $DEPLOY_DIR does not exist" >&2
    exit 1
fi

mkdir -p "$STAGE"

# data/ — SQLite database (storage.db), all transaction data, balances, state
if [ -d "$DEPLOY_DIR/data" ]; then
    cp -r "$DEPLOY_DIR/data" "$STAGE/data"
    echo "Copied data/" >&2
else
    echo "Warning: $DEPLOY_DIR/data not found, skipping" >&2
fi

# .env — bot token and owner ID
if [ -f "$DEPLOY_DIR/.env" ]; then
    cp "$DEPLOY_DIR/.env" "$STAGE/.env"
    echo "Copied .env" >&2
else
    echo "Warning: $DEPLOY_DIR/.env not found, skipping" >&2
fi

mkdir -p "$BACKUP_ROOT"
ZIP_FILE="$(cd "$BACKUP_ROOT" && pwd)/backup-$TIMESTAMP.zip"

(cd "$TMPDIR" && zip -qr "$ZIP_FILE" "$(basename "$STAGE")")

echo "$ZIP_FILE"
