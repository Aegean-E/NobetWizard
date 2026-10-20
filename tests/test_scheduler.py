import unittest
from datetime import date, timedelta

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

    def test_two_day_rest_applies_even_when_consecutive_is_allowed(self):
        crew = personnel()
        scheduler = DutyScheduler(
            2026, 2, crew, config(allow_consecutive=True, require_two_rest_days=True)
        )
        worked = date(2026, 2, 2)
        scheduler.schedule[worked] = [dict(crew[0])]
        person = dict(crew[0], duty_count=1, weekend_duty_count=0)

        self.assertFalse(scheduler.check_constraints(person, worked + timedelta(days=2), []))

    def test_mixed_gender_allows_single_person_days(self):
        scheduler = DutyScheduler(
            2026, 2, personnel(3), config(people_per_day=1, gender_mode="Mixed")
        )

        success, schedule, error = scheduler.generate()

        self.assertTrue(success, error)
        self.assertTrue(all(len(team) == 1 for team in schedule.values()))

    def test_conditional_rule_uses_previous_week_trigger(self):
        crew = personnel()
        scheduler = DutyScheduler(
            2026,
            2,
            crew,
            config(allow_consecutive=True, conditional_rules=[{"trigger": 6, "forbidden": 0}]),
        )
        sunday = date(2026, 2, 1)
        self.assertEqual(sunday.weekday(), 6)
        scheduler.schedule[sunday] = [dict(crew[0])]
        person = dict(crew[0], duty_count=1, weekend_duty_count=1)

        self.assertFalse(scheduler.check_constraints(person, sunday + timedelta(days=1), []))

    def test_fixed_duty_on_leave_is_reported(self):
        crew = personnel()
        crew[0]["fixed_dates"] = "01/02/2026"
        crew[0]["leave_dates"] = "01/02/2026"
        scheduler = DutyScheduler(2026, 2, crew, config())

        success, _schedule, error = scheduler.generate()

        self.assertFalse(success)
        self.assertIn("fixed", error.lower())

    def test_fixed_duties_cannot_exceed_people_per_day(self):
        crew = personnel()
        for person in crew[:3]:
            person["fixed_dates"] = "01/02/2026"
        scheduler = DutyScheduler(2026, 2, crew, config(people_per_day=2))

        success, _schedule, error = scheduler.generate()

        self.assertFalse(success)
        self.assertIn("fixed", error.lower())

    def test_fixed_duties_cannot_pair_incompatible_people(self):
        crew = personnel()
        crew[0]["fixed_dates"] = "01/02/2026"
        crew[1]["fixed_dates"] = "01/02/2026"
        scheduler = DutyScheduler(
            2026, 2, crew, config(forbidden_pairs=[{"p1": "P1", "p2": "P2"}])
        )

        success, _schedule, error = scheduler.generate()

        self.assertFalse(success)
        self.assertIn("fixed", error.lower())

    def test_fixed_duties_cannot_exceed_max_duties(self):
        crew = personnel()
        crew[0]["max_duties"] = 2
        crew[0]["fixed_dates"] = "01/02/2026, 02/02/2026, 03/02/2026"
        scheduler = DutyScheduler(2026, 2, crew, config(allow_consecutive=True))

        success, _schedule, error = scheduler.generate()

        self.assertFalse(success)
        self.assertIn("fixed", error.lower())


if __name__ == "__main__":
    unittest.main()
