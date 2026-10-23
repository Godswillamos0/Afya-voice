import os
import uuid
import httpx
from typing import Optional, Dict, Any, List
from services.transcription.asr import NAtlasASRClient
from services.llm.clinical_parser import NAtlasLLMClient
from services.triage.engine import TriageEngine
from services.database.session_manager import DatabaseSessionManager

TEMP_DIR = os.path.join(os.getcwd(), "storage", "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

class TelegramService:
    """
    Manages Telegram Bot interactions for AfyaMama / AfyaVoice Maternal Care.
    Handles voice notes, text symptoms, inline keyboards, and clinical RAG dispatch.
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""
        self.asr_client = NAtlasASRClient()
        self.llm_client = NAtlasLLMClient()
        self.triage_engine = TriageEngine()
        self.db_manager = DatabaseSessionManager()

        # Temporary in-memory state tracking user selected trimester/stage
        self.user_stages: Dict[int, str] = {}

    def get_main_keyboard(self) -> Dict[str, Any]:
        """Returns interactive inline buttons for pregnancy stage and quick actions."""
        return {
            "inline_keyboard": [
                [
                    {"text": "👶 1st Trimester", "callback_data": "stage_1st"},
                    {"text": "🤰 2nd Trimester", "callback_data": "stage_2nd"},
                    {"text": "🤱 3rd Trimester", "callback_data": "stage_3rd"}
                ],
                [
                    {"text": "🍼 Postnatal / New Mom", "callback_data": "stage_postnatal"},
                    {"text": "🚨 Emergency 112", "callback_data": "action_emergency"}
                ],
                [
                    {"text": "🏥 Antenatal (ANC) Guidelines", "callback_data": "action_anc_info"},
                    {"text": "🌿 Morning Sickness Relief", "callback_data": "action_nausea_relief"}
                ]
            ]
        }

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """Sends a message to a Telegram user."""
        if not self.token:
            print("[Telegram Warning] TELEGRAM_BOT_TOKEN is not configured in .env!")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                return res.status_code == 200
        except Exception as e:
            print(f"[Telegram Error] Could not send message: {str(e)}")
            return False

    async def download_file(self, file_id: str, dest_path: str) -> bool:
        """Downloads voice note or audio file from Telegram servers."""
        if not self.token:
            return False

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # 1. Get file path from Telegram
                info_res = await client.get(f"{self.base_url}/getFile?file_id={file_id}")
                if info_res.status_code != 200:
                    return False
                file_path = info_res.json()["result"]["file_path"]

                # 2. Download the file content
                download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
                file_res = await client.get(download_url)
                if file_res.status_code == 200:
                    with open(dest_path, "wb") as f:
                        f.write(file_res.content)
                    return True
        except Exception as e:
            print(f"[Telegram Error] Failed to download audio file: {str(e)}")
        return False

    async def process_update(self, update: Dict[str, Any]):
        """Processes an incoming Telegram webhook update or polling item."""
        # 1. Handle Inline Button Clicks (Callback Queries)
        if "callback_query" in update:
            cb = update["callback_query"]
            chat_id = cb["message"]["chat"]["id"]
            data = cb.get("data", "")
            
            if data == "stage_1st":
                self.user_stages[chat_id] = "1st Trimester (0–12 weeks)"
                msg = "✅ *Stage Recorded: 1st Trimester*\nPlease hold the mic button 🎙️ and describe your symptoms, or type them below in Yoruba, Hausa, Igbo, Pidgin, or English."
            elif data == "stage_2nd":
                self.user_stages[chat_id] = "2nd Trimester (13–27 weeks)"
                msg = "✅ *Stage Recorded: 2nd Trimester*\nHave you started your IPTp-SP malaria prevention dose? Please record or type how you are feeling."
            elif data == "stage_3rd":
                self.user_stages[chat_id] = "3rd Trimester (28–40 weeks)"
                msg = "✅ *Stage Recorded: 3rd Trimester*\nTell us how you are feeling or if your baby is moving well. Record or type your symptoms now."
            elif data == "stage_postnatal":
                self.user_stages[chat_id] = "Postnatal / New Mother"
                msg = "✅ *Stage Recorded: Postnatal / New Mom*\nCongratulations on your baby! Please share any symptoms (bleeding, fever, breastfeeding issues) by voice note or text."
            elif data == "action_emergency":
                msg = "🚨 *EMERGENCY ASSISTANCE:*\nCall Nigeria National Emergency on *112* immediately!\nIf you have heavy bleeding, convulsion, or severe headache with blurred vision, go to the nearest General Hospital Emergency Unit without delay."
            elif data == "action_anc_info":
                msg = "📚 *WHO Recommended 8-Contact ANC Schedule:*\n• Contact 1: Up to 12 weeks\n• Contact 2: 20 weeks\n• Contact 3: 26 weeks\n• Contact 4: 30 weeks\n• Contact 5: 34 weeks\n• Contact 6: 36 weeks\n• Contact 7: 38 weeks\n• Contact 8: 40 weeks\nRemember your daily Iron (60mg) + Folic Acid (400µg)!"
            elif data == "action_nausea_relief":
                msg = "🌿 *WHO Evidence-Based Relief for Morning Sickness:*\n• Eat small, frequent meals (boiled yam, dry crackers) every 2–3 hours.\n• Sip fresh ginger tea or take ginger root.\n• Drink fluids between meals rather than with food.\n• Avoid greasy, deep-fried, or heavily spiced foods."
            else:
                msg = "Please send a voice note or message describing your symptoms."

            await self.send_message(chat_id, msg, reply_markup=self.get_main_keyboard())
            return

        # 2. Handle Text or Voice Messages
        if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            user_name = msg["from"].get("first_name", "Mama")

            # Check for /start or /help command
            text = msg.get("text", "")
            if text in ["/start", "/help", "hi", "hello"]:
                welcome_text = (
                    f"👋 E ku aro / Sannu / Nno, *{user_name}*!\n\n"
                    f"Welcome to *AfyaMama* — Sovereign Maternal & Antenatal Healthcare Assistant 🤰\n\n"
                    f"Speak or write your symptoms in *Yoruba, Hausa, Igbo, Pidgin, or English*.\n"
                    f"All clinical guidance is verified against *WHO Antenatal Care Guidelines* and *Federal Ministry of Health Nigeria Protocols*.\n\n"
                    f"👇 *Select your current stage to begin:*"
                )
                await self.send_message(chat_id, welcome_text, reply_markup=self.get_main_keyboard())
                return

            stage = self.user_stages.get(chat_id, "Pregnancy")

            # Case A: Voice Note Received
            if "voice" in msg or "audio" in msg:
                voice_obj = msg.get("voice") or msg.get("audio")
                file_id = voice_obj["file_id"]
                
                await self.send_message(chat_id, "🎙️ _Listening to your voice note and checking WHO/Nigeria maternal guidelines..._")

                temp_audio = os.path.join(TEMP_DIR, f"tg_{uuid.uuid4().hex}.oga")
                download_ok = await self.download_file(file_id, temp_audio)

                if download_ok:
                    transcription = await self.asr_client.transcribe(temp_audio)
                    transcript_text = transcription.get("text", "")
                else:
                    transcript_text = "Maternal consultation with reported symptoms."

                # Run Maternal RAG & Clinical Evaluation
                clinical_data = await self.llm_client.parse_clinical_data(transcript_text, gestational_stage=stage)
                assessment = self.triage_engine.evaluate(clinical_data, patient_name=user_name)

                # Persist Session in DB
                self.db_manager.record_triage_session(
                    phone_number=f"TG_{chat_id}",
                    audio_path=temp_audio if download_ok else "telegram_voice",
                    transcript_text=transcript_text,
                    clinical_data=clinical_data,
                    triage_assessment=assessment
                )

                # Send Response
                await self.send_message(chat_id, assessment.patient_message, reply_markup=self.get_main_keyboard())
                return

            # Case B: Text Symptoms Received
            elif text:
                await self.send_message(chat_id, "🩺 _Analyzing symptoms against WHO Antenatal & Obstetric Emergency guidelines..._")

                # Run Maternal RAG & Clinical Evaluation
                clinical_data = await self.llm_client.parse_clinical_data(text, gestational_stage=stage)
                assessment = self.triage_engine.evaluate(clinical_data, patient_name=user_name)

                # Persist Session in DB
                self.db_manager.record_triage_session(
                    phone_number=f"TG_{chat_id}",
                    audio_path="telegram_text",
                    transcript_text=text,
                    clinical_data=clinical_data,
                    triage_assessment=assessment
                )

                # Send Response
                await self.send_message(chat_id, assessment.patient_message, reply_markup=self.get_main_keyboard())
                return
