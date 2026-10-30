"""Orthodontic Assistant: website-style home page + booking chat + doctor view.
Run with:  python -m streamlit run app.py
"""
import itertools
import json
import os
from html import escape
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="Orthodontic Assistant", page_icon="🦷", layout="wide")

BASE = Path(__file__).parent
load_dotenv(BASE / ".env")
load_dotenv(BASE / "Hospital_Assistant" / ".env")

# When deployed online, keys come from Streamlit "Secrets" instead of .env
try:
    for _k in ("GEMINI_API_KEY", "GEMINI_MODEL", "DOCTOR_PIN"):
        if _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass  # no secrets file when running locally

from Hospital_Assistant import tools  # noqa: E402
from Hospital_Assistant.agent import OrthoAgent  # noqa: E402
from Hospital_Assistant.data import APPOINTMENTS, DOCTORS  # noqa: E402

# ----------------------------------------------------------------------------
# EDIT YOUR CLINIC DETAILS HERE
# ----------------------------------------------------------------------------
CLINIC_NAME = "New Shree Dental Clinic"
PHONE = "8668992833"
WHATSAPP = "918668992833"  # country code 91 + number, no + or spaces
ADDRESS = ("Shivanjali Lane No 2, Katraj - Ambegaon BK Rd, near Dattanagar, "
           "Dattanagar, chawk, Ambegaon Budruk, Pune, Maharashtra 411046")
TIMING = "10 am to 8 pm"
DOCTOR_INTRO = ("Dr. Avinash Shankar Sherker is an orthodontist whose care focuses on "
                "precision, aesthetics and comfort. He treats children, teens and adults "
                "with braces, clear aligners and bite correction, and also offers early "
                "treatment to guide jaw growth in children.")

COLLECTIONS = [
    ("Braces & Aligners", [
        ("Metal / Ceramic / Self-Ligating Braces", "Fixed braces to align teeth and correct the bite.", "braces"),
        ("Invisible / Lingual Braces", "Braces placed behind the teeth, hidden from view.", "lingual braces"),
        ("Clear Aligners", "Removable, nearly invisible trays (Invisalign, Flash, etc.).", "clear aligners"),
    ]),
    ("Kids & Growth", [
        ("Early Orthodontic Treatment", "Growth modification to guide jaw development in children.", "early orthodontic treatment"),
        ("Interceptive Orthodontics for Kids", "Early treatment while teeth and jaws are still growing.", "interceptive orthodontics for kids"),
    ]),
    ("Adults & Advanced Care", [
        ("Adult Orthodontics", "Braces and aligners planned for adult smiles.", "adult orthodontics"),
        ("Smile Designing & Aesthetic Corrections", "Improve the look of your smile.", "smile designing"),
        ("Surgical Orthodontics (Orthognathic Cases)", "Jaw surgery combined with braces for suitable cases.", "surgical orthodontics"),
        ("TMJ & Bite Correction", "Care for jaw joint and bite concerns.", "TMJ and bite correction"),
        ("Retention & Relapse Management", "Keep your results in place after treatment.", "retainers and relapse management"),
    ]),
]

APPT_FILE = BASE / "appointments.json"
DOCTOR_PIN = os.getenv("DOCTOR_PIN", "1234")  # set your own in .env or Secrets
DOCTOR = next(iter(DOCTORS.values()))

# ----------------------------------------------------------------------------
# Saving appointments to a file so they survive a restart
# ----------------------------------------------------------------------------
@st.cache_resource
def init_storage():
    if APPT_FILE.exists():
        try:
            APPOINTMENTS.update(json.loads(APPT_FILE.read_text(encoding="utf-8")))
        except Exception:
            pass
    nums = [int(k[3:]) for k in APPOINTMENTS if k[3:].isdigit()]
    tools._counter = itertools.count(max(nums, default=0) + 1)  # avoid duplicate IDs
    return True


def save_appointments():
    APPT_FILE.write_text(json.dumps(APPOINTMENTS, indent=2), encoding="utf-8")


init_storage()

