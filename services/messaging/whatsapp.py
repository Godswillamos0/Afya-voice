import os
import httpx
from typing import Optional

class WhatsAppMessenger:
    """
    Outbound messaging client using Meta's WhatsApp Cloud API (Graph API v25.0).
    Sends direct clinical triage messages, advice, and alerts back to patients.
    """

    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN", "")
        self.phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "1335118959691412")
        self.api_version = os.getenv("META_API_VERSION", "v25.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    async def send_text_message(self, to_phone: str, message_text: str) -> bool:
        """
        Sends a freeform text message to the patient within the 24-hour service window.
        """
        if not self.access_token:
            print("[MESSENGER ERROR] META_ACCESS_TOKEN is missing in .env")
            return False

        # Clean recipient phone number (strip '+' or leading spaces)
        clean_phone = to_phone.strip().replace("+", "")

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        print(f"[MESSENGER] Dispatching WhatsApp message to {clean_phone}...")

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(self.base_url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    resp_data = response.json()
                    message_id = resp_data.get("messages", [{}])[0].get("id", "UNKNOWN")
                    print(f"[MESSENGER SUCCESS] WhatsApp message delivered to Meta! (ID: {message_id})")
                    return True
                else:
                    print(f"[MESSENGER ERROR] Failed to send WhatsApp message ({response.status_code}): {response.text}")
                    return False
            except Exception as e:
                print(f"[MESSENGER ERROR] Exception while sending WhatsApp message: {str(e)}")
                return False
