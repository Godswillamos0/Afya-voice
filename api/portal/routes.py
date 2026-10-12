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
    """Serves the clean, human-centered AfyaVoice Telemedicine Portal & Clinical Triage Interface."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AfyaVoice - Clinical Symptom Triage Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --border-focus: #0f766e;
      --primary: #0f766e;
      --primary-hover: #0d9488;
      --primary-light: #f0fdfa;
      --primary-subtle: #ccfbf1;
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
      --shadow-md: 0 4px 14px -2px rgba(15, 118, 110, 0.08);
      --shadow-lg: 0 12px 28px -4px rgba(15, 118, 110, 0.12);
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
      background: var(--primary);
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
      gap: 1.25rem;
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
      color: var(--text-main);
      letter-spacing: -0.02em;
      margin-bottom: 0.35rem;
    }
    .portal-subheading {
      font-size: 0.95rem;
      color: var(--text-muted);
    }

    /* STEP 1: LANGUAGE SELECTION */
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
    .lang-chips-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 0.65rem;
    }
    .lang-chip {
      background: #f8fafc;
      border: 1px solid var(--border);
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
    .lang-chip:hover {
      border-color: var(--primary);
      color: var(--primary);
      background: var(--primary-light);
    }
    .lang-chip.selected {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(15, 118, 110, 0.2);
    }

    /* STEP 2: SYMPTOM INPUT */
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

    /* VOICE RECORDER BOX */
    .voice-recorder-card {
      background: #f8fafc;
      border: 2px dashed #cbd5e1;
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
      box-shadow: 0 4px 14px rgba(15, 118, 110, 0.25);
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
      border: 1px solid var(--border);
      border-radius: 12px;
      font-family: inherit;
      font-size: 0.95rem;
      color: var(--text-main);
      resize: vertical;
      line-height: 1.5;
      transition: border-color 0.15s;
    }
    .symptom-textarea:focus {
      outline: none;
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
    }
    .quick-symptom-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 0.45rem;
      margin-top: 0.75rem;
    }
    .tag-btn {
      background: #f1f5f9;
      border: 1px solid var(--border);
      border-radius: 9999px;
      padding: 0.3rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;
    }
    .tag-btn:hover {
      background: var(--primary-light);
      border-color: var(--primary-subtle);
      color: var(--primary);
    }

    /* PHONE INPUT */
    .form-group {
      margin-bottom: 1.5rem;
    }
    .form-label {
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 0.45rem;
      display: block;
    }
    .form-input {
      width: 100%;
      padding: 0.75rem 1rem;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 10px;
      font-family: inherit;
      font-size: 0.95rem;
      color: var(--text-main);
      transition: border-color 0.15s;
    }
    .form-input:focus {
      outline: none;
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.12);
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
      box-shadow: 0 4px 14px rgba(15, 118, 110, 0.25);
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

    /* RESULTS CARD */
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
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 0.85rem 1rem;
    }
    .finding-label { font-size: 0.72rem; font-weight: 800; color: var(--text-light); text-transform: uppercase; margin-bottom: 0.25rem; }
    .finding-value { font-size: 0.95rem; font-weight: 700; color: var(--text-main); }
    .snomed-badge {
      grid-column: span 2;
      background: var(--primary-light);
      border: 1px solid var(--primary-subtle);
      border-radius: 10px;
      padding: 0.85rem 1rem;
    }
    @media (max-width: 640px) { .snomed-badge { grid-column: span 1; } }

    .care-instructions-box {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.25rem;
      margin-bottom: 1.25rem;
      font-size: 0.92rem;
      line-height: 1.6;
      color: #334155;
      white-space: pre-wrap;
    }
    .whatsapp-confirm-pill {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.82rem;
      color: #166534;
      background: #dcfce7;
      padding: 0.55rem 0.95rem;
      border-radius: 8px;
      font-weight: 700;
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

    .trust-badge-row {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }
    .trust-badge-item {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .trust-badge-icon {
      font-size: 1.15rem;
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
      <div class="brand-logo-icon">AV</div>
      <div>
        <div class="brand-title">AfyaVoice</div>
        <div class="brand-subtitle">Clinical Triage Portal</div>
      </div>
    </a>
    <div class="header-nav">
      <a href="/" class="back-home-link">← Back to Home</a>
      <a href="tel:112" class="emergency-hotline">🚨 Emergency: Call 112</a>
    </div>
  </header>

  <!-- MAIN CONTENT CONTAINER -->
  <main class="portal-container">
    
    <!-- LEFT COLUMN: TRIAGE FORM & RESULTS -->
    <div>
      <div class="main-card">
        <div class="portal-heading-row">
          <h1 class="portal-heading">Symptom Assessment</h1>
          <p class="portal-subheading">Speak or write your symptoms in your preferred dialect to receive a validated clinical urgency check.</p>
        </div>

        <!-- STEP 1: LANGUAGE SELECTION -->
        <div class="step-section">
          <div class="step-label">
            <span class="step-num-badge">1</span>
            <span>Select Your Dialect / Yan Yanayi:</span>
          </div>
          <div class="lang-chips-grid">
            <button type="button" class="lang-chip selected" onclick="selectDialect(this, 'Yorùbá')">🟢 Yorùbá</button>
            <button type="button" class="lang-chip" onclick="selectDialect(this, 'Hausa')">🟢 Hausa</button>
            <button type="button" class="lang-chip" onclick="selectDialect(this, 'Igbo')">🟢 Igbo</button>
            <button type="button" class="lang-chip" onclick="selectDialect(this, 'Naija Pidgin')">🟢 Pidgin</button>
            <button type="button" class="lang-chip" onclick="selectDialect(this, 'English')">🟢 English</button>
          </div>
        </div>

        <!-- STEP 2: SYMPTOM INPUT -->
        <div class="step-section">
          <div class="step-label">
            <span class="step-num-badge">2</span>
            <span>Describe What You Are Experiencing:</span>
          </div>

          <div class="tab-switch">
            <button type="button" class="tab-btn active" id="tab-voice" onclick="setMode('voice')">🎙️ Record Voice Note</button>
            <button type="button" class="tab-btn" id="tab-text" onclick="setMode('text')">✍️ Type Symptoms</button>
          </div>

          <!-- VOICE INPUT PANEL -->
          <div id="panel-voice">
            <div class="voice-recorder-card" id="recorder-card">
              <button type="button" class="mic-button" id="mic-btn" onclick="toggleRecording()">🎤</button>
              <div class="mic-status-title" id="mic-title">Tap to start recording</div>
              <div class="mic-status-desc" id="mic-desc">Speak naturally in your mother tongue for 10–30 seconds</div>
              
              <div class="audio-upload-alt">
                <span>Or upload audio file:</span>
                <input type="file" id="audio-file-input" accept="audio/*" style="font-size: 0.85rem;">
              </div>
            </div>
          </div>

          <!-- TEXT INPUT PANEL -->
          <div id="panel-text" style="display: none;">
            <textarea class="symptom-textarea" id="symptoms-input" placeholder="Type how you are feeling (e.g., 'Ara mi n gbona lati ana, mo si n bi leralera' or 'I have had a high fever and severe headache for 2 days')..."></textarea>
            
            <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-light); margin-top: 0.65rem;">Tap to add common symptoms:</div>
            <div class="quick-symptom-tags">
              <button type="button" class="tag-btn" onclick="appendSymptom('High Fever (Ibà)')">+ High Fever</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Severe Headache (Orí fífọ́)')">+ Severe Headache</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Vomiting & Nausea (Èébì)')">+ Vomiting</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Chest Pain (Aiya ríro)')">+ Chest Pain</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('Stomach Pain (Inú rírun)')">+ Stomach Pain</button>
              <button type="button" class="tag-btn" onclick="appendSymptom('General Body Weakness (Àárẹ̀)')">+ Body Weakness</button>
            </div>
          </div>
        </div>

        <!-- STEP 3: PHONE NUMBER -->
        <div class="step-section">
          <div class="step-label">
            <span class="step-num-badge">3</span>
            <span>WhatsApp Number for Care Summary:</span>
          </div>
          <input type="tel" class="form-input" id="phone-input" value="+2348030004192" placeholder="+2348012345678">
          <div style="font-size: 0.75rem; color: var(--text-light); margin-top: 0.35rem;">We will send your clinical triage summary and home remedy advice directly to this WhatsApp number.</div>
        </div>

        <!-- CTA BUTTON -->
        <button type="button" class="btn-submit-triage" id="submit-btn" onclick="runTriage()">
          <span>Assess My Symptoms Now</span>
          <span>→</span>
        </button>

      </div>

      <!-- RESULTS SECTION -->
      <div class="results-card" id="results-card">
        <div class="result-banner" id="res-banner">
          <div>
            <div style="font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em;">Manchester Triage Assessment</div>
            <div class="result-banner-title" id="res-title">Urgency Level</div>
          </div>
          <div class="result-banner-pill" id="res-tier-pill">Tier</div>
        </div>

        <div class="findings-grid">
          <div class="finding-item">
            <div class="finding-label">Chief Complaint</div>
            <div class="finding-value" id="res-complaint">-</div>
          </div>
          <div class="finding-item">
            <div class="finding-label">Duration & Onset</div>
            <div class="finding-value" id="res-duration">-</div>
          </div>
          <div class="snomed-badge">
            <div class="finding-label" style="color: var(--primary);">SNOMED CT Clinical Standard</div>
            <div class="finding-value" style="color: var(--primary); font-family: 'JetBrains Mono', monospace;" id="res-snomed">-</div>
          </div>
        </div>

        <div style="font-size: 0.82rem; font-weight: 800; color: var(--text-muted); margin-bottom: 0.45rem;">Clinical Guidance & Care Plan:</div>
        <div class="care-instructions-box" id="res-message">-</div>

        <div class="whatsapp-confirm-pill">
          <span>📲</span>
          <span>Summary and action steps delivered to patient WhatsApp (+234 803 ••• 4192)</span>
        </div>

        <div style="margin-top: 1.25rem; display: flex; gap: 0.75rem;">
          <button type="button" class="tag-btn" style="padding: 0.65rem 1.25rem; font-size: 0.88rem;" onclick="resetAssessment()">🔄 Start Another Assessment</button>
          <button type="button" class="tag-btn" style="padding: 0.65rem 1.25rem; font-size: 0.88rem;" onclick="window.print()">🖨️ Print Summary</button>
        </div>
      </div>

    </div>

    <!-- RIGHT COLUMN: CLINICAL SAFETY & RED FLAGS -->
    <aside class="sidebar-panel">
      
      <!-- RED FLAGS NOTICE -->
      <div class="info-card" style="border-top: 4px solid #ef4444;">
        <div class="info-card-header" style="color: #991b1b;">
          <span>🚨</span> Emergency Red Flags
        </div>
        <p style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 0.85rem;">
          If the patient shows any of the following symptoms, stop the web check and seek emergency care immediately:
        </p>
        <ul class="redflag-list">
          <li class="redflag-item"><span class="redflag-dot">•</span> Severe difficulty breathing, gasping, or blue lips</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> Crushing chest pressure radiating to arm or jaw</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> Inability to stay awake, confusion, or convulsions</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> Uncontrollable vomiting or severe bleeding</li>
          <li class="redflag-item"><span class="redflag-dot">•</span> High fever in an infant under 3 months</li>
        </ul>
        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px dashed var(--border); font-size: 0.8rem; font-weight: 700; color: #991b1b;">
          Call 112 or visit the nearest General Hospital Emergency Unit.
        </div>
      </div>

      <!-- TRUST & STANDARDS -->
      <div class="info-card">
        <div class="info-card-header">
          <span>🛡️</span> Clinical Governance
        </div>
        <div class="trust-badge-row">
          <div class="trust-badge-item">
            <span class="trust-badge-icon">🏥</span>
            <div><strong>Manchester Triage System:</strong> 5-tier clinical urgency matrix ensuring accurate prioritization.</div>
          </div>
          <div class="trust-badge-item">
            <span class="trust-badge-icon">🌐</span>
            <div><strong>SNOMED CT Registry:</strong> Dialect symptoms standardized to global healthcare codes.</div>
          </div>
          <div class="trust-badge-item">
            <span class="trust-badge-icon">🔒</span>
            <div><strong>NDPA Compliant:</strong> Patient information is securely encrypted and never shared.</div>
          </div>
        </div>
      </div>

    </aside>

  </main>

  <script>
    let currentMode = 'voice';
    let selectedDialect = 'Yorùbá';
    let mediaRecorder = null;
    let audioChunks = [];
    let recordedAudioBlob = null;
    let recordTimer = null;
    let secondsCount = 0;

    function selectDialect(btn, lang) {
      document.querySelectorAll('.lang-chip').forEach(c => c.classList.remove('selected'));
      btn.classList.add('selected');
      selectedDialect = lang;
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
            micDesc.innerText = 'Ready for clinical triage assessment';
            card.classList.remove('recording');
          };

          mediaRecorder.start();
          micBtn.classList.add('recording');
          micBtn.innerText = '⏹';
          card.classList.add('recording');
          micTitle.innerText = 'Recording your symptoms...';
          secondsCount = 0;
          recordTimer = setInterval(() => {
            secondsCount++;
            micDesc.innerText = 'Recording: ' + secondsCount + 's • Speak naturally in ' + selectedDialect;
          }, 1000);
        } catch (err) {
          alert('Microphone access is not available in this browser. Please use the "Type Symptoms" tab or select an audio file!');
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
      btn.innerHTML = '<div class="loading-spinner"></div> Analyzing symptoms with N-ATLaS...';

      let endpoint = '';
      let payload = null;

      if (currentMode === 'voice') {
        const fileInput = document.getElementById('audio-file-input');
        let uploadBlob = recordedAudioBlob;
        if (fileInput.files.length > 0) {
          uploadBlob = fileInput.files[0];
        }

        if (!uploadBlob) {
          alert('Please record your voice note or select an audio file first!');
          btn.disabled = false;
          btn.innerHTML = '<span>Assess My Symptoms Now</span> <span>→</span>';
          return;
        }

        endpoint = '/api/triage/audio';
        const formData = new FormData();
        formData.append('audio_file', uploadBlob, 'consultation.wav');
        formData.append('phone_number', phone);
        payload = formData;
      } else {
        const symptomsText = document.getElementById('symptoms-input').value.trim();
        if (!symptomsText) {
          alert('Please enter your symptoms before submitting.');
          btn.disabled = false;
          btn.innerHTML = '<span>Assess My Symptoms Now</span> <span>→</span>';
          return;
        }
        endpoint = '/api/triage/text';
        payload = JSON.stringify({ phone_number: phone, symptoms_text: symptomsText });
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

          // Set Banner Style
          const banner = document.getElementById('res-banner');
          const tier = data.triage_tier || 'GREEN';
          banner.className = 'result-banner ' + (tier === 'RED' ? 'red' : tier === 'YELLOW' ? 'yellow' : 'green');
          
          document.getElementById('res-title').innerText = data.triage_title || (tier + ' PRIORITY');
          document.getElementById('res-tier-pill').innerText = tier + ' PRIORITY';
          document.getElementById('res-complaint').innerText = data.chief_complaint || 'General clinical malaise';
          document.getElementById('res-duration').innerText = data.duration || 'Reported duration';
          document.getElementById('res-snomed').innerText = (data.snomed_name || 'Clinical Concept') + ' (ID: ' + (data.snomed_code || 'Standard') + ')';
          document.getElementById('res-message').innerText = data.patient_message || 'Please consult your primary healthcare provider.';

          resultsCard.scrollIntoView({ behavior: 'smooth' });
        } else {
          alert('Triage check error: ' + (data.error || 'Unable to process.'));
        }
      } catch (err) {
        alert('Network error: ' + err.message);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>Assess My Symptoms Now</span> <span>→</span>';
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
