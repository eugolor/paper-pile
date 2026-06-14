from datetime import datetime
import re

def generate_ics(docs: list[dict]) -> str | None:
    events = []
    for doc in docs:
        deadline = doc.get("deadline")
        if not deadline:
            continue
        sender = doc.get("sender", "Unknown")
        action = doc.get("action_needed", "Review document")
        summary = doc.get("summary", "")

        # Try to parse the date
        parsed = None
        formats = ["%B %d, %Y", "%b %d, %Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]
        for fmt in formats:
            try:
                cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', deadline)
                parsed = datetime.strptime(cleaned.strip(), fmt)
                break
            except ValueError:
                continue

        if not parsed:
            continue

        dtstart = parsed.strftime("%Y%m%d")
        events.append(f"""BEGIN:VEVENT
SUMMARY:📬 {sender} — {action[:50]}
DTSTART;VALUE=DATE:{dtstart}
DESCRIPTION:{summary}
END:VEVENT""")

    if not events:
        return None

    return "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//PaperPile//EN\n" + \
           "\n".join(events) + "\nEND:VCALENDAR"