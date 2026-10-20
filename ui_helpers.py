"""Pure presentation helpers shared by the Streamlit UI and the test suite."""

import calendar
import html
from datetime import date


GENDER_MODES = ["Any", "Mixed", "Single Gender"]


def gender_label(options, mode):
    """Return the localized label for an internal gender mode."""
    return options[GENDER_MODES.index(mode)]


def normalize_gender_mode(value, option_sets):
    """Accept an internal mode or a legacy localized label from saved data."""
    if value in GENDER_MODES:
        return value
    for options in option_sets:
        if value in options:
            return GENDER_MODES[options.index(value)]
    return "Any"


def get_calendar_html(year, month, schedule, t):
    """Render the month grid, escaping every personnel name it embeds."""
    weeks = calendar.monthcalendar(year, month)

    headers = "".join(
        [
            f"<th style='border:1px solid var(--text-color); padding:8px; "
            f"background:var(--secondary-background-color); width:14%; "
            f"color:var(--text-color);'>{html.escape(str(day))}</th>"
            for day in t["short_days"]
        ]
    )

    calendar_html = (
        f"<table style='width:100%; border-collapse:collapse; table-layout: fixed;'>"
        f"<thead><tr>{headers}</tr></thead><tbody>"
    )

    for week in weeks:
        calendar_html += "<tr>"
        for day in week:
            if day == 0:
                calendar_html += (
                    "<td style='border:1px solid var(--text-color); "
                    "background:var(--background-color); opacity:0.5;'></td>"
                )
            else:
                current_date = date(year, month, day)
                is_weekend = current_date.weekday() >= 5
                bg_color = (
                    "var(--background-color)"
                    if not is_weekend
                    else "var(--secondary-background-color)"
                )

                day_content = (
                    "<div style='font-weight:bold; margin-bottom:5px; "
                    f"color:var(--text-color);'>{day}</div>"
                )

                if current_date in schedule:
                    for person in schedule[current_date]:
                        name = html.escape(str(person.get("name", "")))
                        day_content += (
                            "<div style='background:#e6f3ff; padding:2px 4px; "
                            "margin-bottom:2px; border-radius:4px; font-size:11px; "
                            "border:1px solid #cce5ff; color:#004085; "
                            f"font-weight:bold;'>{name}</div>"
                        )

                calendar_html += (
                    f"<td style='border:1px solid var(--text-color); padding:5px; "
                    f"height:100px; vertical-align:top; background:{bg_color};'>"
                    f"{day_content}</td>"
                )
        calendar_html += "</tr>"

    calendar_html += "</tbody></table>"
    return calendar_html
