# YT2AudioBot

![CI](https://github.com/MasalovichViacheslav/YT2AudioBot/actions/workflows/ci.yml/badge.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Docker](https://img.shields.io/badge/docker-supported-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A self-hosted Telegram bot that extracts audio from YouTube videos and delivers it straight to your phone.

---

## Who Is This For

You love listening to YouTube podcasts, talks, and videos on the go — but you're tired of shady apps that require sideloading, break after every update, and don't want to pay for YouTube Premium.

Here's a free self-hosted Telegram bot that extracts audio from any YouTube video and sends it straight to your phone.

---

## Features

- Extracts audio from YouTube videos, Shorts, and live stream recordings
- Up to three quality options — Economy, Standard, High — with estimated file size shown upfront
- Files up to 50 MB are sent directly to Telegram chat; larger files are automatically uploaded to Pixeldrain and delivered as a link
- Download progress bar with the ability to cancel at any stage — quality selection, download, or before uploading to Pixeldrain
- Prefers m4a format (plays on any device); falls back to mp3, then webm (webm may not play on iOS without third-party apps)
- Audio files are tagged with title and source URL
- Access control via whitelist; invite links for temporary 24-hour access — can be enabled or disabled by the bot owner at any time

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for a detailed overview of the system design and component interactions.

---

## A Note on Performance

This bot is completely free — no subscriptions, no ads, no paywalls. To keep it that way, it runs on free tiers of third-party services, which comes with a few limitations.

> ⚠️ Limits below are accurate as of June 2026. Please verify with the respective service before deploying.

**Render free tier** ([see limits](https://render.com/docs/free#free-web-services)):
- 512 MB RAM
- 6 GB outbound traffic per month
- Container spins down after 15 minutes of inactivity (first request may take 30–60s to wake up — consider [UptimeRobot](https://uptimerobot.com) to keep it alive)

These constraints mean the bot is recommended for **2–3 whitelist users** at most.

**Telegram** ([see limits](https://core.telegram.org/bots/api#sending-files)):
- Files up to 50 MB are sent directly to chat with unlimited storage duration
- Larger files are delivered via Pixeldrain

**Pixeldrain free tier** ([see limits](https://pixeldrain.com/home#pro)):
- 10 GB total storage
- Files are deleted after 60 days

---

## Requirements

Before deploying the bot, you will need:

- **Telegram bot token** — create a bot via [@BotFather](https://t.me/BotFather)
- **Pixeldrain API key** — register at [pixeldrain.com](https://pixeldrain.com) and get your key in account settings
- **Render account** — sign up at [render.com](https://render.com)
- **Your Telegram user ID** — can be obtained via [@userinfobot](https://t.me/userinfobot)
- **YouTube cookies** *(optional)* — if YouTube starts returning errors or blocking requests from your server's IP, you can provide a cookies file exported from a browser where you are logged into YouTube. This helps bypass bot detection. See [`COOKIES_FILE`](#environment-variables) for details.

---

## Environment Variables

See [`.env.example`](.env.example) for a template.

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from [@BotFather](https://t.me/BotFather) |
| `OWNER_USER_ID` | ✅ | — | Telegram user ID of the bot owner. Has access to `/enable_invite` and `/disable_invite` commands |
| `ALLOWED_USER_IDS` | ✅ | — | JSON array of Telegram user IDs with permanent access, e.g. `[123456789, 987654321]` |
| `INVITE_TOKEN` | ✅ | — | Secret token for the invite link: `t.me/your_bot?start=TOKEN` |
| `WEBHOOK_URL` | ✅ | — | Public HTTPS URL of your Render service, e.g. `https://your-app.onrender.com` |
| `PIXELDRAIN_API_KEY` | ✅ | — | Pixeldrain API key from account settings |
| `TEMP_DIR` | ❌ | `temp` | Directory for temporary files during download |
| `MAX_FILE_SIZE_MB` | ❌ | `50` | Files above this threshold are uploaded to Pixeldrain instead of sent directly to chat |
| `PIXELDRAIN_TIMEOUT_SEC` | ❌ | `60` | Timeout in seconds for Pixeldrain upload requests |
| `PROGRESS_BAR_INTERVAL_SEC` | ❌ | `2` | How often (in seconds) the download progress message is updated |
| `COOKIES_FILE` | ❌ | — | Path to a Netscape-format cookies file exported from a browser logged into YouTube |

---

## Deployment

See [docs/deployment.md](docs/deployment.md) for step-by-step instructions on deploying to Render.

---

## Legal Disclaimer

Downloading audio from YouTube videos may violate [YouTube's Terms of Service](https://www.youtube.com/static?template=terms), and downloaded content may be protected by copyright law. In practice, personal offline use for a small circle of people carries minimal real-world risk.

That said, copyright laws vary by country — assess the risks yourself and use the bot accordingly.

---

## License

This project is licensed under the [MIT License](LICENSE).