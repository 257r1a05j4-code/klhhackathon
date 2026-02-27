import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import io
import os
import time
# ─────────────────────────────────────────
#  CONFIG  (set your key here like $env)
# ─────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL   = "gemini-2.0-flash"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="RxVernacular — Prescription Parser",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────
#  GLOBAL CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body, .stApp {
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
    background-color: #f3f6f4;
    color: #111827;
}

/* Fix Streamlit widgets */
.stTextInput input,
.stSelectbox div[data-baseweb="select"],
.stFileUploader {
    background-color: #ffffff !important;
    color: #111827 !important;
    border-radius: 10px !important;
}

/* Better secondary text */
.navbar-right,
.tile-label,
.step-label {
    color: #4b5563 !important;
}

/* Card readability */
.info-tile,
.lang-card,
.audio-card,
.med-card {
    background: #ffffff;
    border: 1px solid #d1d5db;
}

/* Hover clarity */
.med-card:hover {
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}
            
/* ── Top navbar ── */
.navbar {
    display: flex; align-items: center; justify-content: space-between;
    background: #ffffff; border-bottom: 1px solid #e4ede8;
    padding: 0.9rem 2.5rem; margin: -1rem -1rem 2rem -1rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
.navbar-brand { display: flex; align-items: center; gap: 0.6rem; }
.navbar-brand span.logo { font-size: 1.5rem; }
.navbar-brand span.name { font-size: 1.1rem; font-weight: 700; color: #0f5c30; letter-spacing: -0.02em; }
.navbar-brand span.tag  { font-size: 0.72rem; background: #e6f4ec; color: #1a8a4a;
    border-radius: 20px; padding: 0.15rem 0.6rem; font-weight: 600; margin-left: 0.2rem; }
.navbar-right { font-size: 0.8rem; color: #888; }

/* ── Hero section ── */
.hero {
    background: linear-gradient(135deg, #0f5c30 0%, #1a8a4a 60%, #22c55e 100%);
    color: white; border-radius: 20px; padding: 2.4rem 2.8rem;
    margin-bottom: 2rem; position: relative; overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px; border-radius: 50%;
    background: rgba(255,255,255,0.06);
}
.hero::after {
    content: ''; position: absolute; bottom: -60px; right: 80px;
    width: 140px; height: 140px; border-radius: 50%;
    background: rgba(255,255,255,0.04);
}
.hero h1 { font-size: 1.85rem; font-weight: 700; margin: 0 0 0.5rem; letter-spacing: -0.03em; }
.hero p  { margin: 0; opacity: 0.85; font-size: 0.97rem; max-width: 520px; line-height: 1.6; }
.hero-pills { display: flex; gap: 0.6rem; margin-top: 1.2rem; flex-wrap: wrap; }
.hero-pill {
    background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px; padding: 0.25rem 0.8rem; font-size: 0.78rem; font-weight: 500;
}

/* ── Upload zone ── */
.upload-label {
    font-size: 0.78rem; font-weight: 600; color: #0f5c30;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.4rem;
}

/* ── Language selector card ── */
.lang-card {
    background: white; border-radius: 14px; padding: 1.2rem 1.4rem;
    border: 1px solid #e4ede8; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    margin-bottom: 1rem;
}
.lang-card label { font-size: 0.78rem; font-weight: 600; color: #0f5c30;
    text-transform: uppercase; letter-spacing: 0.07em; }

/* ── Parse button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #0f5c30, #1a8a4a) !important;
    color: white !important; border: none !important; border-radius: 12px !important;
    padding: 0.7rem 2rem !important; font-size: 0.97rem !important;
    font-weight: 600 !important; width: 100% !important;
    box-shadow: 0 4px 14px rgba(15,92,48,0.3) !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.9 !important; box-shadow: 0 6px 18px rgba(15,92,48,0.4) !important;
}

/* ── Section header ── */
.section-header {
    display: flex; align-items: center; gap: 0.5rem;
    margin: 1.8rem 0 1rem;
}
.section-header .dot {
    width: 8px; height: 8px; border-radius: 50%; background: #1a8a4a; flex-shrink: 0;
}
.section-header h3 { margin: 0; font-size: 1rem; font-weight: 700; color: #0f5c30; }

/* ── Info tiles (patient/doctor/date) ── */
.info-tile {
    background: white; border-radius: 14px; padding: 1.1rem 1.2rem;
    border: 1px solid #e4ede8; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    text-align: center;
}
.info-tile .tile-icon { font-size: 1.5rem; margin-bottom: 0.3rem; }
.info-tile .tile-label { font-size: 0.7rem; font-weight: 600; color: #888;
    text-transform: uppercase; letter-spacing: 0.07em; }
.info-tile .tile-value { font-size: 0.95rem; font-weight: 600; color: #1a1a1a; margin-top: 0.2rem; }

/* ── Diagnosis banner ── */
.diagnosis-banner {
    background: #fffbeb; border: 1px solid #fcd34d; border-radius: 12px;
    padding: 1rem 1.3rem; display: flex; align-items: center; gap: 0.8rem;
}
.diagnosis-banner .d-icon { font-size: 1.4rem; }
.diagnosis-banner .d-label { font-size: 0.72rem; font-weight: 600; color: #92400e;
    text-transform: uppercase; letter-spacing: 0.06em; }
.diagnosis-banner .d-value { font-size: 0.97rem; color: #1a1a1a; font-weight: 500; }

/* ── Medicine cards ── */
.med-card {
    background: white; border-radius: 14px; padding: 1.2rem 1.4rem;
    border: 1px solid #e4ede8; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    margin-bottom: 0.8rem; border-left: 4px solid #1a8a4a;
    transition: box-shadow 0.2s;
}
.med-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.09); }
.med-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.7rem; }
.med-pill-icon {
    background: #e6f4ec; color: #0f5c30; width: 36px; height: 36px;
    border-radius: 10px; display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0;
}
.med-name { font-size: 1rem; font-weight: 700; color: #0f5c30; }
.med-badges { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
.badge {
    background: #f0f7f3; color: #0f5c30; border-radius: 8px;
    padding: 0.2rem 0.6rem; font-size: 0.75rem; font-weight: 500;
    border: 1px solid #c8e6d4;
}
.med-explanation {
    background: #f7faf8; border-radius: 8px; padding: 0.7rem 0.9rem;
    font-size: 0.88rem; color: #333; line-height: 1.6;
    border-left: 3px solid #86efac;
}
.med-explanation .exp-label { font-size: 0.72rem; font-weight: 600; color: #1a8a4a;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.3rem; }

/* ── Summary card ── */
.summary-card {
    background: linear-gradient(135deg, #f0faf5, #e8f5ee);
    border-radius: 14px; padding: 1.4rem 1.6rem;
    border: 1px solid #c8e6d4; margin-bottom: 0.8rem;
}
.summary-card .sum-label { font-size: 0.75rem; font-weight: 700; color: #0f5c30;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.6rem; }
.summary-card .sum-text { font-size: 0.97rem; color: #1a1a1a; line-height: 1.7; }

/* ── Instructions card ── */
.instr-card {
    background: #eff6ff; border-radius: 14px; padding: 1.2rem 1.4rem;
    border: 1px solid #bfdbfe; margin-bottom: 0.8rem;
}
.instr-card .instr-label { font-size: 0.75rem; font-weight: 700; color: #1d4ed8;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem; }
.instr-card .instr-text { font-size: 0.95rem; color: #1e3a5f; line-height: 1.7; }

/* ── Warning card ── */
.warn-card {
    background: #fff7ed; border-radius: 12px; padding: 0.9rem 1.1rem;
    border: 1px solid #fed7aa; margin-bottom: 0.5rem;
    display: flex; align-items: flex-start; gap: 0.6rem;
}
.warn-card .warn-icon { font-size: 1rem; margin-top: 0.05rem; flex-shrink: 0; }
.warn-card .warn-text { font-size: 0.9rem; color: #9a3412; line-height: 1.5; }

/* ── Audio section ── */
.audio-card {
    background: white; border-radius: 14px; padding: 1.2rem 1.4rem;
    border: 1px solid #e4ede8; box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.audio-card .aud-label { font-size: 0.75rem; font-weight: 700; color: #0f5c30;
    text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.8rem; }

/* ── Raw OCR expander ── */
.raw-text-box {
    background: #0f172a; color: #86efac; border-radius: 10px;
    padding: 1rem 1.2rem; font-family: 'Courier New', monospace;
    font-size: 0.85rem; white-space: pre-wrap; word-break: break-word;
    line-height: 1.6;
}

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 4rem 2rem; color: #aaa;
}
.empty-state .es-icon { font-size: 4rem; margin-bottom: 1rem; }
.empty-state h3 { color: #0f5c30; font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.92rem; max-width: 380px; margin: 0 auto; line-height: 1.6; }

/* ── Steps indicator ── */
.steps-row {
    display: flex; gap: 0; margin-bottom: 2rem; background: white;
    border-radius: 14px; border: 1px solid #e4ede8; overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.step-item {
    flex: 1; padding: 0.9rem 0.5rem; text-align: center;
    border-right: 1px solid #e4ede8; position: relative;
}
.step-item:last-child { border-right: none; }
.step-item.active { background: #f0faf5; }
.step-item.done { background: #e6f4ec; }
.step-num {
    width: 24px; height: 24px; border-radius: 50%; background: #e4ede8;
    color: #888; font-size: 0.72rem; font-weight: 700;
    display: flex; align-items: center; justify-content: center; margin: 0 auto 0.3rem;
}
.step-item.active .step-num { background: #1a8a4a; color: white; }
.step-item.done .step-num { background: #0f5c30; color: white; }
.step-label { font-size: 0.72rem; font-weight: 600; color: #888; }
.step-item.active .step-label, .step-item.done .step-label { color: #0f5c30; }

/* ── Divider ── */
.divider { border: none; border-top: 1px solid #e4ede8; margin: 1.5rem 0; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  NAVBAR
# ─────────────────────────────────────────
st.markdown("""
<div class="navbar">
    <div class="navbar-brand">
        <span class="logo">💊</span>
        <span class="name">RxVernacular</span>
        <span class="tag">BETA</span>
    </div>
    <div class="navbar-right">Powered by Gemini 1.5 Flash · For informational use only</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  HERO
# ─────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>Vernacular Medical Prescription Parser</h1>
    <p>Upload any prescription — printed or handwritten — and instantly understand it in your local language with voice output.</p>
    <div class="hero-pills">
        <span class="hero-pill">🇮🇳 Hindi</span>
        <span class="hero-pill">🌿 Telugu</span>
        <span class="hero-pill">🎭 Tamil</span>
        <span class="hero-pill">🌴 Malayalam</span>
        <span class="hero-pill">🌸 Kannada</span>
        <span class="hero-pill">🐟 Bengali</span>
        <span class="hero-pill">🔊 Voice Output</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  LAYOUT: Left (upload + settings) | Right (results)
# ─────────────────────────────────────────
left_col, right_col = st.columns([1, 1.6], gap="large")

with left_col:
    # Upload
    st.markdown('<div class="upload-label">📁 Upload Prescription</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "upload", type=["jpg", "jpeg", "png", "webp", "bmp"],
        label_visibility="collapsed",
        help="Supports printed and handwritten prescriptions"
    )

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption=f"{uploaded_file.name}", use_container_width=True)

    # Language selector
    st.markdown('<div class="lang-card">', unsafe_allow_html=True)
    language = st.selectbox("🌐 Explain & translate in:", [
        "Hindi (हिन्दी)", "Telugu (తెలుగు)", "Tamil (தமிழ்)",
        "Malayalam (മലയാളം)", "Kannada (ಕನ್ನಡ)", "Bengali (বাংলা)", "English"
    ])
    st.markdown('</div>', unsafe_allow_html=True)

    lang_map = {
        "Hindi (हिन्दी)":     ("hi", "Hindi"),
        "Telugu (తెలుగు)":    ("te", "Telugu"),
        "Tamil (தமிழ்)":      ("ta", "Tamil"),
        "Malayalam (മലയാളം)": ("ml", "Malayalam"),
        "Kannada (ಕನ್ನಡ)":    ("kn", "Kannada"),
        "Bengali (বাংলা)":    ("bn", "Bengali"),
        "English":            ("en", "English"),
    }
    tts_lang, lang_name = lang_map[language]

    parse_clicked = st.button("🚀 Parse Prescription", disabled=not uploaded_file)

    if not uploaded_file:
        st.markdown("""
        <div style="margin-top:1.5rem; background:white; border-radius:14px; padding:1.2rem 1.4rem;
            border:1px solid #e4ede8; font-size:0.85rem; color:#666; line-height:1.8;">
            <b style="color:#0f5c30;">How it works:</b><br>
            1️⃣ Upload a prescription image<br>
            2️⃣ Select your language<br>
            3️⃣ Click Parse — Gemini reads it<br>
            4️⃣ Get medicines explained + audio
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────
#  CORE FUNCTIONS
# ─────────────────────────────────────────
def gemini_ocr(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image_bytes = buf.getvalue()  # extract once, reuse safely across retries

    for attempt in range(4):
        try:
            response = model.generate_content([
                "You are a precise OCR engine. Extract ALL text from this medical prescription image "
                "exactly as written. Output only the raw extracted text, preserve line breaks. "
                "If handwritten, read carefully and accurately.",
                {"mime_type": "image/png", "data": image_bytes}
            ])
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                waits = [10, 30, 60, 90]
                time.sleep(waits[attempt])
                print(f"Fall back executed at: {waits[attempt]}")
            else:
                raise

def gemini_parse(raw_text: str, lang_name: str) -> dict:
    lang_key = lang_name.lower()
    prompt = f"""You are an expert medical prescription parser and translator for Indian languages.

Raw prescription text:
---
{raw_text}
---

Tasks:
1. Parse all medicines with dosage, frequency, duration.
2. Extract patient name, doctor name, date.
3. Identify diagnosis or condition if mentioned.
4. Explain each medicine in simple, plain {lang_name} that a rural patient can understand.
5. Write a complete patient-friendly summary in {lang_name}.
6. Write general instructions (with food, timing, storage) in {lang_name}.
7. List any important warnings.

Return ONLY valid JSON, no markdown fences, no extra text:
{{
  "patient_name": "...",
  "doctor_name": "...",
  "date": "...",
  "diagnosis": "...",
  "medicines": [
    {{
      "name": "...",
      "dosage": "...",
      "frequency": "...",
      "duration": "...",
      "purpose": "one line in English what this medicine is for",
      "explanation_{lang_key}": "plain simple explanation in {lang_name}"
    }}
  ],
  "summary_{lang_key}": "Complete patient-friendly summary in {lang_name}",
  "general_instructions_{lang_key}": "Instructions about food, timing, storage in {lang_name}",
  "warnings": ["warning 1", "warning 2"]
}}

Use "Not specified" for missing fields. All explanations/summaries MUST be in {lang_name}."""

    response = model.generate_content(prompt)
    text = response.text.strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else parts[0]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def tts_audio(text: str, lang_code: str) -> bytes | None:
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang_code, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


# ─────────────────────────────────────────
#  RIGHT COLUMN — RESULTS
# ─────────────────────────────────────────

with right_col:
    if not uploaded_file:
        st.markdown("""
        <div class="empty-state">
            <div class="es-icon">🏥</div>
            <h3>Ready to parse your prescription</h3>
            <p>Upload a prescription image on the left, choose your language, and click Parse.</p>
        </div>
        """, unsafe_allow_html=True)

    elif parse_clicked:
        # ── Progress steps ──
        steps_placeholder = st.empty()

        def render_steps(active: int):
            statuses = ["", "", "", ""]
            for i in range(4):
                if i < active:
                    statuses[i] = "done"
                elif i == active:
                    statuses[i] = "active"
            labels = ["OCR Extraction", "AI Parsing", "Translation", "Voice Output"]
            icons  = ["🔍", "🤖", "🌐", "🔊"]
            html = '<div class="steps-row">'
            for i, (label, icon) in enumerate(zip(labels, icons)):
                html += f'<div class="step-item {statuses[i]}"><div class="step-num">{"✓" if statuses[i]=="done" else i+1}</div><div class="step-label">{icon} {label}</div></div>'
            html += '</div>'
            steps_placeholder.markdown(html, unsafe_allow_html=True)

        # ── STEP 1: OCR ──
        render_steps(0)
        with st.spinner("🔍 Reading prescription with Gemini Vision..."):
            try:
                raw_text = gemini_ocr(image)
            except Exception as e:
                st.error(f"OCR failed: {e}")
                st.stop()

        # ── STEP 2 & 3: Parse + Translate ──
        render_steps(1)
        with st.spinner(f"🤖 Parsing medicines & translating to {lang_name}..."):
            try:
                parsed = gemini_parse(raw_text, lang_name)
            except json.JSONDecodeError:
                st.error("Gemini returned malformed JSON. Please try again.")
                st.stop()
            except Exception as e:
                st.error(f"Parsing failed: {e}")
                st.stop()

        render_steps(2)
        lang_key = lang_name.lower()

        # ── Patient / Doctor / Date ──
        st.markdown('<div class="section-header"><div class="dot"></div><h3>Patient Information</h3></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        tiles = [
            (c1, "👤", "Patient",  parsed.get("patient_name","Not specified")),
            (c2, "👨‍⚕️", "Doctor",   parsed.get("doctor_name","Not specified")),
            (c3, "📅", "Date",     parsed.get("date","Not specified")),
        ]
        for col, icon, label, value in tiles:
            with col:
                st.markdown(f"""
                <div class="info-tile">
                    <div class="tile-icon">{icon}</div>
                    <div class="tile-label">{label}</div>
                    <div class="tile-value">{value}</div>
                </div>""", unsafe_allow_html=True)

        # ── Diagnosis ──
        diag = parsed.get("diagnosis","Not specified")
        if diag != "Not specified":
            st.markdown(f"""
            <div class="diagnosis-banner" style="margin-top:0.8rem;">
                <div class="d-icon">🩺</div>
                <div><div class="d-label">Diagnosis / Condition</div>
                <div class="d-value">{diag}</div></div>
            </div>""", unsafe_allow_html=True)

        # ── Medicines ──
        medicines = parsed.get("medicines", [])
        if medicines:
            st.markdown(f'<div class="section-header"><div class="dot"></div><h3>Medicines ({len(medicines)} prescribed)</h3></div>', unsafe_allow_html=True)
            for med in medicines:
                exp = med.get(f"explanation_{lang_key}", "")
                purpose = med.get("purpose", "")
                dosage   = med.get("dosage","—")
                freq     = med.get("frequency","—")
                duration = med.get("duration","—")
                st.markdown(f"""
                <div class="med-card">
                    <div class="med-header">
                        <div class="med-pill-icon">💊</div>
                        <div>
                            <div class="med-name">{med.get('name','Unknown')}</div>
                            {f'<div style="font-size:0.8rem;color:#666;margin-top:0.1rem;">{purpose}</div>' if purpose else ''}
                        </div>
                    </div>
                    <div class="med-badges">
                        <span class="badge">📏 {dosage}</span>
                        <span class="badge">🔁 {freq}</span>
                        <span class="badge">⏱️ {duration}</span>
                    </div>
                    {f'<div class="med-explanation"><div class="exp-label">📖 {lang_name} Explanation</div>{exp}</div>' if exp else ''}
                </div>""", unsafe_allow_html=True)

        # ── Summary ──
        summary = parsed.get(f"summary_{lang_key}", "")
        if summary:
            st.markdown('<div class="section-header"><div class="dot"></div><h3>Patient Summary</h3></div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="summary-card">
                <div class="sum-label">📝 Summary in {lang_name}</div>
                <div class="sum-text">{summary}</div>
            </div>""", unsafe_allow_html=True)

        # ── Instructions ──
        instructions = parsed.get(f"general_instructions_{lang_key}", "")
        if instructions and instructions != "Not specified":
            st.markdown(f"""
            <div class="instr-card">
                <div class="instr-label">📋 General Instructions ({lang_name})</div>
                <div class="instr-text">{instructions}</div>
            </div>""", unsafe_allow_html=True)

        # ── Warnings ──
        warnings = parsed.get("warnings", [])
        if warnings:
            st.markdown('<div class="section-header"><div class="dot"></div><h3>⚠️ Warnings</h3></div>', unsafe_allow_html=True)
            for w in warnings:
                st.markdown(f'<div class="warn-card"><div class="warn-icon">⚠️</div><div class="warn-text">{w}</div></div>', unsafe_allow_html=True)

        # ── Voice Output ──
        render_steps(3)
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-header"><div class="dot"></div><h3>🔊 Voice Output</h3></div>', unsafe_allow_html=True)

        tts_text = summary or raw_text
        if instructions and instructions != "Not specified":
            tts_text += ". " + instructions

        with st.spinner("🔊 Generating audio..."):
            audio_bytes = tts_audio(tts_text, tts_lang)

        if audio_bytes:
            st.markdown('<div class="audio-card"><div class="aud-label">🔊 Listen in ' + lang_name + '</div>', unsafe_allow_html=True)
            st.audio(audio_bytes, format="audio/mp3")
            st.markdown('</div>', unsafe_allow_html=True)
            st.download_button("⬇️ Download Audio (.mp3)",
                data=audio_bytes, file_name=f"prescription_{tts_lang}.mp3", mime="audio/mp3")
        else:
            st.info("Install gTTS for voice output: `pip install gtts`")

        # ── Raw OCR + JSON ──
        render_steps(4)
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        with st.expander("📄 View Raw OCR Text"):
            st.markdown(f'<div class="raw-text-box">{raw_text}</div>', unsafe_allow_html=True)
        with st.expander("🗂️ Export Parsed JSON"):
            st.json(parsed)
            st.download_button("⬇️ Download JSON",
                data=json.dumps(parsed, ensure_ascii=False, indent=2),
                file_name="prescription_parsed.json", mime="application/json")

        st.markdown("""
        <div style="text-align:center; color:#aaa; font-size:0.78rem; margin-top:1.5rem;">
            ⚕️ For informational purposes only. Always consult a qualified healthcare professional.
        </div>""", unsafe_allow_html=True)

    else:
        # Image uploaded but not parsed yet
        st.markdown("""
        <div class="empty-state">
            <div class="es-icon">✅</div>
            <h3>Image ready!</h3>
            <p>Select your language and click <b>Parse Prescription</b> to begin.</p>
        </div>
        """, unsafe_allow_html=True)