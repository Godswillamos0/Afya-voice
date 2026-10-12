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
    """Serves the authentic AfyaVoice Sovereign Telemedicine Portal & Clinical Triage Interface."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AfyaVoice - Dedicated Voice-First Clinical Triage</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #edf7f2;
      --card-bg: #ffffff;
      --border-color: #d1e7dd;
      --primary-dark: #064e3b;
      --primary: #0d6045;
      --primary-hover: #0a4d37;
      --primary-light: #e6f6ee;
      --accent-mint: #d1fae5;
      --accent-mint-text: #065f46;
      --text-main: #13271f;
      --text-muted: #526b60;
      --text-light: #7c988d;
      --danger-bg: #fee2e2;
      --danger-text: #991b1b;
      --danger-border: #fecaca;
      --warning-bg: #fef3c7;
      --warning-text: #92400e;
      --shadow-sm: 0 1px 3px rgba(13, 96, 69, 0.05);
      --shadow-md: 0 4px 14px rgba(13, 96, 69, 0.08);
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      line-height: 1.5;
    }

    /* TOP GLOBAL NAVBAR */
    .top-nav {
      background: #ffffff;
      border-bottom: 1px solid var(--border-color);
      padding: 0.65rem 1.75rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: var(--shadow-sm);
    }
    .brand-section { display: flex; align-items: center; gap: 0.85rem; }
    .brand-logo-icon {
      width: 38px;
      height: 38px;
      background: var(--primary);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 1.15rem;
    }
    .brand-text h1 { font-size: 1.25rem; font-weight: 800; color: var(--primary-dark); line-height: 1.1; }
    .brand-text span { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); letter-spacing: 0.08em; text-transform: uppercase; }
    
    .status-badge-active {
      background: var(--primary-light);
      color: var(--primary);
      font-weight: 700;
      font-size: 0.78rem;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      border: 1px solid var(--border-color);
    }
    .dot-live { width: 7px; height: 7px; border-radius: 50%; background: #10b981; animation: blink 1.6s infinite; }
    @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

    .nav-links { display: flex; align-items: center; gap: 0.4rem; }
    .nav-tab {
      background: transparent;
      border: none;
      font-family: inherit;
      font-size: 0.88rem;
      font-weight: 600;
      color: var(--text-muted);
      padding: 0.5rem 0.95rem;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .nav-tab:hover { background: var(--primary-light); color: var(--primary-dark); }
    .nav-tab.active { background: var(--primary); color: #ffffff; }

    .nav-right { display: flex; align-items: center; gap: 1rem; }
    .emergency-pill {
      background: var(--danger-bg);
      color: var(--danger-text);
      border: 1px solid var(--danger-border);
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }
    .lang-selector {
      background: #f8fafc;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 0.35rem 0.65rem;
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-main);
      cursor: pointer;
    }
    .user-profile {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      padding-left: 0.5rem;
      border-left: 1px solid var(--border-color);
    }
    .user-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #0284c7;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 0.85rem;
    }
    .user-info { text-align: right; line-height: 1.15; }
    .user-phone { font-size: 0.8rem; font-weight: 700; color: var(--text-main); }
    .user-tag { font-size: 0.68rem; color: #059669; font-weight: 700; }

    /* TELEMETRY BANNER */
    .telemetry-bar {
      background: #e3f2ea;
      border-bottom: 1px solid var(--border-color);
      padding: 0.45rem 1.75rem;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 1.25rem;
      font-size: 0.78rem;
      color: var(--text-muted);
      font-weight: 600;
    }
    .telemetry-item { display: flex; align-items: center; gap: 0.4rem; }
    .telemetry-pill {
      background: #ffffff;
      padding: 0.15rem 0.55rem;
      border-radius: 6px;
      border: 1px solid var(--border-color);
      color: var(--primary-dark);
      font-weight: 700;
    }

    /* MAIN CONTAINER LAYOUT */
    .main-wrapper {
      max-width: 1360px;
      margin: 1.5rem auto;
      padding: 0 1.5rem;
      width: 100%;
      display: grid;
      grid-template-columns: 1.85fr 1fr;
      gap: 1.5rem;
      flex: 1;
    }
    @media (max-width: 1024px) { .main-wrapper { grid-template-columns: 1fr; } }

    /* WHITE CARDS */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 1.5rem;
      box-shadow: var(--shadow-sm);
    }

    /* LEFT COLUMN HEADER */
    .triage-header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }
    .pill-session {
      background: var(--accent-mint);
      color: var(--accent-mint-text);
      font-size: 0.75rem;
      font-weight: 800;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      letter-spacing: 0.04em;
    }
    .ticket-id { font-size: 0.82rem; font-weight: 600; color: var(--text-muted); margin-left: 0.4rem; }
    
    .speed-controls {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      background: #f1f5f9;
      padding: 0.2rem 0.35rem;
      border-radius: 8px;
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-muted);
    }
    .speed-btn {
      background: #ffffff;
      border: 1px solid #cbd5e1;
      padding: 0.15rem 0.45rem;
      border-radius: 5px;
      cursor: pointer;
      font-weight: 700;
      color: var(--text-main);
    }

    .page-title {
      font-size: 1.45rem;
      font-weight: 800;
      color: var(--primary-dark);
      letter-spacing: -0.02em;
      margin-bottom: 1.25rem;
    }

    /* DIALECT SELECTOR */
    .dialect-label {
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-muted);
      margin-bottom: 0.5rem;
    }
    .dialect-group {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
    }
    .dialect-chip {
      background: #f8fafc;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-family: inherit;
      font-size: 0.85rem;
      font-weight: 700;
      padding: 0.45rem 1rem;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .dialect-chip:hover { border-color: var(--primary); color: var(--primary); }
    .dialect-chip.selected {
      background: var(--primary);
      border-color: var(--primary);
      color: #ffffff;
    }

    /* PATIENT VOICE PLAYBACK CARD */
    .voice-call-card {
      background: #f9fbf9;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 1.25rem;
      margin-bottom: 1.25rem;
    }
    .caller-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    .caller-meta { display: flex; align-items: center; gap: 0.75rem; }
    .caller-icon {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: var(--primary-light);
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.1rem;
    }
    .caller-name { font-size: 0.95rem; font-weight: 800; color: var(--text-main); }
    .caller-time { font-size: 0.75rem; color: var(--text-light); }
    .tag-call-source {
      background: #e2e8f0;
      color: #475569;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.15rem 0.5rem;
      border-radius: 4px;
      margin-left: 0.4rem;
    }
    .audio-length-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      font-weight: 700;
      background: #d1fae5;
      color: #065f46;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
    }

    /* CUSTOM AUDIO PLAYER / RECORDER */
    .player-row {
      display: flex;
      align-items: center;
      gap: 1rem;
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 0.75rem 1rem;
      margin-bottom: 1rem;
    }
    .play-btn-circle {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      background: var(--primary);
      color: #fff;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 1rem;
      flex-shrink: 0;
      transition: transform 0.15s;
    }
    .play-btn-circle:hover { background: var(--primary-hover); transform: scale(1.05); }
    
    .wave-bars {
      flex: 1;
      height: 28px;
      display: flex;
      align-items: center;
      gap: 3px;
    }
    .wave-bar {
      width: 3px;
      background: #94a3b8;
      border-radius: 2px;
      height: 8px;
    }
    .wave-bar.active { background: var(--primary); height: 22px; }
    .wave-bar:nth-child(2) { height: 14px; }
    .wave-bar:nth-child(3) { height: 24px; background: var(--primary); }
    .wave-bar:nth-child(4) { height: 18px; background: var(--primary); }
    .wave-bar:nth-child(5) { height: 12px; }
    .wave-bar:nth-child(6) { height: 20px; background: var(--primary); }
    .wave-bar:nth-child(7) { height: 26px; background: var(--primary); }
    .wave-bar:nth-child(8) { height: 16px; }
    .wave-bar:nth-child(9) { height: 10px; }
    .wave-bar:nth-child(10) { height: 22px; background: var(--primary); }

    .player-timestamp {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: var(--text-muted);
      font-weight: 600;
    }

    /* TRANSCRIPT CONTAINER */
    .transcript-box {
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 1rem 1.15rem;
    }
    .transcript-title-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }
    .transcript-label {
      font-size: 0.75rem;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }
    .btn-toggle-trans {
      background: none;
      border: none;
      color: var(--primary);
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
    }
    .transcript-text {
      font-size: 0.95rem;
      color: var(--text-main);
      font-style: italic;
      line-height: 1.55;
    }
    .translation-subtext {
      margin-top: 0.65rem;
      padding-top: 0.65rem;
      border-top: 1px dashed var(--border-color);
      font-size: 0.85rem;
      color: var(--text-muted);
      font-style: normal;
    }

    /* ACTION & LIVE CONSULTATION CONTROLS */
    .interactive-panel {
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 1.25rem;
      margin-top: 1.25rem;
    }
    .tabs-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
    .tab-toggle-btn {
      background: #f1f5f9;
      border: 1px solid transparent;
      padding: 0.45rem 0.85rem;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--text-muted);
      cursor: pointer;
    }
    .tab-toggle-btn.active {
      background: var(--primary);
      color: #fff;
    }
    .record-controls {
      display: flex;
      align-items: center;
      gap: 1rem;
      padding: 1rem;
      background: #f8fafc;
      border: 1px dashed var(--border-color);
      border-radius: 12px;
      margin-bottom: 1rem;
    }
    .btn-mic-round {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: var(--primary);
      border: none;
      color: #fff;
      font-size: 1.2rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }
    .btn-mic-round.recording { background: var(--danger-text); animation: pulse 1s infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.85; transform: scale(1.08); } }
    
    .input-field {
      width: 100%;
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 0.65rem 0.85rem;
      font-family: inherit;
      font-size: 0.88rem;
      color: var(--text-main);
      margin-bottom: 0.85rem;
    }
    .input-field:focus { outline: none; border-color: var(--primary); }
    textarea.input-field { min-height: 80px; resize: vertical; }

    .btn-submit-triage {
      width: 100%;
      background: var(--primary);
      color: #ffffff;
      border: none;
      padding: 0.85rem;
      border-radius: 10px;
      font-size: 0.95rem;
      font-weight: 800;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      box-shadow: 0 2px 8px rgba(13, 96, 69, 0.2);
    }
    .btn-submit-triage:hover { background: var(--primary-hover); }

    /* RIGHT COLUMN: CITIZEN RECORD & GUARDRAILS */
    .sidebar-col { display: flex; flex-direction: column; gap: 1.25rem; }
    
    .citizen-card {
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 1.5rem;
    }
    .citizen-card-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
    }
    .label-meta-title { font-size: 0.72rem; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .badge-synced {
      background: #e0f2fe;
      color: #0369a1;
      font-size: 0.72rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
    }
    .citizen-profile-row {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }
    .citizen-avatar-box {
      width: 58px;
      height: 58px;
      border-radius: 12px;
      background: #0d9488;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.4rem;
      flex-shrink: 0;
    }
    .citizen-title-name { font-size: 1.15rem; font-weight: 800; color: var(--text-main); line-height: 1.2; }
    .citizen-location { font-size: 0.8rem; color: var(--text-muted); margin-top: 0.15rem; }
    .citizen-gsm { font-size: 0.78rem; color: var(--primary); font-weight: 700; margin-top: 0.15rem; }

    .quota-box {
      background: var(--primary-light);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 0.85rem 1rem;
    }
    .quota-header-row { display: flex; justify-content: space-between; font-size: 0.78rem; font-weight: 700; color: var(--primary-dark); margin-bottom: 0.4rem; }
    .progress-bar-bg { width: 100%; height: 6px; background: #c6e6d6; border-radius: 4px; overflow: hidden; margin-bottom: 0.4rem; }
    .progress-fill { width: 65%; height: 100%; background: var(--primary); }
    .quota-footer-row { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--text-muted); font-weight: 600; }
    .quota-highlight { color: #b91c1c; font-weight: 800; }

    /* GUARDRAILS CARD */
    .guardrails-card {
      background: #ffffff;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 1.5rem;
    }
    .guardrails-title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.95rem;
      font-weight: 800;
      color: var(--primary-dark);
      margin-bottom: 0.5rem;
    }
    .guardrails-desc { font-size: 0.82rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 1rem; }
    
    .protocol-box {
      background: #f0fdf4;
      border: 1px solid #bbf7d0;
      border-radius: 10px;
      padding: 0.85rem;
      margin-bottom: 0.75rem;
    }
    .protocol-title { font-size: 0.82rem; font-weight: 800; color: #166534; display: flex; align-items: center; gap: 0.35rem; }
    .protocol-desc { font-size: 0.75rem; color: #374151; margin-top: 0.2rem; }

    /* LIVE RESULTS MODAL / CARD */
    .triage-output-card {
      display: none;
      background: #ffffff;
      border: 2px solid var(--primary);
      border-radius: var(--radius-lg);
      padding: 1.25rem;
      margin-top: 1.25rem;
      box-shadow: var(--shadow-md);
    }
    .badge-tier-red { background: var(--danger-bg); color: var(--danger-text); border: 1px solid var(--danger-border); }
    .badge-tier-yellow { background: var(--warning-bg); color: var(--warning-text); border: 1px solid #fde68a; }
    .badge-tier-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }

    .loader-ring {
      border: 3px solid rgba(255,255,255,0.3);
      border-top: 3px solid #fff;
      border-radius: 50%;
      width: 18px;
      height: 18px;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
  </style>
</head>
<body>

  <!-- 1. TOP GLOBAL NAVBAR -->
  <header class="top-nav">
    <div class="brand-section">
      <div class="brand-logo-icon">AV</div>
      <div class="brand-text">
        <h1>AfyaVoice</h1>
        <span>N-ATLAS SOVEREIGN HEALTH</span>
      </div>
      <div class="status-badge-active">
        <div class="dot-live"></div>
        N-ATLAS Voice Active
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="nav-links">
      <button class="nav-tab active">Voice Triage</button>
      <button class="nav-tab">Care Plan & Remedy</button>
      <button class="nav-tab">Doctor Consult</button>
      <button class="nav-tab">Micro-Pass & Airtime</button>
      <button class="nav-tab">Clinic Finder</button>
    </div>

    <!-- Right Controls -->
    <div class="nav-right">
      <div class="emergency-pill">
        <span>*</span> Emergency: 112 / 0800-AFYA
      </div>
      <select class="lang-selector">
        <option>English</option>
        <option>Yorùbá</option>
        <option>Hausa</option>
        <option>Igbo</option>
        <option>Naija Pidgin</option>
      </select>
      <div class="user-profile">
        <div class="user-info">
          <div class="user-phone">+234 803 ••• 4192</div>
          <div class="user-tag">Verified Citizen</div>
        </div>
        <div class="user-avatar">MB</div>
      </div>
    </div>
  </header>

  <!-- 2. NETWORK TELEMETRY BANNER -->
  <div class="telemetry-bar">
    <div class="telemetry-item">
      <span>●</span> Edge Sovereign NLP: <strong>Oyo Zone (Node #04)</strong>
    </div>
    <div class="telemetry-item">
      <span>((•))</span> 2G/EDGE Optimized Audio Codec <strong>(AMR-WB 12.65 kbps)</strong>
    </div>
    <div class="telemetry-item">
      <span>🔒</span> End-to-End Clinical Encryption (NDPR Sovereign)
    </div>
    <div class="telemetry-item" style="margin-left: auto;">
      <span>👨‍⚕️</span> <strong>3 GP Tele-Triage Doctors Online</strong>
    </div>
  </div>

  <!-- 3. MAIN DASHBOARD CONTENT -->
  <div class="main-wrapper">
    
    <!-- LEFT COLUMN: VOICE-FIRST CLINICAL TRIAGE -->
    <div>
      <div class="card">
        
        <div class="triage-header-row">
          <div style="display: flex; align-items: center;">
            <span class="pill-session">SESSION ACTIVE</span>
            <span class="ticket-id">Triage Ticket: #NG-IBD-8942</span>
          </div>
          <div class="speed-controls">
            <span>⏱ Speed:</span>
            <button class="speed-btn">1.0x</button>
            <button class="speed-btn" style="color: var(--text-muted); border: none; background: transparent;">0.8x (Elderly)</button>
          </div>
        </div>

        <h2 class="page-title">Dedicated Voice-First Clinical Triage</h2>

        <!-- DIALECT SELECTOR -->
        <div class="dialect-label">Select Consultation Dialect (Èka èdè re):</div>
        <div class="dialect-group">
          <button class="dialect-chip selected" onclick="selectDialect(this, 'Yorùbá')">✔ Yorùbá</button>
          <button class="dialect-chip" onclick="selectDialect(this, 'Hausa')">Hausa</button>
          <button class="dialect-chip" onclick="selectDialect(this, 'Igbo')">Igbo</button>
          <button class="dialect-chip" onclick="selectDialect(this, 'Naija Pidgin')">Naija Pidgin</button>
          <button class="dialect-chip" onclick="selectDialect(this, 'English')">English</button>
        </div>

        <!-- VOICE NOTE CALLER CARD -->
        <div class="voice-call-card">
          <div class="caller-header">
            <div class="caller-meta">
              <div class="caller-icon">👤</div>
              <div>
                <div class="caller-name">Mama Bisi (Patient) <span class="tag-call-source">Caller Voice</span></div>
                <div class="caller-time">Yesterday 16:42 • Recorded via Sovereign Audio Engine</div>
              </div>
            </div>
            <div class="audio-length-badge" id="duration-badge">0:34 / 2:00</div>
          </div>

          <!-- AUDIO WAVEFORM PLAYER -->
          <div class="player-row">
            <button class="play-btn-circle" id="btn-play-audio" onclick="playAudioDemo()">▶</button>
            <div class="wave-bars">
              <div class="wave-bar active"></div><div class="wave-bar"></div><div class="wave-bar active"></div>
              <div class="wave-bar active"></div><div class="wave-bar"></div><div class="wave-bar active"></div>
              <div class="wave-bar active"></div><div class="wave-bar"></div><div class="wave-bar"></div>
              <div class="wave-bar active"></div><div class="wave-bar"></div><div class="wave-bar active"></div>
              <div class="wave-bar"></div><div class="wave-bar active"></div><div class="wave-bar active"></div>
              <div class="wave-bar"></div><div class="wave-bar active"></div><div class="wave-bar"></div>
            </div>
            <div class="player-timestamp" id="player-time">0:14 / 0:34</div>
            <audio id="real-audio-player" style="display: none;"></audio>
          </div>

          <!-- TRANSCRIPT BOX -->
          <div class="transcript-box">
            <div class="transcript-title-row">
              <span class="transcript-label" id="transcript-heading">ORIGINAL YORÙBÁ TRANSCRIPT</span>
              <button class="btn-toggle-trans" onclick="toggleTranslation()">文A Toggle English Translation</button>
            </div>
            <div class="transcript-text" id="transcript-content">
              "Ara mi n gbona ti n si n bi leralera lati ana. Mi o le je ounje rara, gbogbo ara mi lo n ro mi, oju mi si n dudu..."
            </div>
            <div class="translation-subtext" id="translation-content">
              <strong>English Clinical Translation:</strong> "My body has been burning with fever and I have been vomiting continuously since yesterday. I cannot eat any food, my entire body aches, and I feel dizzy..."
            </div>
          </div>
        </div>

        <!-- INTERACTIVE RECORDING & CONSULTATION PANEL -->
        <div class="interactive-panel">
          <div class="tabs-row">
            <button class="tab-toggle-btn active" id="tab-voice-btn" onclick="switchInputMode('voice')">🎙️ Record Live Voice</button>
            <button class="tab-toggle-btn" id="tab-text-btn" onclick="switchInputMode('text')">💬 Type Symptoms Text</button>
          </div>

          <div id="panel-voice-record">
            <div class="record-controls">
              <button class="btn-mic-round" id="mic-record-btn" onclick="toggleMicRecording()">🎤</button>
              <div>
                <div style="font-weight: 700; font-size: 0.95rem;" id="mic-status-title">Click microphone to record your voice</div>
                <div style="font-size: 0.78rem; color: var(--text-muted);" id="mic-timer-text">Speak symptoms in Yoruba, Hausa, Igbo, Pidgin, or English</div>
              </div>
            </div>
            <input type="file" id="portal-file-upload" class="input-field" accept="audio/*">
          </div>

          <div id="panel-text-record" style="display: none;">
            <textarea id="portal-text-input" class="input-field" placeholder="Describe symptoms e.g., 'Aiya n dun mi ati fever lati ana' or 'I have severe chest pain and breathlessness'"></textarea>
          </div>

          <input type="text" id="portal-phone-input" class="input-field" value="+2348030004192" placeholder="Patient Phone Number (+234...)">

          <button class="btn-submit-triage" id="btn-submit-triage" onclick="submitClinicalTriage()">
            <span>Execute N-ATLAS Sovereign Clinical Triage</span>
          </button>
        </div>

        <!-- REAL-TIME TRIAGE DIAGNOSIS RESULT CARD -->
        <div class="triage-output-card" id="output-triage-card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem;">
            <div style="font-weight: 800; font-size: 1.05rem; color: var(--primary-dark);">🏥 N-ATLAS Clinical Triage Assessment</div>
            <span id="res-triage-badge" style="font-weight: 800; font-size: 0.78rem; padding: 0.3rem 0.75rem; border-radius: 9999px;">URGENCY</span>
          </div>

          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-bottom: 1rem;">
            <div style="background: #f8fafc; border: 1px solid var(--border-color); padding: 0.65rem 0.85rem; border-radius: 8px;">
              <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">CHIEF COMPLAINT</div>
              <div id="res-complaint" style="font-weight: 800; color: var(--text-main);">-</div>
            </div>
            <div style="background: #f8fafc; border: 1px solid var(--border-color); padding: 0.65rem 0.85rem; border-radius: 8px;">
              <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">DURATION & ONSET</div>
              <div id="res-duration" style="font-weight: 800; color: var(--text-main);">-</div>
            </div>
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 0.65rem 0.85rem; border-radius: 8px; grid-column: span 2;">
              <div style="font-size: 0.7rem; color: #166534; font-weight: 700;">SNOMED CT CONCEPT CODE</div>
              <div id="res-snomed" style="font-family: monospace; font-weight: 800; color: #047857; font-size: 0.9rem;">-</div>
            </div>
          </div>

          <div style="background: #ffffff; border: 1px solid var(--border-color); border-radius: 10px; padding: 1rem; font-size: 0.88rem; white-space: pre-wrap; line-height: 1.5; color: #1e293b;" id="res-whatsapp-msg">
            -
          </div>
        </div>

      </div>
    </div>

    <!-- RIGHT COLUMN: CITIZEN RECORD & SAFETY PROTOCOLS -->
    <div class="sidebar-col">
      
      <!-- CITIZEN RECORD -->
      <div class="citizen-card">
        <div class="citizen-card-head">
          <span class="label-meta-title">CITIZEN TRIAGE RECORD</span>
          <span class="badge-synced">Synced via USSD</span>
        </div>

        <div class="citizen-profile-row">
          <div class="citizen-avatar-box">MB</div>
          <div>
            <div class="citizen-title-name">Mama Bisi</div>
            <div class="citizen-location">Bodija Market Trader • Ibadan, Oyo State</div>
            <div class="citizen-gsm">Verified GSM: 0803 ••• 4192</div>
          </div>
        </div>

        <!-- VOICE PASS QUOTA -->
        <div class="quota-box">
          <div class="quota-header-row">
            <span>Active Sovereign Voice Pass:</span>
            <span>Instant Pass</span>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-fill"></div>
          </div>
          <div class="quota-footer-row">
            <span>Remaining Allocation:</span>
            <span class="quota-highlight">1 Exchange Left</span>
          </div>
        </div>
      </div>

      <!-- CLINICAL SAFETY GUARDRAILS -->
      <div class="guardrails-card">
        <div class="guardrails-title">
          <span>🛡️</span> Clinical Safety Guardrails
        </div>
        <p class="guardrails-desc">
          Strict regulatory protocols enforced by the Federal Ministry of Health (FMoH) and NAFDAC clinical algorithms:
        </p>

        <div class="protocol-box">
          <div class="protocol-title">
            <span>✅</span> NAFDAC Approved Protocol
          </div>
          <div class="protocol-desc">
            Evidence-based triage standard algorithms for malaria, enteric fever, and respiratory distress.
          </div>
        </div>

        <div class="protocol-box" style="background: #f8fafc; border-color: #e2e8f0;">
          <div class="protocol-title" style="color: #0369a1;">
            <span>🔬</span> Manchester Triage System (MTS)
          </div>
          <div class="protocol-desc">
            Certified 5-level clinical urgency discriminator matrix (Version 3.2-MDCN).
          </div>
        </div>

        <div class="protocol-box" style="background: #fdf4ff; border-color: #f0abfc;">
          <div class="protocol-title" style="color: #86198f;">
            <span>🌐</span> Sovereign SNOMED CT Registry
          </div>
          <div class="protocol-desc">
            Indigenous terminology mapping across Yoruba, Hausa, Igbo, and Naija Pidgin dialects.
          </div>
        </div>
      </div>

    </div>

  </div>

  <script>
    let activeInputMode = 'voice';
    let selectedDialect = 'Yorùbá';
    let mediaRecorder = null;
    let audioChunks = [];
    let recordedBlob = null;
    let timerInterval = null;
    let secondsElapsed = 0;

    function selectDialect(btn, dialect) {
      document.querySelectorAll('.dialect-chip').forEach(c => {
        c.classList.remove('selected');
        c.innerText = c.innerText.replace('✔ ', '');
      });
      btn.classList.add('selected');
      btn.innerText = '✔ ' + dialect;
      selectedDialect = dialect;
      document.getElementById('transcript-heading').innerText = 'ORIGINAL ' + dialect.toUpperCase() + ' TRANSCRIPT';
    }

    function switchInputMode(mode) {
      activeInputMode = mode;
      document.getElementById('tab-voice-btn').classList.toggle('active', mode === 'voice');
      document.getElementById('tab-text-btn').classList.toggle('active', mode === 'text');
      document.getElementById('panel-voice-record').style.display = mode === 'voice' ? 'block' : 'none';
      document.getElementById('panel-text-record').style.display = mode === 'text' ? 'block' : 'none';
    }

    function toggleTranslation() {
      const transEl = document.getElementById('translation-content');
      transEl.style.display = transEl.style.display === 'none' ? 'block' : 'none';
    }

    function playAudioDemo() {
      const btn = document.getElementById('btn-play-audio');
      if (btn.innerText === '▶') {
        btn.innerText = '⏸';
      } else {
        btn.innerText = '▶';
      }
    }

    async function toggleMicRecording() {
      const micBtn = document.getElementById('mic-record-btn');
      const statusTitle = document.getElementById('mic-status-title');
      const timerText = document.getElementById('mic-timer-text');

      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          mediaRecorder = new MediaRecorder(stream);
          audioChunks = [];

          mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data); };
          mediaRecorder.onstop = () => {
            recordedBlob = new Blob(audioChunks, { type: 'audio/wav' });
            statusTitle.innerText = 'Voice note recorded successfully!';
            timerText.innerText = 'Duration: ' + secondsElapsed + 's • Ready to triage.';
          };

          mediaRecorder.start();
          micBtn.classList.add('recording');
          micBtn.innerText = '⏹';
          statusTitle.innerText = 'Recording patient speech...';
          secondsElapsed = 0;
          timerInterval = setInterval(() => {
            secondsElapsed++;
            timerText.innerText = 'Recording: ' + secondsElapsed + 's (Speak clearly)';
          }, 1000);
        } catch (err) {
          alert('Microphone access denied. You can select an audio file or use the text tab!');
        }
      } else {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        micBtn.classList.remove('recording');
        micBtn.innerText = '🎤';
        clearInterval(timerInterval);
      }
    }

    async function submitClinicalTriage() {
      const submitBtn = document.getElementById('btn-submit-triage');
      const phone = document.getElementById('portal-phone-input').value.trim();

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<div class="loader-ring"></div> Running N-ATLAS Sovereign Engine...';

      let endpoint = '';
      let payload = null;

      if (activeInputMode === 'voice') {
        const fileInput = document.getElementById('portal-file-upload');
        let fileToUpload = recordedBlob;
        if (fileInput.files.length > 0) {
          fileToUpload = fileInput.files[0];
        }

        if (!fileToUpload) {
          alert('Please record a voice note or choose an audio file first!');
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Execute N-ATLAS Sovereign Clinical Triage</span>';
          return;
        }

        endpoint = '/api/triage/audio';
        const formData = new FormData();
        formData.append('audio_file', fileToUpload, 'consultation.wav');
        formData.append('phone_number', phone);
        payload = formData;
      } else {
        const textSymptoms = document.getElementById('portal-text-input').value.trim();
        if (!textSymptoms) {
          alert('Please type patient symptoms!');
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>Execute N-ATLAS Sovereign Clinical Triage</span>';
          return;
        }
        endpoint = '/api/triage/text';
        payload = JSON.stringify({ phone_number: phone, symptoms_text: textSymptoms });
      }

      try {
        const res = await fetch(endpoint, {
          method: 'POST',
          headers: activeInputMode === 'text' ? { 'Content-Type': 'application/json' } : {},
          body: payload
        });

        const data = await res.json();

        if (data.status === 'success') {
          // Display Output Card
          const outCard = document.getElementById('output-triage-card');
          outCard.style.display = 'block';

          // Update Triage Badge
          const badgeEl = document.getElementById('res-triage-badge');
          badgeEl.innerText = data.triage_title || (data.triage_tier + ' PRIORITY');
          badgeEl.className = data.triage_tier === 'RED' ? 'badge-tier-red' : data.triage_tier === 'YELLOW' ? 'badge-tier-yellow' : 'badge-tier-green';

          // Populate Fields
          document.getElementById('res-complaint').innerText = data.chief_complaint || 'N/A';
          document.getElementById('res-duration').innerText = data.duration || 'N/A';
          document.getElementById('res-snomed').innerText = (data.snomed_name || 'Clinical Finding') + ' (SNOMED ID: ' + (data.snomed_code || 'Standard') + ')';
          document.getElementById('res-whatsapp-msg').innerText = data.patient_message;

          // Update Transcript in Player Card if text was processed
          if (data.transcript) {
            document.getElementById('transcript-content').innerText = '"' + data.transcript + '"';
          }

          outCard.scrollIntoView({ behavior: 'smooth' });
        } else {
          alert('Triage processing failed: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Connection error: ' + err.message);
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Execute N-ATLAS Sovereign Clinical Triage</span>';
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
