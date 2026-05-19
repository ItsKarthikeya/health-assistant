import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="HealthPulse Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Dark medical theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #0a0f1e;
        color: #e8f4f8;
    }
    .stApp { background-color: #0a0f1e; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0d1526 100%);
        border-right: 1px solid #1e3a5f;
    }
    [data-testid="stSidebar"] * { color: #e8f4f8 !important; }

    /* Cards */
    .health-card {
        background: #1a2235;
        border: 1px solid #1e3a5f;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .stat-card {
        background: #1a2235;
        border: 1px solid #1e3a5f;
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        border-top: 3px solid #00d4ff;
    }
    .stat-value { font-size: 2rem; font-weight: 800; color: #00d4ff; }
    .stat-label { font-size: 0.75rem; color: #6b8cae; text-transform: uppercase; letter-spacing: 1px; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff, #00ff9d) !important;
        color: #0a0f1e !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px 22px !important;
        width: 100%;
    }
    .stButton > button:hover { opacity: 0.85; transform: translateY(-1px); }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stTimeInput > div > div > input,
    .stTextArea textarea {
        background: #111827 !important;
        border: 1px solid #1e3a5f !important;
        color: #e8f4f8 !important;
        border-radius: 10px !important;
    }

    /* Chat messages */
    .chat-user {
        background: linear-gradient(135deg, #00d4ff33, #00ff9d22);
        border: 1px solid #00d4ff44;
        border-radius: 16px 16px 4px 16px;
        padding: 12px 16px;
        margin: 8px 0;
        margin-left: 20%;
        color: #e8f4f8;
    }
    .chat-ai {
        background: #1a2235;
        border: 1px solid #1e3a5f;
        border-radius: 16px 16px 16px 4px;
        padding: 12px 16px;
        margin: 8px 0;
        margin-right: 20%;
        color: #e8f4f8;
    }

    /* Progress bars */
    .stProgress > div > div { background: #1e3a5f; }
    .stProgress > div > div > div { background: linear-gradient(90deg, #00d4ff, #00ff9d); }

    /* Metric */
    [data-testid="metric-container"] {
        background: #1a2235;
        border: 1px solid #1e3a5f;
        border-radius: 14px;
        padding: 14px;
        border-top: 3px solid #00d4ff;
    }
    [data-testid="metric-container"] label { color: #6b8cae !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #00d4ff !important; font-weight: 800; }

    /* Divider */
    hr { border-color: #1e3a5f !important; }

    /* Success / warning */
    .stSuccess { background: #00ff9d22 !important; border: 1px solid #00ff9d44 !important; border-radius: 10px; }
    .stWarning { background: #ffd16622 !important; border: 1px solid #ffd16644 !important; border-radius: 10px; }
    .stError   { background: #ff6b6b22 !important; border: 1px solid #ff6b6b44 !important; border-radius: 10px; }

    /* Section headers */
    h1, h2, h3 { color: #e8f4f8 !important; }
    .section-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #00d4ff;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #1e3a5f;
    }

    /* Dataframe */
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    .dataframe { background: #1a2235 !important; color: #e8f4f8 !important; }

    /* Selectbox label */
    label { color: #6b8cae !important; font-size: 0.85rem !important; }

    /* Pill badge */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .badge-green  { background: #00ff9d22; color: #00ff9d; border: 1px solid #00ff9d44; }
    .badge-red    { background: #ff6b6b22; color: #ff6b6b; border: 1px solid #ff6b6b44; }
    .badge-yellow { background: #ffd16622; color: #ffd166; border: 1px solid #ffd16644; }
    .badge-blue   { background: #00d4ff22; color: #00d4ff; border: 1px solid #00d4ff44; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
@st.cache_resource
def get_db():
    conn = sqlite3.connect("health_assistant.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dose TEXT,
            time TEXT,
            days TEXT DEFAULT 'All',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS health_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TEXT NOT NULL,
            steps INTEGER DEFAULT 0,
            water REAL DEFAULT 0,
            calories INTEGER DEFAULT 0,
            sleep REAL DEFAULT 0,
            weight REAL,
            mood TEXT,
            notes TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS med_intake (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            med_id INTEGER,
            taken_date TEXT,
            taken INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn, c

conn, c = get_db()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_meds():
    c.execute("SELECT * FROM medications ORDER BY time")
    return c.fetchall()

def get_logs():
    c.execute("SELECT * FROM health_logs ORDER BY log_date DESC LIMIT 30")
    return c.fetchall()

def get_today_log():
    today = date.today().isoformat()
    c.execute("SELECT * FROM health_logs WHERE log_date=?", (today,))
    return c.fetchone()

def bmi_category(bmi):
    if bmi < 18.5: return "Underweight", "#ffd166"
    if bmi < 25:   return "Normal ✓", "#00ff9d"
    if bmi < 30:   return "Overweight", "#ffd166"
    return "Obese", "#ff6b6b"


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "👋 Hello! I'm your **HealthPulse AI** — ask me anything about medications, symptoms, nutrition, fitness, or general health advice. I'm here to help!"}
    ]
if "chat_input_key" not in st.session_state:
    st.session_state.chat_input_key = 0


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🩺 HealthPulse")
    st.markdown("*Your Personal Health Assistant*")
    st.markdown("---")

    menu = st.selectbox("Navigation", [
        "🏠  Dashboard",
        "💊  Medications",
        "🏃  Fitness Tracker",
        "🔍  Symptom Checker",
        "⚖️  BMI & Tools",
        "🤖  AI Health Chat",
    ], label_visibility="collapsed")

    st.markdown("---")

    # Quick stats in sidebar
    today_log = get_today_log()
    st.markdown("### Today's Quick Stats")
    if today_log:
        st.metric("👣 Steps", f"{today_log[2]:,}" if today_log[2] else "—")
        st.metric("💧 Water", f"{today_log[3]}L" if today_log[3] else "—")
        st.metric("😴 Sleep", f"{today_log[5]}h" if today_log[5] else "—")
    else:
        st.info("No data logged today")

    st.markdown("---")
    now = datetime.now()
    st.markdown(f"📅 **{now.strftime('%A, %B %d')}**")
    st.markdown(f"🕐 **{now.strftime('%I:%M %p')}**")


# ─────────────────────────────────────────────
# ── DASHBOARD ──
# ─────────────────────────────────────────────
if "Dashboard" in menu:
    hour = datetime.now().hour
    greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"

    st.markdown(f"# {greeting}! 👋")
    st.markdown("Here's your health overview for today.")
    st.markdown("---")

    # Stats row
    today_log = get_today_log()
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("👣 Steps", f"{today_log[2]:,}" if today_log and today_log[2] else "—", help="Daily step count")
    with col2: st.metric("💧 Water", f"{today_log[3]}L" if today_log and today_log[3] else "—", help="Water intake today")
    with col3: st.metric("🔥 Calories", f"{today_log[4]:,}" if today_log and today_log[4] else "—")
    with col4: st.metric("😴 Sleep", f"{today_log[5]}h" if today_log and today_log[5] else "—")
    with col5:
        meds = get_meds()
        st.metric("💊 Meds", f"{len(meds)}", help="Total medications scheduled")

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 💊 Today's Medications")
        meds = get_meds()
        if not meds:
            st.info("No medications added yet. Go to **Medications** to add some.")
        else:
            for med in meds:
                with st.container():
                    m1, m2 = st.columns([3, 1])
                    with m1:
                        st.markdown(f"**{med[1]}** — {med[3] or '—'}")
                        st.caption(f"💊 {med[2] or 'N/A'} · {med[4] or 'Daily'}")
                    with m2:
                        key = f"taken_{med[0]}"
                        if st.checkbox("Taken", key=key):
                            st.markdown('<span class="badge badge-green">✓ Done</span>', unsafe_allow_html=True)
                    st.markdown("---")

    with col_b:
        st.markdown("### 📅 Recent Health History")
        logs = get_logs()
        if logs:
            df = pd.DataFrame(logs, columns=["ID","Date","Steps","Water(L)","Calories","Sleep(h)","Weight","Mood","Notes"])
            df = df[["Date","Steps","Water(L)","Calories","Sleep(h)","Mood"]].head(7)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No health logs yet. Go to **Fitness Tracker** to log data.")

    # Quick water log
    st.markdown("### 💧 Quick Water Log")
    wc1, wc2, wc3, wc4 = st.columns(4)
    for col, amount in zip([wc1, wc2, wc3, wc4], [0.25, 0.5, 0.75, 1.0]):
        with col:
            if st.button(f"+{amount}L 💧"):
                today_str = date.today().isoformat()
                existing = get_today_log()
                if existing:
                    new_water = round((existing[3] or 0) + amount, 2)
                    c.execute("UPDATE health_logs SET water=? WHERE log_date=?", (new_water, today_str))
                else:
                    c.execute("INSERT INTO health_logs (log_date, water) VALUES (?,?)", (today_str, amount))
                conn.commit()
                st.rerun()


# ─────────────────────────────────────────────
# ── MEDICATIONS ──
# ─────────────────────────────────────────────
elif "Medications" in menu:
    st.markdown("# 💊 Medication Manager")
    st.markdown("---")

    tab1, tab2 = st.tabs(["➕ Add Medication", "📋 View All"])

    with tab1:
        with st.form("add_med_form"):
            st.markdown("### Add New Medication")
            c1, c2 = st.columns(2)
            with c1:
                med_name = st.text_input("Medicine Name *", placeholder="e.g. Vitamin D3")
                med_dose = st.text_input("Dosage", placeholder="e.g. 1 tablet, 500mg")
            with c2:
                med_time = st.time_input("Time to Take")
                med_days = st.multiselect("Days", ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
                                           default=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
            med_notes = st.text_area("Notes (optional)", placeholder="Take with food, avoid alcohol, etc.")

            submitted = st.form_submit_button("➕ Add Medication")
            if submitted:
                if med_name:
                    days_str = ",".join(med_days) if med_days else "All"
                    c.execute("INSERT INTO medications (name, dose, time, days, notes) VALUES (?,?,?,?,?)",
                              (med_name, med_dose, med_time.strftime("%H:%M"), days_str, med_notes))
                    conn.commit()
                    st.success(f"✅ **{med_name}** added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a medicine name.")

    with tab2:
        meds = get_meds()
        if not meds:
            st.info("No medications added yet.")
        else:
            for med in meds:
                with st.expander(f"💊 {med[1]} — {med[3] or 'No time set'}"):
                    mc1, mc2, mc3 = st.columns([2, 2, 1])
                    with mc1:
                        st.markdown(f"**Dose:** {med[2] or 'Not specified'}")
                        st.markdown(f"**Time:** {med[3] or '—'}")
                    with mc2:
                        st.markdown(f"**Days:** {med[4] or 'All'}")
                        st.markdown(f"**Notes:** {med[5] or 'None'}")
                    with mc3:
                        if st.button("🗑️ Delete", key=f"del_{med[0]}"):
                            c.execute("DELETE FROM medications WHERE id=?", (med[0],))
                            conn.commit()
                            st.success("Deleted!")
                            st.rerun()


# ─────────────────────────────────────────────
# ── FITNESS TRACKER ──
# ─────────────────────────────────────────────
elif "Fitness" in menu:
    st.markdown("# 🏃 Fitness & Health Tracker")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📝 Log Today", "📊 History & Progress"])

    with tab1:
        today_log = get_today_log()
        st.markdown("### Log Today's Health Data")

        with st.form("fitness_form"):
            fc1, fc2 = st.columns(2)
            with fc1:
                steps   = st.number_input("👣 Steps Walked", min_value=0, value=int(today_log[2]) if today_log and today_log[2] else 0)
                water   = st.number_input("💧 Water Intake (litres)", min_value=0.0, step=0.25, value=float(today_log[3]) if today_log and today_log[3] else 0.0)
                weight  = st.number_input("⚖️ Weight (kg)", min_value=0.0, step=0.1, value=float(today_log[6]) if today_log and today_log[6] else 0.0)
            with fc2:
                calories= st.number_input("🔥 Calories Consumed", min_value=0, value=int(today_log[4]) if today_log and today_log[4] else 0)
                sleep   = st.number_input("😴 Sleep Last Night (hrs)", min_value=0.0, max_value=24.0, step=0.5, value=float(today_log[5]) if today_log and today_log[5] else 0.0)
                mood    = st.selectbox("😊 Mood", ["", "😄 Great", "🙂 Good", "😐 Okay", "😔 Low", "😩 Terrible"],
                                       index=0)
            notes = st.text_area("📝 Notes", value=today_log[8] if today_log and today_log[8] else "")

            if st.form_submit_button("💾 Save Today's Data"):
                today_str = date.today().isoformat()
                if today_log:
                    c.execute("""UPDATE health_logs SET steps=?,water=?,calories=?,sleep=?,weight=?,mood=?,notes=?
                                 WHERE log_date=?""", (steps, water, calories, sleep, weight or None, mood, notes, today_str))
                else:
                    c.execute("""INSERT INTO health_logs (log_date,steps,water,calories,sleep,weight,mood,notes)
                                 VALUES (?,?,?,?,?,?,?,?)""", (today_str, steps, water, calories, sleep, weight or None, mood, notes))
                conn.commit()
                st.success("✅ Health data saved!")
                st.rerun()

        # Goals progress
        st.markdown("### 🎯 Today's Goals")
        gc1, gc2, gc3, gc4 = st.columns(4)
        today_log = get_today_log()
        with gc1:
            s = int(today_log[2]) if today_log and today_log[2] else 0
            st.markdown(f"**👣 Steps** — {s:,} / 10,000")
            st.progress(min(s / 10000, 1.0))
        with gc2:
            w = float(today_log[3]) if today_log and today_log[3] else 0
            st.markdown(f"**💧 Water** — {w}L / 2.5L")
            st.progress(min(w / 2.5, 1.0))
        with gc3:
            cal = int(today_log[4]) if today_log and today_log[4] else 0
            st.markdown(f"**🔥 Calories** — {cal} / 2000")
            st.progress(min(cal / 2000, 1.0))
        with gc4:
            sl = float(today_log[5]) if today_log and today_log[5] else 0
            st.markdown(f"**😴 Sleep** — {sl}h / 8h")
            st.progress(min(sl / 8, 1.0))

    with tab2:
        logs = get_logs()
        if logs:
            df = pd.DataFrame(logs, columns=["ID","Date","Steps","Water(L)","Calories","Sleep(h)","Weight(kg)","Mood","Notes"])
            display_df = df[["Date","Steps","Water(L)","Calories","Sleep(h)","Weight(kg)","Mood"]].copy()
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            # Charts
            st.markdown("### 📈 Trends (Last 14 Days)")
            chart_df = df.iloc[:14][::-1].copy()
            chart_df["Steps"] = pd.to_numeric(chart_df["Steps"], errors="coerce")
            chart_df["Water(L)"] = pd.to_numeric(chart_df["Water(L)"], errors="coerce")

            cht1, cht2 = st.columns(2)
            with cht1:
                st.markdown("**👣 Steps**")
                st.bar_chart(chart_df.set_index("Date")["Steps"])
            with cht2:
                st.markdown("**💧 Water Intake**")
                st.line_chart(chart_df.set_index("Date")["Water(L)"])
        else:
            st.info("No logs yet. Log your first entry above!")


# ─────────────────────────────────────────────
# ── SYMPTOM CHECKER ──
# ─────────────────────────────────────────────
elif "Symptom" in menu:
    st.markdown("# 🔍 Symptom Checker")
    st.markdown("> ⚠️ *This tool provides general information only. Always consult a qualified healthcare professional for diagnosis and treatment.*")
    st.markdown("---")

    SYMPTOM_DB = {
        "headache": {
            "info": "A headache can result from tension, dehydration, eye strain, sinusitis, or migraines.",
            "severity": "Mild",
            "color": "badge-green",
            "tips": ["Drink 2-3 glasses of water", "Rest in a quiet, dark room", "Apply a cold or warm compress", "Try OTC pain relievers (paracetamol/ibuprofen)", "Reduce screen time"],
            "see_doctor": "Seek care if headache is sudden/severe, with stiff neck, vision changes, or lasts >72 hours."
        },
        "fever": {
            "info": "Fever (>38°C) is the body's immune response to infection — bacterial, viral, or inflammatory.",
            "severity": "Moderate",
            "color": "badge-yellow",
            "tips": ["Stay well hydrated", "Rest as much as possible", "Use paracetamol or ibuprofen", "Apply cool damp cloth to forehead", "Monitor temperature every 2-4 hours"],
            "see_doctor": "See a doctor if fever >39.5°C, lasts >3 days, or accompanied by rash, breathing difficulty."
        },
        "cough": {
            "info": "A cough can be caused by viral infection (cold/flu), allergies, asthma, acid reflux, or bacterial infection.",
            "severity": "Mild",
            "color": "badge-green",
            "tips": ["Honey + warm water or lemon tea", "Stay hydrated", "Use a humidifier", "Avoid smoking/irritants", "Elevate head while sleeping"],
            "see_doctor": "Consult a doctor if cough persists >2 weeks, has blood, or causes breathing difficulty."
        },
        "fatigue": {
            "info": "Fatigue can result from poor sleep, anemia, thyroid issues, dehydration, depression, or overexertion.",
            "severity": "Mild",
            "color": "badge-green",
            "tips": ["Aim for 7-9 hours of sleep", "Eat balanced meals", "Exercise regularly", "Reduce caffeine/alcohol", "Check iron/vitamin D levels"],
            "see_doctor": "See a doctor if fatigue is persistent (>2 weeks) with no clear cause."
        },
        "chest pain": {
            "info": "Chest pain can range from mild (muscle strain, acid reflux) to life-threatening (heart attack, pulmonary embolism).",
            "severity": "SEVERE",
            "color": "badge-red",
            "tips": ["Call emergency services (112/108) IMMEDIATELY if sudden or severe", "Do NOT ignore or wait", "Sit upright and stay calm", "Chew aspirin if available and no allergy"],
            "see_doctor": "⚠️ EMERGENCY — Call 112/108 immediately if chest pain is sudden, crushing, or spreads to arm/jaw."
        },
        "diabetes": {
            "info": "Diabetes is a chronic metabolic condition causing high blood sugar due to insufficient insulin production or resistance.",
            "severity": "Chronic",
            "color": "badge-yellow",
            "tips": ["Monitor blood sugar regularly", "Follow a low-glycemic diet", "Exercise 30 min/day", "Take medications as prescribed", "Attend regular check-ups"],
            "see_doctor": "Always managed with a doctor. See one immediately if blood sugar is extremely high/low."
        },
        "cold": {
            "info": "The common cold is a viral infection of the upper respiratory tract, usually caused by rhinovirus.",
            "severity": "Mild",
            "color": "badge-green",
            "tips": ["Rest and sleep well", "Drink warm fluids", "Saline nasal spray", "Steam inhalation", "Vitamin C supplements"],
            "see_doctor": "See a doctor if symptoms worsen after 10 days or include high fever/breathing difficulty."
        },
        "back pain": {
            "info": "Back pain is commonly caused by muscle strain, poor posture, herniated disc, or arthritis.",
            "severity": "Mild-Moderate",
            "color": "badge-yellow",
            "tips": ["Apply hot/cold pack", "Gentle stretching", "Avoid prolonged sitting", "Sleep on firm mattress", "OTC anti-inflammatories"],
            "see_doctor": "Seek care if pain radiates down legs, causes numbness, or follows an injury."
        },
    }

    col1, col2 = st.columns([1, 1])

    with col1:
        query = st.text_input("🔍 Enter symptom", placeholder="e.g. headache, fever, cough...")

        st.markdown("**Common symptoms — click to check:**")
        pill_cols = st.columns(3)
        symptoms_list = list(SYMPTOM_DB.keys())
        for i, sym in enumerate(symptoms_list):
            with pill_cols[i % 3]:
                if st.button(sym.title(), key=f"pill_{sym}"):
                    query = sym

        result = None
        if query:
            key = None
            for k in SYMPTOM_DB:
                if k in query.lower():
                    key = k
                    break
            result = SYMPTOM_DB.get(key) if key else None

    with col2:
        if query and result:
            sev_color = {"Mild": "badge-green", "Moderate": "badge-yellow", "SEVERE": "badge-red", "Chronic": "badge-yellow", "Mild-Moderate": "badge-yellow"}.get(result["severity"], "badge-blue")
            st.markdown(f'<span class="badge {sev_color}">{result["severity"].upper()}</span>', unsafe_allow_html=True)
            st.markdown(f"### {query.title()}")
            st.info(result["info"])

            st.markdown("**✅ Recommendations:**")
            for tip in result["tips"]:
                st.markdown(f"• {tip}")

            st.markdown("---")
            st.warning(f"🏥 **When to see a doctor:** {result['see_doctor']}")

            if st.button("🤖 Ask AI for More Details"):
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"Tell me more about {query} — causes, treatment, and when to see a doctor."
                })
                st.session_state["menu_jump"] = "AI"
                st.info("Message added! Go to **🤖 AI Health Chat** in the menu.")

        elif query and not result:
            st.warning("No specific data found for that symptom. Try the AI Chat for personalized guidance!")


# ─────────────────────────────────────────────
# ── BMI & TOOLS ──
# ─────────────────────────────────────────────
elif "BMI" in menu:
    st.markdown("# ⚖️ Health Tools")
    st.markdown("---")

    tool_tab1, tool_tab2, tool_tab3 = st.tabs(["⚖️ BMI Calculator", "🔥 Calorie/TDEE", "💊 Medicine Info"])

    with tool_tab1:
        st.markdown("### Body Mass Index (BMI)")
        bc1, bc2 = st.columns(2)
        with bc1:
            height = st.number_input("Height (cm)", min_value=50.0, max_value=250.0, value=170.0)
            weight_bmi = st.number_input("Weight (kg)", min_value=10.0, max_value=300.0, value=70.0)
            age = st.number_input("Age", min_value=1, max_value=120, value=25)

        bmi = weight_bmi / ((height / 100) ** 2)
        cat, cat_color = bmi_category(bmi)

        with bc2:
            st.markdown(f"""
            <div style="text-align:center; padding: 30px; background:#1a2235; border-radius:16px; border: 2px solid {cat_color};">
                <div style="font-size:3.5rem; font-weight:900; color:{cat_color};">{bmi:.1f}</div>
                <div style="font-size:1.2rem; color:{cat_color}; font-weight:700;">{cat}</div>
                <div style="color:#6b8cae; font-size:0.85rem; margin-top:8px;">Body Mass Index</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### BMI Reference Chart")
        ref_data = {"Category": ["Underweight","Normal","Overweight","Obese"],
                    "BMI Range": ["< 18.5","18.5 – 24.9","25.0 – 29.9","≥ 30.0"],
                    "Risk Level": ["Low-Moderate","Minimal","Increased","High"]}
        st.dataframe(pd.DataFrame(ref_data), use_container_width=True, hide_index=True)

        # Ideal weight
        ideal_min = 18.5 * ((height / 100) ** 2)
        ideal_max = 24.9 * ((height / 100) ** 2)
        st.info(f"💡 **Your ideal weight range** for {height:.0f}cm: **{ideal_min:.1f}kg – {ideal_max:.1f}kg**")

    with tool_tab2:
        st.markdown("### Daily Calorie (TDEE) Calculator")
        tc1, tc2 = st.columns(2)
        with tc1:
            t_gender = st.selectbox("Gender", ["Male", "Female"])
            t_age = st.number_input("Age", min_value=1, max_value=120, value=25, key="t_age")
            t_height = st.number_input("Height (cm)", min_value=50.0, value=170.0, key="t_h")
            t_weight = st.number_input("Weight (kg)", min_value=10.0, value=70.0, key="t_w")
        with tc2:
            t_activity = st.selectbox("Activity Level", [
                "Sedentary (desk job, no exercise)",
                "Light (1-3 days/week)",
                "Moderate (3-5 days/week)",
                "Active (6-7 days/week)",
                "Very Active (athlete/physical job)"
            ])
            t_goal = st.selectbox("Goal", ["Maintain weight", "Lose weight (−500 kcal)", "Build muscle (+300 kcal)"])

        act_map = {
            "Sedentary (desk job, no exercise)": 1.2,
            "Light (1-3 days/week)": 1.375,
            "Moderate (3-5 days/week)": 1.55,
            "Active (6-7 days/week)": 1.725,
            "Very Active (athlete/physical job)": 1.9
        }
        if t_gender == "Male":
            bmr = 88.362 + 13.397 * t_weight + 4.799 * t_height - 5.677 * t_age
        else:
            bmr = 447.593 + 9.247 * t_weight + 3.098 * t_height - 4.330 * t_age

        tdee = bmr * act_map[t_activity]
        adjust = -500 if "Lose" in t_goal else 300 if "Build" in t_goal else 0
        final_cal = int(tdee + adjust)

        st.markdown("---")
        crc1, crc2, crc3 = st.columns(3)
        with crc1: st.metric("🔥 BMR", f"{int(bmr)} kcal", help="Basal Metabolic Rate — calories at rest")
        with crc2: st.metric("⚡ TDEE", f"{int(tdee)} kcal", help="Total Daily Energy Expenditure")
        with crc3: st.metric("🎯 Your Goal", f"{final_cal} kcal")

        macros = {"Protein (g)": int(final_cal * 0.30 / 4), "Carbs (g)": int(final_cal * 0.45 / 4), "Fats (g)": int(final_cal * 0.25 / 9)}
        st.markdown("### Recommended Macros")
        mc1, mc2, mc3 = st.columns(3)
        for (label, val), col in zip(macros.items(), [mc1, mc2, mc3]):
            with col: st.metric(label, f"{val}g")

    with tool_tab3:
        st.markdown("### 💊 Medicine Quick Reference")
        med_db = {
            "Paracetamol": {"use": "Pain, fever", "dose": "500–1000mg every 4-6h", "note": "Max 4g/day. Avoid alcohol."},
            "Ibuprofen": {"use": "Pain, inflammation, fever", "dose": "200–400mg every 6-8h", "note": "Take with food. Avoid if kidney issues."},
            "Cetirizine": {"use": "Allergies, hay fever", "dose": "10mg once daily", "note": "May cause drowsiness."},
            "Amoxicillin": {"use": "Bacterial infections", "dose": "250–500mg every 8h", "note": "Prescription required. Complete full course."},
            "Omeprazole": {"use": "Acid reflux, ulcers", "dose": "20mg once daily before meal", "note": "Take 30 min before eating."},
            "Metformin": {"use": "Type 2 Diabetes", "dose": "500–1000mg twice daily", "note": "Take with meals. Prescription required."},
            "Vitamin D3": {"use": "Bone health, immunity", "dose": "1000–2000 IU daily", "note": "Take with fatty meal for absorption."},
        }
        search_med = st.text_input("Search medicine", placeholder="e.g. Paracetamol")
        meds_to_show = {k: v for k, v in med_db.items() if search_med.lower() in k.lower()} if search_med else med_db
        for med_name_db, info in meds_to_show.items():
            with st.expander(f"💊 {med_name_db}"):
                i1, i2, i3 = st.columns(3)
                with i1: st.markdown(f"**Use:** {info['use']}")
                with i2: st.markdown(f"**Dose:** {info['dose']}")
                with i3: st.markdown(f"**Note:** {info['note']}")

        st.warning("⚠️ Always follow your doctor's prescription. Never self-medicate for serious conditions.")


# ─────────────────────────────────────────────
# ── AI HEALTH CHAT ──
# ─────────────────────────────────────────────
elif "AI" in menu:
    st.markdown("# 🤖 AI Health Assistant")
    st.markdown("Powered by Claude AI — Ask me anything about your health, medications, symptoms, or fitness.")
    st.markdown("---")

    # Display messages
    for msg in st.session_state.chat_history:
        if msg["role"] == "assistant":
            st.markdown(f'<div class="chat-ai">🤖 <strong>HealthPulse AI</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-user">👤 <strong>You</strong><br>{msg["content"]}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Your question:", placeholder="e.g. What are the side effects of ibuprofen?", label_visibility="collapsed")
        col_send, col_clear = st.columns([4, 1])
        with col_send:
            send = st.form_submit_button("📤 Send Message", use_container_width=True)
        with col_clear:
            clear = st.form_submit_button("🗑️ Clear", use_container_width=True)

    if clear:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "👋 Chat cleared! How can I help you today?"}
        ]
        st.rerun()

    if send and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        with st.spinner("🤖 Thinking..."):
            try:
                client = Groq()
                system_prompt = """You are HealthPulse AI, a compassionate and knowledgeable personal health assistant. 
You help users with questions about medications, symptoms, fitness, nutrition, and general wellness.
Always:
- Give accurate, helpful, practical health information
- Use simple language, not medical jargon
- Recommend consulting a doctor for serious concerns
- Be empathetic and supportive
- Use bullet points for clarity when listing information
- Keep responses concise but complete (2-4 paragraphs max)
Never diagnose conditions definitively — you provide information, not medical diagnosis."""

                messages = [{"role": "system", "content": system_prompt}] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.chat_history
                    if m["role"] in ("user", "assistant")
                ]

                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    max_tokens=1000,
                    messages=messages
                )
                reply = response.choices[0].message.content
            except Exception as e:
                reply = f"❌ Error: {str(e)}"

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    # Quick prompt buttons
    st.markdown("### 💡 Quick Questions")
    qp_cols = st.columns(3)
    quick_prompts = [
        "How much water should I drink daily?",
        "What foods boost immunity?",
        "Tips for better sleep?",
        "How to reduce stress naturally?",
        "What vitamins should I take?",
        "How to manage Type 2 Diabetes?"
    ]
    for i, qp in enumerate(quick_prompts):
        with qp_cols[i % 3]:
            if st.button(qp, key=f"qp_{i}"):
                st.session_state.chat_history.append({"role": "user", "content": qp})
                with st.spinner("🤖 Thinking..."):
                    try:
                        client = Groq()
                        system_prompt = """You are HealthPulse AI, a compassionate and knowledgeable personal health assistant. 
You help users with questions about medications, symptoms, fitness, nutrition, and general wellness.
Always:
- Give accurate, helpful, practical health information
- Use simple language, not medical jargon
- Recommend consulting a doctor for serious concerns
- Be empathetic and supportive
- Use bullet points for clarity when listing information
- Keep responses concise but complete (2-4 paragraphs max)
Never diagnose conditions definitively — you provide information, not medical diagnosis."""

                        messages = [{"role": "system", "content": system_prompt}] + [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.chat_history
                            if m["role"] in ("user", "assistant")
                        ]

                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            max_tokens=1000,
                            messages=messages
                        )
                        reply = response.choices[0].message.content
                    except Exception as e:
                        reply = f"❌ Error: {str(e)}"

                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.rerun()
#To enable the AI chatbot feature:
#1. Create a file named `.env` in the project root folder.
#2. Add your Groq API key in this format:
#GROQ_API_KEY=your_actual_api_key
#3. Save the file.
#4. Run the project normally using:
#python -m streamlit run app.py
#The `.env` file is intentionally excluded from GitHub for security purposes.
