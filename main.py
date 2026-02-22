import streamlit as st
import pandas as pd
from datetime import date, timedelta
import calendar
from scheduler import DutyScheduler
import json
import os
import hashlib
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import holidays as holidays_lib
import statistics

# --- Translation Dictionary ---
LANG_TEXT = {
    "English": {
        "title": "🧙‍♂️ Nöbet Wizard (Duty Roster Generator)",
        "sidebar_gen": "1. General Settings",
        "year": "Year",
        "month": "Month",
        "sidebar_rules": "2. Rules",
        "ppl_day": "Personnel per Day",
        "gender_rules": "Gender Rules",
        "gender_help": "Mixed: Requires at least one Male and one Female per shift.",
        "consecutive": "Allow Consecutive Duties",
        "consecutive_help": "If checked, personnel can be assigned to duties on back-to-back days.",
        "two_day_rule": "Require 2 Days Rest",
        "two_day_help": "If checked, personnel cannot hold duty every other day (e.g. Mon -> Wed is forbidden).",
        "header_personnel": "Personnel Management",
        "add_expander": "Add New Personnel",
        "name": "Name",
        "gender": "Gender",
        "max_duties": "Max Duties",
        "fixed_total": "Fixed Total",
        "fixed_total_help": "Target total duties. Overrides Max if > 0.",
        "fixed_wknd": "Fixed Wknd",
        "fixed_wknd_help": "Target weekend duties. Overrides Max Wknd if > 0.",
        "max_wknd": "Max Wknd",
        "mixed_ok": "Mixed OK?",
        "mixed_ok_help": "Uncheck if person cannot work in mixed-gender teams",
        "busy_days": "Busy Days (Cannot hold duty)",
        "off_dates": "Specific Off Dates",
        "leave_dates": "Leave Dates",
        "fixed_dates": "Fixed Duty Dates (Must hold)",
        "add_btn": "Add Person",
        "added": "Added {}",
        "save_csv": "💾 Save CSV",
        "load_csv": "📂 Load CSV",
        "loaded": "Loaded!",
        "save_db": "💾 Save to DB",
        "db_saved": "Database saved to user profile!",
        "download_db": "📥 Download DB",
        "clear_all": "🗑️ Clear All",
        "info_start": "Please add personnel to start.",
        "header_gen": "Generate Schedule",
        "btn_gen": "🪄 Create Nöbet List",
        "err_no_pers": "No personnel added!",
        "spinner": "Calculating optimal schedule...",
        "success": "Schedule generated successfully!",
        "err_fail": "Could not generate a valid schedule with current constraints. Try increasing Max Duties or reducing constraints.",
        "stats": "Statistics",
        "col_date": "Date",
        "col_day": "Day",
        "col_team": "Team",
        "col_type": "Type",
        "type_wknd": "Weekend",
        "type_wkday": "Weekday",
        "col_assigned": "Assigned",
        "col_assigned_help": "Total duties assigned in last generation",
        "col_busy_help": "Comma-separated days (e.g. Monday, Tuesday)",
        "col_off_help": "Specific dates (YYYY-MM-DD)",
        "col_leave_help": "Dates on leave (YYYY-MM-DD)",
        "col_fixed_help": "Specific dates (YYYY-MM-DD)",
        "gender_opts": ["Any", "Mixed (Must have M & F)", "Single Gender (All M or All F)"],
        "rule_header": "Conditional Rules",
        "rule_trigger": "If holds duty on:",
        "rule_forbidden": "Cannot hold duty on:",
        "btn_add_rule": "Add Rule",
        "rule_desc": "If {} then NO {}",
        "login_tab": "Login",
        "register_tab": "Register",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "register_btn": "Register",
        "logout": "Logout",
        "login_success": "Logged In as {}",
        "login_failed": "Incorrect Username or Password",
        "user_exists": "User already exists",
        "reg_success": "Account Created! Please Login.",
        "export_excel": "📊 Export to Excel",
        "export_pdf": "📄 Export to PDF",
        "holidays": "Holidays (Count as Weekend)",
        "holidays_help": "Select dates that should be treated as weekends (e.g. National Holidays).",
        "load_tr_holidays": "🇹🇷 Load TR Holidays",
        "cal_view": "📅 Calendar View",
        "list_view": "📋 List View",
        "fairness_score": "Fairness Score (Std Dev)",
        "fairness_help": "Lower is better. 0 means perfect equality.",
        "short_days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "conflict_header": "Incompatible Pairs",
        "conflict_help": "Select two people who should NOT work together.",
        "btn_add_conflict": "Block Pair",
        "conflict_desc": "🚫 {} & {}"
    },
    "Türkçe": {
        "title": "🧙‍♂️ Nöbet Sihirbazı",
        "sidebar_gen": "1. Genel Ayarlar",
        "year": "Yıl",
        "month": "Ay",
        "sidebar_rules": "2. Kurallar",
        "ppl_day": "Günlük Personel",
        "gender_rules": "Cinsiyet Kuralları",
        "gender_help": "Karma: Her vardiyada en az bir Erkek ve bir Kadın gerektirir.",
        "consecutive": "Ardışık Nöbet İzni",
        "consecutive_help": "İşaretlenirse, personel arka arkaya günlerde nöbet tutabilir.",
        "two_day_rule": "Nöbet Arası 2 Gün (2 Günde Bir Yok)",
        "two_day_help": "İşaretlenirse, personel gün aşırı nöbet tutamaz (örn. Pzt -> Çarş olmaz, en erken Perş).",
        "header_personnel": "Personel Yönetimi",
        "add_expander": "Yeni Personel Ekle",
        "name": "İsim",
        "gender": "Cinsiyet",
        "max_duties": "Maks Nöbet",
        "fixed_total": "Sabit Toplam",
        "fixed_total_help": "Hedef toplam nöbet. >0 ise Maks yerine geçer.",
        "fixed_wknd": "Sabit H.Sonu",
        "fixed_wknd_help": "Hedef hafta sonu nöbet. >0 ise Maks H.Sonu yerine geçer.",
        "max_wknd": "Maks H.Sonu",
        "mixed_ok": "Karma Olur?",
        "mixed_ok_help": "Kişi karma ekiplerde çalışamıyorsa işareti kaldırın",
        "busy_days": "Meşgul Günler",
        "off_dates": "İzinli Tarihler",
        "leave_dates": "Yıllık İzin",
        "fixed_dates": "Sabit Nöbetler",
        "add_btn": "Personel Ekle",
        "added": "{} Eklendi",
        "save_csv": "💾 CSV Kaydet",
        "load_csv": "📂 CSV Yükle",
        "loaded": "Yüklendi!",
        "save_db": "💾 DB Kaydet",
        "db_saved": "Veritabanı kullanıcı profiline kaydedildi!",
        "download_db": "📥 DB İndir",
        "clear_all": "🗑️ Temizle",
        "info_start": "Başlamak için personel ekleyin.",
        "header_gen": "Takvim Oluştur",
        "btn_gen": "🪄 Nöbet Listesi Oluştur",
        "err_no_pers": "Personel eklenmedi!",
        "spinner": "Hesaplanıyor...",
        "success": "Takvim başarıyla oluşturuldu!",
        "err_fail": "Uygun takvim oluşturulamadı. Kısıtlamaları azaltmayı deneyin.",
        "stats": "İstatistikler",
        "col_date": "Tarih",
        "col_day": "Gün",
        "col_team": "Ekip",
        "col_type": "Tip",
        "type_wknd": "Hafta Sonu",
        "type_wkday": "Hafta İçi",
        "col_assigned": "Atanan",
        "col_assigned_help": "Son üretimde atanan toplam nöbet",
        "col_busy_help": "Virgülle ayrılmış günler (örn. Monday, Tuesday)",
        "col_off_help": "Belirli tarihler (YYYY-AA-GG)",
        "col_leave_help": "İzinli olunan tarihler (YYYY-AA-GG)",
        "col_fixed_help": "Belirli tarihler (YYYY-AA-GG)",
        "gender_opts": ["Fark etmez", "Karma (E & K olmalı)", "Tek Cinsiyet (Hepsi E veya Hepsi K)"],
        "rule_header": "Koşullu Kurallar",
        "rule_trigger": "Eğer şu gün nöbetçiyse:",
        "rule_forbidden": "Şu gün nöbet tutamaz:",
        "btn_add_rule": "Kural Ekle",
        "rule_desc": "Eğer {} ise {} YOK",
        "login_tab": "Giriş",
        "register_tab": "Kayıt Ol",
        "username": "Kullanıcı Adı",
        "password": "Şifre",
        "login_btn": "Giriş Yap",
        "register_btn": "Kayıt Ol",
        "logout": "Çıkış",
        "login_success": "Giriş Başarılı: {}",
        "login_failed": "Hatalı Kullanıcı Adı veya Şifre",
        "user_exists": "Kullanıcı zaten var",
        "reg_success": "Hesap Oluşturuldu! Lütfen Giriş Yapın.",
        "export_excel": "📊 Excel Olarak İndir",
        "export_pdf": "📄 PDF Olarak İndir",
        "holidays": "Tatiller (Hafta Sonu Say)",
        "holidays_help": "Hafta sonu gibi sayılacak günleri seçin (örn. Resmi Tatiller).",
        "load_tr_holidays": "🇹🇷 TR Tatillerini Yükle",
        "cal_view": "📅 Takvim Görünümü",
        "list_view": "📋 Liste Görünümü",
        "fairness_score": "Adalet Puanı (Std Sapma)",
        "fairness_help": "Düşük olması iyidir. 0 olması mükemmel eşitlik demektir.",
        "short_days": ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"],
        "conflict_header": "Uyumsuz Çiftler",
        "conflict_help": "Birlikte çalışmaması gereken iki kişiyi seçin.",
        "btn_add_conflict": "Çifti Engelle",
        "conflict_desc": "🚫 {} & {}"
    }
}

