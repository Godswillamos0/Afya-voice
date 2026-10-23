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
    gestational_stage: Optional[str] = "Pregnancy"

@router.get("/portal", response_class=HTMLResponse)
def get_portal_ui():
    """Serves the AfyaMama Maternal & Antenatal Healthcare Clinical Portal."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AfyaMama - Maternal & Antenatal Health Triage Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #fdf2f8;
      --card-bg: #ffffff;
      --border: #fbcfe8;
      --border-focus: #be185d;
      --primary: #be185d;
      --primary-hover: #9d174d;
      --primary-light: #fff1f2;
      --primary-subtle: #fce7f3;
      --teal: #0f766e;
      --teal-light: #f0fdfa;
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-light: #94a3b8;
      --danger-bg: #fef2f2;
      --danger-text: #991b1b;
      --danger-border: #fecaca;
      --warning-bg: #fffbeb;
      --warning-text: #92400e;
      --warning-border: #fde68a;
      --success-bg: #f0fdf4;
      --success-text: #166534;
      --success-border: #bbf7d0;
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
      --shadow-md: 0 4px 14px -2px rgba(190, 24, 93, 0.08);
      --shadow-lg: 0 12px 28px -4px rgba(190, 24, 93, 0.12);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    /* TOP HEADER */
    header {
      background: #ffffff;
      border-bottom: 1px solid var(--border);
      padding: 0.85rem 2rem;
      position: sticky;
      top: 0;
      z-index: 50;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: var(--shadow-sm);
    }
    .brand-group {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
      color: var(--text-main);
    }
    .brand-logo-icon {
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--primary), #fb7185);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.1rem;
    }
    .brand-title {
      font-size: 1.2rem;
      font-weight: 800;
      color: var(--primary);
      line-height: 1.1;
    }
    .brand-subtitle {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--text-muted);
    }
    .header-nav {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .back-home-link {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-muted);
      text-decoration: none;
      padding: 0.4rem 0.85rem;
      border-radius: 8px;
      transition: all 0.15s;
    }
    .back-home-link:hover {
      background: #f1f5f9;
      color: var(--primary);
    }
    .btn-tg-pill {
      background: #0284c7;
      color: #fff;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 700;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
    }
    .emergency-hotline {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      background: var(--danger-bg);
      color: var(--danger-text);
      border: 1px solid var(--danger-border);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 700;
      text-decoration: none;
    }

    /* MAIN LAYOUT */
    .portal-container {
      max-width: 1200px;
      margin: 2rem auto;
      padding: 0 1.5rem;
      width: 100%;
      display: grid;
      grid-template-columns: 1.8fr 1fr;
      gap: 2rem;
      flex: 1;
    }
    @media (max-width: 992px) {
      .portal-container {
        grid-template-columns: 1fr;
        margin: 1.25rem auto;
      }
    }

    /* FORM CARD */
    .main-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 2rem;
      box-shadow: var(--shadow-sm);
    }
    .portal-heading-row {
      margin-bottom: 1.5rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--border);
    }
    .portal-heading {
      font-size: 1.55rem;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: -0.02em;
      margin-bottom: 0.35rem;
    }
    .portal-subheading {
      font-size: 0.95rem;
      color: var(--text-muted);
    }

    /* STEP LABELS */
    .step-section {
      margin-bottom: 1.85rem;
    }
    .step-label {
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 0.65rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .step-num-badge {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--primary-light);
      color: var(--primary);
      font-size: 0.75rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* CHIP SELECTORS */
    .chips-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 0.65rem;
    }
    .chip-btn {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 0.65rem 0.85rem;
      font-family: inherit;
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }
    .chip-btn:hover {
      border-color: var(--primary);
      color: var(--primary);
      background: var(--primary-light);
    }
    .chip-btn.selected {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(190, 24, 93, 0.2);
    }

    /* TABS */
    .tab-switch {
      display: flex;
      background: #f1f5f9;
      border-radius: 10px;
      padding: 0.25rem;
      margin-bottom: 1rem;
      gap: 0.25rem;
    }
    .tab-btn {
      flex: 1;
      padding: 0.6rem 1rem;
      border: none;
      background: transparent;
      border-radius: 8px;
      font-family: inherit;
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;
    }
    .tab-btn.active {
      background: #ffffff;
      color: var(--primary);
      box-shadow: var(--shadow-sm);
    }

    /* VOICE RECORDER */
    .voice-recorder-card {
      background: #fff5f8;
      border: 2px dashed #fbcfe8;
      border-radius: 14px;
      padding: 2rem 1.5rem;
      text-align: center;
      transition: all 0.2s;
    }
    .voice-recorder-card.recording {
      border-color: #ef4444;
      background: #fff5f5;
    }
    .mic-button {
      width: 64px;
      height: 64px;
      border-radius: 50%;
      background: var(--primary);
      color: #ffffff;
      border: none;
      font-size: 1.6rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 1rem;
      transition: all 0.2s;
      box-shadow: 0 4px 14px rgba(190, 24, 93, 0.25);
    }
    .mic-button:hover {
      background: var(--primary-hover);
      transform: scale(1.05);
    }
    .mic-button.recording {
      background: #dc2626;
      animation: mic-pulse 1.2s infinite;
    }
    @keyframes mic-pulse {
      0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.5); }
      50% { transform: scale(1.08); box-shadow: 0 0 0 12px rgba(220, 38, 38, 0); }
    }
    .mic-status-title {
      font-weight: 800;
      font-size: 1.05rem;
      color: var(--text-main);
      margin-bottom: 0.35rem;
    }
    .mic-status-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .audio-upload-alt {
      margin-top: 1.25rem;
      padding-top: 1.25rem;
      border-top: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.65rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }

    /* TEXT INPUT */
    .symptom-textarea {
      width: 100%;
      min-height: 110px;
      padding: 0.85rem 1rem;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      font-family: inherit;
      font-size: 0.95rem;
      color: var(--text-main);
      resize: vertical;
      line-height: 1.5;
    }
    .symptom-textarea:focus {
      outline: none;
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(190, 24, 93, 0.12);
    }
    .quick-symptom-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
      margin-top: 0.75rem;
    }
    .tag-btn {
      background: #fdf2f8;
      border: 1px solid #fbcfe8;
      border-radius: 9999px;
      padding: 0.3rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--primary);
      cursor: pointer;
      transition: all 0.15s;
    }
    .tag-btn:hover {
      background: var(--primary);
      color: #fff;
    }

    /* INPUTS */
    .form-input {
      width: 100%;
      padding: 0.75rem 1rem;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      font-family: inherit;
      font-size: 0.95rem;
      color: var(--text-main);
    }
    .form-input:focus {
      outline: none;
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(190, 24, 93, 0.12);
    }

    /* SUBMIT BUTTON */
    .btn-submit-triage {
      width: 100%;
      background: var(--primary);
      color: #ffffff;
      border: none;
      padding: 1rem 1.5rem;
      border-radius: 12px;
      font-size: 1.05rem;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.65rem;
      transition: all 0.2s;
      box-shadow: 0 4px 14px rgba(190, 24, 93, 0.25);
    }
    .btn-submit-triage:hover {
      background: var(--primary-hover);
      transform: translateY(-1px);
    }
    .btn-submit-triage:disabled {
      background: #94a3b8;
      cursor: not-allowed;
      transform: none;
    }

    /* RESULTS SECTION */
    .results-card {
      display: none;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 1.75rem;
      margin-top: 2rem;
      box-shadow: var(--shadow-md);
      animation: fadeIn 0.3s ease-in-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

    .result-banner {
      padding: 1rem 1.25rem;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.25rem;
    }
    .result-banner.red { background: var(--danger-bg); border: 1px solid var(--danger-border); color: var(--danger-text); }
    .result-banner.yellow { background: var(--warning-bg); border: 1px solid var(--warning-border); color: var(--warning-text); }
    .result-banner.green { background: var(--success-bg); border: 1px solid var(--success-border); color: var(--success-text); }
    .result-banner-title { font-size: 1.15rem; font-weight: 800; }
    .result-banner-pill {
      font-size: 0.78rem;
      font-weight: 800;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.9);
    }

    .findings-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 1rem;
      margin-bottom: 1.25rem;
    }
    @media (max-width: 640px) { .findings-grid { grid-template-columns: 1fr; } }
    .finding-item {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 0.85rem 1rem;
    }
    .finding-label { font-size: 0.72rem; font-weight: 800; color: var(--text-light); text-transform: uppercase; margin-bottom: 0.25rem; }
    .finding-value { font-size: 0.95rem; font-weight: 700; color: var(--text-main); }
    
    .snomed-badge {
      grid-column: span 2;
      background: #fdf2f8;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.85rem 1rem;
    }
    @media (max-width: 640px) { .snomed-badge { grid-column: span 1; } }

    .rag-evidence-box {
      background: #f0fdfa;
      border: 1px solid #ccfbf1;
      border-radius: 12px;
      padding: 1rem 1.25rem;
      margin-bottom: 1.25rem;
      font-size: 0.82rem;
      color: #0f766e;
      line-height: 1.5;
    }

    .care-instructions-box {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1.25rem;
      font-size: 0.92rem;
      line-height: 1.6;
      color: #334155;
      white-space: pre-wrap;
    }

    /* RIGHT SIDEBAR */
    .sidebar-panel {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .info-card {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 1.5rem;
      box-shadow: var(--shadow-sm);
    }
    .info-card-header {
      font-size: 1rem;
      font-weight: 800;
      color: var(--text-main);
      margin-bottom: 0.85rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .redflag-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0.65rem;
    }
    .redflag-item {
      display: flex;
      align-items: flex-start;
      gap: 0.5rem;
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.4;
    }
    .redflag-dot {
      color: #ef4444;
      font-weight: bold;
    }

    /* SPINNER */
    .loading-spinner {
      width: 20px;
      height: 20px;
      border: 3px solid rgba(255, 255, 255, 0.3);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>

  <!-- HEADER -->
  <header>
    <a href="/" class="brand-group">
      <div class="brand-logo-icon">AM</div>
      <div>
        <div class="brand-title">AfyaMama</div>
        <div class="brand-subtitle">Maternal & Antenatal Triage</div>
      </div>
    </a>
    <div class="header-nav">
      <a href="/" class="back-home-link">← Back to Home</a>
      <a href="https://t.me/afyavoice_bot" target="_blank" class="btn-tg-pill">📱 Open Telegram Bot</a>
      <a href="tel:112" class="emergency-hotline">🚨 Emergency: 112</a>
    </div>
  </header>

  <!-- MAIN CONTAINER -->
  <main class="portal-container">
    
    <!-- LEFT COLUMN: FORM & RESULTS -->
    <div>
      <div class="main-card">
        <div class="portal-heading-row">
          <h1 class="portal-heading">Maternal Health Consultation</h1>
          <p class="portal-subheading">Speak or write your pregnancy symptoms in your native dialect for instant clinical evaluation powered by WHO and Nigerian Health Guidelines.</p>
        </div>

        <!-- STEP 1: LANGUAGE -->
        <div class="step-section">
          <div class="step-label">
            <span class="step-num-badge">1</span>
            <span>Select Consultation Dialect (Ede / Harshe):</span>
          </div>
          <div class="chips-grid">
            <button type="button" class="chip-btn selected" onclick="selectChip(this, 'lang', 'Yorùbá')">🟢 Yorùbá</button>
            <button type="button" class="chip-btn" onclick="selectChip(this, 'lang', 'Hausa')">🟢 Hausa</button>
            <button type="button" class="chip-btn" onclick="selectChip(this, 'lang', 'Igbo')">🟢 Igbo</button>
            <button type="button" class="chip-btn" onclick="selectChip(this, 'lang', 'Naija Pidgin')">🟢 Pidgin</button>
            <button type="button" class="chip-btn" onclick="selectChip(this, 'lang', 'English')">🟢 English</button>
          </div>
        </div>

        <!-- STEP 2: GESTATIONAL STAGE -->
        <div class="step-section">
          <div class="step-label">
            <span class="step-num-badge">2</span>
            <span>Current Stage of Pregnancy:</span>
          </div>
          <div class="chips-grid">
            <button type="button" class="chip-btn" onclick="selectChip(this, 'stage', '1st Trimester')">👶 1st Trimester (0–12w)</button>
            <button type="button" class="chip-btn selected" onclick="selectChip(this, 'stage', '2nd Trimester')">🤰 2nd Trimester (13–27w)</button>
            <button type="button" class="chip-btn" onclick="selectChip(this, 'stage', '3rd Trimester')">🤱 3rd Trimester (28–40w)</button>
            <button type="button" class="chip-btn" onclick="selectChip(this, 'stage', 'Postnatal')">🍼 Postnatal / New Mom</button>
          </div>
        </div>

        <!-- STEP 3: SYMPTOM INPUT -->
        <div class="step-section">
          <div class="step-label">
            <span class="step-num-badge">3</span>
            <span>Describe What You Are Feeling:</span>
          </div>

          <div class="tab-switch">
            <button type="button" class="tab-btn active" id="tab-voice" onclick="setMode('voice')">🎙️ Record Voice Note</button>
            <button type="button" class="tab-btn" id="tab-text" onclick="setMode('text')">✍️ Type Symptoms</button>
          </div>

          <!-- VOICE PANEL -->
          <div id="panel-voice">
            <div class="voice-recorder-card" id="recorder-card">
              <button type="button" class="mic-button" id="mic-btn" onclick="toggleRecording()">🎤</button>
              <div class="mic-status-title" id="mic-title">Tap microphone to speak</div>
              <div class="mic-status-desc" id="mic-desc">Speak naturally in your dialect for 10–30 seconds</div>
              
              <div class="audio-upload-alt">
                <span>Or select audio recording:</span>
                <input type="file" id="audio-file-input" accept="audio/*" style="font-size: 0.85rem;">
              </div>
            </div>
          </div>

          <!-- TEXT PANEL -->
          <div id="panel-text" style="display: none;">
            <textarea class="symptom-textarea" id="symptoms-input" placeholder="Type how you are feeling (e.g. 'Ori n fo mi gidigidi, oju mi n dudu' or 'I have severe headache and blurry vision, 7 months pregnant')..."></textarea>
            
            <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-light); margin-top: 0.65rem;">Tap to add common symptoms:</div>
            <div class="quick-symptom-tags">
              <button type="button" class="tag-btn" onclick="appendSymptom('Severe Headache & Blurry Vision')">⚠️ Severe Headache & Blurry Vision</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Vaginal Bleeding / Spotting')">🚨 Vaginal Bleeding</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('High Fever & Chills')">+ High Fever / Chills</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Baby Not Moving / Stop Kicking')">⚠️ Baby Not Moving</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Swollen Face & Hands')">+ Swollen Face/Hands</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Nausea & Morning Sickness')">+ Nausea / Morning Sickness</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Lower Abdominal Cramping')">+ Abdominal Cramping</button>
            </div>
          </div>
        </div>

        <!-- STEP 4: PHONE NUMBER -->
        <div class="step-section">
          <div class="step-label">
            <span class="step-num-badge">4</span>
            <span>Contact Number (Optional):</span>
          </div>
          <input type="tel" class="form-input" id="phone-input" value="+2348030004192" placeholder="+2348012345678">
        </div>

        <!-- CTA BUTTON -->
        <button type="button" class="btn-submit-triage" id="submit-btn" onclick="runTriage()">
          <span>Evaluate Maternal Symptoms (WHO RAG)</span>
          <span>→</span>
        </button>

      </div>

      <!-- RESULTS SECTION -->
      <div class="results-card" id="results-card">
        <div class="result-banner" id="res-banner">
          <div>
            <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">Obstetric Triage Classification</div>
            <div class="result-banner-title" id="res-title">Urgency Level</div>
          </div>
          <div class="result-banner-pill" id="res-tier-pill">Tier</div>
        </div>

        <div class="findings-grid">
          <div class="finding-item">
            <div class="finding-label">Chief Maternal Issue</div>
            <div class="finding-value" id="res-complaint">-</div>
          </div>
          <div class="finding-item">
            <div class="finding-label">Stage & Duration</div>
            <div class="finding-value" id="res-duration">-</div>
          </div>
          <div class="snomed-badge">
            <div class="finding-label" style="color: var(--primary);">SNOMED CT Clinical Standard</div>
            <div class="finding-value" style="color: var(--primary); font-family: 'JetBrains Mono', monospace;" id="res-snomed">-</div>
          </div>
        </div>

        <div class="rag-evidence-box" id="res-rag-box">
          <strong>📚 Retrieved WHO & Nigeria Clinical Guideline Evidence:</strong>
          <div id="res-rag-text" style="margin-top: 0.35rem;">-</div>
        </div>

        <div style="font-size: 0.82rem; font-weight: 800; color: var(--text-muted); margin-bottom: 0.45rem;">Clinical Guidance & Care Plan:</div>
        <div class="care-instructions-box" id="res-message">-</div>

        <div style="margin-top: 1.25rem; display: flex; gap: 0.75rem; flex-wrap: wrap;">
          <button type="button" class="tag-btn" style="padding: 0.65rem 1.25rem; font-size: 0.88rem;" onclick="resetAssessment()">🔄 New Assessment</button>
          <a href="https://t.me/afyavoice_bot" target="_blank" class="tag-btn" style="padding: 0.65rem 1.25rem; font-size: 0.88rem; background: #0284c7; color: #fff; text-decoration: none;">📱 Continue on Telegram</a>
          <button type="button" class="tag-btn" style="padding: 0.65rem 1.25rem; font-size: 0.88rem;" onclick="window.print()">🖨️ Print Summary</button>
        </div>
      </div>

    </div>

    <!-- RIGHT COLUMN: DANGER SIGNS & GOVERNANCE -->
    <aside class="sidebar-panel">
      
      <!-- RED FLAGS NOTICE -->
      <div class="info-card" style="border-top: 4px solid #ef4444;">
        <div class="info-card-header" style="color: #991b1b;">
          <span>🚨</span> Cardinal Obstetric Danger Signs
        </div>
        <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.85rem;">
          If a pregnant or newly delivered woman exhibits any of these signs, seek hospital care immediately:
        </p>
        <ul class="redflag-list">
          <li class="redflag-item"><span class="redflag-dot">•</span> <strong>Vaginal Bleeding:</strong> Even slight spotting in pregnancy requires urgent hospital evaluation.</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> <strong>Severe Headache with Blurred Vision:</strong> Warning sign of life-threatening pre-eclampsia.</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> <strong>Convulsions or Fits:</strong> Eclampsia requires immediate Magnesium Sulfate.</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> <strong>Fever with Foul Discharge:</strong> Risk of chorioamnionitis or puerperal sepsis.</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> <strong>Reduced Baby Movement:</strong> Less than 10 kicks over 2 hours during rest.</li>
        </ul>
        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px dashed var(--border); font-size: 0.85rem; font-weight: 700; color: #991b1b; text-align: center;">
          National Emergency: Call 112
        </div>
      </div>

      <!-- TELEGRAM BOT PROMO -->
      <div class="info-card" style="background: #f0f9ff; border-color: #bae6fd;">
        <div class="info-card-header" style="color: #0369a1;">
          <span>📱</span> AfyaMama on Telegram
        </div>
        <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 1rem;">
          Get 24/7 maternal voice triage, trimester tracking, and pregnancy care reminders on your phone without downloading any new app.
        </p>
        <a href="https://t.me/afyavoice_bot" target="_blank" style="background: #0284c7; color: #fff; text-decoration: none; padding: 0.75rem 1rem; border-radius: 10px; font-weight: 800; font-size: 0.88rem; display: block; text-align: center;">
          Open Telegram Bot 🚀
        </a>
      </div>

    </aside>

  </main>

  <script>
    let currentMode = 'voice';
    let selectedDialect = 'Yorùbá';
    let selectedStage = '2nd Trimester';
    let mediaRecorder = null;
    let audioChunks = [];
    let recordedAudioBlob = null;
    let recordTimer = null;
    let secondsCount = 0;

    function selectChip(btn, type, val) {
      btn.parentElement.querySelectorAll('.chip-btn').forEach(c => c.classList.remove('selected'));
      btn.classList.add('selected');
      if (type === 'lang') selectedDialect = val;
      if (type === 'stage') selectedStage = val;
    }

    function setMode(mode) {
      currentMode = mode;
      document.getElementById('tab-voice').classList.toggle('active', mode === 'voice');
      document.getElementById('tab-text').classList.toggle('active', mode === 'text');
      document.getElementById('panel-voice').style.display = mode === 'voice' ? 'block' : 'none';
      document.getElementById('panel-text').style.display = mode === 'text' ? 'block' : 'none';
    }

    function appendSymptom(tag) {
      const txt = document.getElementById('symptoms-input');
      txt.value = txt.value ? (txt.value + ', ' + tag) : tag;
      txt.focus();
    }

    async function toggleRecording() {
      const micBtn = document.getElementById('mic-btn');
      const micTitle = document.getElementById('mic-title');
      const micDesc = document.getElementById('mic-desc');
      const card = document.getElementById('recorder-card');

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
          mediaRecorder.onstop = () => {
            recordedAudioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            micTitle.innerText = 'Voice note recorded (' + secondsCount + 's)';
            micDesc.innerText = 'Ready for maternal clinical triage';
            card.classList.remove('recording');
          };

          mediaRecorder.start();
          micBtn.classList.add('recording');
          micBtn.innerText = '⏹';
          card.classList.add('recording');
          micTitle.innerText = 'Recording maternal voice...';
          secondsCount = 0;
          recordTimer = setInterval(() => {
            secondsCount++;
            micDesc.innerText = 'Recording: ' + secondsCount + 's • Speak naturally in ' + selectedDialect;
          }, 1000);
        } catch (err) {
          alert('Microphone access unavailable. Please use the "Type Symptoms" tab or select an audio file!');
        }
      } else {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(t => t.stop());
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
        clearInterval(recordTimer);
      }
    }

    async function runTriage() {
      const btn = document.getElementById('submit-btn');
      const phone = document.getElementById('phone-input').value.trim();

      btn.disabled = true;
      btn.innerHTML = '<div class="loading-spinner"></div> Cross-referencing WHO & Nigeria Guidelines...';

      let endpoint = '';
      let payload = null;

      if (currentMode === 'voice') {
        const fileInput = document.getElementById('audio-file-input');
        let uploadBlob = recordedAudioBlob;
        if (fileInput.files.length > 0) {
          uploadBlob = fileInput.files[0];
        }

        if (!uploadBlob) {
          alert('Please record a voice note or select an audio file first!');
          btn.disabled = false;
          btn.innerHTML = '<span>Evaluate Maternal Symptoms (WHO RAG)</span> <span>→</span>';
          return;
        }

        endpoint = '/api/triage/audio';
        const formData = new FormData();
        formData.append('audio_file', uploadBlob, 'consultation.wav');
        formData.append('phone_number', phone);
        formData.append('gestational_stage', selectedStage);
        payload = formData;
      } else {
        const symptomsText = document.getElementById('symptoms-input').value.trim();
        if (!symptomsText) {
          alert('Please enter symptoms before submitting.');
          btn.disabled = false;
          btn.innerHTML = '<span>Evaluate Maternal Symptoms (WHO RAG)</span> <span>→</span>';
          return;
        }
        endpoint = '/api/triage/text';
        payload = JSON.stringify({
          phone_number: phone,
          symptoms_text: symptomsText,
          gestational_stage: selectedStage
        });
      }

      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: currentMode === 'text' ? { 'Content-Type': 'application/json' } : {},
          body: payload
        });

        const data = await res.json();

        if (data.status === 'success') {
          const resultsCard = document.getElementById('results-card');
          resultsCard.style.display = 'block';

          const banner = document.getElementById('res-banner');
          const tier = data.triage_tier || 'GREEN';
          banner.className = 'result-banner ' + (tier === 'RED' ? 'red' : tier === 'YELLOW' ? 'yellow' : 'green');
          
          document.getElementById('res-title').innerText = data.triage_title || (tier + ' PRIORITY');
          document.getElementById('res-tier-pill').innerText = tier + ' PRIORITY';
          document.getElementById('res-complaint').innerText = data.chief_complaint || 'Maternal Consultation';
          document.getElementById('res-duration').innerText = (data.gestational_stage || selectedStage) + ' • ' + (data.duration || 'Recent');
          document.getElementById('res-snomed').innerText = (data.snomed_name || 'Clinical Concept') + ' (SNOMED ID: ' + (data.snomed_code || 'Standard') + ')';
          document.getElementById('res-message').innerText = data.patient_message;

          // Evidence
          const ragText = data.guideline_context ? data.guideline_context.substring(0, 320) + '...' : 'Verified against WHO Antenatal Care Standards (2016) & Nigeria FMOH Guidelines.';
          document.getElementById('res-rag-text').innerText = ragText;

          resultsCard.scrollIntoView({ behavior: 'smooth' });
        } else {
          alert('Triage check error: ' + (data.error || 'Unable to process.'));
        }
      } catch (err) {
        alert('Network error: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Evaluate Maternal Symptoms (WHO RAG)</span> <span>→</span>';
      }
    }

    function resetAssessment() {
      document.getElementById('results-card').style.display = 'none';
      document.getElementById('symptoms-input').value = '';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@router.post("/api/triage/audio")
async def process_audio_triage(
    audio_file: UploadFile = File(...),
    phone_number: str = Form(...),
    gestational_stage: Optional[str] = Form("Pregnancy")
):
    """Processes uploaded or recorded audio through the Maternal RAG pipeline."""
    try:
        temp_filename = f"portal_{uuid.uuid4().hex}_{audio_file.filename}"
        temp_path = os.path.join(TEMP_DIR, temp_filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        # 1. Speech to Text via N-ATLAS ASR
        transcription_result = await asr_client.transcribe(temp_path)
        transcript_text = transcription_result.get("text", "")

        # 2. Clinical Extraction via N-ATLAS LLM & Maternal RAG
        clinical_data = await llm_client.parse_clinical_data(transcript_text, gestational_stage=gestational_stage)

        # 3. Obstetric Triage Decision Engine
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
            "gestational_stage": clinical_data.gestational_stage,
            "danger_signs": clinical_data.danger_signs,
            "guideline_context": clinical_data.guideline_context,
            "detected_language": clinical_data.language_detected,
            "snomed_code": assessment.snomed_concept_code,
            "snomed_name": assessment.snomed_display_name,
            "patient_message": assessment.patient_message
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/api/triage/text")
async def process_text_triage(request: TextTriageRequest):
    """Processes typed maternal symptoms through Maternal RAG and Triage Engine."""
    try:
        # 1. Clinical Extraction via N-ATLAS LLM & Maternal RAG
        clinical_data = await llm_client.parse_clinical_data(request.symptoms_text, gestational_stage=request.gestational_stage)

        # 2. Obstetric Triage Decision Engine
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
            "gestational_stage": clinical_data.gestational_stage,
            "danger_signs": clinical_data.danger_signs,
            "guideline_context": clinical_data.guideline_context,
            "detected_language": clinical_data.language_detected,
            "snomed_code": assessment.snomed_concept_code,
            "snomed_name": assessment.snomed_display_name,
            "patient_message": assessment.patient_message
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
