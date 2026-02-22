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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import urllib.request
import holidays as holidays_lib
import statistics

# --- Cloud Database Imports ---
try:
    from google.cloud import firestore
    from google.oauth2 import service_account
except ImportError:
    firestore = None

# --- Translation Dictionary ---
LANG_TEXT = {
    "English": {
        "title": "🧙‍♂️ Nöbet Wizard (Duty Roster Generator)",
        "sidebar_gen": "General Settings",
        "year": "Year",
        "month": "Month",
        "sidebar_rules": "Rules",
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
        "save_db": "💾 Save Personnel to the Database",
        "load_db_btn": "☁️ Load Personnel Database",
        "db_saved": "Database saved to user profile!",
        "db_cleared": "Database cleared!",
        "download_db": "📥 Download Personnel Database",
        "clear_all": "🗑️ Clear Current List",
        "clear_db_btn": "🔥 Clear Personnel Database",
        "info_start": "Please add personnel to start.",
        "btn_gen": "🪄 Create Duty List",
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
        "col_busy_help": "Comma-separated days. Use the tool below to select days.",
        "col_off_help": "Specific dates (YYYY-MM-DD)",
        "col_leave_help": "Dates on leave (DD/MM/YYYY). Use the tool below for date ranges.",
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
        "conflict_desc": "🚫 {} & {}",
        "template_download": "📥 Download Excel Template",
        "co_occurrence": "🤝 Team Co-occurrence (Who works with whom?)",
        "day_distribution": "📅 Day of Week Distribution",
        "role": "Role",
        "role_senior": "Senior",
        "role_junior": "Junior",
        "min_seniors": "Min. Seniors per Shift",
        "confirm_yes": "Yes, I'm sure",
        "confirm_no": "Cancel",
        "placeholder_select": "Choose options",
        "export_ics": "📅 Export to Calendar (.ics)",
        "btn_reset_month": "🔄 Start New Month (Reset Dates)",
        "reset_month_help": "Keeps personnel profiles but clears specific date constraints (Busy, Off, Leave, Fixed) for a fresh month.",
        "reset_success": "Date constraints cleared for the new month!",
        "tools_expander": "🛠️ Personnel Tools (Leave & Busy Days)",
        "header_leave": "Add Leave Range",
        "header_busy": "Manage Busy Days",
        "btn_add_leave": "Add Leave Range",
        "btn_save_busy": "Update Busy Days",
        "busy_updated": "Busy days updated for {}!"
    },
    "Türkçe": {
        "title": "🧙‍♂️ Nöbet Sihirbazı",
        "sidebar_gen": "Genel Ayarlar",
        "year": "Yıl",
        "month": "Ay",
        "sidebar_rules": "Kurallar",
        "ppl_day": "Günlük Personel Sayısı",
        "gender_rules": "Cinsiyet Kuralları",
        "gender_help": "Karma: Her vardiyada en az bir Erkek ve bir Kadın gerektirir.",
        "consecutive": "Nöbet Ertesi İzni Yasağı",
        "consecutive_help": "İşaretlenirse, personel arka arkaya günlerde nöbet tutabilir.",
        "two_day_rule": "Gün Aşırı Nöbet Yasağı",
        "two_day_help": "İşaretlenirse, personel gün aşırı nöbet tutamaz (örn. Pzt -> Çarş olmaz, en erken Perş).",
        "header_personnel": "Personel Yönetimi",
        "add_expander": "Yeni Personel Ekle",
        "name": "İsim",
        "gender": "Cinsiyet",
        "max_duties": "Maksimum Nöbet",
        "fixed_total": "Sabit Toplam Nöbet",
        "fixed_total_help": "Hedef toplam nöbet. >0 ise Maks yerine geçer.",
        "fixed_wknd": "Sabit Haftasonu Nöbet",
        "fixed_wknd_help": "Hedef hafta sonu nöbet. >0 ise Maks H.Sonu yerine geçer.",
        "max_wknd": "Maksimum Hafta Sonu Nöbeti Sayısı",
        "mixed_ok": "Karma Nöbet Tutmaya Uygundur",
        "mixed_ok_help": "Kişi karma ekiplerde çalışamıyorsa işareti kaldırın",
        "busy_days": "Nöbet Tutamayacağı Günler",
        "off_dates": "İzinli Tarihler",
        "leave_dates": "Yıllık İzin",
        "fixed_dates": "Önceden Belirlenmiş Nöbet Tarihi",
        "add_btn": "Personel Ekle",
        "added": "{} Eklendi",
        "save_csv": "💾 CSV Kaydet",
        "load_csv": "📂 CSV Yükle",
        "loaded": "Yüklendi!",
        "save_db": "💾 Personeli Veritabanına Kaydet",
        "load_db_btn": "☁️ Personel Veritabanını Yükle",
        "db_saved": "Veritabanı kullanıcı profiline kaydedildi!",
        "db_cleared": "Veritabanı temizlendi!",
        "download_db": "📥 Personel Veritabanını İndir",
        "clear_all": "🗑️ Mevcut Listeyi Temizle",
        "clear_db_btn": "🔥 Personel Veritabanını Temizle",
        "info_start": "Başlamak için personel ekleyin.",
        "header_gen": "Takvim Oluştur",
        "btn_gen": "🪄 Nöbet Listesi Oluştur",
        "err_no_pers": "Personel eklenmedi!",
        "spinner": "Hesaplanıyor...",
        "success": "Nöbet takvimi başarıyla oluşturuldu!",
        "err_fail": "Uygun takvim oluşturulamadı. Kuralları azaltmayı ya da nöbet sayılarını arttırmayı deneyin.",
        "stats": "İstatistikler",
        "col_date": "Tarih",
        "col_day": "Gün",
        "col_team": "Ekip",
        "col_type": "Tip",
        "type_wknd": "Hafta Sonu",
        "type_wkday": "Hafta İçi",
        "col_assigned": "Atanan",
        "col_assigned_help": "Son üretimde atanan toplam nöbet",
        "col_busy_help": "Virgülle ayrılmış günler. Gün seçmek için aşağıdaki aracı kullanın.",
        "col_off_help": "Belirli tarihler (YYYY-AA-GG)",
        "col_leave_help": "İzinli olunan tarihler (GG/AA/YYYY). Tarih aralığı için aşağıdaki aracı kullanın.",
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
        "load_tr_holidays": "TR Tatillerini Yükle",
        "cal_view": "📅 Takvim Görünümü",
        "list_view": "📋 Liste Görünümü",
        "fairness_score": "Adalet Puanı (Standart Sapma)",
        "fairness_help": "Düşük olması iyidir. 0 olması mükemmel eşitlik demektir.",
        "short_days": ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"],
        "conflict_header": "Uyumsuz Çiftler",
        "conflict_help": "Birlikte çalışmaması gereken iki kişiyi seçin.",
        "btn_add_conflict": "Çifti Engelle",
        "conflict_desc": "🚫 {} & {}",
        "template_download": "📥 Excel Şablonu İndir",
        "co_occurrence": "🤝 Birlikte Çalışma Sıklığı",
        "day_distribution": "📅 Gün Bazlı Dağılım",
        "role": "Rol",
        "role_senior": "Kıdemli",
        "role_junior": "Kıdemsiz",
        "min_seniors": "Vardiya Başı Min. Kıdemli",
        "confirm_yes": "Evet, Eminim",
        "confirm_no": "İptal",
        "placeholder_select": "Seçiniz",
        "export_ics": "📅 Takvime Ekle (.ics)",
        "btn_reset_month": "🔄 Yeni Ay Başlat (Tarihleri Sıfırla)",
        "reset_month_help": "Personel profillerini korur ancak aya özel tarihleri (Mazeret, İzin, Sabit) temizler.",
        "reset_success": "Yeni ay için tarih kısıtlamaları temizlendi!",
        "tools_expander": "🛠️ Personel Araçları (İzin & Meşgul Günler)",
        "header_leave": "İzin Aralığı Ekle",
        "header_busy": "Meşgul Günleri Yönet",
        "btn_add_leave": "İzin Aralığı Ekle",
        "btn_save_busy": "Meşgul Günleri Güncelle",
        "busy_updated": "{} için meşgul günler güncellendi!"
    }
}

