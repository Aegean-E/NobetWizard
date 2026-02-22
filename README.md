# 🧙‍♂️ Nöbet Wizard (Duty Roster Generator)

**Nöbet Wizard** is a powerful, web-based application built with Python and Streamlit designed to automate the creation of monthly duty rosters (nöbet listesi). It handles complex constraints, personnel preferences, and fair distribution rules to generate optimal schedules in seconds.

## 🌟 Features

### 👥 Personnel Management
*   **Detailed Profiles:** Manage staff with attributes like Name, Gender, and Max Duty limits.
*   **Availability Constraints:**
    *   **Busy Days:** Block specific days of the week (e.g., "No Mondays").
    *   **Off Dates:** Block specific calendar dates (e.g., holidays or leave).
    *   **Fixed Duties:** Force assignment on specific dates.
*   **Preferences:**
    *   **Mixed Gender:** Option to opt-out of mixed-gender teams.
    *   **Fixed Duty Count:** Set a target number of duties to override maximums.
*   **User-Specific Database:** Personnel lists are saved to your user profile.

### ⚙️ Scheduling Rules
*   **Team Composition:** Configure number of people per day.
*   **Gender Rules:**
    *   *Any*: No restrictions.
    *   *Mixed*: Requires at least one Male and one Female per shift.
    *   *Single Gender*: Teams must be all Male or all Female.
*   **Rest Rules:**
    *   **Consecutive Days:** Allow or disallow back-to-back duties.
    *   **2-Day Rest:** Prevent duties on alternate days (e.g., Mon -> Wed forbidden).
*   **Conditional Logic:** Create custom rules like "If someone holds duty on Wednesday, they cannot hold duty on Saturday".

### 📊 Output & Export
*   **Interactive Calendar:** View the generated schedule in a table format.
*   **Statistics:** Track total duties and weekend shifts per person.
*   **Export:** Download the final roster as **Excel (.xlsx)** or **PDF**.

### 🌍 Localization
*   Full support for **English** and **Turkish** (Türkçe) languages.

### 🔐 Security
*   Built-in Login/Register system.
*   Secure password hashing.

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

3.  **Workflow**:
    *   **General Settings:** Select the Year and Month.
    *   **Rules:** Set personnel per day and gender constraints.
    *   **Personnel:** Add your team members. Use the "Edit" table to fine-tune constraints.
    *   **Generate:** Click "Create Nöbet List".
    *   **Export:** Download your schedule.

---

## 🛠️ Technologies Used

*   **Streamlit:** Web interface and state management.
*   **Pandas:** Data manipulation.
*   **ReportLab:** PDF generation.
*   **OpenPyXL:** Excel export.
*   **Python Standard Library:** `calendar`, `random`, `hashlib`, `json`.

## 📂 Project Structure

*   `main.py`: The main application entry point and UI logic.
*   `scheduler.py`: The core algorithm for constraint satisfaction and schedule generation.
*   `requirements.txt`: Python dependencies.
*   `*_db.json`: Local storage for users and personnel data.