import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from core.database.session import SessionLocal
from core.database.models import Patient, TriageSession, SessionAudioLog
from services.audio.processor import AudioProcessor
from services.transcription.asr import NAtlasASRClient
from services.llm.clinical_parser import NAtlasLLMClient
from services.triage.engine import TriageEngine
from services.database.session_manager import DatabaseSessionManager

router = APIRouter()

TEMP_DIR = os.path.join(os.getcwd(), "storage", "temp_uploads")
os.makedirs(TEMP_DIR, exist_ok=True)

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "portal_token")
processor = AudioProcessor(meta_access_token=META_ACCESS_TOKEN)
asr_client = NAtlasASRClient()
llm_client = NAtlasLLMClient()
triage_engine = TriageEngine()
db_manager = DatabaseSessionManager()

class TextTriageRequest(BaseModel):
    phone_number: str
    symptoms_text: str

@router.get("/portal", response_class=HTMLResponse)
def get_portal_ui():
    """Serves the interactive AfyaVoice Telemedicine Portal and Live Simulator."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AfyaVoice - Clinical Triage Portal & Simulator</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090e17;
      --card-bg: #111a2e;
      --card-border: #1e2c4a;
      --primary: #10b981;
      --primary-hover: #059669;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --danger: #ef4444;
      --warning: #f59e0b;
      --success: #10b981;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: var(--bg);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: #0f172a;
      border-bottom: 1px solid var(--card-border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .logo-container { display: flex; align-items: center; gap: 0.75rem; }
    .logo-badge {
      background: linear-gradient(135deg, #10b981, #06b6d4);
      color: #fff;
      font-weight: 800;
      padding: 0.4rem 0.75rem;
      border-radius: 8px;
      font-size: 1.1rem;
    }
    .logo-title { font-weight: 700; font-size: 1.25rem; letter-spacing: -0.02em; }
    .status-pill {
      background: rgba(16, 185, 129, 0.15);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #10b981;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; animation: pulse 2s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    
    .container {
      max-width: 1400px;
      margin: 2rem auto;
      padding: 0 1.5rem;
      width: 100%;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 2rem;
      flex: 1;
    }
    @media (max-width: 1024px) { .container { grid-template-columns: 1fr; } }
    
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.75rem;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    h2 { font-size: 1.3rem; margin-bottom: 0.5rem; font-weight: 700; }
    p.subtitle { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem; }
    
    .tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--card-border); padding-bottom: 0.5rem; }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.5rem 1rem;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      border-radius: 8px;
      transition: all 0.2s;
    }
    .tab-btn.active { background: #1e293b; color: #fff; }
    
    .form-group { margin-bottom: 1.25rem; }
    label { display: block; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; }
    input[type="text"], textarea {
      width: 100%;
      background: #090e17;
      border: 1px solid var(--card-border);
      color: #fff;
      padding: 0.75rem 1rem;
      border-radius: 10px;
      font-family: inherit;
      font-size: 0.95rem;
      transition: border-color 0.2s;
    }
    input[type="text"]:focus, textarea:focus { outline: none; border-color: var(--primary); }
    textarea { min-height: 120px; resize: vertical; }

    /* Voice recording interface */
    .record-box {
      border: 2px dashed var(--card-border);
      border-radius: 12px;
      padding: 2rem;
      text-align: center;
      margin-bottom: 1.25rem;
      background: rgba(15, 23, 42, 0.5);
    }
    .mic-btn {
      width: 72px;
      height: 72px;
      border-radius: 50%;
      background: #1e293b;
      border: 2px solid var(--primary);
      color: var(--primary);
      font-size: 1.8rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.3s;
      margin-bottom: 1rem;
    }
    .mic-btn.recording {
      background: var(--danger);
      border-color: #f87171;
      color: #fff;
      animation: pulse 1s infinite;
    }
    .record-timer { font-family: 'JetBrains Mono', monospace; font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; }
    
    .btn-submit {
      width: 100%;
      background: var(--primary);
      color: #fff;
      border: none;
      padding: 0.85rem;
      font-size: 1rem;
      font-weight: 700;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }
    .btn-submit:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; }

    /* WhatsApp Phone Mockup */
    .phone-mockup {
      background: #075e54;
      border: 12px solid #1e293b;
      border-radius: 36px;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
      height: 100%;
      min-height: 600px;
      display: flex;
      flex-direction: column;
    }
    .phone-header {
      background: #128c7e;
      color: #fff;
      padding: 0.85rem 1.25rem;
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .phone-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #128c7e;
      font-size: 1rem;
    }
    .phone-chat {
      flex: 1;
      background: #0b141a;
      background-image: radial-gradient(#1f2c34 1px, transparent 1px);
      background-size: 16px 16px;
      padding: 1.25rem;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .chat-bubble {
      max-width: 85%;
      padding: 0.75rem 1rem;
      border-radius: 12px;
      font-size: 0.9rem;
      line-height: 1.45;
      position: relative;
    }
    .bubble-patient {
      align-self: flex-end;
      background: #005c4b;
      color: #e9edef;
      border-top-right-radius: 2px;
    }
    .bubble-bot {
      align-self: flex-start;
      background: #202c33;
      color: #d1d7db;
      border-top-left-radius: 2px;
      white-space: pre-wrap;
    }

    /* Live Analysis Breakdown */
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
      margin-top: 1rem;
    }
    .metric-card {
      background: #090e17;
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 0.75rem 1rem;
    }
    .metric-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 1rem; font-weight: 700; margin-top: 0.2rem; }
    
    .badge-red { color: #ef4444; }
    .badge-yellow { color: #f59e0b; }
    .badge-green { color: #10b981; }

    .loader {
      border: 3px solid rgba(255, 255, 255, 0.2);
      border-top: 3px solid #fff;
      border-radius: 50%;
      width: 20px;
      height: 20px;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  </style>
</head>
<body>

  <header>
    <div class="logo-container">
      <div class="logo-badge">AV</div>
      <div>
        <div class="logo-title">AfyaVoice Telemedicine Portal</div>
        <div style="font-size: 0.75rem; color: var(--text-muted);">Sovereign N-ATLAS Clinical Triage Engine</div>
      </div>
    </div>
    <div class="status-pill">
      <div class="status-dot"></div>
      N-ATLAS Engine Live (Port 8000)
    </div>
  </header>

  <div class="container">
    
    <!-- LEFT COLUMN: Patient Ingestion Simulator -->
    <div class="card">
      <h2>Patient Consultation Simulator</h2>
      <p class="subtitle">Submit a patient consultation using Voice or Text in English, Yoruba, Hausa, Igbo, or Pidgin.</p>

      <div class="tabs">
        <button class="tab-btn active" id="tab-voice-btn" onclick="switchTab('voice')">🎙️ Voice Note Recording</button>
        <button class="tab-btn" id="tab-text-btn" onclick="switchTab('text')">💬 Text Message</button>
      </div>

      <!-- VOICE INPUT FORM -->
      <div id="voice-pane">
        <div class="record-box">
          <button class="mic-btn" id="mic-record-btn" onclick="toggleRecording()">🎤</button>
          <div class="record-timer" id="record-timer">00:00</div>
          <div style="font-size: 0.85rem; color: var(--text-muted);" id="record-status">Click microphone to record voice note</div>
          <audio id="audio-playback" controls style="display: none; margin: 1rem auto 0; width: 100%;"></audio>
        </div>

        <div class="form-group">
          <label>Or Upload Voice Note File (.wav, .ogg, .mp3, .m4a)</label>
          <input type="file" id="audio-file-input" accept="audio/*">
        </div>
      </div>

      <!-- TEXT INPUT FORM -->
      <div id="text-pane" style="display: none;">
        <div class="form-group">
          <label>Patient Symptoms / Message</label>
          <textarea id="text-symptoms" placeholder="E.g., I have been having a severe headache and high fever for the past 3 days..."></textarea>
        </div>
      </div>

      <div class="form-group">
        <label>Patient Phone Number (MSISDN)</label>
        <input type="text" id="patient-phone" value="+2348179359528">
      </div>

      <button class="btn-submit" id="submit-triage-btn" onclick="submitTriage()">
        <span>Run N-ATLAS Clinical Triage</span>
      </button>

      <!-- LIVE DIAGNOSTIC BOX -->
      <div id="results-analytics" style="display: none; margin-top: 1.5rem;">
        <h3 style="font-size: 1rem; border-top: 1px solid var(--card-border); padding-top: 1.25rem;">Live Clinical AI Extraction</h3>
        <div class="metric-grid">
          <div class="metric-card">
            <div class="metric-label">Triage Urgency</div>
            <div class="metric-value" id="val-triage-tier">-</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Detected Language</div>
            <div class="metric-value" id="val-lang">-</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Chief Complaint</div>
            <div class="metric-value" id="val-complaint">-</div>
          </div>
          <div class="metric-card">
            <div class="metric-label">Reported Duration</div>
            <div class="metric-value" id="val-duration">-</div>
          </div>
          <div class="metric-card" style="grid-column: span 2;">
            <div class="metric-label">SNOMED CT Clinical Standard & Code</div>
            <div class="metric-value" id="val-snomed" style="font-size: 0.9rem; font-family: monospace; color: #38bdf8;">-</div>
          </div>
        </div>
        <div style="margin-top: 0.75rem; font-size: 0.8rem; color: var(--text-muted);">
          💾 Database Session ID: <span id="val-session-id" style="font-family: monospace; color: #fff;">-</span>
        </div>
      </div>

    </div>

    <!-- RIGHT COLUMN: Live WhatsApp Phone Mockup -->
    <div>
      <div class="phone-mockup">
        <div class="phone-header">
          <div class="phone-avatar">AV</div>
          <div>
            <div style="font-weight: 700; font-size: 0.95rem;">AfyaVoice Clinical Assistant</div>
            <div style="font-size: 0.75rem; opacity: 0.85;">Official Healthcare Verified</div>
          </div>
        </div>
        <div class="phone-chat" id="chat-stream">
          <div class="chat-bubble bubble-bot">
👋 Hello! Welcome to *AfyaVoice* Sovereign Multilingual Healthcare Voice Triage.

Send a voice note or type your symptoms. Our N-ATLAS clinical AI will instantly evaluate your urgency level and provide medical guidance.
          </div>
        </div>
      </div>
    </div>

  </div>

  <script>
    let activeTab = 'voice';
    let mediaRecorder = null;
    let audioChunks = [];
    let audioBlob = null;
    let recordInterval = null;
    let secondsElapsed = 0;

    function switchTab(tab) {
      activeTab = tab;
      document.getElementById('tab-voice-btn').classList.toggle('active', tab === 'voice');
      document.getElementById('tab-text-btn').classList.toggle('active', tab === 'text');
      document.getElementById('voice-pane').style.display = tab === 'voice' ? 'block' : 'none';
      document.getElementById('text-pane').style.display = tab === 'text' ? 'block' : 'none';
    }

    async function toggleRecording() {
      const micBtn = document.getElementById('mic-record-btn');
      const timerDisplay = document.getElementById('record-timer');
      const statusText = document.getElementById('record-status');

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
          mediaRecorder.onstop = () => {
            audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const playback = document.getElementById('audio-playback');
            playback.src = URL.createObjectURL(audioBlob);
            playback.style.display = 'block';
            statusText.innerText = 'Voice note recorded! Ready to submit.';
          };

          mediaRecorder.start();
          micBtn.classList.add('recording');
          micBtn.innerText = '⏹️';
          statusText.innerText = 'Recording voice note... Speak clearly.';
          secondsElapsed = 0;
          recordInterval = setInterval(() => {
            secondsElapsed++;
            const mins = String(Math.floor(secondsElapsed / 60)).padStart(2, '0');
            const secs = String(secondsElapsed % 60).padStart(2, '0');
            timerDisplay.innerText = `${mins}:${secs}`;
          }, 1000);
        } catch (err) {
          alert('Microphone access denied or not available. You can use the file upload or text tab!');
        }
      } else {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
        clearInterval(recordInterval);
      }
    }

    async function submitTriage() {
      const submitBtn = document.getElementById('submit-triage-btn');
      const phone = document.getElementById('patient-phone').value.trim();
      const chatStream = document.getElementById('chat-stream');

      if (!phone) { alert('Please enter a patient phone number.'); return; }

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<div class="loader"></div> Processing N-ATLAS Clinical Triage...';

      let requestUrl = '';
      let requestBody = null;

      if (activeTab === 'voice') {
        const fileInput = document.getElementById('audio-file-input');
        let uploadBlob = audioBlob;

        if (fileInput.files.length > 0) {
          uploadBlob = fileInput.files[0];
        }

        if (!uploadBlob) {
          alert('Please record a voice note or choose an audio file first!');
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Run N-ATLAS Clinical Triage</span>';
          return;
        }

        requestUrl = '/api/triage/audio';
        const formData = new FormData();
        formData.append('audio_file', uploadBlob, 'voice_note.wav');
        formData.append('phone_number', phone);
        requestBody = formData;

        // Add patient speech bubble
        chatStream.innerHTML += `<div class="chat-bubble bubble-patient">🎙️ Voice Note (Audio submitted)</div>`;
      } else {
        const text = document.getElementById('text-symptoms').value.trim();
        if (!text) {
          alert('Please type patient symptoms!');
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Run N-ATLAS Clinical Triage</span>';
          return;
        }
        requestUrl = '/api/triage/text';
        requestBody = JSON.stringify({ phone_number: phone, symptoms_text: text });

        // Add patient speech bubble
        chatStream.innerHTML += `<div class="chat-bubble bubble-patient">${text}</div>`;
      }

      chatStream.scrollTop = chatStream.scrollHeight;

      try {
        const res = await fetch(requestUrl, {
          method: 'POST',
          headers: activeTab === 'text' ? { 'Content-Type': 'application/json' } : {},
          body: requestBody
        });

        const data = await res.json();

        if (data.status === 'success') {
          // Display Bot WhatsApp Reply
          chatStream.innerHTML += `<div class="chat-bubble bubble-bot">${data.patient_message}</div>`;
          chatStream.scrollTop = chatStream.scrollHeight;

          // Update Analytics Box
          document.getElementById('results-analytics').style.display = 'block';
          const tierEl = document.getElementById('val-triage-tier');
          tierEl.innerText = data.triage_tier;
          tierEl.className = 'metric-value ' + (data.triage_tier === 'RED' ? 'badge-red' : data.triage_tier === 'YELLOW' ? 'badge-yellow' : 'badge-green');
          
          document.getElementById('val-lang').innerText = data.detected_language || 'English';
          document.getElementById('val-complaint').innerText = data.chief_complaint || 'N/A';
          document.getElementById('val-duration').innerText = data.duration || 'N/A';
          document.getElementById('val-snomed').innerText = (data.snomed_name || 'Clinical Standard') + ' (' + (data.snomed_code || '-') + ')';
          document.getElementById('val-session-id').innerText = data.session_id || 'Saved';
        } else {
          alert('Triage processing failed: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Error connecting to backend: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Run N-ATLAS Clinical Triage</span>';
      }
    }
  </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@router.post("/api/triage/audio")
async def process_audio_triage(
    audio_file: UploadFile = File(...),
    phone_number: str = Form(...)
):
    """Processes uploaded or recorded audio through the full N-ATLAS pipeline."""
    try:
        temp_filename = f"portal_{uuid.uuid4().hex}_{audio_file.filename}"
        temp_path = os.path.join(TEMP_DIR, temp_filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        # 1. Speech to Text via N-ATLAS ASR
        transcription_result = await asr_client.transcribe(temp_path)
        transcript_text = transcription_result.get("text", "")

        # 2. Clinical Extraction via N-ATLAS LLM
        clinical_data = await llm_client.parse_clinical_data(transcript_text)

        # 3. Triage Decision Engine
        assessment = triage_engine.evaluate(clinical_data)

        # 4. Save to Database
        session_id = db_manager.record_triage_session(
            phone_number=phone_number,
            audio_path=temp_path,
            transcript_text=transcript_text,
            clinical_data=clinical_data,
            triage_assessment=assessment
        )

        return {
            "status": "success",
            "session_id": str(session_id) if session_id else "RECORDED",
            "transcript": transcript_text,
            "triage_tier": assessment.urgency_tier,
            "triage_title": assessment.urgency_title,
            "chief_complaint": clinical_data.chief_complaint,
            "symptoms": clinical_data.symptoms,
            "duration": clinical_data.duration,
            "detected_language": clinical_data.language_detected,
            "snomed_code": assessment.snomed_concept_code,
            "snomed_name": assessment.snomed_display_name,
            "patient_message": assessment.patient_message
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/api/triage/text")
async def process_text_triage(request: TextTriageRequest):
    """Processes typed clinical symptoms through N-ATLAS LLM and Triage Engine."""
    try:
        # 1. Clinical Extraction via N-ATLAS LLM
        clinical_data = await llm_client.parse_clinical_data(request.symptoms_text)

        # 2. Triage Decision Engine
        assessment = triage_engine.evaluate(clinical_data)

        # 3. Save to Database
        session_id = db_manager.record_triage_session(
            phone_number=request.phone_number,
            audio_path="portal_text",
            transcript_text=request.symptoms_text,
            clinical_data=clinical_data,
            triage_assessment=assessment
        )

        return {
            "status": "success",
            "session_id": str(session_id) if session_id else "RECORDED",
            "transcript": request.symptoms_text,
            "triage_tier": assessment.urgency_tier,
            "triage_title": assessment.urgency_title,
            "chief_complaint": clinical_data.chief_complaint,
            "symptoms": clinical_data.symptoms,
            "duration": clinical_data.duration,
            "detected_language": clinical_data.language_detected,
            "snomed_code": assessment.snomed_concept_code,
            "snomed_name": assessment.snomed_display_name,
            "patient_message": assessment.patient_message
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
