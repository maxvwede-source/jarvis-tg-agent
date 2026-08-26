# JARVIS Telegram Agent

AI agent on Telegram powered by DeepSeek-V4-Flash via Dahl Inference.
Runs entirely on **GitHub Actions** — no server, no webhook, no hosting cost.

## How it works
- GitHub cron triggers `bot.py` every 2 minutes
- Bot long-polls Telegram for new messages
- Messages are answered with JARVIS persona + short conversation memory
- Memory + update offset persist via git (`state.json`)

## Setup (done)
1. Secrets: `TG_BOT_TOKEN`, `DAHL_KEY` (repo secrets)
2. Workflow: `.github/workflows/agent.yml`
3. Talk to [@IqijBot](https://t.me/IqijBot)

## Manual trigger
Actions tab → JARVIS Telegram Agent → Run workflow
