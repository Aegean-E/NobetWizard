# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `4`
- **Total Classes**: `2`
- **Total Top-Level Functions**: `17`
- **Total Class Methods**: `10`
- **Total Source Lines**: `1847`

---

## 📦 Modules & Exported Symbols

### [`main.py`](main.py)
**Size**: `1426` lines (`65060` bytes)

**Functions:**
- `def get_firestore_db()` - *Initialize Firestore Client from Streamlit Secrets*
- `def get_user_db_path(username)`
- `def load_db(username)`
- `def save_db(personnel, username)`
- `def load_users()`
- `def save_users(data)`
- `def make_hashes(password)`
- `def check_hashes(password, hashed_text)`
- `def authenticate(username, password)`
- `def login_page()`
- `def get_calendar_html(year, month, schedule, t)`
- `def generate_ics(schedule, title)` - *Generates an iCalendar string for the schedule.*
- `def generate_excel(df_res)`
- `def generate_pdf(df_res, year, month, t)`
- `def main()`

---

### [`scheduler.py`](scheduler.py)
**Size**: `344` lines (`15229` bytes)

**Classes:**
- `class DutyScheduler`
  - Method `.__init__(year, month, personnel_list, config)` - *personnel_list: list of dicts [{'name': '...', 'gender': 'M/F', 'max_duties': 5, 'max_weekends': 2}]*
  - Method `.is_weekend(d)`
  - Method `.get_week_number(d)`
  - Method `.check_constraints(person, current_date, current_team)`
  - Method `.check_team_constraints(team)`
  - Method `.generate()`

---

### [`tests/__init__.py`](tests/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`tests/test_scheduler.py`](tests/test_scheduler.py)
**Size**: `77` lines (`2406` bytes)

**Classes:**
- `class DutySchedulerTest`
  - Method `.test_generate_fills_every_day_without_consecutive_duties()`
  - Method `.test_fixed_duty_is_assigned_on_its_date()`
  - Method `.test_busy_weekday_blocks_assignment()`
  - Method `.test_holiday_counts_as_weekend()`

**Functions:**
- `def personnel(count)`
- `def config(**overrides)`

---
