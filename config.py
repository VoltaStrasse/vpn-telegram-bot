import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("VPN_BOT_TOKEN")
OPERATOR_ID = int(os.getenv("VPN_OPERATOR_ID", "0"))

NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "127.0.0.1")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8081"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # для информации

if not TOKEN:
    raise ValueError("VPN_BOT_TOKEN не задан")
if OPERATOR_ID == 0:
    raise ValueError("VPN_OPERATOR_ID не задан")
if not NOWPAYMENTS_API_KEY:
    raise ValueError("NOWPAYMENTS_API_KEY не задан")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL не задан")