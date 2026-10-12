from fastapi import APIRouter
from fastapi.responses import HTMLResponse

landing_router = APIRouter()

@landing_router.get("/", response_class=HTMLResponse)
def get_landing_page():
    """Serves the clean, human-centered AfyaVoice telemedicine landing page."""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AfyaVoice - Healthcare Triage in Your Native Language</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #ffffff;
      --bg-alt: #f8fafc;
      --primary: #0f766e;
      --primary-hover: #0d9488;
      --primary-light: #f0fdfa;
      --primary-subtle: #ccfbf1;
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-light: #64748b;
      --border: #e2e8f0;
      --card-bg: #ffffff;
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
      --shadow-md: 0 4px 16px -2px rgba(15, 118, 110, 0.08);
      --shadow-lg: 0 12px 30px -4px rgba(15, 118, 110, 0.12);
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
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: var(--primary);
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.15rem;
    }
    .brand-title {
      font-weight: 800;
      font-size: 1.25rem;
      color: var(--primary);
      letter-spacing: -0.02em;
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
      box-shadow: 0 4px 14px rgba(15, 118, 110, 0.25);
    }
    .btn-primary:hover { background: var(--primary-hover); transform: translateY(-2px); }
    .btn-secondary {
      background: #fff;
      color: var(--text-main);
      border: 1px solid var(--border);
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
    .btn-secondary:hover { background: var(--bg-alt); border-color: #cbd5e1; }

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
      background: #0284c7;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1rem;
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
      background: #f1f5f9;
      color: var(--text-main);
      border-bottom-right-radius: 2px;
    }
    .bubble-bot {
      align-self: flex-start;
      background: var(--primary-light);
      border: 1px solid var(--primary-subtle);
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
    .badge-triage-green {
      background: #dcfce7;
      color: #166534;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      font-weight: 700;
    }

    /* HOW IT WORKS SECTION */
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

    /* LANGUAGE CAROUSEL SECTION */
    .lang-bar {
      background: var(--bg-alt);
      border-top: 1px solid var(--border);
      border-bottom: 1px solid var(--border);
      padding: 3rem 1.5rem;
      text-align: center;
    }
    .lang-grid {
      max-width: 1000px;
      margin: 1.5rem auto 0;
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 1rem;
    }
    .lang-card {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 0.85rem 1.5rem;
      display: flex;
      align-items: center;
      gap: 0.65rem;
      font-weight: 700;
      font-size: 0.95rem;
      color: var(--text-main);
      box-shadow: var(--shadow-sm);
    }
    .lang-flag { font-size: 1.25rem; }

    /* STANDARDS & CLINICAL SAFETY */
    .standards-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 2rem;
      margin-top: 2rem;
    }
    @media (max-width: 768px) { .standards-grid { grid-template-columns: 1fr; } }
    .standard-box {
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 1.75rem;
      display: flex;
      gap: 1.25rem;
    }
    .standard-icon {
      font-size: 2rem;
      line-height: 1;
    }
    .standard-box h4 { font-size: 1.1rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.35rem; }
    .standard-box p { font-size: 0.88rem; color: var(--text-muted); }

    /* CTA BANNER */
    .cta-banner {
      background: linear-gradient(135deg, #0f766e, #0d9488);
      border-radius: var(--radius-lg);
      padding: 3.5rem 2rem;
      text-align: center;
      color: #ffffff;
      margin: 4rem auto;
      max-width: 1100px;
      box-shadow: 0 10px 30px rgba(15, 118, 110, 0.2);
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
      <div class="logo-badge">AV</div>
      <div class="brand-title">AfyaVoice</div>
    </a>
    <ul class="nav-links">
      <li><a href="#how-it-works">How It Works</a></li>
      <li><a href="#languages">Languages</a></li>
      <li><a href="#clinical-safety">Clinical Safety</a></li>
      <li><a href="#standards">Medical Standards</a></li>
    </ul>
    <a href="/portal" class="btn-header-cta">Launch Triage Portal →</a>
  </nav>

  <!-- HERO SECTION -->
  <section class="hero">
    <div>
      <div class="tag-pill">
        <span>🇳🇬</span> Sovereign Healthcare Triage for Nigeria
      </div>
      <h1>Healthcare triage in your <span>mother tongue</span>.</h1>
      <p class="hero-lead">
        Speak or type symptoms in <strong>Yoruba, Hausa, Igbo, Nigerian Pidgin, or English</strong>. Receive validated clinical urgency assessment, home remedy guidance, or immediate emergency doctor referral in seconds.
      </p>
      <div class="cta-group">
        <a href="/portal" class="btn-primary">
          <span>Start Consultation (Free)</span>
          <span>→</span>
        </a>
        <a href="#how-it-works" class="btn-secondary">
          <span>Explore How It Works</span>
        </a>
      </div>
    </div>

    <!-- HERO PREVIEW CARD -->
    <div>
      <div class="hero-card">
        <div class="hero-card-header">
          <div class="doctor-avatar-group">
            <div class="avatar-circle">AV</div>
            <div>
              <div class="doctor-name">AfyaVoice Clinical Assistant</div>
              <div class="doctor-status"><span class="status-dot"></span> Online • MDCN Protocol Active</div>
            </div>
          </div>
          <span style="font-size: 0.75rem; background: #f1f5f9; padding: 0.25rem 0.55rem; border-radius: 6px; font-weight: 700; color: #475569;">Ticket #NG-2041</span>
        </div>

        <div class="chat-preview">
          <div class="bubble bubble-patient">
            🎙️ <em>"Ara mi n gbona ti n si n bi leralera lati ana..."</em>
            <div style="font-size: 0.72rem; color: #64748b; margin-top: 0.3rem;">Yoruba Dialect • Patient Voice Note</div>
          </div>
          <div class="bubble bubble-bot">
            <strong>🏥 Clinical Assessment:</strong>
            <br>• <strong>Primary Finding:</strong> Fever & Persistent Vomiting
            <br>• <strong>Urgency Level:</strong> 🟡 Urgent (Review within 12–24h)
            <br>• <strong>Immediate Step:</strong> Hydrate with ORS clean water and visit your primary clinic today.
          </div>
        </div>

        <div class="triage-tag-row">
          <span class="badge-triage-green">✓ Manchester Triage Verified</span>
          <span style="font-family: monospace; font-size: 0.75rem; color: var(--text-light);">SNOMED CT: 386661006</span>
        </div>
      </div>
    </div>
  </section>

  <!-- NATIVE LANGUAGES BANNER -->
  <section class="lang-bar" id="languages">
    <div style="font-size: 0.8rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.08em;">Linguistic Inclusion by Design</div>
    <h2 style="font-size: 1.8rem; font-weight: 800; color: var(--text-main); margin-top: 0.35rem;">Supported Sovereign Dialects</h2>
    <div class="lang-grid">
      <div class="lang-card"><span class="lang-flag">🟢</span> Yorùbá (Èdè Yorùbá)</div>
      <div class="lang-card"><span class="lang-flag">🟢</span> Hausa (Harshen Hausa)</div>
      <div class="lang-card"><span class="lang-flag">🟢</span> Igbo (Asụsụ Igbo)</div>
      <div class="lang-card"><span class="lang-flag">🟢</span> Nigerian Pidgin (Naija)</div>
      <div class="lang-card"><span class="lang-flag">🟢</span> Nigerian English</div>
    </div>
  </section>

  <!-- HOW IT WORKS SECTION -->
  <section class="section" id="how-it-works">
    <div class="section-header">
      <div style="font-size: 0.8rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.08em;">Streamlined Patient Journey</div>
      <h2 class="section-title">How AfyaVoice Works</h2>
      <p class="section-sub">From your spoken voice note to verified clinical decision support in 3 simple steps.</p>
    </div>

    <div class="steps-grid">
      <div class="step-card">
        <div class="step-num">1</div>
        <h3>Describe Symptoms</h3>
        <p>Record a short voice note or type how you feel in your natural dialect. No complex medical terms needed.</p>
      </div>

      <div class="step-card">
        <div class="step-num">2</div>
        <h3>Sovereign AI Understanding</h3>
        <p>Powered by Nigeria's <strong>N-ATLaS-LLM</strong>, your words are translated and standardized using international <strong>SNOMED CT</strong> concept codes.</p>
      </div>

      <div class="step-card">
        <div class="step-num">3</div>
        <h3>Manchester Clinical Triage</h3>
        <p>Deterministic triage algorithms classify urgency into Red (Emergency), Yellow (Urgent), or Green (Routine) with actionable care guidance.</p>
      </div>
    </div>
  </section>

  <!-- MEDICAL STANDARDS SECTION -->
  <section class="section" id="standards" style="padding-top: 0;">
    <div class="section-header">
      <div style="font-size: 0.8rem; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.08em;">Clinical Rigor</div>
      <h2 class="section-title">Built on Healthcare Standards</h2>
      <p class="section-sub">Empowering patient safety with globally recognized protocols and regulatory alignment.</p>
    </div>

    <div class="standards-grid">
      <div class="standard-box">
        <div class="standard-icon">🏥</div>
        <div>
          <h4>Manchester Triage System (MTS)</h4>
          <p>Standardized 52-flowchart clinical urgency matrix ensuring life-threatening conditions are escalated immediately to emergency care.</p>
        </div>
      </div>

      <div class="standard-box">
        <div class="standard-icon">🌐</div>
        <div>
          <h4>SNOMED CT Terminology</h4>
          <p>Universal medical ontology mapping colloquial indigenous phrases into global clinical concept IDs for seamless healthcare interoperability.</p>
        </div>
      </div>

      <div class="standard-box">
        <div class="standard-icon">🇳🇬</div>
        <div>
          <h4>MDCN Telemedicine Guidelines</h4>
          <p>Engineered strictly in compliance with Medical and Dental Council of Nigeria (MDCN) ethical telemedicine protocols.</p>
        </div>
      </div>

      <div class="standard-box">
        <div class="standard-icon">🔒</div>
        <div>
          <h4>NDPA / NDPC Data Privacy</h4>
          <p>Compliant with the Nigeria Data Protection Act. Patient phone numbers and consultation logs are encrypted and hashed.</p>
        </div>
      </div>
    </div>

    <!-- CTA BANNER -->
    <div class="cta-banner">
      <h2>Ready to start your consultation?</h2>
      <p>Try our voice-first clinical triage right in your browser or connect directly with our WhatsApp assistant.</p>
      <a href="/portal" class="btn-cta-white">
        <span>Launch Triage Portal</span>
        <span>→</span>
      </a>
    </div>
  </section>

  <!-- FOOTER -->
  <footer>
    <div style="margin-bottom: 0.5rem; font-weight: 700; color: var(--primary);">AfyaVoice Sovereign Telemedicine Platform</div>
    <div>Powered by N-ATLaS-LLM • Developed in partnership with Nigerian Languages AI Initiative • © 2026 AfyaVoice. All rights reserved.</div>
  </footer>

</body>
</html>
    """
    return HTMLResponse(content=html_content)
