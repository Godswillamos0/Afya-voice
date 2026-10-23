import os
from fastapi import APIRouter, Request, BackgroundTasks
from services.messaging.telegram import TelegramService

router = APIRouter()
telegram_service = TelegramService()

@router.post("")
async def handle_telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Webhook receiver for incoming Telegram updates (voice notes, text messages, button clicks).
    """
    try:
        update_data = await request.json()
        # Process asynchronously in the background so Telegram receives instant 200 OK
        background_tasks.add_task(telegram_service.process_update, update_data)
        return {"status": "ok"}
    except Exception as e:
        print(f"[Telegram Webhook Error] {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/info")
def telegram_info():
    """Returns status of Telegram Bot integration."""
    has_token = bool(os.getenv("TELEGRAM_BOT_TOKEN", ""))
    return {
        "service": "AfyaMama Telegram Bot",
        "status": "configured" if has_token else "missing_token",
        "instructions": "Set TELEGRAM_BOT_TOKEN in .env or run python telegram_runner.py for local polling."
    }
