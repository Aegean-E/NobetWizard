import unittest
from datetime import date

from scheduler import DutyScheduler


def personnel(count=6):
    return [
        {
            "name": f"P{i}",
            "gender": "M" if i % 2 else "F",
            "role": "Senior" if i <= 3 else "Junior",
            "max_duties": 20,
            "max_weekends": 10,
        }
        for i in range(1, count + 1)
    ]


def config(**overrides):
    base = {
        "people_per_day": 2,
        "allow_consecutive": False,
        "gender_mode": "Any",
        "max_weekly_duties": 3,
    }
    base.update(overrides)
    return base


class DutySchedulerTest(unittest.TestCase):
    def test_generate_fills_every_day_without_consecutive_duties(self):
        scheduler = DutyScheduler(2026, 2, personnel(), config())

        success, schedule, error = scheduler.generate()

        self.assertTrue(success, error)
        self.assertEqual(len(schedule), 28)
        previous = set()
        for day in range(1, 29):
            team = schedule[date(2026, 2, day)]
            names = [person["name"] for person in team]
            self.assertEqual(len(names), 2)
            self.assertEqual(len(set(names)), 2)
            self.assertFalse(previous & set(names), f"consecutive duty on 2026-02-{day:02d}")
            previous = set(names)

    def test_fixed_duty_is_assigned_on_its_date(self):
        crew = personnel()
        crew[0]["fixed_dates"] = "01/02/2026"
        scheduler = DutyScheduler(2026, 2, crew, config())

        success, schedule, error = scheduler.generate()

        self.assertTrue(success, error)
        names = [person["name"] for person in schedule[date(2026, 2, 1)]]
        self.assertIn("P1", names)

    def test_busy_weekday_blocks_assignment(self):
        crew = personnel()
        crew[0]["busy_days"] = "Monday"
        scheduler = DutyScheduler(2026, 2, crew, config())
        monday = date(2026, 2, 2)
        self.assertEqual(monday.weekday(), 0)
        person = dict(crew[0], duty_count=0, weekend_duty_count=0)

        self.assertFalse(scheduler.check_constraints(person, monday, []))

    def test_holiday_counts_as_weekend(self):
        scheduler = DutyScheduler(2026, 2, personnel(), config(holidays=["02/02/2026"]))

        self.assertTrue(scheduler.is_weekend(date(2026, 2, 2)))
        self.assertFalse(scheduler.is_weekend(date(2026, 2, 3)))


if __name__ == "__main__":
    unittest.main()
