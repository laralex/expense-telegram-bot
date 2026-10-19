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

## Running locally (uv)

Use `uv` for environment management and running the bot.

```sh
# Create and sync environment
uv sync

# Start the bot
bash run_local.sh
```

`run_local.sh` does **not** source `.env` — make sure it exists in the project directory so `python-dotenv` picks it up.

---

## Deploying on a VPS (systemd)

### 1. Copy files

```sh
sudo mkdir -p /opt/expense-telegram-bot
sudo cp bot.py parser.py storage.py categories.yaml expense-tracker.service /opt/expense-telegram-bot/
```

### 2. Install dependencies

```sh
cd /opt/expense-telegram-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Update `expense-tracker.service` to use the venv:

```ini
ExecStart=/opt/expense-telegram-bot/.venv/bin/python bot.py
```

### 3. Set up the .env file

```sh
sudo cp .env.example /opt/expense-telegram-bot/.env
sudo nano /opt/expense-telegram-bot/.env   # fill in BOT_TOKEN and OWNER_ID
sudo chmod 600 /opt/expense-telegram-bot/.env
```

The service file uses `EnvironmentFile=/opt/expense-telegram-bot/.env` — systemd injects the variables directly, so `python-dotenv` also picks them up.

### 4. Install and enable systemd service

```sh
sudo cp /opt/expense-telegram-bot/expense-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now expense-tracker
sudo systemctl status expense-tracker
```

### Managing the service

```sh
sudo systemctl restart expense-tracker   # apply code changes
sudo systemctl stop expense-tracker
sudo journalctl -u expense-tracker -f     # live logs
```

---

## Running tests

Run tests using `uv`:

```sh
uv run pytest
```

To run a specific test file:

```sh
uv run pytest tests/test_parser.py
uv run pytest tests/test_storage.py
```

Tests do not need `BOT_TOKEN` or `OWNER_ID`.

---

## Data storage

Records are stored in a single SQLite database file `data/storage.db` (gitignored).

The database contains five tables: `state`, `expenses`, `incomes`, `balances`, and `name_registry`.

### Migrating from legacy file-based storage

If you have an existing `data/` folder (with legacy files like `state.json`, `outcome-*.txt`, `income-*.txt`, `balances.json`), convert it to SQLite:

```sh
python migrate_backup.py data/
```

This reads all legacy files from the given directory and writes an SQLite database (`data/storage.db`). The resulting database can be placed in `data/` of a new deployment and will be automatically used by the bot.

The bot does not auto-import legacy files on startup — run this script first, then place the generated `storage.db` in the `data/` folder of the deployment.

---

## Bot commands

Any plain text message (non-command) is parsed as an expense.

### Expense format

```
<amount> [category] [title]
```

Examples: `12.50 food coffee`, `5 TT bus`, `80`

Category is matched against `categories.yaml` (exact match first, then prefix).

- `80` — amount only, no title → default category `F` (food).
- `50 F test` — explicit category → `F`, title `test`.
- `50 test F` — the category may sit anywhere among the words → `F`, title `test`.
- `50 test` — **rejected**. A title without a category is ambiguous, so the default category is never inferred. The bot replies with a hint that lists the known categories.

### Income format

```
/income <amount> [T] [YYYY-MM] [name]
```

- `T` marks the income as taxable
- `YYYY-MM` overrides the active month
- Everything else becomes the name

Example: `/income 3000 T 2026-03 Salary`

The name is checked against `categories.yaml`. A name that matches **two or more
different categories** is ambiguous, so the entry is rejected with an error
naming the conflicting categories:

- `/in 3000 Salary` — accepted
- `/in 3000 Rent` — accepted (`rent` matches a single category, `r`)
- `/in 3000 Rent Food` — **rejected**: `rent` → `r` and `food` → `F` conflict

### categories.yaml

Edit to add or rename categories. Each entry needs `abbrev` (stored in records) and `keywords` (matched in messages):

```yaml
- abbrev: F
  keywords: [F, food]
```