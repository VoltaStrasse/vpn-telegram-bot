# VaultTech VPN Bot

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-beta-yellow)
![Telegram](https://img.shields.io/badge/telegram-bot-blue?logo=telegram)
![NowPayments](https://img.shields.io/badge/payments-NowPayments-blueviolet)
![aiohttp](https://img.shields.io/badge/aiohttp-3.9%2B-blue)

A fully automated Telegram bot for selling Outline VPN keys with **cryptocurrency payments** via NowPayments.  
After successful payment, the user receives a VPN key instantly — no manual intervention required.

## Features
- 📘 **Step‑by‑step instructions** for Android, iOS, Windows, macOS.
- 📊 **Multiple tariff plans** (from 100 GB to 1200 GB).
- 💳 **Crypto payments** (NowPayments) – automatic invoice creation and webhook confirmation.
- 🔑 **Automatic key issuance** from a SQLite database (FIFO/random selection).
- 📩 **Operator notifications** for every purchase (optional).
- 🚀 **Fully automated flow** – user gets the key right after payment.

## Screenshots

| Welcome Menu                        | Instruction                             | Payment | Tariffs                         |
|-------------------------------------|-----------------------------------------|---------|---------------------------------|
| ![welcome](screenshots/welcome.jpg) | ![instruction](screenshots/Instruction.jpg) | ![payment](screenshots/payment.jpg) | ![tariffs](screenshots/Tariffs.jpg) |

## Technologies
- Python 3.10+
- aiogram 3.x
- aiohttp (webhook server)
- NowPayments API
- SQLite (key storage)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/VoltaStrasse/vpn-telegram-bot.git
   cd vpn-telegram-bot
Create a virtual environment:

bash
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
Install dependencies:

bash
pip install -r requirements.txt
Create .env file from .env.example and fill in:

VPN_BOT_TOKEN – your bot token from @BotFather.

VPN_OPERATOR_ID – your Telegram user ID (for notifications).

NOWPAYMENTS_API_KEY – your NowPayments API key.

WEBHOOK_URL – the public URL where NowPayments will send webhooks (e.g., https://your-domain:8443/webhook).

Set up nginx reverse proxy (if you use the default webhook binding on 127.0.0.1:8081):

Copy nginx.conf.example to /etc/nginx/sites-available/vpnbot and adjust domain and SSL paths.

Enable the site: sudo ln -s /etc/nginx/sites-available/vpnbot /etc/nginx/sites-enabled/

Test nginx config: sudo nginx -t

Reload nginx: sudo systemctl reload nginx

Make sure your firewall allows port 8443.

Run the bot:

bash
python bot.py
Configuration
VPN_BOT_TOKEN – Telegram bot token.

VPN_OPERATOR_ID – Telegram user ID for notifications.

NOWPAYMENTS_API_KEY – NowPayments API key.

WEBHOOK_HOST / WEBHOOK_PORT – internal webhook server binding (default 127.0.0.1:8081).

WEBHOOK_URL – external URL for NowPayments webhooks.

Demo
Test the bot live: @VaultTechVPNbot

License
MIT © 2026 Valentin Voltecc

Contact
Email: volttecc@gmail.com

Telegram: @volttecc

GitHub: VoltaStrasse

Actual bot: https://t.me/VaultTechVPNbot