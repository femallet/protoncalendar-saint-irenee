from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import re
import sys
import os  # ← ajouter cette ligne
# ---------------------------------------------------------------------------
# 4. Fusion avec le fichier ICS existant + génération (RFC 5545)
# ---------------------------------------------------------------------------
ICS_FILE = "messe.ics"

def ics_dt(dt):
    return dt.strftime("%Y%m%dT%H%M%S") + "-0400"

def ics_now():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

# --- Lire les UIDs déjà présents dans le fichier existant ---
existing_uids = set()
existing_blocks = []

if os.path.exists(ICS_FILE):
    with open(ICS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Extraire chaque bloc VEVENT complet
    for block in re.findall(r"BEGIN:VEVENT.*?END:VEVENT", content, re.DOTALL):
        uid_match = re.search(r"^UID:(.+)$", block, re.MULTILINE)
        if uid_match:
            uid = uid_match.group(1).strip()
            existing_uids.add(uid)
            existing_blocks.append(block.strip())

# --- Construire les nouveaux blocs VEVENT (sans doublons) ---
new_blocks = []
added = 0

for i, (start, end, summary) in enumerate(events):
    uid = f"{int(start.timestamp())}-{i}@st-irenee"
    if uid in existing_uids:
        continue  # déjà présent, on skip
    block_lines = [
        "BEGIN:VEVENT",
        f"SUMMARY:{summary}",
        f"DTSTART:{ics_dt(start)}",
        f"DTEND:{ics_dt(end)}",
        f"DTSTAMP:{ics_now()}",
        f"UID:{uid}",
        "LOCATION:560 Atwater Ave\\, Montréal\\, QC H4C 1M9",
        "DESCRIPTION:Messe en forme extraordinaire du rite romain (messe chantée).",
        "END:VEVENT",
    ]
    new_blocks.append("\r\n".join(block_lines))
    added += 1

# --- Réécrire le fichier complet ---
all_blocks = existing_blocks + new_blocks

header = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Saint-Irénée//Messe Chantée//FR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
]

parts = ["\r\n".join(header)]
parts.extend(all_blocks)
parts.append("END:VCALENDAR")

with open(ICS_FILE, "w", encoding="utf-8") as f:
    f.write("\r\n".join(parts) + "\r\n")

print(f"\n✓ {added} nouveaux événements ajoutés ({len(all_blocks)} au total) dans {ICS_FILE}")
