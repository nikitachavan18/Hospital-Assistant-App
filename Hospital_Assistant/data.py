"""Mock data for an Orthodontics & Dentofacial Orthopedics clinic.
Replace with a real database (SQLite/PostgreSQL) later."""
 
QUALIFICATION = "BDS ,MDS, Gold Medalist  (Orthodontics & Dentofacial Orthopedics)"
 
DOCTORS = {
    "O001": {"name": "Dr. Avinash Shankar Sherker", "qualification": QUALIFICATION,
             "focus": ["braces", "clear aligners", "dentofacial orthopedics", "retainers", "children and adults"]},
}
 
DAILY_SLOTS = ["10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00"]
 
VISIT_TYPES = ["consultation", "adjustment", "retainer check", "emergency repair"]
 
CLINIC_INFO = {
    "location": "Shivanjali Lane No 2, Katraj - Ambegaon BK Rd, near Dattanagar, Dattanagar, chawk, Ambegaon Budruk, Pune, Maharashtra 411046",
    "hours": "Mon-Sat 10:00-17:00 (closed Sunday)",
    "emergency_line": "Call the clinic for broken wires/brackets; for facial trauma or swelling go to a hospital emergency room.",
}
 
# General, approximate information only. The orthodontist decides the real plan.
TREATMENTS = {
    "metal braces": "Stainless-steel brackets and wires. Most widely used and effective for most cases. Typical treatment about 12-30 months.",
    "ceramic braces": "Tooth-coloured brackets, less visible than metal. Can stain more easily and need careful hygiene. Duration similar to metal braces.",
    "lingual braces": "Brackets bonded behind the teeth, so hidden. Can affect speech at first and need a specialist. Often costlier.",
    "clear aligners": "Removable transparent trays changed every 1-2 weeks. Best for mild to moderate cases; must be worn about 20-22 hours/day.",
    "retainers": "Worn after braces/aligners to hold teeth in place. Fixed or removable; wear as instructed by your orthodontist.",
    "functional appliances": "Used in growing children to guide jaw growth and correct bite (part of dentofacial orthopedics).",
    "palatal expander": "Widens a narrow upper jaw, usually in children/teens, to create space and fix crossbites.",
    "orthognathic surgery": "Jaw surgery combined with braces for significant jaw discrepancies, in adults after growth is complete. Planned with an oral surgeon.",
}
 
AFTERCARE = {
    "sore teeth": "Mild soreness for 2-5 days after fitting/adjustment is normal. Eat soft foods; an over-the-counter pain reliever per its label may help.",
    "poking wire": "Try pushing the wire gently with the eraser end of a pencil or cover it with orthodontic wax. Book an 'emergency repair' visit; do not cut the wire yourself.",
    "loose bracket": "Keep the bracket if it comes off, avoid hard/sticky foods, and book a repair visit soon. If it is still attached to the wire, leave it.",
    "mouth sores": "Use orthodontic wax on the rubbing area and rinse with warm salt water. If sores persist, mention at your next visit.",
    "lost retainer": "Contact the clinic as soon as possible; teeth can shift quickly. Do not wear an old, ill-fitting retainer forcefully.",
    "broken aligner": "Switch to the previous aligner tray if you have it and contact the clinic for guidance.",
    "cleaning": "Brush after meals, use an interdental brush/floss threader, and a fluoride mouthwash if advised. Cleaning around brackets matters most.",
}
 
# In-memory appointment store: {appointment_id: {...}}
APPOINTMENTS: dict = {}
 