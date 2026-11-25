"""Sends WhatsApp reminders 1 day, 6, 4 and 2 hours before each appointment.

Runs on a schedule (GitHub Actions, see .github/workflows/reminders.yml).
It reads appointments from Supabase, sends an approved WhatsApp template message,
and remembers what it sent in the column auto_reminders_sent so nobody gets a
message twice.

Safe by default: while DRY_RUN is not set to "false" it only prints what it WOULD send.
"""
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

# ----------------------------------------------------------------------------
# Clinic details used inside the message (edit here)
# ----------------------------------------------------------------------------
CLINIC_NAME = os.getenv("CLINIC_NAME", "New Shree Dental Clinic")
DOCTOR_NAME = os.getenv("DOCTOR_NAME", "Dr. Avinash Shankar Sherker")
ADDRESS = os.getenv("CLINIC_ADDRESS", "Shivanjali Lane No 2, Katraj - Ambegaon BK Rd, "
                    "Ambegaon Budruk, Pune, Maharashtra 411046")
PHONE = os.getenv("CLINIC_PHONE", "8668992833")

IST = timezone(timedelta(hours=5, minutes=30))  # India time (no daylight saving)
STAGES = [24, 6, 4, 2]            # hours before the appointment
QUIET_FROM, QUIET_TO = 21, 8      # no messages from 9 pm to 8 am India time

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
WA_TOKEN = os.getenv("WHATSAPP_TOKEN", "").strip()
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "").strip()
WA_TEMPLATE = os.getenv("WHATSAPP_TEMPLATE", "appointment_reminder").strip()
WA_LANG = os.getenv("WHATSAPP_LANG", "en").strip()
WA_VERSION = os.getenv("WHATSAPP_API_VERSION", "v26.0").strip()  # check Meta's docs
WA_BASE = os.getenv("WHATSAPP_API_BASE", "https://graph.facebook.com").rstrip("/")
DRY_RUN = os.getenv("DRY_RUN", "true").strip().lower() != "false"


def db_headers(extra=None):
    headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
    if SUPABASE_KEY.startswith("eyJ"):  # old-style JWT keys also go in Authorization
        headers["Authorization"] = f"Bearer {SUPABASE_KEY}"
    if extra:
        headers.update(extra)
    return headers


def fetch_appointments(today: str, tomorrow: str) -> list:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/appointments",
        params=[("select", "*"), ("status", "eq.confirmed"), ("date", f"gte.{today}"),
                ("date", f"lte.{tomorrow}"), ("limit", "1000")],
        headers=db_headers(), timeout=30)
    resp.raise_for_status()
    return resp.json()


def mark_sent(appt_id: str, stages: list) -> None:
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/appointments", params={"id": f"eq.{appt_id}"},
        json={"auto_reminders_sent": ",".join(stages)},
        headers=db_headers({"Prefer": "return=minimal"}), timeout=30)
    resp.raise_for_status()


def clean_mobile(number) -> str | None:
    digits = re.sub(r"\D", "", str(number or ""))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return digits if len(digits) == 10 and digits[0] in "6789" else None


def appt_start(a: dict):
    try:
        return datetime.strptime(f'{a["date"]} {a["time"]}', "%Y-%m-%d %H:%M").replace(tzinfo=IST)
    except Exception:
        return None


def due_stage(hours_left: float):
    """Smallest window (24, 6, 4, 2) that still fits, or None."""
    if hours_left <= 0 or hours_left > STAGES[0]:
        return None
    return min(h for h in STAGES if hours_left <= h)


def parse_iso(text):
    try:
        value = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except Exception:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def booked_too_late(a: dict, start: datetime, stage: int) -> bool:
    """True if the patient booked after this reminder's time (no point reminding at once)."""
    created = parse_iso(a.get("created_at"))
    return bool(created and created > start - timedelta(hours=stage))


def template_params(a: dict, start: datetime, now: datetime, hours_left: float, stage: int) -> list:
    """Values for {{1}}..{{7}} in the WhatsApp template (no line breaks allowed)."""
    day = "today" if start.date() == now.date() else "tomorrow"
    when = day if stage == STAGES[0] else f"today, in about {max(1, round(hours_left))} hours"
    time_txt = start.strftime("%I:%M %p").lstrip("0")
    date_txt = f"{start.strftime('%A, %d %B %Y')} at {time_txt}"
    return [str(a.get("patient_name", "")).strip() or "Patient", CLINIC_NAME, DOCTOR_NAME,
            when, date_txt, ADDRESS, PHONE]


def send_whatsapp(number: str, params: list) -> None:
    body = {"messaging_product": "whatsapp", "to": "91" + number, "type": "template",
            "template": {"name": WA_TEMPLATE, "language": {"code": WA_LANG},
                         "components": [{"type": "body",
                                         "parameters": [{"type": "text", "text": p} for p in params]}]}}
    resp = requests.post(f"{WA_BASE}/{WA_VERSION}/{WA_PHONE_ID}/messages", json=body,
                         headers={"Authorization": f"Bearer {WA_TOKEN}"}, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"WhatsApp error {resp.status_code}: {resp.text[:300]}")


def run(now: datetime) -> int:
    if now.hour >= QUIET_FROM or now.hour < QUIET_TO:
        print(f"Quiet hours ({now:%H:%M} India time). No messages sent.")
        return 0
    today = now.date()
    appointments = fetch_appointments(today.isoformat(), (today + timedelta(days=1)).isoformat())
    print(f"{len(appointments)} confirmed appointment(s) today/tomorrow. DRY_RUN={DRY_RUN}")
    sent = failed = 0
    for a in appointments:
        start = appt_start(a)
        if start is None:
            continue
        hours_left = (start - now).total_seconds() / 3600
        stage = due_stage(hours_left)
        if stage is None:
            continue
        done = [s for s in (a.get("auto_reminders_sent") or "").split(",") if s]
        if str(stage) in done or booked_too_late(a, start, stage):
            continue
        number = clean_mobile(a.get("patient_contact"))
        if number is None:
            print(f"Skip {a['id']}: no valid mobile number.")
            continue
        params = template_params(a, start, now, hours_left, stage)
        if DRY_RUN:
            print(f"[DRY RUN] would send the {stage}-hour reminder for {a['id']} to ***{number[-4:]}: {params}")
            continue
        try:
            send_whatsapp(number, params)
        except Exception as e:
            print(f"FAILED {a['id']}: {e}")
            failed += 1
            continue
        try:
            mark_sent(a["id"], done + [str(stage)])
        except Exception as e:
            print(f"WARNING: sent {a['id']} but could not save it ({e}). It may be sent again.")
        sent += 1
        print(f"Sent the {stage}-hour reminder for {a['id']} to ***{number[-4:]}")
    print(f"Done. Sent {sent}, failed {failed}.")
    return 1 if failed else 0


if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        sys.exit("SUPABASE_URL and SUPABASE_KEY must be set.")
    if not DRY_RUN and not (WA_TOKEN and WA_PHONE_ID):
        sys.exit("WHATSAPP_TOKEN and WHATSAPP_PHONE_ID must be set when DRY_RUN is false.")
    sys.exit(run(datetime.now(IST)))