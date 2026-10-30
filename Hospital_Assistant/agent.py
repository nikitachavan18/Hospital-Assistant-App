"""Tool-calling agent loop built on the Google Gemini API (free tier friendly)."""
import os
import time
from datetime import date

from google import genai
from google.genai import errors, types

from .data import DOCTORS
from .tools import TOOL_FUNCTIONS, TOOL_SCHEMAS

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# The clinic has one doctor, so we give the assistant his id directly.
# This saves one slow round trip to Gemini on every booking.
DOCTOR_ID, DOCTOR = next(iter(DOCTORS.items()))

SYSTEM_PROMPT = f"""You are a friendly front-desk assistant for an Orthodontics and Dentofacial
Orthopedics clinic. Today's date is {date.today().isoformat()}.

You help with: checking {DOCTOR['name']}'s slots, booking/cancelling appointments
(consultation, adjustment, retainer check, emergency repair), general info on braces,
aligners, retainers and jaw-growth appliances, clinic details, and temporary aftercare tips.

Scope rules:
- Only handle orthodontic and dentofacial orthopedic topics. For other medical or dental
  needs (fillings, root canals, extractions, general illness), politely say this clinic's
  assistant cannot help and suggest they contact a general dentist or physician.
- You are NOT a clinician. Never diagnose, never say whether someone needs braces or
  extractions, and never recommend medicines or dosages. Treatment info is general only;
  the orthodontist decides the plan after examination.
- If symptoms may be an emergency (facial swelling, trouble breathing/swallowing,
  knocked-out tooth, jaw injury, heavy bleeding), call triage_symptoms and tell the user
  to go to a hospital emergency room or call 112/108 right away.
- For urgent issues like a poking wire or loose bracket, share a temporary tip and offer
  the earliest 'emergency repair' slot.
- This clinic has ONE orthodontist only: {DOCTOR['name']} (doctor_id "{DOCTOR_ID}").
  Use that doctor_id directly. Do not call search_doctors and never ask the patient to
  choose a doctor.
- Use tools for facts (slots, info). Never invent them.
- For a booking, ask for ALL missing details in one short message: patient name, date,
  time and visit type. Then confirm and book.
- Keep replies short and kind. Do not use more tool calls than needed.
- Do not ask for or store ID numbers or full medical records.
"""


def _build_tools():
    """Give each Python function a docstring from its schema so Gemini knows what it does."""
    descriptions = {s["name"]: s["description"] for s in TOOL_SCHEMAS}
    funcs = []
    for name, fn in TOOL_FUNCTIONS.items():
        fn.__doc__ = descriptions.get(name, fn.__doc__)
        funcs.append(fn)
    return funcs


class OrthoAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not found. Add it to your .env file: GEMINI_API_KEY=your-key"
            )
        self.client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=45000),  # 45 seconds, in milliseconds
        )

        config = dict(system_instruction=SYSTEM_PROMPT, tools=_build_tools())
        if MODEL.startswith("gemini-3"):
            # Gemini 3 models "think" for a long time by default. "low" is much faster.
            config["thinking_config"] = types.ThinkingConfig(thinking_level="low")

        # Gemini calls the tool functions automatically and keeps the chat history.
        self.chat_session = self.client.chats.create(
            model=MODEL,
            config=types.GenerateContentConfig(**config),
        )

    def chat(self, user_input: str) -> str:
        for attempt in range(4):
            try:
                response = self.chat_session.send_message(user_input)
                return response.text or "(no reply)"
            except errors.ServerError:
                if attempt == 3:
                    return "The AI service is busy right now. Please try again in a minute."
                time.sleep(2 * 2 ** attempt)  # waits 2s, 4s, 8s, then tries again
            except errors.ClientError as e:
                if e.code == 429:
                    return "Free-tier limit reached. Please wait a minute and try again."
                raise
            except Exception as e:
                return f"Sorry, I could not answer ({type(e).__name__}). Please try again."