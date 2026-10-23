from fastapi import APIRouter
from fastapi.responses import HTMLResponse

landing_router = APIRouter()

@landing_router.get("/", response_class=HTMLResponse)
def get_landing_page():
    """Serves the modern AfyaMama Maternal & Antenatal Healthcare landing page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AfyaMama - Sovereign Maternal & Antenatal Health in Your Mother Tongue</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #ffffff;
      --bg-alt: #f8fafc;
      --primary: #be185d; /* Warm maternal rose / magenta */
      --primary-hover: #9d174d;
      --primary-light: #fdf2f8;
      --primary-subtle: #fbcfe8;
      --teal: #0f766e;
      --teal-light: #f0fdfa;
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-light: #64748b;
      --border: #e2e8f0;
      --card-bg: #ffffff;
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
      --shadow-md: 0 4px 16px -2px rgba(190, 24, 93, 0.08);
      --shadow-lg: 0 12px 30px -4px rgba(190, 24, 93, 0.12);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    /* NAVIGATION BAR */
    nav {
      position: sticky;
      top: 0;
      z-index: 50;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand-logo {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      text-decoration: none;
      color: var(--text-main);
    }
    .logo-badge {
      width: 40px;
      height: 40px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--primary), #fb7185);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.25rem;
    }
    .brand-title {
      font-weight: 800;
      font-size: 1.25rem;
      color: var(--primary);
      letter-spacing: -0.02em;
    }
    .brand-sub {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--text-muted);
      display: block;
      margin-top: -3px;
    }
    .nav-links {
      display: flex;
      align-items: center;
      gap: 2rem;
      list-style: none;
    }
    .nav-links a {
      text-decoration: none;
      color: var(--text-muted);
      font-size: 0.92rem;
      font-weight: 600;
      transition: color 0.15s;
    }
    .nav-links a:hover { color: var(--primary); }
    
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .btn-telegram {
      background: #0284c7;
      color: #fff;
      padding: 0.65rem 1.15rem;
      border-radius: 9999px;
      text-decoration: none;
      font-weight: 700;
      font-size: 0.88rem;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.2s;
    }
    .btn-telegram:hover { background: #0369a1; transform: translateY(-1px); }
    
    .btn-header-cta {
      background: var(--primary);
      color: #fff;
      padding: 0.65rem 1.25rem;
      border-radius: 9999px;
      text-decoration: none;
      font-weight: 700;
      font-size: 0.88rem;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    .btn-header-cta:hover { background: var(--primary-hover); transform: translateY(-1px); }

    /* HERO SECTION */
    .hero {
      max-width: 1240px;
      margin: 0 auto;
      padding: 4.5rem 1.5rem 3.5rem;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 3.5rem;
      align-items: center;
    }
    @media (max-width: 960px) {
      .hero { grid-template-columns: 1fr; padding-top: 2.5rem; gap: 2.5rem; }
      .nav-links { display: none; }
    }
    .tag-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      background: var(--primary-light);
      border: 1px solid var(--primary-subtle);
      color: var(--primary);
      font-weight: 700;
      font-size: 0.82rem;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      margin-bottom: 1.25rem;
    }
    .hero h1 {
      font-size: 3rem;
      font-weight: 800;
      line-height: 1.18;
      letter-spacing: -0.03em;
      color: var(--text-main);
      margin-bottom: 1.25rem;
    }
    .hero h1 span { color: var(--primary); }
    .hero-lead {
      font-size: 1.12rem;
      color: var(--text-muted);
      line-height: 1.6;
      margin-bottom: 2rem;
      max-width: 560px;
    }
    .cta-group {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      align-items: center;
    }
    .btn-primary {
      background: var(--primary);
      color: #fff;
      padding: 0.95rem 1.85rem;
      border-radius: 12px;
      text-decoration: none;
      font-weight: 700;
      font-size: 1rem;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      box-shadow: 0 4px 14px rgba(190, 24, 93, 0.25);
    }
    .btn-primary:hover { background: var(--primary-hover); transform: translateY(-2px); }
    .btn-secondary {
      background: #0284c7;
      color: #fff;
      padding: 0.95rem 1.65rem;
      border-radius: 12px;
      text-decoration: none;
      font-weight: 700;
      font-size: 1rem;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }
    .btn-secondary:hover { background: #0369a1; }

    /* HERO MOCKUP CARD */
    .hero-card {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 1.85rem;
      box-shadow: var(--shadow-lg);
      position: relative;
    }
    .hero-card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 1.25rem;
      padding-bottom: 0.85rem;
      border-bottom: 1px solid var(--border);
    }
    .doctor-avatar-group { display: flex; align-items: center; gap: 0.75rem; }
    .avatar-circle {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: var(--primary-light);
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.2rem;
    }
    .doctor-name { font-size: 0.95rem; font-weight: 800; color: var(--text-main); }
    .doctor-status { font-size: 0.75rem; color: #16a34a; font-weight: 600; display: flex; align-items: center; gap: 0.3rem; }
    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #16a34a; }
    
    .chat-preview {
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }
    .bubble {
      padding: 0.85rem 1.15rem;
      border-radius: 14px;
      font-size: 0.9rem;
      line-height: 1.45;
      max-width: 90%;
    }
    .bubble-patient {
      align-self: flex-end;
      background: #fdf2f8;
      border: 1px solid var(--primary-subtle);
      color: var(--text-main);
      border-bottom-right-radius: 2px;
    }
    .bubble-bot {
      align-self: flex-start;
      background: #f0fdfa;
      border: 1px solid #ccfbf1;
      color: #0f766e;
      border-bottom-left-radius: 2px;
    }
    .triage-tag-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-top: 0.5rem;
      padding-top: 0.75rem;
      border-top: 1px dashed var(--border);
      font-size: 0.78rem;
    }
    .badge-triage-red {
      background: #fee2e2;
      color: #991b1b;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-weight: 700;
    }

    /* SECTION */
    .section {
      max-width: 1240px;
      margin: 0 auto;
      padding: 4.5rem 1.5rem;
    }
    .section-header {
      text-align: center;
      max-width: 680px;
      margin: 0 auto 3.5rem;
    }
    .section-title {
      font-size: 2.25rem;
      font-weight: 800;
      color: var(--text-main);
      letter-spacing: -0.02em;
      margin-bottom: 0.75rem;
    }
    .section-sub {
      font-size: 1.05rem;
      color: var(--text-muted);
    }
    .steps-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 2rem;
    }
    @media (max-width: 860px) { .steps-grid { grid-template-columns: 1fr; } }
    .step-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 2rem;
      box-shadow: var(--shadow-sm);
      transition: all 0.2s;
    }
    .step-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-md); border-color: var(--primary); }
    .step-num {
      width: 46px;
      height: 46px;
      border-radius: 12px;
      background: var(--primary-light);
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.25rem;
      margin-bottom: 1.25rem;
    }
    .step-card h3 { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.65rem; color: var(--text-main); }
    .step-card p { font-size: 0.95rem; color: var(--text-muted); line-height: 1.55; }

    /* GUIDELINES RAG SECTION */
    .rag-section {
      background: var(--bg-alt);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      padding: 4rem 1.5rem;
    }
    .guideline-cards-grid {
      max-width: 1240px;
      margin: 2rem auto 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
    }
    .guideline-box {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 1.5rem;
      box-shadow: var(--shadow-sm);
    }
    .guideline-badge {
      font-size: 0.72rem;
      font-weight: 800;
      background: var(--teal-light);
      color: var(--teal);
      padding: 0.2rem 0.55rem;
      border-radius: 6px;
      display: inline-block;
      margin-bottom: 0.65rem;
    }
    .guideline-box h4 { font-size: 1.05rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.4rem; }
    .guideline-box p { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; }

    /* CTA BANNER */
    .cta-banner {
      background: linear-gradient(135deg, var(--primary), #be185d);
      border-radius: var(--radius-lg);
      padding: 3.5rem 2rem;
      text-align: center;
      color: #ffffff;
      margin: 4rem auto;
      max-width: 1100px;
      box-shadow: 0 10px 30px rgba(190, 24, 93, 0.2);
    }
    .cta-banner h2 { font-size: 2.2rem; font-weight: 800; margin-bottom: 0.75rem; }
    .cta-banner p { font-size: 1.05rem; opacity: 0.92; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto; }
    .btn-cta-white {
      background: #ffffff;
      color: var(--primary);
      padding: 1rem 2.25rem;
      border-radius: 9999px;
      font-weight: 800;
      text-decoration: none;
      font-size: 1.05rem;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      transition: all 0.2s;
    }
    .btn-cta-white:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }

    /* FOOTER */
    footer {
      background: #ffffff;
      border-top: 1px solid var(--border);
      padding: 2.5rem 2rem;
      text-align: center;
      font-size: 0.85rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>

  <!-- TOP NAVBAR -->
  <nav>
    <a href="/" class="brand-logo">
      <div class="logo-badge">AM</div>
      <div>
        <div class="brand-title">AfyaMama</div>
        <span class="brand-sub">Sovereign Maternal Care</span>
      </div>
    </a>
    <ul class="nav-links">
      <li><a href="#how-it-works">How It Works</a></li>
      <li><a href="#guidelines">WHO & Nigeria Guidelines</a></li>
      <li><a href="#danger-signs">Obstetric Danger Signs</a></li>
      <li><a href="/portal">Web Portal</a></li>
    </ul>
    <div class="nav-actions">
      <a href="https://t.me/afyavoice_bot" target="_blank" class="btn-telegram">📱 Telegram Bot</a>
      <a href="/portal" class="btn-header-cta">Launch Triage Portal →</a>
    </div>
  </nav>

  <!-- HERO SECTION -->
  <section class="hero">
    <div>
      <div class="tag-pill">
        <span>🤰</span> Dedicated Maternal & Antenatal Healthcare for Nigeria
      </div>
      <h1>Safe pregnancy care in your <span>mother tongue</span>.</h1>
      <p class="hero-lead">
        Speak or type symptoms in <strong>Yorùbá, Hausa, Igbo, Nigerian Pidgin, or English</strong>. Receive instant, evidence-based triage and care advice powered by <strong>WHO Antenatal Guidelines</strong> and <strong>FMOH Nigeria Maternal Health Protocols</strong>.
      </p>
      <div class="cta-group">
        <a href="/portal" class="btn-primary">
          <span>Start Consultation (Free)</span>
          <span>→</span>
        </a>
        <a href="https://t.me/afyavoice_bot" target="_blank" class="btn-secondary">
          <span>Chat on Telegram 📱</span>
        </a>
      </div>
    </div>

    <!-- HERO PREVIEW CARD -->
    <div>
      <div class="hero-card">
        <div class="hero-card-header">
          <div class="doctor-avatar-group">
            <div class="avatar-circle">🤰</div>
            <div>
              <div class="doctor-name">AfyaMama Clinical Assistant</div>
              <div class="doctor-status"><span class="status-dot"></span> Online • WHO & FMOH Protocol Active</div>
            </div>
          </div>
          <span style="font-size: 0.75rem; background: #fdf2f8; padding: 0.25rem 0.55rem; border-radius: 6px; font-weight: 700; color: #be185d;">3rd Trimester</span>
        </div>

        <div class="chat-preview">
          <div class="bubble bubble-patient">
            🎙️ <em>"Ori n fo mi gidigidi, oju mi n dudu ti ese mi si n wu lati ana..."</em>
            <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 0.3rem;">Yoruba Dialect • Patient Voice Note</div>
          </div>
          <div class="bubble bubble-bot">
            <strong>⚠️ CRITICAL OBSTETRIC ALERT:</strong>
            <br>• <strong>Primary Risk:</strong> Pre-Eclampsia / Impending Eclampsia
            <br>• <strong>Urgency Level:</strong> 🔴 Obstetric Emergency
            <br>• <strong>Evidence (WHO ANC Guideline):</strong> Severe persistent headache + visual disturbances requires immediate hospital BP evaluation & Magnesium Sulfate protocol.
            <br>• <strong>Action:</strong> Proceed to nearest General Hospital immediately. Call <strong>112</strong>.
          </div>
        </div>

        <div class="triage-tag-row">
          <span class="badge-triage-red">🚨 Obstetric Emergency</span>
          <span style="font-family: monospace; font-size: 0.75rem; color: var(--text-light);">SNOMED CT: 398254007</span>
        </div>
      </div>
    </div>
  </section>

  <!-- WHO & FMOH GUIDELINES RAG SECTION -->
  <section class="rag-section" id="guidelines">
    <div class="section-header">
      <div style="font-size: 0.8rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.08em;">Evidence-Based Maternal Knowledge</div>
      <h2 class="section-title">Integrated Clinical Guidelines (RAG)</h2>
      <p class="section-sub">Every piece of maternal advice is retrieved directly from authoritative clinical guidelines.</p>
    </div>

    <div class="guideline-cards-grid">
      <div class="guideline-box">
        <span class="guideline-badge">WHO Standard</span>
        <h4>Antenatal Care for Positive Pregnancy</h4>
        <p>The WHO 8-contact model, nutritional recommendations (Iron 60mg + Folic Acid 400µg), and relief for physiological symptoms (morning sickness, heartburn, cramps).</p>
      </div>

      <div class="guideline-box">
        <span class="guideline-badge">Nigeria FMOH</span>
        <h4>Nigeria Maternal & Newborn Protocols</h4>
        <p>National guidelines for Malaria in Pregnancy (IPTp-SP schedule from 13 weeks), Tetanus Toxoid (TT1-TT5), and Birth Preparedness and Complication Readiness (BPCR).</p>
      </div>

      <div class="guideline-box">
        <span class="guideline-badge">WHO IMPAC</span>
        <h4>Emergency Obstetric Danger Signs</h4>
        <p>Life-saving algorithms for Antepartum Haemorrhage (Placenta Praevia, Abruption), Severe Pre-Eclampsia, Eclampsia, Cord Prolapse, and Puerperal Sepsis.</p>
      </div>

      <div class="guideline-box">
        <span class="guideline-badge">WHO Intrapartum</span>
        <h4>Labor & Postnatal Care Experience</h4>
        <p>True labor vs. Braxton Hicks distinction, respectful maternity care, Oxytocin 10 IU for PPH prevention, exclusive breastfeeding, and newborn cord care.</p>
      </div>
    </div>
  </section>

  <!-- HOW IT WORKS SECTION -->
  <section class="section" id="how-it-works">
    <div class="section-header">
      <div style="font-size: 0.8rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.08em;">Step-by-Step Care</div>
      <h2 class="section-title">How AfyaMama Protects Mothers</h2>
      <p class="section-sub">From spoken mother-tongue symptom to verified clinical obstetric triage in seconds.</p>
    </div>

    <div class="steps-grid">
      <div class="step-card">
        <div class="step-num">1</div>
        <h3>Select Trimester & Speak</h3>
        <p>Select your stage (1st, 2nd, 3rd Trimester or Postpartum) and speak or write in Yoruba, Hausa, Igbo, Pidgin, or English.</p>
      </div>

      <div class="step-card">
        <div class="step-num">2</div>
        <h3>RAG Clinical Retrieval</h3>
        <p>Our in-process SQLite RAG engine instantly matches your symptoms against indexed WHO and Nigerian Health Guidelines.</p>
      </div>

      <div class="step-card">
        <div class="step-num">3</div>
        <h3>Evidence-Based Action Plan</h3>
        <p>Receive clear emergency classification (Red/Yellow/Green), SNOMED CT clinical coding, and step-by-step home care guidance.</p>
      </div>
    </div>
  </section>

  <!-- CTA BANNER -->
  <div class="cta-banner">
    <h2>Access Safe Maternal Healthcare Today</h2>
    <p>Check your symptoms now using our web portal or chat with our 24/7 assistant directly on Telegram.</p>
    <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;">
      <a href="/portal" class="btn-cta-white">
        <span>Launch Triage Portal</span>
        <span>→</span>
      </a>
      <a href="https://t.me/afyavoice_bot" target="_blank" class="btn-cta-white" style="background: #0284c7; color: #fff;">
        <span>Open Telegram Bot 📱</span>
      </a>
    </div>
  </div>

  <!-- FOOTER -->
  <footer>
    <div style="margin-bottom: 0.5rem; font-weight: 700; color: var(--primary);">AfyaMama • Dedicated Sovereign Maternal Health Platform</div>
    <div>Powered by WHO Antenatal Care Guidelines & Federal Ministry of Health Nigeria Protocols • © 2026. All rights reserved.</div>
  </footer>

</body>
</html>
    """
    return HTMLResponse(content=html_content)
