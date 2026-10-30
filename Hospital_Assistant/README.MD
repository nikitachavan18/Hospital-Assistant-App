# Hospital_Assistant
OrthoAssistant
# Orthodontic Assistant AI Agent

A tool-calling AI agent for an **Orthodontics & Dentofacial Orthopedics** clinic.
Patients can find an orthodontist, check slots, book or cancel visits, learn about
braces/aligners/retainers, get temporary aftercare tips, and run an emergency check.

> **Disclaimer:** Demo project. It does not diagnose or give medical advice.
> In an emergency, go to a hospital or call 112 (ambulance: 108 in India).

## Features
- Doctor search by focus (braces, clear aligners, jaw growth, pediatric, complex cases)
- Appointment booking/cancelling (consultation, adjustment, retainer check, emergency repair)
- General treatment info (metal/ceramic/lingual braces, aligners, retainers, expanders, jaw surgery)
- Aftercare tips (poking wire, loose bracket, lost retainer, sore teeth...)
- Emergency/urgent red-flag triage
- Stays in scope: declines non-orthodontic requests

## Setup
```bash
git clone https://github.com/<your-username>/Ortho-Assistant.git
cd Ortho-Assistant
python -m venv venv
venv\Scripts\activate        # Windows (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env       # then add your ANTHROPIC_API_KEY
python main.py
```

## Project structure
```
Ortho-Assistant/
├── main.py                     # CLI chat loop
├── ortho_assistant/
│   ├── agent.py                # agent loop + system prompt
│   ├── tools.py                # 8 tools + JSON schemas
│   └── data.py                 # mock doctors, treatments, aftercare, appointments
├── requirements.txt
└── .env.example
```

## Example prompts
- "I want to know about clear aligners"
- "My child has a narrow upper jaw, which doctor should we see?"
- "A wire is poking my cheek"
- "Book Dr. Rohan Patil tomorrow at 10:30 for Nikita"

## Ideas to extend
- Replace mock data with SQLite/PostgreSQL
- Streamlit or FastAPI front end
- RAG over clinic FAQs and treatment brochures
- Appointment reminders and unit tests for tools