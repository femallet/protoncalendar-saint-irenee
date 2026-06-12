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
        h = int(match.group(1))
        m = int(match.group(2)) if match.group(2) else 0
        return h, m
    return 10, 0

text = soup.get_text("\n").lower()

today = datetime.utcnow()
sunday = next_sunday(today)

hour, minute = extract_time(text)

cal = Calendar()
cal.add("prodid", "-//Saint-Irénée//Messe//FR")
cal.add("version", "2.0")

def make_event(dt):
    event = Event()
    event.add("summary", "Messe chantée - Saint-Irénée")

    start = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    end = start + timedelta(minutes=90)

    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("dtstamp", datetime.utcnow())
    event.add("uid", f"{start.timestamp()}@st-irenee")

    cal.add_component(event)

make_event(sunday)

for i in range(1, 4):
    make_event(sunday + timedelta(days=7 * i))

with open("messe.ics", "wb") as f:
    f.write(cal.to_ical())

print("OK ICS Proton valide")
