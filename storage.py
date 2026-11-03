"""Saves appointments in a Supabase database (online) or, if not set up, in a local file.

Rows are never deleted: a cancelled appointment only gets status "cancelled",
so the full history stays in the database.
"""
import json
import os
from pathlib import Path

import requests

TABLE = "appointments"
FIELDS = ["patient_name", "doctor_id", "date", "time", "visit_type", "status"]
PAGE = 1000
_last_saved: dict = {}  # id -> the row we last sent, so we only send changes


def _config():
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_KEY", "").strip()
    return (url, key) if url and key else (None, None)


def using_database() -> bool:
    return _config()[0] is not None


def _headers(key: str, extra: dict | None = None) -> dict:
    headers = {"apikey": key, "Authorization": f"Bearer {key}",
               "Content-Type": "application/json"}
    if extra:
        headers.update(extra)
    return headers


def _snapshot(appt: dict) -> dict:
    return {f: appt.get(f) for f in FIELDS}


def load_all(local_file: Path) -> dict:
    """Read every saved appointment. Raises an error if the database can't be read,
    so the app never starts with an empty list and overwrites old bookings."""
    url, key = _config()
    if url:
        found, start = {}, 0
        while True:
            resp = requests.get(
                f"{url}/rest/v1/{TABLE}",
                params={"select": "*", "order": "id", "limit": PAGE, "offset": start},
                headers=_headers(key), timeout=20)
            resp.raise_for_status()
            rows = resp.json()
            for row in rows:
                found[row["id"]] = {f: row.get(f) for f in FIELDS}
            if len(rows) < PAGE:
                break
            start += PAGE
        _last_saved.clear()
        _last_saved.update({i: dict(a) for i, a in found.items()})
        return found
    if local_file.exists():
        try:
            return json.loads(local_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_changes(appointments: dict, local_file: Path) -> bool:
    """Save new or changed appointments. Returns True if everything was saved."""
    url, key = _config()
    if not url:
        local_file.write_text(json.dumps(appointments, indent=2), encoding="utf-8")
        return True
    changed = [{"id": i, **_snapshot(a)} for i, a in appointments.items()
               if _last_saved.get(i) != _snapshot(a)]
    if not changed:
        return True
    try:
        resp = requests.post(
            f"{url}/rest/v1/{TABLE}", json=changed, timeout=20,
            headers=_headers(key, {"Prefer": "resolution=merge-duplicates,return=minimal"}))
        resp.raise_for_status()
    except Exception as e:
        print("Could not save to the database:", e)
        return False
    for row in changed:
        _last_saved[row["id"]] = {f: row[f] for f in FIELDS}
    return True