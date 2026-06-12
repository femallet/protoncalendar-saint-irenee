from datetime import datetime, timedelta
from icalendar import Calendar, Event
import requests
from bs4 import BeautifulSoup
import re

URL = "https://st-irenee.org/horaires-des-messes/?lang=fr"

html = requests.get(URL, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

cal = Calendar()

def next_sunday(base):
    return base + timedelta(days=(6 - base.weekday()) % 7)

def extract_time(text):
    match = re.search(r"(\d{1,2})\s*h\s*(\d{0,2})", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        return hour, minute
    return 10, 0  # fallback si rien trouvé

text = soup.get_text("\n").lower()

today = datetime.now()
sunday = next_sunday(today)

hour, minute = extract_time(text)

event = Event()
event.add("summary", "Messe chantée - Saint-Irénée")

start = sunday.replace(hour=hour, minute=minute, second=0)
end = start + timedelta(minutes=90)

event.add("dtstart", start)
event.add("dtend", end)

cal.add_component(event)

# 📅 option : prochaines semaines
for i in range(1, 4):
    s = sunday + timedelta(days=7 * i)

    e = Event()
    e.add("summary", "Messe chantée - Saint-Irénée")
    e.add("dtstart", s.replace(hour=hour, minute=minute, second=0))
    e.add("dtend", s.replace(hour=hour, minute=minute, second=0) + timedelta(minutes=90))

    cal.add_component(e)

with open("messe.ics", "wb") as f:
    f.write(cal.to_ical())

print("OK - ICS généré")