# ----------------------------------------------------------------------------
# Look and feel (same colours as the clinic website)
# ----------------------------------------------------------------------------
CSS = """<style>
.stApp, [data-testid="stAppViewContainer"]{background:#F4F8F7}
[data-testid="stSidebar"]{background:#E6F1EF}
.block-container{max-width:1100px;padding-top:4.5rem}
button[kind="primary"], [data-testid="stBaseButton-primary"]{background-color:#0F766E !important;border:0 !important;color:#fff !important;font-weight:700 !important;padding:0.6rem 1.6rem !important}
button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{background-color:#0B544F !important}
.hdr{background:#10282B;color:#fff;font-weight:700;font-size:28px;padding:18px 24px;border-radius:12px;margin-bottom:40px}
.eyebrow{font-weight:700;color:#0F766E;margin-bottom:12px}
.hero-h{font-family:Georgia,serif;font-weight:600;font-size:52px;line-height:1.1;color:#10282B;max-width:760px;margin-bottom:18px}
.hero-p{font-size:19px;line-height:1.6;color:#2D4448;max-width:620px;margin-bottom:24px}
.sec-h{font-family:Georgia,serif;font-weight:600;font-size:32px;color:#10282B;margin:48px 0 18px}
.card{background:#fff;border:1px solid #D5E3E0;border-radius:12px;padding:22px;color:#2D4448}
.card h3{margin:0 0 6px;font-size:19px;color:#10282B}
.card p{margin:0;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}
.collhead{display:flex;justify-content:space-between;align-items:baseline;margin:24px 0 12px}
.collhead b{font-size:21px;color:#10282B}.collhead span{font-size:14px;color:#4B6468}
.item{display:flex;align-items:center;gap:16px;background:#fff;border:1px solid #D5E3E0;border-radius:12px;padding:14px;margin-bottom:12px}
.tile{flex:none;width:60px;height:60px;border-radius:10px;background:#D8ECE8;color:#0B544F;font-family:Georgia,serif;font-size:26px;font-weight:600;display:flex;align-items:center;justify-content:center}
.itext{flex:1;min-width:0;color:#2D4448}.itext b{display:block;font-size:17px;color:#10282B;margin-bottom:3px}.itext span{font-size:14px}
.add{flex:none;width:42px;height:42px;border-radius:8px;background:#F4F8F7;border:1px solid #D5E3E0;color:#0F766E !important;font-size:26px;text-decoration:none !important;display:flex;align-items:center;justify-content:center}
.num{width:34px;height:34px;border-radius:17px;background:#D8ECE8;color:#0B544F;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:10px}
.contact{background:#10282B;color:#E6F1EF;border-radius:12px;padding:32px;margin:48px 0 24px}
.contact h3{color:#fff;margin:0 0 6px;font-size:19px}.contact p{margin:0;line-height:1.6}
.wa{display:inline-block;margin-top:24px;background:#25D366;color:#10282B !important;font-weight:700;padding:13px 26px;border-radius:8px;text-decoration:none !important}
@media(max-width:600px){.hero-h{font-size:34px}.sec-h{font-size:26px}.hdr{font-size:22px}}
</style>"""
st.markdown(CSS, unsafe_allow_html=True)


def wa_link(text: str) -> str:
    return f"https://wa.me/{WHATSAPP}?text={quote(text)}"


def home_top_html() -> str:
    return (f'<div class="hdr">{escape(CLINIC_NAME)}</div>'
            '<div class="eyebrow">Orthodontics &amp; Dentofacial Orthopedics</div>'
            '<div class="hero-h">Straighter teeth, a healthier bite, a confident smile.</div>'
            '<div class="hero-p">Ask about braces, aligners and retainers, or book a visit '
            'in a few minutes with our appointment assistant.</div>')


def home_bottom_html() -> str:
    doc_name = escape(DOCTOR.get("name", ""))
    qual = escape(DOCTOR.get("qualification", ""))
    parts = ['<div class="sec-h">Meet the doctor</div>',
             f'<div class="card"><h3>{doc_name}</h3>'
             f'<p style="font-weight:500;margin-bottom:10px">{qual}</p>'
             f'<p>{escape(DOCTOR_INTRO)}</p></div>',
             '<div class="sec-h">Treatment catalogue</div>',
             '<p style="color:#2D4448;margin:0 0 4px">Tap + on any treatment to ask about it on WhatsApp.</p>']
    for title, items in COLLECTIONS:
        parts.append(f'<div class="collhead"><b>{escape(title)}</b><span>{len(items)} treatments</span></div>')
        for name, desc, topic in items:
            link = wa_link(f"Hello, I would like to know more about {topic}.")
            parts.append(
                f'<div class="item"><div class="tile">{escape(name[0])}</div>'
                f'<div class="itext"><b>{escape(name)}</b><span>{escape(desc)}</span></div>'
                f'<a class="add" href="{link}" target="_blank" rel="noopener" '
                f'aria-label="Ask about {escape(topic)} on WhatsApp">+</a></div>')
    parts.append('<div class="sec-h">How booking works</div><div class="grid">'
                 '<div class="card"><div class="num">1</div><h3>Open the assistant</h3><p>Tap the Book an appointment button.</p></div>'
                 '<div class="card"><div class="num">2</div><h3>Choose a day and time</h3><p>The assistant shows the free slots.</p></div>'
                 '<div class="card"><div class="num">3</div><h3>Get your confirmation</h3><p>You receive an appointment ID for your visit.</p></div></div>')
    parts.append('<div class="contact"><div class="sec-h" style="color:#fff;margin-top:0">Visit the clinic</div>'
                 '<div class="grid">'
                 f'<div><h3>Phone</h3><p>{escape(PHONE)}</p></div>'
                 f'<div><h3>Address</h3><p>{escape(ADDRESS)}</p></div>'
                 f'<div><h3>Time</h3><p>{escape(TIMING)}</p></div></div>'
                 f'<a class="wa" href="{wa_link("Hello, I would like to book an appointment.")}" '
                 'target="_blank" rel="noopener">Chat on WhatsApp</a></div>')
    return "".join(parts)


