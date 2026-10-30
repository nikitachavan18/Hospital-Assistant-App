"""Tools the agent can call. Each tool is a plain Python function + a JSON schema."""
import itertools
from datetime import datetime
 
from .data import (AFTERCARE, APPOINTMENTS, CLINIC_INFO, DAILY_SLOTS, DOCTORS,
                   TREATMENTS, VISIT_TYPES)
 
_counter = itertools.count(1)
 
EMERGENCY_KEYWORDS = [
    "facial swelling", "face swelling", "swollen face", "swelling in my face",
    "difficulty breathing", "can't breathe", "cannot breathe", "trouble swallowing",
    "can't swallow", "knocked out", "knocked-out", "severe bleeding", "heavy bleeding",
    "jaw fracture", "broken jaw", "head injury", "unconscious", "high fever",
]
URGENT_KEYWORDS = [
    "poking", "stabbing", "loose bracket", "broken bracket", "broken wire",
    "lost retainer", "broken retainer", "broken aligner", "loose tooth", "severe pain",
]
 
 
def search_doctors(focus: str = "") -> dict:
    """All doctors are orthodontists. Optionally filter by focus area."""
    f = focus.lower().strip()
    found = [
        {"doctor_id": did, **d}
        for did, d in DOCTORS.items()
        if not f or any(f in x or x in f for x in d["focus"])
    ]
    if not found:  # fall back to listing everyone rather than returning nothing
        found = [{"doctor_id": did, **d} for did, d in DOCTORS.items()]
        return {"doctors": found, "note": "No exact match; showing all orthodontists."}
    return {"doctors": found}
 
 
def check_availability(doctor_id: str, date: str) -> dict:
    if doctor_id not in DOCTORS:
        return {"error": f"Unknown doctor_id {doctor_id}"}
    try:
        d = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return {"error": "date must be in YYYY-MM-DD format"}
    if d.weekday() == 6:
        return {"error": "The clinic is closed on Sundays.", "available_slots": []}
    booked = {
        a["time"] for a in APPOINTMENTS.values()
        if a["doctor_id"] == doctor_id and a["date"] == date and a["status"] == "confirmed"
    }
    return {"doctor": DOCTORS[doctor_id]["name"], "date": date,
            "available_slots": [t for t in DAILY_SLOTS if t not in booked]}
 
 
def book_appointment(patient_name: str, doctor_id: str, date: str, time: str,
                     visit_type: str = "consultation") -> dict:
    if visit_type not in VISIT_TYPES:
        return {"error": f"visit_type must be one of {VISIT_TYPES}"}
    avail = check_availability(doctor_id, date)
    if "error" in avail:
        return avail
    if time not in avail["available_slots"]:
        return {"error": f"{time} is not available.", "available_slots": avail["available_slots"]}
    appt_id = f"ORT{next(_counter):04d}"
    APPOINTMENTS[appt_id] = {"patient_name": patient_name, "doctor_id": doctor_id,
                             "date": date, "time": time, "visit_type": visit_type,
                             "status": "confirmed"}
    return {"appointment_id": appt_id, "doctor": DOCTORS[doctor_id]["name"],
            "date": date, "time": time, "visit_type": visit_type, "status": "confirmed"}
 
 
def cancel_appointment(appointment_id: str) -> dict:
    appt = APPOINTMENTS.get(appointment_id.upper())
    if not appt:
        return {"error": "Appointment not found."}
    appt["status"] = "cancelled"
    return {"appointment_id": appointment_id.upper(), "status": "cancelled"}
 
 
def get_treatment_info(treatment: str) -> dict:
    t = treatment.lower().strip()
    for name, info in TREATMENTS.items():
        if t in name or name in t:
            return {"treatment": name, "info": info,
                    "note": "General information only. Your orthodontist decides the actual plan."}
    return {"error": "Treatment not found.", "available": list(TREATMENTS)}
 
 
def get_aftercare_tip(issue: str) -> dict:
    i = issue.lower().strip()
    for name, tip in AFTERCARE.items():
        if i in name or name in i:
            return {"issue": name, "tip": tip}
    return {"error": "No tip for that issue.", "available": list(AFTERCARE)}
 
 
def get_clinic_info() -> dict:
    return CLINIC_INFO
 
 
def triage_symptoms(symptoms: str) -> dict:
    """Basic safety check ONLY. This is not a diagnosis."""
    text = symptoms.lower()
    if any(k in text for k in EMERGENCY_KEYWORDS):
        return {"urgency": "emergency",
                "advice": "This may be an emergency. Go to the nearest hospital emergency room "
                          "or call 112 (ambulance 108 in India) now."}
    if any(k in text for k in URGENT_KEYWORDS):
        return {"urgency": "urgent",
                "advice": "Offer the earliest 'emergency repair' slot and share a temporary aftercare tip."}
    return {"urgency": "routine",
            "advice": "Suggest a regular consultation or adjustment visit."}
 
 
TOOL_FUNCTIONS = {
    "search_doctors": search_doctors,
    "check_availability": check_availability,
    "book_appointment": book_appointment,
    "cancel_appointment": cancel_appointment,
    "get_treatment_info": get_treatment_info,
    "get_aftercare_tip": get_aftercare_tip,
    "get_clinic_info": get_clinic_info,
    "triage_symptoms": triage_symptoms,
}
 
TOOL_SCHEMAS = [
    {"name": "search_doctors",
     "description": "List orthodontists (MDS Orthodontics & Dentofacial Orthopedics). Optionally filter by focus, e.g. braces, clear aligners, jaw growth, pediatric.",
     "input_schema": {"type": "object", "properties": {"focus": {"type": "string"}}}},
    {"name": "check_availability", "description": "List free appointment slots for a doctor on a date.",
     "input_schema": {"type": "object", "properties": {
         "doctor_id": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"}},
         "required": ["doctor_id", "date"]}},
    {"name": "book_appointment", "description": "Book an appointment. Confirm all details with the patient first.",
     "input_schema": {"type": "object", "properties": {
         "patient_name": {"type": "string"}, "doctor_id": {"type": "string"},
         "date": {"type": "string", "description": "YYYY-MM-DD"},
         "time": {"type": "string", "description": "HH:MM, 24-hour"},
         "visit_type": {"type": "string", "enum": VISIT_TYPES}},
         "required": ["patient_name", "doctor_id", "date", "time"]}},
    {"name": "cancel_appointment", "description": "Cancel an appointment by its ID.",
     "input_schema": {"type": "object", "properties": {"appointment_id": {"type": "string"}}, "required": ["appointment_id"]}},
    {"name": "get_treatment_info",
     "description": "General info on a treatment: metal braces, ceramic braces, lingual braces, clear aligners, retainers, functional appliances, palatal expander, orthognathic surgery.",
     "input_schema": {"type": "object", "properties": {"treatment": {"type": "string"}}, "required": ["treatment"]}},
    {"name": "get_aftercare_tip",
     "description": "Temporary care tip for common braces/aligner issues (sore teeth, poking wire, loose bracket, mouth sores, lost retainer, broken aligner, cleaning).",
     "input_schema": {"type": "object", "properties": {"issue": {"type": "string"}}, "required": ["issue"]}},
    {"name": "get_clinic_info", "description": "Clinic location, hours and emergency guidance.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "triage_symptoms",
     "description": "Check described symptoms for emergency or urgent red flags. Not a diagnosis.",
     "input_schema": {"type": "object", "properties": {"symptoms": {"type": "string"}}, "required": ["symptoms"]}},
]