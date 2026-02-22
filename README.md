# 🧙‍♂️ Nöbet Wizard (Duty Roster Generator)

<p align="center">
  <img src="https://github.com/Aegean-E/NobetWizard/blob/main/banner.jpg?raw=true" alt="Nöbet Wizard Banner" width="1200">
</p>


<p align="center">https://nobetwizard.streamlit.app/</p>

**Nöbet Wizard** is a powerful, web-based application built with Python and Streamlit designed to automate the creation of monthly duty rosters (nöbet listesi). It handles complex constraints, personnel preferences, and fair distribution rules to generate optimal schedules in seconds.

## 🌟 Features

### 👥 Personnel Management
*   **Detailed Profiles:** Manage staff with attributes like Name, Gender, **Role (Senior/Junior)**, and Max Duty limits.
*   **Availability Constraints:**
    *   **Busy Days:** Block specific days of the week (e.g., "No Mondays").
    *   **Off Dates:** Block specific calendar dates (e.g., holidays or specific appointments).
    *   **Leave Dates:** Define date ranges for annual leave (Yıllık İzin).
    *   **Fixed Duties:** Force assignment on specific dates (Priority assignment).
*   **Workload Targets:**
    *   **Max Duties:** Set a hard limit on the total number of duties per month.
    *   **Max Weekend Duties:** Set a hard limit on weekend shifts.
    *   **Fixed Total:** Set a *target* number of duties. The scheduler prioritizes these individuals to reach this number.
    *   **Fixed Weekend:** Set a *target* number of weekend duties.
*   **Preferences:**
    *   **Mixed Gender:** Option to opt-out of mixed-gender teams (e.g., a person who prefers not to be on a mixed team).
*   **Editable Grid:** Inline editing of all personnel data for quick adjustments.
*   **Smart Tools:**
    *   **Leave Range Adder:** Quickly add annual leave for a date range (e.g., 01/02/2024 - 10/02/2024) instead of selecting days one by one.
    *   **Busy Days Manager:** Multi-select interface to easily manage weekly unavailable days (e.g., "Every Monday").
    *   **Start New Month (Reset):** One-click reset for date-specific constraints (Busy, Off, Leave, Fixed) to prepare for the next month. This preserves personnel profiles, roles, and targets, saving time on data entry.
*   **Persistence:**
    *   **User-Specific Database:** Personnel lists are saved to your user profile (Local JSON or Cloud Firestore).
    *   **Import/Export:** Save and load personnel lists via CSV or JSON.

### ⚙️ Scheduling Rules & Constraints
*   **Team Composition:** Configure number of people per day.
*   **Seniority Rules:**
    *   **Roles:** Assign personnel as **Senior** or **Junior**.
    *   **Min. Seniors:** Enforce a minimum number of Seniors per shift to ensure experience balance in the team.
*   **Gender Rules:**
    *   *Any*: No restrictions on team composition.
    *   *Mixed*: Requires at least one Male and one Female per shift (if team size > 1).
    *   *Single Gender*: Teams must be all Male or all Female.
*   **Rest & Spacing Rules:**
    *   **Consecutive Days:** Toggle to allow or disallow back-to-back duties (e.g., Mon & Tue).
    *   **2-Day Rest (Nöbet Arası 2 Gün):** Prevent duties on alternate days (e.g., Mon -> Wed forbidden, must wait until Thu).
    *   **Weekly Limits:** Soft constraint to prevent burnout (max ~3 duties per week).
    *   **Previous Month Continuity:** Input who worked on the last days of the previous month to ensure rest rules are respected at the start of the new month.
*   **Advanced Logic:**
    *   **Conditional Rules:** Create custom logic like "If someone holds duty on Wednesday, they cannot hold duty on Saturday".
    *   **Incompatible Pairs:** Define pairs of people who should **never** work together (Conflict resolution).
*   **Optimization Algorithm:**
    *   **Fairness-First (Best-of-N):** The system generates multiple valid schedules (Monte Carlo simulation) in the background and automatically selects the one with the lowest standard deviation (most equal distribution).
    *   **Water-Filling Logic:** The scheduler prioritizes personnel with the fewest current duties when assigning shifts to prevent "clumping" of shifts.
*   **Holidays:**
    *   **Manual Selection:** Mark specific dates to be treated as weekends (affecting weekend counts and coloring).
    *   **Auto-Load:** One-click integration to fetch Turkish National Holidays for the selected year.

### 📊 Output & Visualization
*   **Multiple Views:**
    *   **List View:** A sortable data table of the generated schedule.
    *   **Calendar View:** A visual monthly calendar grid (Dark Mode compatible) showing assignments.
    *   **Statistics:** Detailed breakdown of total and weekend duties per person.
*   **Fairness Metrics:**
    *   **Fairness Score:** Calculates the Standard Deviation of duty counts to mathematically quantify how equal the distribution is (Lower is better).
    *   **Visual Charts:** Bar charts to visualize duty distribution.
*   **Export:**
    *   **Excel (.xlsx):** Download formatted spreadsheets with auto-adjusted column widths.
    *   **PDF:** Download professional-looking PDF reports with Turkish font support (Roboto).
    *   **iCalendar (.ics):** Export the schedule to standard calendar format for integration with Google Calendar, Outlook, or Apple Calendar.

### 🌍 Localization
*   Full support for **English** and **Turkish** (Türkçe) languages.
*   UI elements, day names, and help text dynamically translate.

### 🔐 Security & Cloud
*   **Authentication:**
*   Built-in Login/Register system.
*   Secure password hashing.
    *   **Super Admin Fallback:** Configurable via Streamlit Secrets for emergency access.

---

## 🚀 Installation

1.  **Clone the repository** or download the source code.
2.  **Install dependencies**:
    Ensure you have Python installed, then run:
    ```bash
    pip install -r requirements.txt
    ```

## 🏃‍♂️ Usage

1.  **Run the application**:
    ```bash
    streamlit run main.py
    ```
    *Note: You can also run `python main.py`, and the script will automatically launch Streamlit.*

2.  **Login / Register**:
    *   Create a new account on the "Register" tab.
    *   Log in to access your dashboard.
    *   *Tip: If configured, use Admin credentials from secrets.*

3.  **Workflow**:
    *   **General Settings:** Select the Year and Month.
    *   **Rules:** Set personnel per day, gender constraints, and rest rules.
    *   **Personnel:** Add your team members. Use the "Edit" table to fine-tune constraints like "Busy Days" or "Leave Dates".
    *   **Advanced:** Add conditional rules or incompatible pairs in the sidebar.
    *   **Generate:** Click "Create Nöbet List".
    *   **Analyze:** Check the "Calendar View" and "Statistics" tabs.
    *   **Export:** Download your schedule as PDF or Excel.

---

## 🛠️ Technologies Used

*   **Streamlit:** Web interface and state management.
*   **Pandas:** Data manipulation and Excel export.
*   **ReportLab:** PDF generation.
*   **OpenPyXL:** Excel engine.
*   **Holidays:** Automated holiday fetching.
*   **Google Cloud Firestore:** NoSQL database for cloud persistence.
*   **Python Standard Library:** `calendar`, `random`, `hashlib`, `json`, `statistics`.

## 📂 Project Structure

*   `main.py`: The main application entry point and UI logic.
*   `scheduler.py`: The core algorithm for constraint satisfaction and schedule generation.
*   `requirements.txt`: Python dependencies.
*   `*_db.json`: Local storage for users and personnel data (used if Firestore is not configured).
