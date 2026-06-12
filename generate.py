"""
generate.py — Générateur de calendrier ICS pour les messes chantées de Saint-Irénée
Scrape https://st-irenee.org/horaires-des-messes/ et produit messe.ics
avec les 4 prochaines occurrences de chaque messe chantée.

Dépendances : requests, beautifulsoup4
  pip install requests beautifulsoup4
"""

from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
import re
import sys

URL = "https://st-irenee.org/horaires-des-messes/?lang=fr"

# ---------------------------------------------------------------------------
# 1. Scraping
# ---------------------------------------------------------------------------
try:
    html = requests.get(URL, timeout=30).text
except Exception as e:
    print(f"Erreur de connexion : {e}", file=sys.stderr)
    sys.exit(1)

soup = BeautifulSoup(html, "html.parser")
text = soup.get_text("\n")

# ---------------------------------------------------------------------------
# 2. Extraction des messes chantées
#
#    La page peut présenter l'heure chantée de deux façons :
#      A) "10 h (chantée)"  → heure et "chantée" sur la même ligne
#      B) "10 h \n(chantée)" → BeautifulSoup sépare sur deux lignes (balise <em>)
#
#    Algorithme :
#      - On suit le "jour courant" (dernière ligne égale exactement à un nom de jour).
#      - Cas A : "chantée" + une heure sur la même ligne → heure juste avant "chantée".
#      - Cas B : "(chantée)" seul sur une ligne → heure la plus récente de la ligne précédente.
# ---------------------------------------------------------------------------
JOURS = {
    "dimanche": 6,
    "lundi":    0,
    "mardi":    1,
    "mercredi": 2,
    "jeudi":    3,
    "vendredi": 4,
    "samedi":   5,
}

messes_chantees = {}   # { "dimanche": [(10, 0)], "vendredi": [(19, 0)], ... }
current_day = None
prev_line   = ""

for line in text.split("\n"):
    stripped = line.strip()
    lower    = stripped.lower()

    # Détecter un titre de jour
    for jour in JOURS:
        if lower == jour:
            current_day = jour
            break

    if not current_day:
        prev_line = stripped
        continue

    # Cas A : heure et "chantée" sur la même ligne
    if "chantée" in lower and re.search(r"\d{1,2}\s*h", stripped):
        chantee_pos = lower.find("chantée")
        heures = [
            (m.start(), int(m.group(1)), int(m.group(2)) if m.group(2) else 0)
            for m in re.finditer(r"(\d{1,2})\s*h\s*(\d{0,2})", stripped)
        ]
        heures_avant = [(p, h, m) for p, h, m in heures if p < chantee_pos]
        if heures_avant:
            _, h, m = max(heures_avant, key=lambda x: x[0])
            messes_chantees.setdefault(current_day, []).append((h, m))

    # Cas B : "(chantée)" seul sur sa ligne → heure sur la ligne précédente
    elif re.fullmatch(r"\(?chantée\)?", lower) and prev_line:
        heures = [
            (m.start(), int(m.group(1)), int(m.group(2)) if m.group(2) else 0)
            for m in re.finditer(r"(\d{1,2})\s*h\s*(\d{0,2})", prev_line)
        ]
        if heures:
            _, h, m = max(heures, key=lambda x: x[0])
            messes_chantees.setdefault(current_day, []).append((h, m))

    prev_line = stripped

if not messes_chantees:
    print("Aucune messe chantée trouvée sur la page.", file=sys.stderr)
    sys.exit(1)

print("Messes chantées détectées :")
for jour, heures in messes_chantees.items():
    for h, m in heures:
        print(f"  {jour.capitalize()} à {h:02d}h{m:02d}")

# ---------------------------------------------------------------------------
# 3. Calcul des occurrences de la semaine courante (lun–dim)
# ---------------------------------------------------------------------------
def is_first_friday(dt):
    return dt.weekday() == 4 and dt.day <= 7

today      = datetime.now().date()
week_start = today - timedelta(days=today.weekday())   # lundi
week_end   = week_start + timedelta(days=6)             # dimanche
events     = []

for jour, heures in messes_chantees.items():
    weekday_num = JOURS[jour]
    date = week_start + timedelta(days=weekday_num)
    if not (week_start <= date <= week_end):
        continue
    for h, m in heures:
        start = datetime(date.year, date.month, date.day, h, m, 0)
        end   = start + timedelta(minutes=90)
        if is_first_friday(start):
            summary = "Messe solennelle chantée - Saint-Irénée"
        elif jour == "dimanche":
            summary = "Messe chantée (dimanche) - Saint-Irénée"
        elif jour == "vendredi":
            summary = "Messe chantée (vendredi) - Saint-Irénée"
        else:
            summary = f"Messe chantée ({jour}) - Saint-Irénée"
        events.append((start, end, summary))

events.sort(key=lambda x: x[0])

# ---------------------------------------------------------------------------
# 4. Génération du fichier ICS (RFC 5545)
# ---------------------------------------------------------------------------
def ics_dt(dt):
    return dt.strftime("%Y%m%dT%H%M%S")

def ics_now():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Saint-Irénée//Messe Chantée//FR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
]

for i, (start, end, summary) in enumerate(events):
    lines += [
        "BEGIN:VEVENT",
        f"SUMMARY:{summary}",
        f"DTSTART:{ics_dt(start)}",
        f"DTEND:{ics_dt(end)}",
        f"DTSTAMP:{ics_now()}",
        f"UID:{int(start.timestamp())}-{i}@st-irenee",
        "LOCATION:560 Atwater Ave\\, Montréal\\, QC H4C 1M9",
        "DESCRIPTION:Messe en forme extraordinaire du rite romain (messe chantée).",
        "END:VEVENT",
    ]

lines.append("END:VCALENDAR")

ics_content = "\r\n".join(lines) + "\r\n"

with open("messe.ics", "w", encoding="utf-8") as f:
    f.write(ics_content)

print(f"\n✓ {len(events)} événements écrits dans messe.ics")
