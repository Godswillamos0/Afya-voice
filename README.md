# AfyaMama / AfyaVoice: Sovereign Maternal & Antenatal Healthcare Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB.svg?logo=python)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-0284C7.svg?logo=telegram)](https://telegram.org)
[![Clinical RAG](https://img.shields.io/badge/Knowledge-WHO%20%7C%20Nigeria%20FMOH-BE185D.svg)](#)
[![Clinical Standards](https://img.shields.io/badge/Standards-MTS%20%7C%20SNOMED%20CT-0284C7.svg)](https://www.snomed.org)

> **AfyaMama** is Nigeria's sovereign maternal and antenatal voice triage platform designed specifically for **pregnant women and new mothers**. It bridges indigenous languages (**Yorùbá, Hausa, Igbo, Nigerian Pidgin, and English**) with evidence-based maternal medicine by combining sovereign AI with an authoritative **RAG (Retrieval-Augmented Generation) knowledge engine** built on **WHO Antenatal Guidelines** and **Federal Ministry of Health (FMOH) Nigeria Maternal Care Protocols**.

---

## 🤰 Platform Overview

Maternal mortality remains a critical challenge in West Africa. Many mothers face language barriers, delayed recognition of cardinal obstetric danger signs (such as pre-eclampsia and antepartum hemorrhage), and lack of timely antenatal guidance.

AfyaMama allows pregnant women and new mothers to speak or type their symptoms and concerns in their natural mother tongue, receiving verified clinical guidance:

1. **Evidence-Based Maternal RAG:** All clinical recommendations are grounded in indexed **WHO Antenatal Care Guidelines (8-contact model)**, **WHO Obstetric Emergencies (IMPAC)**, and **Nigeria FMOH Basic Newborn & Maternal Care Guidelines**.
2. **Obstetric Triage & Safety:** Automatic detection of cardinal danger signs:
   * **🔴 RED (Obstetric Emergency):** Antepartum Haemorrhage (vaginal bleeding), Pre-eclampsia (severe headache + blurred vision), Eclamptic convulsions, Reduced/Absent fetal movement, Puerperal sepsis, Cord prolapse.
   * **🟡 YELLOW (Urgent PHC Review):** Hyperemesis gravidarum, high fever (suspected malaria/pyelonephritis), severe dysuria.
   * **🟢 GREEN (Routine Care & Remedies):** Physiological morning sickness, dietary ginger remedies, heartburn, lower back ache, routine ANC visit scheduling, and daily Iron (60 mg) + Folic Acid (400 µg).
3. **Indigenous Linguistic Support:** Spoken and written comprehension in **Yorùbá**, **Hausa**, **Igbo**, **Nigerian Pidgin**, and **English**.
4. **Accessible Delivery Channels:**
   * **Telegram Bot:** Real-time voice note and text triage with interactive trimester buttons (`python telegram_runner.py`).
   * **Web Telemedicine Portal:** Clean web assessment with voice recorder and live RAG evidence citations.

---

## 🏛️ System Architecture

```
[ Pregnant Mother Voice Note / Text ]
          │ (Spoken in Yoruba, Hausa, Igbo, Pidgin, or English)
          ▼
┌─────────────────────────────────┐
│     Conversational Ingestion    │
│  • Telegram Bot (@AfyaVoiceBot) │
│  • Web Portal (/portal)         │
└────────────────┬────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  Maternal Query Expansion & Translation Engine         │
│  - Maps indigenous terms (e.g., "eje", "ori fifo",     │
│    "omo o gbon", "pikin no dey kick") to clinical concepts│
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  Maternal RAG Knowledge Base (SQLite FTS5 BM25 Engine) │
│  ───────────────────────────────────────────────────── │
│  • WHO Recommendations on Antenatal Care (2016)        │
│  • WHO Integrated Management of Pregnancy (PCPNC/IMPAC)│
│  • Nigeria FMOH Maternal & Newborn Care Protocols      │
│  • WHO Intrapartum & Postnatal Care Guidelines         │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│  Obstetric Triage Decision Engine & SNOMED CT Mapping  │
│  - RED: Immediate referral to CEmONC / Call 112        │
│  - YELLOW: Urgent review at Primary Health Center      │
│  - GREEN: Guideline-approved remedies & ANC schedule   │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
[ Formatted Clinical Guidance with Evidence Citations Delivered to Mother ]
```

---

## 📂 Maternal Knowledge Base (RAG)

The knowledge base is authored in high-yield, structured Markdown documents under `storage/guidelines_md/` and indexed into `storage/maternal_rag.db` using SQLite FTS5 for sub-millisecond retrieval:

* **`who_antenatal_care.md`**: WHO 8-contact model, daily Iron (60mg) + Folic Acid (400µg), calcium supplementation, and physiological relief for morning sickness (ginger, small frequent meals), heartburn, backache, and constipation.
* **`who_obstetric_emergencies_impac.md`**: Triage algorithms for antepartum hemorrhage (placenta previa, abruption), pre-eclampsia/eclampsia management (Magnesium Sulfate protocols), maternal sepsis, and reduced fetal movement.
* **`nigeria_fmoh_maternal_guidelines.md`**: National malaria in pregnancy protocol (IPTp-SP schedule from 13 weeks), Tetanus Toxoid immunization (TT1–TT5), anemia prevention with indigenous foods (Ugwu, spinach, citrus), and Birth Preparedness and Complication Readiness (BPCR).
* **`who_intrapartum_and_postnatal.md`**: True vs. false labor, active management of third stage of labor (Oxytocin 10 IU for PPH prevention), and postnatal maternal danger signs.

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.11+ or 3.14+
* FFmpeg (for audio transcoding)

### 2. Installation
```bash
git clone https://github.com/Godswillamos0/Afya-voice.git
cd "Afya voice"

# Activate virtual environment
.\venv\Scripts\activate   # On Windows
source venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
Create or update your `.env` file:
```env
# 1. Telegram Bot Credentials (obtain from @BotFather in 30 seconds)
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"

# 2. Database Connection (SQLite default)
DATABASE_URL="sqlite:///./afyavoice.db"

# 3. N-ATLaS AI Access
NATLAS_API_KEY="your_hugging_face_token"
NATLAS_ASR_ENDPOINT="https://api-inference.huggingface.co/models/openai/whisper-small"
NATLAS_LLM_ENDPOINT="https://api-inference.huggingface.co/models/NCAIR1/N-ATLaS/v1/chat/completions"
```

### 4. Build or Rebuild Maternal RAG Index
To parse the markdown guidelines and index them into SQLite FTS5:
```bash
python -m services.rag.indexer
```

---

## 💻 Running the Application

### Option A: Run the Telegram Bot (Local Long Polling)
**No public tunnel or webhook needed!** Simply run:
```bash
python telegram_runner.py
```
Open Telegram, search for your bot, send `/start`, choose your gestational stage, and speak or write symptoms in any Nigerian dialect!

### Option B: Run the Web Telemedicine Server
```bash
python main.py
```
* **Patient Landing Page:** [http://localhost:8000/](http://localhost:8000/)
* **Clinical Triage Portal:** [http://localhost:8000/portal](http://localhost:8000/portal)
* **Telegram Webhook Info:** [http://localhost:8000/webhooks/telegram/info](http://localhost:8000/webhooks/telegram/info)

---

## 📋 Clinical Standards Compliance
* **World Health Organization (WHO):** Standards for improving quality of maternal and newborn care.
* **Federal Ministry of Health Nigeria (FMOH):** National guidelines for Maternal, Newborn, and Child Health (MNCH).
* **SNOMED CT:** Standardized clinical health terminology (Concepts: Pre-eclampsia `398254007`, Antepartum Haemorrhage `237244005`, Routine Antenatal Care `424441002`).
* **Manchester Triage System (MTS):** Validated clinical urgency prioritization.
* **NDPA / NDPC Compliant:** Complies with the Nigeria Data Protection Act.
