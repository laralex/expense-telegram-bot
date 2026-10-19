#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

# Ensure uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed."
    echo "Please install uv first: https://github.com/astral-sh/uv"
    exit 1
fi

# Ensure the required Python version is installed via uv
echo "==> Ensuring required Python version is installed via uv..."
uv python install

# Ensure dependencies are synced and environment is up to date
echo "==> Syncing dependencies with uv..."
uv sync

# Kill any existing instance
pkill -f "python bot.py" || true

# Start the bot
echo "==> Bot starting..."
exec uv run python bot.py
