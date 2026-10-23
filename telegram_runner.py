import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

from services.messaging.telegram import TelegramService

async def run_telegram_polling():
    """
    Runs the AfyaMama Telegram Bot via Long Polling.
    This works locally with zero webhook setup, zero public URLs, and zero tunnels!
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "your_telegram_bot_token_here":
        print("=" * 60)
        print("[!] TELEGRAM_BOT_TOKEN IS MISSING OR NOT SET!")
        print("=" * 60)
        print("To connect your Telegram Bot:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot and follow instructions to name your bot")
        print("3. Copy the HTTP API token")
        print("4. Add it to your .env file:")
        print('   TELEGRAM_BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"')
        print("5. Run this runner script again: python telegram_runner.py")
        print("=" * 60)
        return

    print("=" * 60)
    print("[+] Starting AfyaMama Maternal Health Telegram Bot (Long Polling Mode)...")
    print("Zero tunnel required! Listening for live voice notes & text symptoms...")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    service = TelegramService(token=token)
    offset = 0

    # Delete any webhook to allow polling
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(f"{service.base_url}/deleteWebhook")

    while True:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.get(f"{service.base_url}/getUpdates?offset={offset}&timeout=20")
                if res.status_code == 200:
                    data = res.json()
                    updates = data.get("result", [])
                    for update in updates:
                        update_id = update["update_id"]
                        offset = update_id + 1
                        # Process update
                        await service.process_update(update)
                elif res.status_code == 401:
                    print("❌ Invalid TELEGRAM_BOT_TOKEN. Please verify your token from @BotFather.")
                    await asyncio.sleep(10)
        except asyncio.CancelledError:
            print("\nShutting down Telegram Bot...")
            break
        except Exception as e:
            print(f"[Polling Error] {str(e)}")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(run_telegram_polling())
    except KeyboardInterrupt:
        print("\nAfyaMama Telegram Bot stopped.")
