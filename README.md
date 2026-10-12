# AfyaVoice (Sovereign Multilingual Healthcare Voice Triage)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB.svg?logo=python)](https://python.org)
[![Model](https://img.shields.io/badge/LLM-N--ATLaS%20(Llama--3%208B)-FF6F00.svg)](https://huggingface.co/NCAIR1/N-ATLaS)
[![Clinical](https://img.shields.io/badge/Standards-MTS%20%7C%20SNOMED%20CT-0284C7.svg)](https://www.snomed.org)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20FMCIDE-gray.svg)](#)

> **AfyaVoice** is Nigeria's sovereign multilingual clinical voice triage and telemedicine platform. It bridges the gap between everyday Nigerian local languages (**Yoruba, Hausa, Igbo, Nigerian Pidgin, and English**) and professional healthcare by combining sovereign indigenous AI with international clinical triage standards (**Manchester Triage System & SNOMED CT**).

---

## 🏥 Platform Overview & Purpose

Millions of Nigerians face barriers in accessing primary healthcare due to language mismatch, high emergency room congestion, and low physician density. AfyaVoice allows patients to submit health complaints using their own voice or text messages.

1. **Indigenous Linguistic Comprehension:** Powered by **N-ATLaS-LLM** (an indigenous fine-tune of Llama-3 8B developed by Awarri Technologies and the Federal Ministry of Communications, Innovation and Digital Economy - FMCIDE).
2. **Clinical Safety by Design:** Pure generative AI is never allowed to hallucinate medical advice. Symptoms are standardized via **SNOMED CT Concept IDs** and triaged through the deterministic **Manchester Triage System (MTS)** decision matrix.
3. **Omnichannel Access:** Patients can interact either directly via **WhatsApp** (voice notes and text) or through the **Web Telemedicine Portal & Simulator**.

---

## 🏛️ System Architecture

```
[ Patient Voice Note / Text ]
              │
              ▼
   [ Audio Ingestion Engine ] ──► FFmpeg Normalization (16kHz PCM mono WAV)
              │
              ▼
     [ Speech-to-Text ASR ]   ──► Native Audio Transcription (Whisper / Local Engine)
              │
              ▼
    [ N-ATLaS Sovereign LLM ] ──► Extracts Chief Complaint, Symptoms, Duration & Severity
              │
              ▼
   [ SNOMED CT Concept Registry ] ──► Maps colloquial terms (e.g., "aiya n dun mi") to SNOMED IDs
              │
              ▼
    [ MTS Triage Decision Engine ] ──► Evaluates MTS Discriminators (RED / YELLOW / GREEN / WHITE)
              │
              ├───────────────────────────────┐
              ▼                               ▼
 [ WhatsApp Cloud API Auto-Reply ]   [ Database Record & Web Portal ]
 (Personalized Clinical Guidance)     (SQLite / PostgreSQL Persistence)
```

---

## 🌟 Core Features & Subsystems

### 1. Conversational Audio Ingestion Engine
* Integrates directly with Meta's **WhatsApp Cloud API (v25.0)**.
* Automatic media fetching, decapsulation, and **FFmpeg** audio normalization to 16kHz mono linear PCM `.wav`.
* Handles `.ogg` (Opus), `.mp4`, `.m4a`, and `.wav` formats.

### 2. Sovereign Multilingual AI Pipeline (N-ATLaS)
* **Linguistic Specialization:** Supports **Hausa (`ha`)**, **Yoruba (`yo`)**, **Igbo (`ig`)**, **Nigerian Pidgin (`pcm`)**, and **English (`en`)**.
* Extracts structured clinical entities via Pydantic schema validation:
  * Chief Complaint
  * Associated Symptoms List
  * Duration & Onset
  * Patient-Perceived Severity

### 3. Standards-Compliant Clinical Triage (SNOMED CT & MTS)
* **SNOMED CT Concept Registry (`services/triage/snomed_registry.py`):** Standardizes informal indigenous complaints:
  * *"aiya n dun mi"* (Yoruba) / *"ciwon kirji"* (Hausa) $\rightarrow$ **SNOMED Concept `29857009`** (Chest Pain)
  * *"no fit breathe"* (Pidgin) / *"mi o le mi daada"* (Yoruba) $\rightarrow$ **SNOMED Concept `267036007`** (Dyspnea)
  * *"body dey hot"* (Pidgin) / *"zazzabi"* (Hausa) $\rightarrow$ **SNOMED Concept `386661006`** (Fever)
  * *"ori n fo mi"* (Yoruba) / *"isi owuwa"* (Igbo) $\rightarrow$ **SNOMED Concept `25064002`** (Headache)
  * *"farfadiya"* (Hausa) / *"warapa"* (Yoruba) $\rightarrow$ **SNOMED Concept `91175000`** (Seizure)
* **Manchester Triage System Matrix (`config/mts_protocols.json`):**
  * **🔴 RED (Emergency / 0 mins):** Cardiac Chest Pain, Inadequate Breathing, Convulsion, Hemorrhage.
  * **🟡 YELLOW (Urgent / 60 mins):** Persistent High Fever, Severe Abdominal Pain, Dehydration Risk.
  * **🟢 GREEN (Routine / 120 mins):** Mild Upper Respiratory Symptoms, Mild Headache, General Malaise.
  * **⚪ WHITE (Self-Care / 240 mins):** Minor self-limiting symptoms.

### 4. Dual Channel Interfaces
* **WhatsApp Cloud API:** Automated outbound patient messaging with clinical advice and Nigerian emergency hotline (**112**) directives within the 24-hour service window.
* **Web Telemedicine Portal & Simulator (`http://localhost:8000/portal`):**
  * Microphone voice recorder with live audio wave player.
  * Multi-language text symptoms tester.
  * Real-time SNOMED CT and MTS analytics card.
  * Interactive WhatsApp phone mockup.

### 5. Regulatory & Data Privacy Compliance
* Compliant with **Nigeria Data Protection Act (NDPA / NDPC)** and **HIPAA**.
* Phone numbers (MSISDN) are stored using **SHA-256 cryptographic one-way hashing**.
* Complete consultation history and audio logs stored in SQLite / PostgreSQL.

---

## 📂 Project Structure

```
Afya voice/
├── api/
│   ├── portal/
│   │   └── routes.py              # Web Telemedicine Portal & Live Simulator (/portal)
│   └── webhooks/
│       └── whatsapp.py            # Meta WhatsApp Cloud API Webhook Handler
├── config/
│   └── mts_protocols.json         # Manchester Triage System (MTS) Discriminator Matrix
├── core/
│   ├── database/
│   │   ├── models.py              # SQLAlchemy ERD Models (Patients, Sessions, AudioLogs)
│   │   └── session.py             # Database engine & sessionmaker factory
│   └── schemas/
│       └── payloads.py            # Pydantic schemas for data interchange
├── services/
│   ├── audio/
│   │   └── processor.py           # FFmpeg audio pipeline (download, normalize to 16kHz)
│   ├── database/
│   │   └── session_manager.py     # Database session recorder with phone hashing
│   ├── llm/
│   │   └── clinical_parser.py     # N-ATLaS LLM Clinical NLP Symptom Extractor
│   ├── messaging/
│   │   └── whatsapp.py            # Meta Outbound Graph API Messenger
│   └── triage/
│       ├── engine.py              # MTS Triage Decision Support Engine
│       └── snomed_registry.py     # SNOMED CT Multilingual Concept Registry
├── storage/
│   ├── audio/                     # Normalized WAV audio storage
│   └── temp_uploads/              # Temporary audio uploads
├── .env                           # Environment secrets & API configuration
├── main.py                        # FastAPI Application entry point
├── requirements.txt               # Python dependencies
└── README.md                      # Documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python 3.11+** installed.
* **FFmpeg** installed and accessible in your system `PATH` (for audio decoding).
  * *Windows:* `winget install Gyan.FFmpeg`
  * *Ubuntu/Debian:* `sudo apt-get install ffmpeg`
  * *macOS:* `brew install ffmpeg`

### 2. Installation
Clone the repository and set up a virtual environment:

```bash
# Clone the repository
git clone https://github.com/your-org/afyavoice.git
cd afyavoice

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration (`.env`)
Create a `.env` file in the root directory:

```env
# 1. Meta WhatsApp Cloud API Credentials
META_ACCESS_TOKEN="your_meta_system_user_or_temporary_token"
META_PHONE_NUMBER_ID="your_meta_phone_number_id"
META_API_VERSION="v25.0"
WHATSAPP_VERIFY_TOKEN="afyavoice_secure_verify_token"

# 2. Database Connection (SQLite default, or PostgreSQL)
DATABASE_URL="sqlite:///./afyavoice.db"

# 3. N-ATLaS Sovereign AI (Hugging Face)
NATLAS_API_KEY="your_hugging_face_access_token_hf_xxx"
NATLAS_ASR_ENDPOINT="https://api-inference.huggingface.co/models/openai/whisper-small"
NATLAS_LLM_ENDPOINT="https://api-inference.huggingface.co/models/NCAIR1/N-ATLaS/v1/chat/completions"
```

---

## 🏃 Running the Application

### Start the AfyaVoice Backend
```bash
python main.py
```
The server will start at **`http://localhost:8000`**.

### Access the Web Telemedicine Portal & Simulator
Open your browser and navigate to:
👉 **[http://localhost:8000/portal](http://localhost:8000/portal)**

* Click the **Microphone** button to speak a voice note into your laptop.
* Or use the **Text Message** tab to type symptoms in English, Yoruba, Hausa, Igbo, or Pidgin.
* Click **Run N-ATLAS Clinical Triage** to see real-time SNOMED CT mapping, urgency classification, and the simulated WhatsApp response.

---

## 📱 Testing with Real WhatsApp

To connect real WhatsApp traffic to your local server:

1. **Start Cloudflare Tunnel:**
   ```bash
   ./cloudflared.exe tunnel --url http://localhost:8000
   ```
2. **Configure Meta Webhook:**
   * Go to **Meta for Developers** $\rightarrow$ **WhatsApp** $\rightarrow$ **Configuration**.
   * Set **Callback URL**: `https://<your-subdomain>.trycloudflare.com/webhooks/whatsapp`
   * Set **Verify Token**: `afyavoice_secure_verify_token`
   * Under **Webhook fields**, click **Manage** and subscribe to **`messages`**.
3. **Send a Voice Note:**
   * Send a voice note from your phone to the Meta WhatsApp Test Number.
   * AfyaVoice will ingest the voice note, process it through N-ATLaS, map the SNOMED concept, score the MTS tier, and reply directly on WhatsApp!

---

## 📜 Clinical & Ethical Disclaimers
* AfyaVoice is a **Clinical Decision Support & Triage Tool** designed to assist healthcare workers and prioritize patient queues. It does **not** provide final medical diagnoses or prescribe controlled medications autonomously.
* All high-urgency **RED** cases mandate immediate physical escalation to an accredited Nigerian Emergency Department.
* Built in alignment with **Medical and Dental Council of Nigeria (MDCN)** telemedicine ethical guidelines.

---

## 📄 License & Attribution
* **N-ATLaS-LLM** is powered by **Awarri Technologies** and the **Nigerian Languages AI Initiative** (Federal Ministry of Communications, Innovation and Digital Economy - FMCIDE).
* AfyaVoice Architecture & Development © 2026. All rights reserved.