USER_DB_FILE = "users_db.json"
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

def get_user_db_path(username):
    safe_user = "".join([c for c in username if c.isalnum() or c in ('-', '_')])
    return f"personnel_db_{safe_user}.json"

def load_db(username):
    path = get_user_db_path(username)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Backward compatibility: if list, it's just personnel
            if isinstance(data, list):
                return {"personnel": data}
            return data
    return {"personnel": []}

def save_db(personnel, username):
    path = get_user_db_path(username)
    
    # Save full project state
    state_data = {
        "personnel": personnel,
        "conditional_rules": st.session_state.get("conditional_rules", []),
        "forbidden_pairs": st.session_state.get("forbidden_pairs", []),
        "holidays_multiselect": st.session_state.get("holidays_multiselect", []),
        # Save config settings if they exist in state
        "cfg_year": st.session_state.get("cfg_year"),
        "cfg_month": st.session_state.get("cfg_month"),
        "cfg_ppl": st.session_state.get("cfg_ppl"),
        "cfg_gender": st.session_state.get("cfg_gender"),
        "cfg_consecutive": st.session_state.get("cfg_consecutive"),
        "cfg_two_rest": st.session_state.get("cfg_two_rest")
    }
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=4)

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

def authenticate(username, password):
    # 1. Check Local DB (Hashed passwords)
    users = load_users()
    if username in users and check_hashes(password, users[username]):
        return True
    
    # 2. Check Secrets (Fallback Admin - Plain text in secrets)
    # Useful if the local DB is wiped or empty
    if hasattr(st, "secrets") and "admin" in st.secrets:
        try:
            if username == st.secrets["admin"]["username"] and password == st.secrets["admin"]["password"]:
                return True
        except KeyError:
            pass
            
    return False

