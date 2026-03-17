# Expense Tracker Bot

A personal Telegram bot for logging expenses and income by month.

## Requirements

- Python 3.11+
- A Telegram bot token ([@BotFather](https://t.me/BotFather))
- Your Telegram user ID (message [@userinfobot](https://t.me/userinfobot))

---

## Environment variables

The bot reads two variables at startup:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `OWNER_ID` | Your numeric Telegram user ID — all other users are silently rejected |

`.env` is gitignored. Copy the example and fill it in:

```sh
cp .env.example .env
# then edit .env
```

---

## Running locally (venv)

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# .env is loaded automatically by python-dotenv at startup
python bot.py
```

## Running locally (micromamba / conda)

`run_local.sh` targets a conda environment named `bill-tracker-bot`. Adjust the name if yours differs.

```sh
# create once
micromamba create -n bill-tracker-bot python=3.11
micromamba run -n bill-tracker-bot pip install -r requirements.txt

# start (kills any existing instance first)
bash run_local.sh
```

`run_local.sh` does **not** source `.env` — make sure it exists in the project directory so `python-dotenv` picks it up.

---

## Deploying on a VPS (systemd)

### 1. Copy files

```sh
sudo mkdir -p /opt/expense-tracker-bot
sudo cp bot.py parser.py storage.py categories.yaml expense-tracker.service /opt/expense-tracker-bot/
```

### 2. Install dependencies

```sh
cd /opt/expense-tracker-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Update `expense-tracker.service` to use the venv:

```ini
ExecStart=/opt/expense-tracker-bot/.venv/bin/python bot.py
```

### 3. Set up the .env file

```sh
sudo cp .env.example /opt/expense-tracker-bot/.env
sudo nano /opt/expense-tracker-bot/.env   # fill in BOT_TOKEN and OWNER_ID
sudo chmod 600 /opt/expense-tracker-bot/.env
```

The service file uses `EnvironmentFile=/opt/expense-tracker-bot/.env` — systemd injects the variables directly, so `python-dotenv` also picks them up.

### 4. Install and start the service

```sh
sudo cp /opt/expense-tracker-bot/expense-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now expense-tracker
sudo systemctl status expense-tracker
```

### Managing the service

```sh
sudo systemctl restart expense-tracker   # apply code changes
sudo systemctl stop expense-tracker
sudo journalctl -u expense-tracker -f    # live logs
```

---

## Running tests

Tests require the dev dependencies:

```sh
pip install -r requirements-dev.txt
pytest
```

To run a specific test file:

```sh
pytest tests/test_parser.py
pytest tests/test_storage.py
```

Tests do not need `BOT_TOKEN` or `OWNER_ID`.

---

## Data storage

Records are written to `data/` (gitignored), relative to the working directory:

| File | Contents |
|------|----------|
| `data/YYYY-MM.txt` | Expense records for that month |
| `data/income-YYYY-MM.txt` | Income records for that month |
| `data/state.json` | Currently active month |

---

## Bot commands

Any plain text message (non-command) is parsed as an expense.

### Expense format

```
<amount> [category] [title]
```

Examples: `12.50 food coffee`, `5 TT bus`, `80`

Category is matched against `categories.yaml` (exact match first, then prefix). Defaults to `F` (food) if no match.

### Income format

```
/income <amount> [T] [YYYY-MM] [name]
```

- `T` marks the income as taxable
- `YYYY-MM` overrides the active month
- Everything else becomes the name

Example: `/income 3000 T 2026-03 Salary`

### categories.yaml

Edit to add or rename categories. Each entry needs `abbrev` (stored in records) and `keywords` (matched in messages):

```yaml
- abbrev: F
  keywords: [F, food]
```
