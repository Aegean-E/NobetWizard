# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `10`
- **Total Classes**: `7`
- **Total Top-Level Functions**: `23`
- **Total Class Methods**: `37`
- **Total Source Lines**: `2314`

---

## 📦 Modules & Exported Symbols

### [`main.py`](main.py)
**Size**: `1443` lines (`65537` bytes)

**Functions:**
- `def get_secrets()` - *st.secrets raises when no secrets file exists; an empty mapping keeps local runs working.*
- `def clear_user_state()` - *Drop every user-scoped key so the next login starts from a clean session.*
- `def get_firestore_db()` - *Initialize Firestore Client from Streamlit Secrets*
- `def get_user_db_path(username)`
- `def load_db(username)`
- `def save_db(personnel, username)`
- `def load_users()`
- `def save_users(data)`
- `def authenticate(username, password)`
- `def login_page()`
- `def generate_ics(schedule, title)` - *Generates an iCalendar string for the schedule.*
- `def generate_excel(df_res)`
- `def generate_pdf(df_res, year, month, t)`
- `def main()`

---

### [`scheduler.py`](scheduler.py)
**Size**: `462` lines (`20267` bytes)

**Classes:**
- `class DutyScheduler`
  - Method `.__init__(year, month, personnel_list, config)` - *personnel_list: list of dicts [{'name': '...', 'gender': 'M/F', 'max_duties': 5, 'max_weekends': 2}]*
  - Method `.is_weekend(d)`
  - Method `.get_week_number(d)`
  - Method `._split_dates(person, field)`
  - Method `._is_fixed_on(person_name, d)`
  - Method `._duties_in_week(person_name, week)`
  - Method `._reset_counters()`
  - Method `._increment_fixed(person, d)`
  - Method `._restore_baseline()`
  - Method `._index_fixed_duties()`
  - Method `._validate_fixed_duties()` - *Commit every fixed duty first: a fixed duty that breaks availability, rest,*
  - Method `.check_constraints(person, current_date, current_team)`
  - Method `.check_team_constraints(team)`
  - Method `.generate()`

---

### [`security.py`](security.py)
> *Password and credential helpers kept free of UI dependencies.*

**Size**: `31` lines (`909` bytes)

**Functions:**
- `def secure_equals(left, right)` - *Compare two values in constant time, including non-ASCII text.*
- `def make_hashes(password)` - *Hash a password with bcrypt.*
- `def check_hashes(password, hashed_text)` - *Return True only when the stored hash is a valid bcrypt hash matching the password.*

---

### [`storage.py`](storage.py)
**Size**: `27` lines (`916` bytes)

**Functions:**
- `def atomic_write_json(path, data)` - *Write JSON without leaving a truncated file when the process dies mid-write.*

---

### [`tests/__init__.py`](tests/__init__.py)
**Size**: `0` lines (`0` bytes)

---

### [`tests/test_scheduler.py`](tests/test_scheduler.py)
**Size**: `159` lines (`5449` bytes)

**Classes:**
- `class DutySchedulerTest`
  - Method `.test_generate_fills_every_day_without_consecutive_duties()`
  - Method `.test_fixed_duty_is_assigned_on_its_date()`
  - Method `.test_busy_weekday_blocks_assignment()`
  - Method `.test_holiday_counts_as_weekend()`
  - Method `.test_two_day_rest_applies_even_when_consecutive_is_allowed()`
  - Method `.test_mixed_gender_allows_single_person_days()`
  - Method `.test_conditional_rule_uses_previous_week_trigger()`
  - Method `.test_fixed_duty_on_leave_is_reported()`
  - Method `.test_fixed_duties_cannot_exceed_people_per_day()`
  - Method `.test_fixed_duties_cannot_pair_incompatible_people()`
  - Method `.test_fixed_duties_cannot_exceed_max_duties()`

**Functions:**
- `def personnel(count)`
- `def config(**overrides)`

---

### [`tests/test_security.py`](tests/test_security.py)
**Size**: `25` lines (`824` bytes)

**Classes:**
- `class SecureEqualsTest`
  - Method `.test_compares_ascii_and_unicode_text()`
  - Method `.test_treats_missing_values_as_text()`
- `class CheckHashesTest`
  - Method `.test_rejects_missing_or_malformed_hashes()`

---

### [`tests/test_storage.py`](tests/test_storage.py)
**Size**: `34` lines (`1098` bytes)

**Classes:**
- `class AtomicWriteJsonTest`
  - Method `.test_writes_and_overwrites_json()`
  - Method `.test_leaves_no_temporary_files()`
  - Method `.test_creates_missing_parent_directory()`

---

### [`tests/test_ui_helpers.py`](tests/test_ui_helpers.py)
**Size**: `49` lines (`1915` bytes)

**Classes:**
- `class GenderModeTest`
  - Method `.test_internal_modes_are_unchanged()`
  - Method `.test_legacy_localized_labels_normalize()`
  - Method `.test_unknown_value_falls_back_to_any()`
  - Method `.test_label_follows_the_selected_language()`
- `class CalendarHtmlTest`
  - Method `.test_personnel_names_are_html_escaped()`
  - Method `.test_empty_cells_and_assignments_still_render()`

---

### [`ui_helpers.py`](ui_helpers.py)
> *Pure presentation helpers shared by the Streamlit UI and the test suite.*

**Size**: `84` lines (`3006` bytes)

**Functions:**
- `def gender_label(options, mode)` - *Return the localized label for an internal gender mode.*
- `def normalize_gender_mode(value, option_sets)` - *Accept an internal mode or a legacy localized label from saved data.*
- `def get_calendar_html(year, month, schedule, t)` - *Render the month grid, escaping every personnel name it embeds.*

---
