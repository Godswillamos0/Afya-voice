import os
import json
import httpx
from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse
from services.audio.processor import AudioProcessor

router = APIRouter()

# In production, these should be securely loaded via Pydantic BaseSettings
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "afyavoice_secure_verify_token")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "test_meta_token")

# Initialize Audio Processor (Subsystem 1)
processor = AudioProcessor(meta_access_token=META_ACCESS_TOKEN)

@router.get("")
@router.get("/")
async def verify_webhook(request: Request):
    """
    Endpoint for Meta to verify the webhook URL.
    """
    mode = request.query_params.get("hub.mode")
    challenge = request.query_params.get("hub.challenge")
    token = request.query_params.get("hub.verify_token")
    
    print(f"\n--- WEBHOOK VERIFICATION ATTEMPT ---")
    print(f"Mode: {mode}")
    print(f"Token: {token}")
    print(f"Challenge: {challenge}")
    print(f"------------------------------------\n")
    
    # Blindly return the challenge as plain text to guarantee Meta accepts it if it reaches here
    if challenge:
        return PlainTextResponse(content=challenge)
        
    raise HTTPException(status_code=403, detail="Verification failed.")

@router.post("")
@router.post("/")
async def handle_whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives incoming WhatsApp messages from Meta.
    (FR-AUD-001: Multi-Format Ingestion)
    """
    try:
        body = await request.json()
        print("\n[WEBHOOK] Incoming event received from Meta!")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # WhatsApp Cloud API payload structure
    if "entry" in body:
        for entry in body["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                
                for message in messages:
                    msg_type = message.get("type")
                    sender_phone = message.get("from")
                    print(f"[WEBHOOK] Message type: {msg_type} from {sender_phone}")
                    
                    # 1. Voice Note / Audio Message
                    if msg_type == "audio":
                        audio_id = message["audio"]["id"]
                        mime_type = message["audio"].get("mime_type", "audio/ogg")
                        background_tasks.add_task(
                            process_incoming_audio, 
                            audio_id, 
                            sender_phone,
                            mime_type
                        )
                    # 2. Text Message (typed by user)
                    elif msg_type == "text":
                        text_body = message.get("text", {}).get("body", "")
                        background_tasks.add_task(
                            process_incoming_text,
                            text_body,
                            sender_phone
                        )
                        
    return {"status": "ok"}

async def process_incoming_text(text_body: str, sender_phone: str):
    """
    Background task to process text messages, run clinical NLP, evaluate triage, and reply.
    """
    print(f"\n[INCOMING TEXT] From {sender_phone}: {text_body}")
    
    from services.llm.clinical_parser import NAtlasLLMClient
    from services.triage.engine import TriageEngine
    from services.database.session_manager import DatabaseSessionManager
    from services.messaging.whatsapp import WhatsAppMessenger
    
    llm_client = NAtlasLLMClient()
    triage_engine = TriageEngine()
    db_manager = DatabaseSessionManager()
    messenger = WhatsAppMessenger()
    
    try:
        # Step 1: Clinical Extraction
        print("[TEXT PIPELINE] Running N-ATLAS Clinical Extraction...")
        clinical_data = await llm_client.parse_clinical_data(text_body)
        
        # Step 2: Triage Assessment
        print("[TEXT PIPELINE] Calculating Clinical Triage Urgency...")
        assessment = triage_engine.evaluate(clinical_data)
        
        print("\n==================================================")
        print("--- N-ATLAS CLINICAL TRIAGE RESULT ---")
        print("==================================================")
        print(f"Chief Complaint : {clinical_data.chief_complaint}")
        print(f"Symptoms        : {', '.join(clinical_data.symptoms)}")
        print(f"Duration        : {clinical_data.duration}")
        print(f"Severity        : {clinical_data.severity}")
        print(f"Detected Lang   : {clinical_data.language_detected}")
        print(f"Triage Tier     : {assessment.urgency_title}")
        print("==================================================\n")
        
        # Step 3: Record in DB
        db_manager.record_triage_session(
            phone_number=sender_phone,
            audio_path="text_chat",
            transcript_text=text_body,
            clinical_data=clinical_data,
            triage_assessment=assessment
        )
        
        # Step 4: Dispatch WhatsApp reply
        print(f"[TEXT PIPELINE] Sending WhatsApp Triage Advice to {sender_phone}...")
        send_success = await messenger.send_text_message(
            to_phone=sender_phone,
            message_text=assessment.patient_message
        )
        if send_success:
            print(f"[SUCCESS] Triage response dispatched to patient on WhatsApp!")
        else:
            print(f"[WARNING] Could not deliver WhatsApp message to {sender_phone}.")
            
    except Exception as e:
        print(f"[ERROR] Text processing pipeline failed: {str(e)}")

async def process_incoming_audio(media_id: str, sender_phone: str, mime_type: str):
    """
    Background task to fetch media URL, download, and process the audio.
    """
    print(f"Incoming audio {media_id} from {sender_phone} (Mime: {mime_type})")
    
    # Step 1: Fetch Media URL from Meta Graph API
    meta_api_version = os.getenv("META_API_VERSION", "v25.0")
    meta_url = f"https://graph.facebook.com/{meta_api_version}/{media_id}"
    headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(meta_url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            media_url = data.get("url")
            
            # Extract input format from mime type (e.g., audio/ogg; codecs=opus -> ogg)
            input_format = "ogg"
            if "mp4" in mime_type or "aac" in mime_type or "m4a" in mime_type:
                input_format = "mp4" # pydub maps m4a/aac to mp4 container decoder
            elif "wav" in mime_type:
                input_format = "wav"

            # Step 2: Execute Subsystem 1 Pipeline (Download -> Normalize -> VAD -> Clean)
            try:
                final_audio_path = await processor.process_pipeline(media_url=media_url, input_format=input_format)
                print(f"SUCCESS: Audio processed and stored at {final_audio_path}")
                
                # --- Subsystem 2: N-ATLAS AI Processing Pipeline ---
                from services.transcription.asr import NAtlasASRClient
                from services.llm.clinical_parser import NAtlasLLMClient
                from services.triage.engine import TriageEngine
                from services.database.session_manager import DatabaseSessionManager
                from services.messaging.whatsapp import WhatsAppMessenger
                
                asr_client = NAtlasASRClient()
                llm_client = NAtlasLLMClient()
                triage_engine = TriageEngine()
                db_manager = DatabaseSessionManager()
                messenger = WhatsAppMessenger()
                
                # Step A: Speech to Text
                print("2. Running N-ATLAS Speech-to-Text...")
                transcription_result = await asr_client.transcribe(final_audio_path)
                transcript_text = transcription_result.get("text", "")
                print(f"   [Transcript]: {transcript_text}")
                
                # Step B: Clinical NLP Extraction
                print("3. Running N-ATLAS Clinical Extraction...")
                clinical_data = await llm_client.parse_clinical_data(transcript_text)
                
                # Step C: Subsystem 3 - Clinical Triage Evaluation
                print("4. Calculating Clinical Triage Urgency...")
                assessment = triage_engine.evaluate(clinical_data)
                
                print("\n==================================================")
                print("--- N-ATLAS CLINICAL TRIAGE RESULT ---")
                print("==================================================")
                print(f"Chief Complaint : {clinical_data.chief_complaint}")
                print(f"Symptoms        : {', '.join(clinical_data.symptoms)}")
                print(f"Duration        : {clinical_data.duration}")
                print(f"Severity        : {clinical_data.severity}")
                print(f"Detected Lang   : {clinical_data.language_detected}")
                print(f"Triage Tier     : {assessment.urgency_title}")
                print("==================================================\n")
                
                # Step D: Save Consultation in Database
                db_manager.record_triage_session(
                    phone_number=sender_phone,
                    audio_path=final_audio_path,
                    transcript_text=transcript_text,
                    clinical_data=clinical_data,
                    triage_assessment=assessment
                )
                
                # Step E: Subsystem 3 - Send WhatsApp Clinical Guidance back to Patient
                print(f"5. Sending WhatsApp Triage Advice to patient ({sender_phone})...")
                send_success = await messenger.send_text_message(
                    to_phone=sender_phone,
                    message_text=assessment.patient_message
                )
                if send_success:
                    print(f"[SUCCESS] Triage response dispatched to patient on WhatsApp!")
                else:
                    print(f"[WARNING] Could not deliver WhatsApp message to {sender_phone}.")
                
            except Exception as e:
                print(f"ERROR: Audio processing pipeline failed: {str(e)}")
        else:
            print(f"ERROR: Failed to fetch media metadata from Meta: {resp.text}")
