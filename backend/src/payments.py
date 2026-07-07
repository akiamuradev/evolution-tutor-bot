import os
from yookassa import Configuration, Payment
from datetime import datetime

Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")

PRICES = {"student": "290.00", "business": "990.00", "standard": "490.00"}

async def create_link(tg_id: int, mode: str) -> str:
    p = Payment.create({
        "amount": {"value": PRICES.get(mode, "490.00"), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": f"https://t.me/{os.getenv('BOT_USERNAME')}"},
        "capture": True,
        "description": f"Подписка {mode} 30 дней (tg: {tg_id})",
        "metadata": {"tg_id": str(tg_id), "mode": mode}
    }, f"idem-{tg_id}-{mode}")
    return p.confirmation.confirmation_url

def handle_webhook(data: dict) -> dict:
    if data.get("event") == "payment.succeeded":
        obj = data.get("object", {})
        meta = obj.get("metadata", {})
        return {"tg_id": int(meta.get("tg_id", 0)), "mode": meta.get("mode", "standard"), "status": "ok"}
    return {"status": "ignored"}