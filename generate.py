from datetime import datetime, timedelta
from icalendar import Calendar, Event
import requests

url = "https://st-irenee.org/horaires-des-messes/?lang=fr"
html = requests.get(url, timeout=30).text.lower()

cal = Calendar()

if "chantée" in html:
    event = Event()
    event.add("summary", "Messe chantée - Saint-Irénée")

    now = datetime.utcnow()
    next_sunday = now + timedelta((6 - now.weekday()) % 7)

    start = next_sunday.replace(hour=10, minute=0, second=0, microsecond=0)
    end = next_sunday.replace(hour=11, minute=30, second=0, microsecond=0)

    event.add("dtstart", start)
    event.add("dtend", end)

    cal.add_component(event)

with open("docs/messe.ics", "wb") as f:
    f.write(cal.to_ical())
