from datetime import datetime, timedelta
from icalendar import Calendar, Event
import requests
from bs4 import BeautifulSoup
import re

URL = "https://st-irenee.org/horaires-des-messes/?lang=fr"

html = requests.get(URL, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

def next_sunday(base):
    return base + timedelta(days=(6 - base.weekday()) % 7)

def extract_time(text):
    match = re.search(r"(\d{1,2})\s*h\s*(\d{0,2})", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        return hour, minute
    return 10, 0

text = soup.get_text("\n").lower()

today = datetime.now()
sunday = next_sunday(today)

hour, minute = extract_time(text)

cal = Calendar()

# 🔥 IMPORTANT: metadata requis par Proton
cal.add("prodid", "-//Saint-Irénée Calendar//FR//")
cal.add("version", "2.0")

start = sunday.replace(hour=hour, minute=minute, second=0, microsecond=0)
end = start + timedelta(minutes=90)

event = Event()
event.add("summary", "Messe chantée - Saint-Irénée")

# 🔥 Champs obligatoires pour Proton
event.add("dtstart", start)
event.add("dtend", end)
event.add("dtstamp", datetime.utcnow())
event.add("uid", f"messe-{start.timestamp()}@st-irenee")

cal.add_component(event)

for i in range(1, 4):
    s = sunday + timedelta(days=7 * i)
    start = s.replace(hour=hour, minute=minute, second=0, microsecond=0)

    e = Event()
    e.add("summary", "Messe chantée - Saint-Irénée")
    e.add("dtstart", start)
    e.add("dtend", start + timedelta(minutes=90))
    e.add("dtstamp", datetime.utcnow())
    e.add("uid", f"messe-{start.timestamp()}@st-irenee")

    cal.add_component(e)

with open("messe.ics", "wb") as f:
    f.write(cal.to_ical())

print("ICS Proton-compatible généré")