USER_DB_FILE = "users_db.json"
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

def get_firestore_db():
    """Initialize Firestore Client from Streamlit Secrets"""
    if firestore is None:
        return None
    
    if "firebase" in st.secrets:
        try:
            # Construct credentials from secrets dictionary
            key_dict = dict(st.secrets["firebase"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            db = firestore.Client(credentials=creds, project=key_dict["project_id"])
            return db
        except Exception as e:
            st.error(f"Firebase Connection Error: {e}")
            return None
    return None

def get_user_db_path(username):
    safe_user = "".join([c for c in username if c.isalnum() or c in ('-', '_')])
    return f"personnel_db_{safe_user}.json"

def load_db(username):
    # 1. Try Cloud Database
    db = get_firestore_db()
    if db:
        doc = db.collection("personnel_data").document(username).get()
        if doc.exists:
            return doc.to_dict()
        return {"personnel": []}

    # 2. Fallback to Local JSON
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
    # Prepare full state data
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
        "cfg_two_rest": st.session_state.get("cfg_two_rest"),
        "cfg_min_seniors": st.session_state.get("cfg_min_seniors"),
        "cfg_language": st.session_state.get("cfg_language")
    }

    # Save generated schedule if exists (Convert date keys to strings)
    if st.session_state.get("schedule_success") and st.session_state.get("generated_schedule"):
        sched_serializable = {}
        for d, team in st.session_state.generated_schedule.items():
            sched_serializable[d.strftime("%Y-%m-%d")] = team
        
        state_data["generated_schedule"] = sched_serializable
        state_data["gen_year"] = st.session_state.get("gen_year")
        state_data["gen_month"] = st.session_state.get("gen_month")
    
    # 1. Try Cloud Database
    db = get_firestore_db()
    if db:
        db.collection("personnel_data").document(username).set(state_data)
        return

    # 2. Fallback to Local JSON
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
    # 1. Check Cloud DB
    db = get_firestore_db()
    if db:
        doc = db.collection("users").document(username).get()
        if doc.exists:
            stored_hash = doc.to_dict().get("password_hash")
            return check_hashes(password, stored_hash)
    
    # 2. Check Local DB (Hashed passwords)
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
            # 1. Cloud Registration
            db = get_firestore_db()
            if db:
                doc_ref = db.collection("users").document(new_user)
                if doc_ref.get().exists:
                    st.error(t["user_exists"])
                else:
                    doc_ref.set({"password_hash": make_hashes(new_pass)})
                    st.success(t["reg_success"])
            else:
                # 2. Local Registration
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

def generate_ics(schedule, title="Duty Roster"):
    """Generates an iCalendar string for the schedule."""
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//NobetWizard//DutyRoster//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    for d, team in schedule.items():
        names = ", ".join([p['name'] for p in team])
        dt_start = d.strftime("%Y%m%d")
        dt_end = (d + timedelta(days=1)).strftime("%Y%m%d") # All day events end next day
        
        ics_content.append("BEGIN:VEVENT")
        ics_content.append(f"DTSTART;VALUE=DATE:{dt_start}")
        ics_content.append(f"DTEND;VALUE=DATE:{dt_end}")
        ics_content.append(f"SUMMARY:{title}: {names}")
        ics_content.append(f"DESCRIPTION:Team: {names}")
        ics_content.append("END:VEVENT")
        
    ics_content.append("END:VCALENDAR")
    return "\n".join(ics_content).encode('utf-8')

def generate_excel(df_res):
    buffer_excel = BytesIO()
    with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
        df_res.to_excel(writer, index=False, sheet_name='Schedule')
        # Adjust column widths
        worksheet = writer.sheets['Schedule']
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
    return buffer_excel.getvalue()

def generate_pdf(df_res, year, month, t):
    buffer_pdf = BytesIO()
    doc = SimpleDocTemplate(buffer_pdf, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # --- Font Registration for Turkish Support ---
    font_name = 'Helvetica' # Default fallback
    font_name_bold = 'Helvetica-Bold'
    try:
        font_path_reg = "Roboto-Regular.ttf"
        font_path_bold = "Roboto-Bold.ttf"
        
        if not os.path.exists(font_path_reg):
            urllib.request.urlretrieve("https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf", font_path_reg)
        
        if not os.path.exists(font_path_bold):
            urllib.request.urlretrieve("https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Bold.ttf", font_path_bold)
        
        pdfmetrics.registerFont(TTFont('Roboto', font_path_reg))
        pdfmetrics.registerFont(TTFont('Roboto-Bold', font_path_bold))
        font_name = 'Roboto'
        font_name_bold = 'Roboto-Bold'
    except Exception as e:
        print(f"Font Error: {e}")

    # Title
    title_style = styles['Title']
    title_style.fontName = font_name_bold
    elements.append(Paragraph(f"{t['title']} - {year}/{month}", title_style))
    
    # Table
    data = [df_res.columns.to_list()] + df_res.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    
    doc.build(elements)
    return buffer_pdf.getvalue()

def main():
    st.set_page_config(page_title="Nöbet Wizard", layout="wide")
    
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        
    if not st.session_state['logged_in']:
        login_page()
        return
    
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
        for key in ["cfg_year", "cfg_month", "cfg_ppl", "cfg_min_seniors", "cfg_gender", "cfg_consecutive", "cfg_two_rest", "cfg_language"]:
            if key in db_data:
                st.session_state[key] = db_data[key]
        
        # Restore generated schedule
        if "generated_schedule" in db_data:
            try:
                sched_loaded = {}
                for d_str, team in db_data["generated_schedule"].items():
                    d_obj = date.fromisoformat(d_str)
                    sched_loaded[d_obj] = team
                st.session_state.generated_schedule = sched_loaded
                st.session_state.gen_year = db_data.get("gen_year")
                st.session_state.gen_month = db_data.get("gen_month")
                st.session_state.schedule_success = True
            except Exception as e:
                print(f"Error loading schedule: {e}")

    # --- Language Setup ---
    if "cfg_language" not in st.session_state:
        st.session_state.cfg_language = "English"
    
    lang = st.session_state.cfg_language
    t = LANG_TEXT[lang]

    # Helper to translate day names for display
    def translate_day(day_en):
        if lang == "Türkçe" and day_en in DAYS_OF_WEEK:
            return DAYS_TR[DAYS_OF_WEEK.index(day_en)]
        return day_en

    # --- Header & Logout ---
    col_header, col_lang, col_logout = st.columns([6, 1.5, 1])
    with col_header:
        st.title(t["title"])
    with col_lang:
        def save_lang():
            save_db(st.session_state.get('personnel', []), st.session_state.get('username'))
        st.selectbox("Language", ["English", "Türkçe"], key="cfg_language", label_visibility="collapsed", on_change=save_lang)

    with col_logout:
        if st.button(t["logout"], key="btn_logout_top"):
            st.session_state['logged_in'] = False
            if 'personnel' in st.session_state:
                del st.session_state['personnel']
            st.rerun()

    # --- Sidebar: Configuration ---
    st.sidebar.header(t["sidebar_gen"])
    
    today = date.today()
    if "cfg_year" not in st.session_state:
        st.session_state.cfg_year = today.year
    year = st.sidebar.number_input(t["year"], min_value=today.year, max_value=today.year+5, key="cfg_year")
    
    if "cfg_month" not in st.session_state:
        st.session_state.cfg_month = today.month
    month = st.sidebar.selectbox(t["month"], range(1, 13), key="cfg_month")
    
    st.sidebar.header(t["sidebar_rules"])
    if "cfg_ppl" not in st.session_state:
        st.session_state.cfg_ppl = 2
    people_per_day = st.sidebar.number_input(t["ppl_day"], min_value=1, key="cfg_ppl")
    
    if "cfg_min_seniors" not in st.session_state:
        st.session_state.cfg_min_seniors = 0
    min_seniors = st.sidebar.number_input(t["min_seniors"], min_value=0, max_value=people_per_day, key="cfg_min_seniors")
    
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
    
    if "cfg_consecutive" not in st.session_state:
        st.session_state.cfg_consecutive = False
    allow_consecutive = st.sidebar.checkbox(t["consecutive"], help=t["consecutive_help"], key="cfg_consecutive")
    
    if "cfg_two_rest" not in st.session_state:
        st.session_state.cfg_two_rest = False
    require_two_rest = st.sidebar.checkbox(t["two_day_rule"], help=t["two_day_help"], key="cfg_two_rest")
    
    # Holidays Selection
    num_days_in_month = calendar.monthrange(year, month)[1]
    all_month_dates = [date(year, month, day).strftime("%d/%m/%Y") for day in range(1, num_days_in_month + 1)]
    
    if "holidays_multiselect" not in st.session_state:
        st.session_state["holidays_multiselect"] = []

    if lang == "Türkçe":
        if st.sidebar.button(t["load_tr_holidays"]):
            try:
                tr_holidays = holidays_lib.TR(years=year)
                month_holidays = [d.strftime("%d/%m/%Y") for d in tr_holidays if d.month == month]
                st.session_state["holidays_multiselect"] = month_holidays
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    # Ensure selected holidays are valid for the current month (prevents errors when changing months)
    st.session_state["holidays_multiselect"] = [d for d in st.session_state["holidays_multiselect"] if d in all_month_dates]
    
    selected_holidays = st.sidebar.multiselect(t["holidays"], all_month_dates, key="holidays_multiselect", help=t["holidays_help"], placeholder=t["placeholder_select"])
    
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

    # --- Main Area: Personnel Management ---
    has_schedule = st.session_state.get("schedule_success") and st.session_state.get("generated_schedule")
    
    if has_schedule:
        col_header, col_dl_fmt, col_dl_btn, col_gen_btn = st.columns([2, 1, 1, 1])
    else:
        col_header, col_gen_btn = st.columns([3, 1])
        
    with col_header:
        st.header(t["header_personnel"])
        
    if has_schedule:
        with col_dl_fmt:
            dl_format = st.selectbox("Format", ["Excel", "PDF", "ICS"], label_visibility="collapsed", key="dl_fmt_top")
        
        # Prepare data for download
        schedule = st.session_state.generated_schedule
        gen_year = st.session_state.gen_year
        gen_month = st.session_state.gen_month
        
        display_data = []
        for d, team in sorted(schedule.items()):
            names = ", ".join([p['name'] for p in team])
            day_name = translate_day(DAYS_OF_WEEK[d.weekday()])
            is_weekend = d.weekday() >= 5
            display_data.append({
                t["col_date"]: d.strftime("%d/%m/%Y"),
                t["col_day"]: day_name,
                t["col_team"]: names,
                t["col_type"]: t["type_wknd"] if is_weekend else t["type_wkday"]
            })
        df_res = pd.DataFrame(display_data)
        
        data = None
        file_name = ""
        mime = ""
        
        if dl_format == "Excel":
            data = generate_excel(df_res)
            file_name = f"nobet_list_{gen_year}_{gen_month}.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif dl_format == "PDF":
            data = generate_pdf(df_res, gen_year, gen_month, t)
            file_name = f"nobet_list_{gen_year}_{gen_month}.pdf"
            mime = "application/pdf"
        elif dl_format == "ICS":
            data = generate_ics(schedule, t["title"].split(" ")[0] + " Duty")
            file_name = f"nobet_list_{gen_year}_{gen_month}.ics"
            mime = "text/calendar"
            
        with col_dl_btn:
            st.download_button(label="⬇️ Download", data=data, file_name=file_name, mime=mime, use_container_width=True, key="btn_download_top")

    with col_gen_btn:
        btn_gen_clicked = st.button(t["btn_gen"], type="primary", use_container_width=True, key="btn_gen_schedule")
    
    # Form to add new person
    with st.expander(t["add_expander"], expanded=True):
        c1, c2, c_role, c3, c4, c5, c6, c7 = st.columns([3, 1, 1.2, 1, 1, 1, 1, 1])
        with c1:
            name = st.text_input(t["name"])
        with c2:
            gender = st.selectbox(t["gender"], ["M", "F"])
        with c_role:
            role = st.selectbox(t["role"], ["Junior", "Senior"], format_func=lambda x: t["role_senior"] if x == "Senior" else t["role_junior"])
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
        date_options = [date(year, month, day).strftime("%d/%m/%Y") for day in range(1, num_days + 1)]
        
        c_row2_1, c_row2_2, c_row2_3, c_row2_4 = st.columns([1, 1, 1, 1])
        with c_row2_1:
            busy_days = st.multiselect(t["busy_days"], DAYS_OF_WEEK, format_func=translate_day, placeholder=t["placeholder_select"])
        with c_row2_2:
            off_dates = st.multiselect(t["off_dates"], date_options, placeholder=t["placeholder_select"])
        with c_row2_3:
            leave_range = st.date_input(
                t["leave_dates"],
                value=[],
                min_value=date(year, month, 1),
                max_value=date(year, month, num_days),
                format="DD/MM/YYYY"
            )
        with c_row2_4:
            fixed_dates = st.multiselect(t["fixed_dates"], date_options, placeholder=t["placeholder_select"])
            
        add_btn = st.button(t["add_btn"], use_container_width=True)

        if add_btn and name:
            leave_dates = []
            if leave_range:
                start = leave_range[0]
                end = leave_range[-1]
                curr = start
                while curr <= end:
                    leave_dates.append(curr.strftime("%d/%m/%Y"))
                    curr += timedelta(days=1)

            st.session_state.personnel.append({
                "name": name,
                "gender": gender,
                "role": role,
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
        if "role" not in df_personnel.columns:
            df_personnel["role"] = "Junior"
        if "fixed_duties_total" not in df_personnel.columns:
            # Migration: Use old fixed_duties if available, else 0
            df_personnel["fixed_duties_total"] = df_personnel.get("fixed_duties", 0)
            
        if "fixed_duties_weekend" not in df_personnel.columns:
            df_personnel["fixed_duties_weekend"] = 0
            
        if "duty_count" not in df_personnel.columns:
            df_personnel["duty_count"] = 0
        if "weekend_duty_count" not in df_personnel.columns:
            df_personnel["weekend_duty_count"] = 0
        if "busy_days" not in df_personnel.columns:
            df_personnel["busy_days"] = ""
        if "off_dates" not in df_personnel.columns:
            df_personnel["off_dates"] = ""
        if "leave_dates" not in df_personnel.columns:
            df_personnel["leave_dates"] = ""
        if "fixed_dates" not in df_personnel.columns:
            df_personnel["fixed_dates"] = ""
            
        # Helper to convert comma-separated strings to lists for the editor
        def str_to_list(val):
            if isinstance(val, list): return val
            if not val or val == "": return []
            return [x.strip() for x in str(val).split(",") if x.strip()]

        # Create a copy for the editor with list types
        df_editor = df_personnel.copy()
        for col in ["busy_days", "off_dates", "leave_dates", "fixed_dates"]:
            df_editor[col] = df_editor[col].apply(str_to_list)

        # Translate roles for display
        role_map_display = {
            "Junior": t["role_junior"],
            "Senior": t["role_senior"]
        }
        # Reverse map for saving
        role_map_save = {v: k for k, v in role_map_display.items()}

        df_editor["role"] = df_editor["role"].map(role_map_display).fillna(df_editor["role"])

        # Editable Dataframe
        edited_df = st.data_editor(
            df_editor[["name", "gender", "role", "fixed_duties_total", "max_duties", "fixed_duties_weekend", "max_weekends", "mixed_gender_allowed", "busy_days", "off_dates", "leave_dates", "fixed_dates", "duty_count", "weekend_duty_count"]],
            column_config={
                "name": t["name"],
                "gender": st.column_config.SelectboxColumn(t["gender"], options=["M", "F"], required=True),
                "role": st.column_config.SelectboxColumn(t["role"], options=[t["role_junior"], t["role_senior"]], required=True),
                "fixed_duties_total": st.column_config.NumberColumn(t["fixed_total"], min_value=0, step=1, help=t["fixed_total_help"]),
                "fixed_duties_weekend": st.column_config.NumberColumn(t["fixed_wknd"], min_value=0, step=1, help=t["fixed_wknd_help"]),
                "max_duties": st.column_config.NumberColumn(t["max_duties"], min_value=0, step=1),
                "max_weekends": st.column_config.NumberColumn(t["max_wknd"], min_value=0, step=1),
                "mixed_gender_allowed": st.column_config.CheckboxColumn(t["mixed_ok"]),
                "busy_days": st.column_config.ListColumn(t["busy_days"], help=t["col_busy_help"]),
                "off_dates": st.column_config.ListColumn(t["off_dates"], help=t["col_off_help"]),
                "leave_dates": st.column_config.ListColumn(t["leave_dates"], help=t["col_leave_help"]),
                "fixed_dates": st.column_config.ListColumn(t["fixed_dates"], help=t["col_fixed_help"]),
                "duty_count": st.column_config.NumberColumn(t["col_assigned"], disabled=True, help=t["col_assigned_help"]),
                "weekend_duty_count": st.column_config.NumberColumn(t["type_wknd"], disabled=True)
            },
            use_container_width=True,
            num_rows="dynamic",
            key="personnel_editor"
        )
        
        # Update session state from editor
        # Convert lists back to comma-separated strings for storage/scheduler compatibility
        def list_to_str(val):
            if isinstance(val, list):
                return ", ".join([str(x) for x in val])
            return val

        df_saved = edited_df.copy()
        
        # Translate roles back to internal values
        df_saved["role"] = df_saved["role"].map(role_map_save).fillna(df_saved["role"])
        
        for col in ["busy_days", "off_dates", "leave_dates", "fixed_dates"]:
            df_saved[col] = df_saved[col].apply(list_to_str)
            
        st.session_state.personnel = df_saved.to_dict('records')

    else:
        st.info(t["info_start"])

    # --- Personnel Tools ---
    if st.session_state.personnel:
        with st.expander(t["tools_expander"]):
            tab_leave, tab_busy = st.tabs([t["header_leave"], t["header_busy"]])
            
            person_names = [p['name'] for p in st.session_state.personnel]
            
            with tab_leave:
                c_b1, c_b2, c_b3 = st.columns([2, 2, 1])
                with c_b1:
                    selected_person_leave = st.selectbox(t["name"], person_names, key="tool_leave_person")
                with c_b2:
                    leave_range_bulk = st.date_input(t["leave_dates"], value=[], key="tool_leave_dates", format="DD/MM/YYYY")
                with c_b3:
                    st.write("") # Spacer
                    st.write("") # Spacer
                    if st.button(t["btn_add_leave"], use_container_width=True, key="btn_tool_leave"):
                        if selected_person_leave and len(leave_range_bulk) == 2:
                            start, end = leave_range_bulk
                            # Find person
                            for p in st.session_state.personnel:
                                if p['name'] == selected_person_leave:
                                    current_leaves = [x.strip() for x in p.get('leave_dates', '').split(',') if x.strip()]
                                    
                                    curr = start
                                    while curr <= end:
                                        d_str = curr.strftime("%d/%m/%Y")
                                        if d_str not in current_leaves:
                                            current_leaves.append(d_str)
                                        curr += timedelta(days=1)
                                    
                                    p['leave_dates'] = ", ".join(current_leaves)
                                    st.toast(t["added"].format(selected_person_leave), icon="✅")
                                    st.rerun()
            
            with tab_busy:
                c_bu1, c_bu2, c_bu3 = st.columns([2, 2, 1])
                with c_bu1:
                    selected_person_busy = st.selectbox(t["name"], person_names, key="tool_busy_person")
                
                # Get current busy days
                current_busy = []
                for p in st.session_state.personnel:
                    if p['name'] == selected_person_busy:
                        if p.get('busy_days'):
                            current_busy = [d.strip() for d in p['busy_days'].split(',') if d.strip()]
                        break
                
                with c_bu2:
                    new_busy_days = st.multiselect(
                        t["busy_days"], 
                        DAYS_OF_WEEK, 
                        default=[d for d in current_busy if d in DAYS_OF_WEEK],
                        format_func=translate_day,
                        key="tool_busy_select",
                        placeholder=t["placeholder_select"]
                    )
                
                with c_bu3:
                    st.write("")
                    st.write("")
                    if st.button(t["btn_save_busy"], use_container_width=True, key="btn_tool_busy"):
                        for p in st.session_state.personnel:
                            if p['name'] == selected_person_busy:
                                p['busy_days'] = ", ".join(new_busy_days)
                                st.toast(t["busy_updated"].format(selected_person_busy), icon="✅")
                                st.rerun()

    # --- Save / Load Section ---
    st.divider()
    
    # 1. Main Actions Toolbar
    col_act1, col_act2, col_act3 = st.columns(3)
    
    with col_act1:
        if st.button(t["save_db"], use_container_width=True):
            save_db(st.session_state.personnel, st.session_state.get('username'))
            st.toast(t["db_saved"], icon="💾")

    with col_act2:
        def load_cloud_data():
            db_data = load_db(st.session_state.get('username'))
            st.session_state.personnel = db_data.get("personnel", [])
            
            # Restore other settings
            if "conditional_rules" in db_data:
                st.session_state.conditional_rules = db_data["conditional_rules"]
            if "forbidden_pairs" in db_data:
                st.session_state.forbidden_pairs = db_data["forbidden_pairs"]
            if "holidays_multiselect" in db_data:
                st.session_state.holidays_multiselect = db_data["holidays_multiselect"]
            
            for key in ["cfg_year", "cfg_month", "cfg_ppl", "cfg_min_seniors", "cfg_gender", "cfg_consecutive", "cfg_two_rest", "cfg_language"]:
                if key in db_data:
                    st.session_state[key] = db_data[key]
            
            # Restore generated schedule
            if "generated_schedule" in db_data:
                try:
                    sched_loaded = {}
                    for d_str, team in db_data["generated_schedule"].items():
                        d_obj = date.fromisoformat(d_str)
                        sched_loaded[d_obj] = team
                    st.session_state.generated_schedule = sched_loaded
                    st.session_state.gen_year = db_data.get("gen_year")
                    st.session_state.gen_month = db_data.get("gen_month")
                    st.session_state.schedule_success = True
                except Exception as e:
                    print(f"Error loading schedule: {e}")
            
            st.toast(t["loaded"], icon="✅")

        st.button(t["load_db_btn"], use_container_width=True, on_click=load_cloud_data)

    with col_act3:
        json_data = json.dumps(st.session_state.personnel, ensure_ascii=False, indent=4)
        st.download_button(
            label=t["download_db"],
            data=json_data,
            file_name="personnel_db.json",
            mime="application/json",
            use_container_width=True
        )
        
    col_act4, col_act5, col_act6 = st.columns(3)
    
    with col_act4:
        if st.button(t["btn_reset_month"], use_container_width=True, help=t["reset_month_help"]):
            for p in st.session_state.personnel:
                p['busy_days'] = ""
                p['off_dates'] = ""
                p['leave_dates'] = ""
                p['fixed_dates'] = ""
                # We don't reset fixed_duties targets or roles, just dates
            st.toast(t["reset_success"], icon="🔄")
            st.rerun()

    with col_act5:
        if st.button(t["clear_all"], use_container_width=True):
            st.session_state.personnel = []
            st.session_state.generated_schedule = {}
            st.session_state.schedule_success = False
            st.rerun()

    with col_act6:
        if "confirm_clear_db" not in st.session_state:
            st.session_state.confirm_clear_db = False
        
        if not st.session_state.confirm_clear_db:
            if st.button(t["clear_db_btn"], use_container_width=True):
                st.session_state.confirm_clear_db = True
                st.rerun()
        else:
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button(t["confirm_yes"], use_container_width=True):
                    save_db([], st.session_state.get('username'))
                    st.toast(t["db_cleared"], icon="🔥")
                    st.session_state.confirm_clear_db = False
                    st.rerun()
            with c_no:
                if st.button(t["confirm_no"], use_container_width=True):
                    st.session_state.confirm_clear_db = False
                    st.rerun()

    # --- Generation Section ---
    if btn_gen_clicked:
        if not st.session_state.personnel:
            st.error(t["err_no_pers"])
        else:
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
                'min_seniors': min_seniors,
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
                st.session_state.generated_schedule = schedule
                st.session_state.gen_year = year
                st.session_state.gen_month = month
                st.session_state.schedule_success = True
                st.toast(t["success"], icon="🎉")
                st.rerun()
            else:
                st.session_state.schedule_success = False
                st.error(t["err_fail"])

    if st.session_state.get("schedule_success") and st.session_state.get("generated_schedule"):
        st.divider()
        st.success(t["success"])
        schedule = st.session_state.generated_schedule
        gen_year = st.session_state.gen_year
        gen_month = st.session_state.gen_month
        
        # Process data for display
        display_data = []
        
        for d, team in sorted(schedule.items()):
            names = ", ".join([p['name'] for p in team])
            day_name = translate_day(DAYS_OF_WEEK[d.weekday()])
            is_weekend = d.weekday() >= 5
            
            display_data.append({
                t["col_date"]: d.strftime("%d/%m/%Y"),
                t["col_day"]: day_name,
                t["col_team"]: names,
                t["col_type"]: t["type_wknd"] if is_weekend else t["type_wkday"]
            })

        df_res = pd.DataFrame(display_data)
        
        # --- TABS ---
        tab_list, tab_cal, tab_stats = st.tabs([t["list_view"], t["cal_view"], t["stats"]])
        
        with tab_list:
            st.dataframe(df_res, use_container_width=True, hide_index=True)
            
        with tab_cal:
            cal_html = get_calendar_html(gen_year, gen_month, schedule, t)
            st.markdown(cal_html, unsafe_allow_html=True)
        
        # Show Stats
        with tab_stats:
            stats = []
            duty_counts = []
            for p in st.session_state.personnel:
                stats.append({
                    t["name"]: p['name'],
                    t["col_assigned"]: p['duty_count'],
                    t["type_wknd"]: p.get('weekend_duty_count', 0)
                })
                duty_counts.append(p['duty_count'])
            
            # Fairness Metric
            if len(duty_counts) > 1:
                stdev = statistics.stdev(duty_counts)
                st.metric(label=t["fairness_score"], value=f"{stdev:.2f}", help=t["fairness_help"])
            
            st.dataframe(pd.DataFrame(stats), use_container_width=True)
            
            if stats:
                # Chart
                st.caption("Duty Distribution / Nöbet Dağılımı")
                st.bar_chart(pd.DataFrame(stats).set_index(t["name"])[[t["col_assigned"], t["type_wknd"]]])
                
                st.divider()
                
                # 1. Day Distribution Heatmap
                st.subheader(t["day_distribution"])
                day_counts = {p['name']: {day: 0 for day in t["short_days"]} for p in st.session_state.personnel}
                for d, team in schedule.items():
                    day_idx = d.weekday()
                    day_name = t["short_days"][day_idx]
                    for p in team:
                        day_counts[p['name']][day_name] += 1
                
                df_days = pd.DataFrame(day_counts).T
                st.dataframe(df_days.style.background_gradient(cmap="Blues", axis=1), use_container_width=True)

                # 2. Co-occurrence Matrix
                st.subheader(t["co_occurrence"])
                names = [p['name'] for p in st.session_state.personnel]
                if len(names) > 0:
                    co_matrix = pd.DataFrame(0, index=names, columns=names)
                    for team in schedule.values():
                        t_names = [p['name'] for p in team]
                        for i in range(len(t_names)):
                            for j in range(i + 1, len(t_names)):
                                p1, p2 = t_names[i], t_names[j]
                                co_matrix.loc[p1, p2] += 1
                                co_matrix.loc[p2, p1] += 1
                    
                    # Display with gradient
                    st.dataframe(co_matrix.style.background_gradient(cmap="Reds"), use_container_width=True)

if __name__ == '__main__':
    if st.runtime.exists():
        main()
    else:
        import sys
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
