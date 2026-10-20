import unittest
from datetime import date

from ui_helpers import GENDER_MODES, gender_label, get_calendar_html, normalize_gender_mode


ENGLISH_OPTIONS = ["Any", "Mixed (Must have M & F)", "Single Gender (All M or All F)"]
TURKISH_OPTIONS = ["Fark etmez", "Karma (E & K olmalı)", "Tek Cinsiyet (Hepsi E veya Hepsi K)"]
LANGUAGE_OPTIONS = [ENGLISH_OPTIONS, TURKISH_OPTIONS]
TEXT = {"short_days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}


class GenderModeTest(unittest.TestCase):
    def test_internal_modes_are_unchanged(self):
        for mode in GENDER_MODES:
            self.assertEqual(normalize_gender_mode(mode, LANGUAGE_OPTIONS), mode)

    def test_legacy_localized_labels_normalize(self):
        self.assertEqual(normalize_gender_mode(ENGLISH_OPTIONS[1], LANGUAGE_OPTIONS), "Mixed")
        self.assertEqual(normalize_gender_mode(TURKISH_OPTIONS[2], LANGUAGE_OPTIONS), "Single Gender")

    def test_unknown_value_falls_back_to_any(self):
        self.assertEqual(normalize_gender_mode("something else", LANGUAGE_OPTIONS), "Any")

    def test_label_follows_the_selected_language(self):
        self.assertEqual(gender_label(ENGLISH_OPTIONS, "Mixed"), ENGLISH_OPTIONS[1])
        self.assertEqual(gender_label(TURKISH_OPTIONS, "Mixed"), TURKISH_OPTIONS[1])


class CalendarHtmlTest(unittest.TestCase):
    def test_personnel_names_are_html_escaped(self):
        schedule = {date(2026, 2, 1): [{"name": '<img src=x onerror="alert(1)">'}]}

        markup = get_calendar_html(2026, 2, schedule, TEXT)

        self.assertNotIn("<img", markup)
        self.assertIn("&lt;img", markup)

    def test_empty_cells_and_assignments_still_render(self):
        schedule = {date(2026, 2, 2): [{"name": "Ada"}]}

        markup = get_calendar_html(2026, 2, schedule, TEXT)

        self.assertIn("Ada", markup)
        self.assertIn("</table>", markup)


if __name__ == "__main__":
    unittest.main()
