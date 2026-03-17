#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
pkill -f "python bot.py" || true
exec micromamba run -n bill-tracker-bot python bot.py
