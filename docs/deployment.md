# Overview

This guide walks you through deploying YT2AudioBot to [Render](https://render.com) — a cloud platform with a free tier that covers everything this bot needs.

No local setup required. Everything is done through a browser.

If YouTube starts returning errors or blocking requests from your server's IP, see the [Cookies](#cookies-optional) section.

---

## Prerequisites

Before you begin, create accounts on the following services if you don't have them already:

- **GitHub** — [github.com](https://github.com). You will fork the bot repository here.
- **Render** — [render.com](https://render.com). This is where the bot will run.
- **Pixeldrain** — [pixeldrain.com](https://pixeldrain.com). Used to deliver audio files larger than 50 MB.
- **UptimeRobot** — [uptimerobot.com](https://uptimerobot.com). Keeps the bot alive on Render's free tier.

That's it. No software to install.

---

## Prepare Your Credentials

Before deploying, you will need to collect several tokens and IDs. This section walks you through each one.

### Telegram Bot Token

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts — choose a name and a username for your bot.
3. BotFather will reply with a token that looks like `9876543210:AAF_your_bot_token`. Copy it.

This goes into `BOT_TOKEN`.

### Your Telegram User ID

1. Start a chat with [@userinfobot](https://t.me/userinfobot).
2. It will immediately reply with your user ID — a plain number like `123456789`.

This goes into `OWNER_USER_ID` and also into `ALLOWED_USER_IDS`.

### Allowed User IDs

Anyone you want to give permanent access to the bot needs to share their Telegram user ID with you. They can get it the same way — via [@userinfobot](https://t.me/userinfobot).

Format the list as a JSON array: `[123456789, 987654321]`.

This goes into `ALLOWED_USER_IDS`.

### Invite Token

A secret string used in invite links: `t.me/your_bot?start=TOKEN`. Pick anything — a random word, a short phrase, a UUID. Keep it private. Avoid spaces.

This goes into `INVITE_TOKEN`.

### Pixeldrain API Key

1. Log into [pixeldrain.com](https://pixeldrain.com).
2. Go to your account settings and find the API key section.
3. Copy your API key.

This goes into `PIXELDRAIN_API_KEY`.

---

## Fork the Repository

1. Open the [YT2AudioBot repository](https://github.com/MasalovichViacheslav/YT2AudioBot) on GitHub.
2. Click **Fork** in the top-right corner.
3. GitHub will create a copy of the repository under your account.

Render will deploy the bot directly from your fork.

---

## Deploy to Render

1. Log into [Render](https://render.com) and click **New → Web Service**.
2. Connect your GitHub account if you haven't already, then select your forked repository.
3. Render will detect the `Dockerfile` automatically. Leave all build settings as-is.
4. Scroll down to **Environment Variables** and add each variable from the table below. Skip `WEBHOOK_URL` for now — you don't have it yet.
5. Click **Deploy**. Render will build the Docker image and start the bot. This takes a few minutes on the first deploy.
6. Once the service is running, copy its URL from the top of the service page — it looks like `https://your-app.onrender.com`. Go back to **Environment Variables**, add `WEBHOOK_URL` with this value, and click **Save and Deploy**.

| Variable | Value |
|---|---|
| `BOT_TOKEN` | Your Telegram bot token |
| `OWNER_USER_ID` | Your Telegram user ID |
| `ALLOWED_USER_IDS` | JSON array of allowed user IDs, e.g. `[123456789]` |
| `INVITE_TOKEN` | Your invite token |
| `WEBHOOK_URL` | Add after the first deploy |
| `PIXELDRAIN_API_KEY` | Your Pixeldrain API key |

---

## Verify

1. Open your Render service URL with `/health` at the end — e.g. `https://your-app.onrender.com/health`. You should see `OK`.
2. Open Telegram and send `/start` to your bot. It should reply with a prompt to send a YouTube link.

---

## Keep-Alive with UptimeRobot

Render's free tier spins down your service after 15 minutes of inactivity. The next request after a cold start can take 30–60 seconds — long enough for Telegram to time out and never deliver the message.

UptimeRobot fixes this by pinging your service every few minutes to keep it alive.

1. Log into [UptimeRobot](https://uptimerobot.com) and click **Add New Monitor**.
2. Set monitor type to **HTTP(s)**.
3. Enter your service URL with `/health` at the end — e.g. `https://your-app.onrender.com/health`.
4. Set the monitoring interval to **5 minutes**.
5. Click **Create Monitor**.

---

## Cookies (Optional)

YouTube applies anti-bot detection measures and may block requests from well-known server IP ranges. Providing a cookies file from a browser where you are logged into YouTube helps bypass this.

**Export the cookies file:**

1. Install the **Get cookies.txt LOCALLY** extension in your browser ([Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) / [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)).
2. Open an incognito window, go to [youtube.com](https://youtube.com), and log in.
3. Click the extension icon and export cookies for the YouTube site. You will get a `cookies.txt` file.

**Add to Render:**

1. In your Render service, go to **Environment Variables** and add `COOKIES_FILE` with the value `/etc/secrets/cookies.txt`.
2. Go to **Secret Files**, create a file at `/etc/secrets/cookies.txt`, and paste the contents of your exported `cookies.txt`.
3. Click **Save and Deploy**.

**A note on cookie lifetime:**

As long as the bot keeps running, yt-dlp updates the cookies automatically — you don't need to do anything. You will only need to repeat this process if the container restarts and the original cookies you provided have expired by then, or if YouTube changes its authentication requirements.

Consider using a separate Google account for this — one you wouldn't mind losing access to if YouTube decides to block it.