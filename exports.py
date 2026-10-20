"""Calendar export helpers that do not depend on the Streamlit UI."""

import os
import urllib.request
from datetime import timedelta


def escape_ics_text(value):
    """Escape a value so it cannot break out of an iCalendar text property."""
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\r", "\\n")
        .replace("\n", "\\n")
    )


def generate_ics(schedule, title="Duty Roster"):
    """Generate an iCalendar document for the schedule."""
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NobetWizard//DutyRoster//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    for day, team in schedule.items():
        names = escape_ics_text(", ".join([person["name"] for person in team]))
        dt_start = day.strftime("%Y%m%d")
        dt_end = (day + timedelta(days=1)).strftime("%Y%m%d")

        ics_content.append("BEGIN:VEVENT")
        ics_content.append(f"DTSTART;VALUE=DATE:{dt_start}")
        ics_content.append(f"DTEND;VALUE=DATE:{dt_end}")
        ics_content.append(f"SUMMARY:{escape_ics_text(title)}: {names}")
        ics_content.append(f"DESCRIPTION:Team: {names}")
        ics_content.append("END:VEVENT")

    ics_content.append("END:VCALENDAR")
    return "\n".join(ics_content).encode("utf-8")


def download_font(url, path, timeout=10):
    """Download a font once, with a timeout and without leaving a partial file."""
    target = os.fspath(path)
    if os.path.exists(target):
        return

    temporary = f"{target}.tmp"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            with open(temporary, "wb") as handle:
                handle.write(response.read())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
