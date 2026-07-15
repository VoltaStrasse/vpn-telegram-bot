import asyncio
import time
import logging
from aiohttp import web, ClientSession, ClientTimeout
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)

class NowPayments:
    def __init__(self, api_key: str, webhook_path: str = "/webhook"):
        self.api_key = api_key
        self.webhook_path = webhook_path
        self._on_payment_completed: Optional[Callable[[int, float, str], None]] = None
        self._transactions: Dict[str, Dict] = {}

    def set_on_payment_callback(self, callback: Callable[[int, float, str], None]):
        self._on_payment_completed = callback

    async def create_invoice(self, user_id: int, amount: float = 5.0, currency: str = "usd",
                             order_description: Optional[str] = None) -> Optional[str]:
        url = "https://api.nowpayments.io/v1/invoice"
        headers = {"x-api-key": self.api_key}
        order_id = f"user_{user_id}_{int(time.time())}"
        payload = {
            "price_amount": amount,
            "price_currency": currency.lower(),
            "order_id": order_id,
            "order_description": order_description or f"VPN key for user {user_id}",
        }
        async with ClientSession(timeout=ClientTimeout(total=30)) as session:
            try:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status in (200, 201):
                        data = await resp.json()
                        invoice_id = data.get("id")
                        invoice_url = data.get("invoice_url")
                        self._transactions[invoice_id] = {
                            "user_id": user_id,
                            "amount": amount,
                            "status": "pending",
                            "created_at": int(time.time())
                        }
                        return invoice_url
                    else:
                        error_text = await resp.text()
                        logger.error(f"NowPayments error: {resp.status} {error_text}")
            except Exception as e:
                logger.exception("NowPayments request failed")
        return None

    async def _webhook_handler(self, request):
        # Проверка IP-адреса NowPayments (список актуальных IP — см. документацию)
        # Здесь можно добавить проверку request.remote, если хотите.
        try:
            data = await request.json()
            logger.info(f"Webhook received: {data}")
            # Проверяем статус
            if data.get("status") == "completed":
                invoice_id = data.get("order_id")
                if invoice_id in self._transactions:
                    tx = self._transactions[invoice_id]
                    if tx["status"] == "pending":
                        tx["status"] = "completed"
                        if self._on_payment_completed:
                            self._on_payment_completed(
                                user_id=tx["user_id"],
                                amount=tx["amount"],
                                invoice_id=invoice_id
                            )
                        logger.info(f"Payment completed: user {tx['user_id']}, amount {tx['amount']}")
                else:
                    logger.warning(f"Unknown invoice_id: {invoice_id}")
        except Exception as e:
            logger.exception("Webhook processing error")
        return web.json_response({"ok": True})

    async def start_webhook_server(self, host: str = "127.0.0.1", port: int = 8081):
        app = web.Application()
        app.router.add_post(self.webhook_path, self._webhook_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info(f"Webhook server running on {host}:{port}{self.webhook_path}")
        return runner