# ----------------------------------------------------------------------------
# Navigation
# ----------------------------------------------------------------------------
PAGES = ["Home", "Book appointment", "Doctor view"]
if "page" not in st.session_state:
    st.session_state.page = "Home"


def go_book():
    st.session_state.page = "Book appointment"


def go_home():
    st.session_state.page = "Home"


with st.sidebar:
    st.radio("Go to", PAGES, key="page")

page = st.session_state.page

# ============================================================================
# HOME (website style)
# ============================================================================
if page == "Home":
    st.markdown(home_top_html(), unsafe_allow_html=True)
    st.button("Book an appointment", type="primary", on_click=go_book, key="hero_book")
    st.markdown(home_bottom_html(), unsafe_allow_html=True)
    
    st.stop()

# ============================================================================
# DOCTOR VIEW
# ============================================================================
if page == "Doctor view":
    st.title("🩺 Doctor view")
    if not st.session_state.get("doctor_ok"):
        pin = st.text_input("Enter doctor PIN", type="password")
        if st.button("Open"):
            if pin == DOCTOR_PIN:
                st.session_state.doctor_ok = True
                st.rerun()
            else:
                st.error("Wrong PIN.")
        st.stop()

    if DOCTOR_PIN == "1234":
        st.warning("Default PIN in use. Set DOCTOR_PIN in your secrets or .env.")
    st.subheader(f"Appointments for {DOCTOR.get('name', '')}")

    rows = [{"ID": i, "Patient": a["patient_name"], "Date": a["date"], "Time": a["time"],
             "Visit type": a["visit_type"], "Status": a["status"]}
            for i, a in APPOINTMENTS.items()]
    df = pd.DataFrame(rows, columns=["ID", "Patient", "Date", "Time", "Visit type", "Status"])

    if not st.checkbox("Show cancelled"):
        df = df[df["Status"] == "confirmed"]
    pick_date = st.text_input("Filter by date (YYYY-MM-DD), leave empty for all")
    if pick_date.strip():
        df = df[df["Date"] == pick_date.strip()]
    if not df.empty:
        df = df.sort_values(["Date", "Time"])

    st.metric("Appointments shown", len(df))
    if df.empty:
        st.info("No appointments to show.")
    else:
        st.dataframe(df, hide_index=True)
        confirmed_ids = [i for i in df["ID"] if APPOINTMENTS[i]["status"] == "confirmed"]
        if confirmed_ids:
            st.markdown("**Cancel an appointment**")
            cancel_id = st.selectbox("Appointment ID", confirmed_ids)
            if st.button("Cancel this appointment"):
                tools.cancel_appointment(cancel_id)
                save_appointments()
                st.rerun()
    if st.button("Refresh"):
        st.rerun()
    st.stop()

# ============================================================================
# BOOK APPOINTMENT (chat page)
# ============================================================================
WELCOME = ("Hello! I can help you book or cancel an appointment and answer general "
           "questions about braces, aligners and retainers. How can I help?")


def new_chat():
    try:
        st.session_state.agent = OrthoAgent()
    except RuntimeError as e:
        st.error(str(e))
        st.stop()
    st.session_state.messages = [{"role": "assistant", "content": WELCOME}]


if "agent" not in st.session_state:
    new_chat()

with st.sidebar:
    st.header("Clinic")
    st.markdown(f"**{DOCTOR.get('name', '')}**  \n{DOCTOR.get('qualification', '')}")
    st.divider()
    if st.button("Start new chat"):
        new_chat()
        st.rerun()

st.button("← Back to home", on_click=go_home, key="back_home")
st.title("🦷 Book an appointment")
st.caption("Demo project. Not medical advice. In an emergency call 112 (ambulance 108). "
           "Please do not enter real patient data.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = st.session_state.agent.chat(prompt)
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    save_appointments()  # keep the file up to date after every message