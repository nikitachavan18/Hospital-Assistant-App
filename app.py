"""Streamlit web app: Patient chat + Doctor view.
Run with:  python -m streamlit run app.py
"""
import itertools
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="Orthodontic Assistant", page_icon="🦷")

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

APPT_FILE = BASE / "appointments.json"
DOCTOR_PIN = os.getenv("DOCTOR_PIN", "1234")  # change this in .env



# ---------- Saving appointments to a file so they survive a restart ----------
@st.cache_resource
def init_storage():
    """Runs once when the app starts: load saved appointments."""
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

# ---------- Sidebar: choose view ----------
with st.sidebar:
    view = st.radio("View", ["Patient chat", "Doctor view"])

# =====================================================================
# DOCTOR VIEW
# =====================================================================
if view == "Doctor view":
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
    doctor = next(iter(DOCTORS.values()))
    st.subheader(f"Appointments for {doctor['name']}")

    rows = [{"ID": i, "Patient": a["patient_name"], "Date": a["date"], "Time": a["time"],
             "Visit type": a["visit_type"], "Status": a["status"]}
            for i, a in APPOINTMENTS.items()]
    df = pd.DataFrame(rows, columns=["ID", "Patient", "Date", "Time", "Visit type", "Status"])

    show_cancelled = st.checkbox("Show cancelled")
    if not show_cancelled:
        df = df[df["Status"] == "confirmed"]
    pick_date = st.text_input("Filter by date (YYYY-MM-DD), leave empty for all")
    if pick_date.strip():
        df = df[df["Date"] == pick_date.strip()]
    df = df.sort_values(["Date", "Time"]) if not df.empty else df

    st.metric("Appointments shown", len(df))
    if df.empty:
        st.info("No appointments to show.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("**Cancel an appointment**")
        confirmed_ids = [i for i in df["ID"] if APPOINTMENTS[i]["status"] == "confirmed"]
        if confirmed_ids:
            cancel_id = st.selectbox("Appointment ID", confirmed_ids)
            if st.button("Cancel this appointment"):
                tools.cancel_appointment(cancel_id)
                save_appointments()
                st.rerun()

    if st.button("Refresh"):
        st.rerun()
    st.stop()

# =====================================================================
# PATIENT CHAT
# =====================================================================
st.title("🦷 Orthodontic Assistant")
st.caption("Demo project. Not medical advice. In an emergency call 112 (ambulance 108). "
           "Please do not enter real patient data.")

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
    doctor = next(iter(DOCTORS.values()))
    st.header("Clinic")
    st.markdown(f"**{doctor['name']}**  \n{doctor['qualification']}")
    st.divider()
    if st.button("Start new chat"):
        new_chat()
        st.rerun()

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