def login_page():
    st.title("🧙‍♂️ Nöbet Wizard - Login")
    
    lang = st.selectbox("Language / Dil", ["English", "Türkçe"], key="login_lang")
    t = LANG_TEXT[lang]

    tab1, tab2 = st.tabs([t["login_tab"], t["register_tab"]])

    with tab1:
        username = st.text_input(t["username"], key="login_user")
        password = st.text_input(t["password"], type='password', key="login_pass")
        if st.button(t["login_btn"]):
            if authenticate(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                if 'personnel' in st.session_state:
                    del st.session_state['personnel']
                st.success(t["login_success"].format(username))
                st.rerun()
            else:
                st.error(t["login_failed"])

    with tab2:
        new_user = st.text_input(t["username"], key="reg_user")
        new_pass = st.text_input(t["password"], type='password', key="reg_pass")
        if st.button(t["register_btn"]):
            users = load_users()
            if new_user in users:
                st.error(t["user_exists"])
            else:
                users[new_user] = make_hashes(new_pass)
                save_users(users)
                st.success(t["reg_success"])

def get_calendar_html(year, month, schedule, t):
    cal = calendar.monthcalendar(year, month)
    
    # Header
    # Use CSS variables for Dark Mode compatibility
    headers = "".join([f"<th style='border:1px solid var(--text-color); padding:8px; background:var(--secondary-background-color); width:14%; color:var(--text-color);'>{day}</th>" for day in t["short_days"]])
    
    html = f"<table style='width:100%; border-collapse:collapse; table-layout: fixed;'><thead><tr>{headers}</tr></thead><tbody>"
    
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td style='border:1px solid var(--text-color); background:var(--background-color); opacity:0.5;'></td>"
            else:
                current_date = date(year, month, day)
                is_weekend = current_date.weekday() >= 5
                bg_color = "var(--background-color)" if not is_weekend else "var(--secondary-background-color)"
                
                day_content = f"<div style='font-weight:bold; margin-bottom:5px; color:var(--text-color);'>{day}</div>"
                
                if current_date in schedule:
                    team = schedule[current_date]
                    for p in team:
                        # Random pastel colors or fixed blue
                        day_content += f"<div style='background:#e6f3ff; padding:2px 4px; margin-bottom:2px; border-radius:4px; font-size:11px; border:1px solid #cce5ff; color:#004085; font-weight:bold;'>{p['name']}</div>"
                
                html += f"<td style='border:1px solid var(--text-color); padding:5px; height:100px; vertical-align:top; background:{bg_color};'>{day_content}</td>"
        html += "</tr>"
    
    html += "</tbody></table>"
    return html

def main():
    st.set_page_config(page_title="Nöbet Wizard", layout="wide")
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        
    if not st.session_state['logged_in']:
        login_page()
        return
    
    # --- Header & Language Selection ---
    col_header, col_lang = st.columns([6, 1])
    with col_lang:
        lang = st.selectbox("Language / Dil", ["English", "Türkçe"], label_visibility="collapsed")
    
    t = LANG_TEXT[lang]
    
    # Helper to translate day names for display
    def translate_day(day_en):
        if lang == "Türkçe" and day_en in DAYS_OF_WEEK:
            return DAYS_TR[DAYS_OF_WEEK.index(day_en)]
        return day_en

    with col_header:
        st.title(t["title"])

    # --- Sidebar: Configuration ---
    st.sidebar.header(t["sidebar_gen"])
    
    today = date.today()
    year = st.sidebar.number_input(t["year"], min_value=today.year, max_value=today.year+5, value=today.year, key="cfg_year")
    month = st.sidebar.selectbox(t["month"], range(1, 13), index=today.month-1, key="cfg_month")
    
    st.sidebar.header(t["sidebar_rules"])
    people_per_day = st.sidebar.number_input(t["ppl_day"], min_value=1, value=2, key="cfg_ppl")
    
    # Map display options to internal logic keys
    gender_map = {
        t["gender_opts"][0]: "Any",
        t["gender_opts"][1]: "Mixed",
        t["gender_opts"][2]: "Single Gender"
    }
    
    gender_mode = st.sidebar.selectbox(
        t["gender_rules"], 
        t["gender_opts"],
        help=t["gender_help"],
        key="cfg_gender"
    )
    allow_consecutive = st.sidebar.checkbox(t["consecutive"], value=False, help=t["consecutive_help"], key="cfg_consecutive")
    require_two_rest = st.sidebar.checkbox(t["two_day_rule"], value=False, help=t["two_day_help"], key="cfg_two_rest")
    
    # Holidays Selection
    num_days_in_month = calendar.monthrange(year, month)[1]
    all_month_dates = [date(year, month, day).strftime("%Y-%m-%d") for day in range(1, num_days_in_month + 1)]
    
    if "holidays_multiselect" not in st.session_state:
        st.session_state["holidays_multiselect"] = []

    if st.sidebar.button(t["load_tr_holidays"]):
        try:
            tr_holidays = holidays_lib.TR(years=year)
            month_holidays = [d.strftime("%Y-%m-%d") for d in tr_holidays if d.month == month]
            st.session_state["holidays_multiselect"] = month_holidays
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

    # Ensure selected holidays are valid for the current month (prevents errors when changing months)
    st.session_state["holidays_multiselect"] = [d for d in st.session_state["holidays_multiselect"] if d in all_month_dates]
    
    selected_holidays = st.sidebar.multiselect(t["holidays"], all_month_dates, key="holidays_multiselect", help=t["holidays_help"])
    
    # --- Conditional Rules ---
    st.sidebar.subheader(t["rule_header"])
    if 'conditional_rules' not in st.session_state:
        st.session_state.conditional_rules = []
        
    c_r1, c_r2 = st.sidebar.columns(2)
    with c_r1:
        trigger_day = st.selectbox(t["rule_trigger"], DAYS_OF_WEEK, format_func=translate_day, key="trig")
    with c_r2:
        forbidden_day = st.selectbox(t["rule_forbidden"], DAYS_OF_WEEK, format_func=translate_day, key="forb")
        
    if st.sidebar.button(t["btn_add_rule"]):
        rule = {"trigger": trigger_day, "forbidden": forbidden_day}
        if rule not in st.session_state.conditional_rules:
            st.session_state.conditional_rules.append(rule)
            
    # Display Rules
    if st.session_state.conditional_rules:
        st.sidebar.markdown("---")
        for i, rule in enumerate(st.session_state.conditional_rules):
            col_txt, col_del = st.sidebar.columns([4, 1])
            with col_txt:
                st.caption(t["rule_desc"].format(translate_day(rule['trigger']), translate_day(rule['forbidden'])))
            with col_del:
                if st.button("❌", key=f"del_rule_{i}"):
                    st.session_state.conditional_rules.pop(i)
                    st.rerun()

    # --- Incompatible Pairs ---
    st.sidebar.subheader(t["conflict_header"])
    if 'forbidden_pairs' not in st.session_state:
        st.session_state.forbidden_pairs = []
        
    # Get list of names
    personnel_names = [p['name'] for p in st.session_state.get('personnel', [])]
    
    if len(personnel_names) >= 2:
        c_c1, c_c2 = st.sidebar.columns(2)
        with c_c1:
            p1 = st.selectbox("Person 1", personnel_names, key="conf_p1", label_visibility="collapsed")
        with c_c2:
            p2 = st.selectbox("Person 2", personnel_names, key="conf_p2", label_visibility="collapsed")
            
        if st.sidebar.button(t["btn_add_conflict"]):
            if p1 != p2:
                pair = {'p1': p1, 'p2': p2}
                # Check duplicates (order doesn't matter)
                exists = any((x['p1'] == p1 and x['p2'] == p2) or (x['p1'] == p2 and x['p2'] == p1) for x in st.session_state.forbidden_pairs)
                if not exists:
                    st.session_state.forbidden_pairs.append(pair)
                    st.rerun()
                else:
                    st.sidebar.warning("Pair already exists")
            else:
                st.sidebar.warning("Select different people")
                
    if st.session_state.forbidden_pairs:
        st.sidebar.markdown("---")
        for i, pair in enumerate(st.session_state.forbidden_pairs):
            col_txt, col_del = st.sidebar.columns([4, 1])
            with col_txt:
                st.caption(t["conflict_desc"].format(pair['p1'], pair['p2']))
            with col_del:
                if st.button("❌", key=f"del_conf_{i}"):
                    st.session_state.forbidden_pairs.pop(i)
                    st.rerun()
    
    # Logout Button
    st.sidebar.markdown("---")
    if st.sidebar.button(t["logout"]):
        st.session_state['logged_in'] = False
        if 'personnel' in st.session_state:
            del st.session_state['personnel']
        st.rerun()

    # --- Main Area: Personnel Management ---
    st.header(t["header_personnel"])
    
    if 'personnel' not in st.session_state:
        # Load full project state
        db_data = load_db(st.session_state.get('username'))
        st.session_state.personnel = db_data.get("personnel", [])
        
        # Restore other settings if available
        if "conditional_rules" in db_data:
            st.session_state.conditional_rules = db_data["conditional_rules"]
        if "forbidden_pairs" in db_data:
            st.session_state.forbidden_pairs = db_data["forbidden_pairs"]
        if "holidays_multiselect" in db_data:
            st.session_state.holidays_multiselect = db_data["holidays_multiselect"]
            
        # Restore config widgets (Streamlit handles this if we set the key in session_state)
        for key in ["cfg_year", "cfg_month", "cfg_ppl", "cfg_gender", "cfg_consecutive", "cfg_two_rest"]:
            if key in db_data:
                st.session_state[key] = db_data[key]

    # Form to add new person
    with st.expander(t["add_expander"], expanded=True):
        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1, 1, 1, 1, 1, 1])
        with c1:
            name = st.text_input(t["name"])
        with c2:
            gender = st.selectbox(t["gender"], ["M", "F"])
        with c3:
            fixed_total = st.number_input(t["fixed_total"], min_value=0, value=0, help=t["fixed_total_help"])
        with c4:
            max_duties = st.number_input(t["max_duties"], min_value=0, value=5)
        with c5:
            fixed_wknd = st.number_input(t["fixed_wknd"], min_value=0, value=0, help=t["fixed_wknd_help"])
        with c6:
            max_weekends = st.number_input(t["max_wknd"], min_value=0, value=2)
        with c7:
            mixed_ok = st.checkbox(t["mixed_ok"], value=True, help=t["mixed_ok_help"])
        
        num_days = calendar.monthrange(year, month)[1]
        date_options = [date(year, month, day).strftime("%Y-%m-%d") for day in range(1, num_days + 1)]
        
        c_row2_1, c_row2_2, c_row2_3, c_row2_4 = st.columns([1, 1, 1, 1])
        with c_row2_1:
            busy_days = st.multiselect(t["busy_days"], DAYS_OF_WEEK, format_func=translate_day)
        with c_row2_2:
            off_dates = st.multiselect(t["off_dates"], date_options)
        with c_row2_3:
            leave_range = st.date_input(
                t["leave_dates"],
                value=[],
                min_value=date(year, month, 1),
                max_value=date(year, month, num_days)
            )
        with c_row2_4:
            fixed_dates = st.multiselect(t["fixed_dates"], date_options)
            
        add_btn = st.button(t["add_btn"], use_container_width=True)

        if add_btn and name:
            leave_dates = []
            if leave_range:
                start = leave_range[0]
                end = leave_range[-1]
                curr = start
                while curr <= end:
                    leave_dates.append(curr.strftime("%Y-%m-%d"))
                    curr += timedelta(days=1)

            st.session_state.personnel.append({
                "name": name,
                "gender": gender,
                "fixed_duties_total": fixed_total,
                "fixed_duties_weekend": fixed_wknd,
                "max_duties": max_duties,
                "max_weekends": max_weekends,
                "mixed_gender_allowed": mixed_ok,
                "busy_days": ", ".join(busy_days),
                "off_dates": ", ".join(off_dates),
                "leave_dates": ", ".join(leave_dates),
                "fixed_dates": ", ".join(fixed_dates),
                "duty_count": 0, # Runtime tracker
                "weekend_duty_count": 0 # Runtime tracker
            })
            st.success(t["added"].format(name))

    # Display current list
    if st.session_state.personnel:
        df_personnel = pd.DataFrame(st.session_state.personnel)
        
        # Ensure columns exist
        if "mixed_gender_allowed" not in df_personnel.columns:
            df_personnel["mixed_gender_allowed"] = True
        if "fixed_duties_total" not in df_personnel.columns:
            # Migration: Use old fixed_duties if available, else 0
            df_personnel["fixed_duties_total"] = df_personnel.get("fixed_duties", 0)
            
        if "fixed_duties_weekend" not in df_personnel.columns:
            df_personnel["fixed_duties_weekend"] = 0
            
        if "duty_count" not in df_personnel.columns:
            df_personnel["duty_count"] = 0
        if "busy_days" not in df_personnel.columns:
            df_personnel["busy_days"] = ""
        if "off_dates" not in df_personnel.columns:
            df_personnel["off_dates"] = ""
        if "leave_dates" not in df_personnel.columns:
            df_personnel["leave_dates"] = ""
        if "fixed_dates" not in df_personnel.columns:
            df_personnel["fixed_dates"] = ""
            
        # Editable Dataframe
        edited_df = st.data_editor(
            df_personnel[["name", "gender", "fixed_duties_total", "max_duties", "fixed_duties_weekend", "max_weekends", "mixed_gender_allowed", "busy_days", "off_dates", "leave_dates", "fixed_dates", "duty_count"]],
            column_config={
                "name": t["name"],
                "gender": st.column_config.SelectboxColumn(t["gender"], options=["M", "F"], required=True),
                "fixed_duties_total": st.column_config.NumberColumn(t["fixed_total"], min_value=0, step=1, help=t["fixed_total_help"]),
                "fixed_duties_weekend": st.column_config.NumberColumn(t["fixed_wknd"], min_value=0, step=1, help=t["fixed_wknd_help"]),
                "max_duties": st.column_config.NumberColumn(t["max_duties"], min_value=0, step=1),
                "max_weekends": st.column_config.NumberColumn(t["max_wknd"], min_value=0, step=1),
                "mixed_gender_allowed": st.column_config.CheckboxColumn(t["mixed_ok"]),
                "busy_days": st.column_config.TextColumn(t["busy_days"], help=t["col_busy_help"]),
                "off_dates": st.column_config.TextColumn(t["off_dates"], help=t["col_off_help"]),
                "leave_dates": st.column_config.TextColumn(t["leave_dates"], help=t["col_leave_help"]),
                "fixed_dates": st.column_config.TextColumn(t["fixed_dates"], help=t["col_fixed_help"]),
                "duty_count": st.column_config.NumberColumn(t["col_assigned"], disabled=True, help=t["col_assigned_help"])
            },
            use_container_width=True,
            num_rows="dynamic",
            key="personnel_editor"
        )
        
        # Update session state from editor
        st.session_state.personnel = edited_df.to_dict('records')

        # --- Save / Load Section ---
        st.divider()
        c_dl, c_db, c_json, c_ul, c_cl = st.columns([1, 1, 1, 2, 1])
        
        with c_dl:
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(t["save_csv"], csv, "nobet_list.csv", "text/csv")
            
        with c_db:
            if st.button(t["save_db"]):
                save_db(st.session_state.personnel, st.session_state.get('username'))
                st.success(t["db_saved"])

        with c_json:
            json_data = json.dumps(st.session_state.personnel, ensure_ascii=False, indent=4) # Keep download as just personnel for portability
            st.download_button(
                label=t["download_db"],
                data=json_data,
                file_name="personnel_db.json",
                mime="application/json"
            )

        with c_ul:
            uploaded_file = st.file_uploader(t["load_csv"], type="csv", label_visibility="collapsed")
            if uploaded_file:
                try:
                    loaded_df = pd.read_csv(uploaded_file)
                    st.session_state.personnel = loaded_df.to_dict('records')
                    st.success(t["loaded"])
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        with c_cl:
            if st.button(t["clear_all"]):
                st.session_state.personnel = []
                st.rerun()
    else:
        st.info(t["info_start"])

    # --- Generation Section ---
    st.divider()
    st.header(t["header_gen"])

    if st.button(t["btn_gen"], type="primary"):
        if not st.session_state.personnel:
            st.error(t["err_no_pers"])
            return

        # Convert rules to indices for scheduler
        # calendar.day_name is ['Monday', 'Tuesday'...] -> Index 0-6
        scheduler_rules = []
        for r in st.session_state.conditional_rules:
            scheduler_rules.append({
                'trigger': DAYS_OF_WEEK.index(r['trigger']),
                'forbidden': DAYS_OF_WEEK.index(r['forbidden'])
            })

        # Prepare Config
        config = {
            'people_per_day': people_per_day,
            'gender_mode': gender_map[gender_mode],
            'allow_consecutive': allow_consecutive,
            'conditional_rules': scheduler_rules,
            'require_two_rest_days': require_two_rest,
            'holidays': selected_holidays,
            'forbidden_pairs': st.session_state.forbidden_pairs
        }

        # Initialize Scheduler
        scheduler = DutyScheduler(year, month, st.session_state.personnel, config)
        
        with st.spinner(t["spinner"]):
            success, schedule = scheduler.generate()

        if success:
            st.success(t["success"])
            
            # Process data for display
            display_data = []
            calendar_data = []
            
            for d, team in sorted(schedule.items()):
                names = ", ".join([p['name'] for p in team])
                day_name = translate_day(DAYS_OF_WEEK[d.weekday()])
                is_weekend = d.weekday() >= 5
                
                display_data.append({
                    t["col_date"]: d.strftime("%Y-%m-%d"),
                    t["col_day"]: day_name,
                    t["col_team"]: names,
                    t["col_type"]: t["type_wknd"] if is_weekend else t["type_wkday"]
                })

            df_res = pd.DataFrame(display_data)
            
            # --- TABS ---
            tab_list, tab_cal, tab_stats = st.tabs([t["list_view"], t["cal_view"], t["stats"]])
            
            with tab_list:
                st.dataframe(df_res, use_container_width=True)
                
            with tab_cal:
                cal_html = get_calendar_html(year, month, schedule, t)
                st.markdown(cal_html, unsafe_allow_html=True)
            
            # Show Stats
            with tab_stats:
                stats = []
                duty_counts = []
                for p in st.session_state.personnel:
                    stats.append({
                        t["name"]: p['name'],
                        t["col_assigned"]: p['duty_count'],
                        t["type_wknd"]: p['weekend_duty_count']
                    })
                    duty_counts.append(p['duty_count'])
                
                # Fairness Metric
                if len(duty_counts) > 1:
                    stdev = statistics.stdev(duty_counts)
                    st.metric(label=t["fairness_score"], value=f"{stdev:.2f}", help=t["fairness_help"])
                
                st.dataframe(pd.DataFrame(stats), use_container_width=True)
                
                # Chart
                st.caption("Duty Distribution / Nöbet Dağılımı")
                st.bar_chart(pd.DataFrame(stats).set_index(t["name"])[[t["col_assigned"], t["type_wknd"]]])
            
            # --- Export Section ---
            st.divider()
            c_ex1, c_ex2 = st.columns(2)
            
            # 1. Excel Export
            buffer_excel = BytesIO()
            try:
                with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                    df_res.to_excel(writer, index=False, sheet_name='Schedule')
                    # Adjust column widths
                    worksheet = writer.sheets['Schedule']
                    for column_cells in worksheet.columns:
                        length = max(len(str(cell.value)) for cell in column_cells)
                        worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
                
                with c_ex1:
                    st.download_button(
                        label=t["export_excel"],
                        data=buffer_excel.getvalue(),
                        file_name=f"nobet_list_{year}_{month}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except ImportError:
                st.error("Missing 'openpyxl' library. Please run: pip install openpyxl")
            except Exception as e:
                st.error(f"Excel Export Error: {e}")

            # 2. PDF Export
            buffer_pdf = BytesIO()
            doc = SimpleDocTemplate(buffer_pdf, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            elements.append(Paragraph(f"{t['title']} - {year}/{month}", styles['Title']))
            
            # Table
            data = [df_res.columns.to_list()] + df_res.values.tolist()
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
            
            try:
                doc.build(elements)
                pdf_data = buffer_pdf.getvalue()
                with c_ex2:
                    st.download_button(
                        label=t["export_pdf"],
                        data=pdf_data,
                        file_name=f"nobet_list_{year}_{month}.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"PDF Generation Error: {e}")
            
        else:
            st.error(t["err_fail"])

if __name__ == '__main__':
    if st.runtime.exists():
        main()
    else:
        import sys
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
