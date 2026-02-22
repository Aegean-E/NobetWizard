import streamlit as st
import pandas as pd
from datetime import date
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
        "fixed_duties": "Fixed Duties",
        "fixed_duties_help": "Target number of duties. Overrides Max if > 0.",
        "max_wknd": "Max Wknd",
        "mixed_ok": "Mixed OK?",
        "mixed_ok_help": "Uncheck if person cannot work in mixed-gender teams",
        "busy_days": "Busy Days (Cannot hold duty)",
        "off_dates": "Specific Off Dates",
        "fixed_dates": "Fixed Duty Dates (Must hold)",
        "add_btn": "Add Person",
        "added": "Added {}",
        "save_csv": "💾 Save CSV",
        "load_csv": "📂 Load CSV",
        "loaded": "Loaded!",
        "save_db": "💾 Save to DB",
        "db_saved": "Database saved to user profile!",
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
        "export_pdf": "📄 Export to PDF"
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
        "fixed_duties": "Sabit Sayı",
        "fixed_duties_help": "Hedef nöbet sayısı. >0 ise Maks yerine geçer.",
        "max_wknd": "Maks H.Sonu",
        "mixed_ok": "Karma Olur?",
        "mixed_ok_help": "Kişi karma ekiplerde çalışamıyorsa işareti kaldırın",
        "busy_days": "Meşgul Günler",
        "off_dates": "İzinli Tarihler",
        "fixed_dates": "Sabit Nöbetler",
        "add_btn": "Personel Ekle",
        "added": "{} Eklendi",
        "save_csv": "💾 CSV Kaydet",
        "load_csv": "📂 CSV Yükle",
        "loaded": "Yüklendi!",
        "save_db": "💾 DB Kaydet",
        "db_saved": "Veritabanı kullanıcı profiline kaydedildi!",
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
        "export_pdf": "📄 PDF Olarak İndir"
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
            return json.load(f)
    return []

def save_db(data, username):
    path = get_user_db_path(username)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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

def login_page():
    st.title("🧙‍♂️ Nöbet Wizard - Login")
    
    lang = st.selectbox("Language / Dil", ["English", "Türkçe"], key="login_lang")
    t = LANG_TEXT[lang]

    tab1, tab2 = st.tabs([t["login_tab"], t["register_tab"]])

    with tab1:
        username = st.text_input(t["username"], key="login_user")
        password = st.text_input(t["password"], type='password', key="login_pass")
        if st.button(t["login_btn"]):
            users = load_users()
            if username in users and check_hashes(password, users[username]):
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
    year = st.sidebar.number_input(t["year"], min_value=today.year, max_value=today.year+5, value=today.year)
    month = st.sidebar.selectbox(t["month"], range(1, 13), index=today.month-1)
    
    st.sidebar.header(t["sidebar_rules"])
    people_per_day = st.sidebar.number_input(t["ppl_day"], min_value=1, value=2)
    
    # Map display options to internal logic keys
    gender_map = {
        t["gender_opts"][0]: "Any",
        t["gender_opts"][1]: "Mixed",
        t["gender_opts"][2]: "Single Gender"
    }
    
    gender_mode = st.sidebar.selectbox(
        t["gender_rules"], 
        t["gender_opts"],
        help=t["gender_help"]
    )
    allow_consecutive = st.sidebar.checkbox(t["consecutive"], value=False, help=t["consecutive_help"])
    require_two_rest = st.sidebar.checkbox(t["two_day_rule"], value=False, help=t["two_day_help"])
    
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
        st.session_state.personnel = load_db(st.session_state.get('username'))

    # Form to add new person
    with st.expander(t["add_expander"], expanded=True):
        c1, c2, c3, c4, c5, c6 = st.columns([3, 1, 1, 1, 1, 1])
        with c1:
            name = st.text_input(t["name"])
        with c2:
            gender = st.selectbox(t["gender"], ["M", "F"])
        with c3:
            fixed_duties = st.number_input(t["fixed_duties"], min_value=0, value=0, help=t["fixed_duties_help"])
        with c4:
            max_duties = st.number_input(t["max_duties"], min_value=0, value=5)
        with c5:
            max_weekends = st.number_input(t["max_wknd"], min_value=0, value=2)
        with c6:
            mixed_ok = st.checkbox(t["mixed_ok"], value=True, help=t["mixed_ok_help"])
        
        c_row2_1, c_row2_2, c_row2_3 = st.columns([1, 1, 1])
        with c_row2_1:
            busy_days = st.multiselect(t["busy_days"], DAYS_OF_WEEK, format_func=translate_day)
        with c_row2_2:
            num_days = calendar.monthrange(year, month)[1]
            date_options = [date(year, month, day).strftime("%Y-%m-%d") for day in range(1, num_days + 1)]
            off_dates = st.multiselect(t["off_dates"], date_options)
        with c_row2_3:
            fixed_dates = st.multiselect(t["fixed_dates"], date_options)
            
        add_btn = st.button(t["add_btn"], use_container_width=True)

        if add_btn and name:
            st.session_state.personnel.append({
                "name": name,
                "gender": gender,
                "fixed_duties": fixed_duties,
                "max_duties": max_duties,
                "max_weekends": max_weekends,
                "mixed_gender_allowed": mixed_ok,
                "busy_days": ", ".join(busy_days),
                "off_dates": ", ".join(off_dates),
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
        if "fixed_duties" not in df_personnel.columns:
            df_personnel["fixed_duties"] = 0
        if "duty_count" not in df_personnel.columns:
            df_personnel["duty_count"] = 0
        if "busy_days" not in df_personnel.columns:
            df_personnel["busy_days"] = ""
        if "off_dates" not in df_personnel.columns:
            df_personnel["off_dates"] = ""
        if "fixed_dates" not in df_personnel.columns:
            df_personnel["fixed_dates"] = ""
            
        # Editable Dataframe
        edited_df = st.data_editor(
            df_personnel[["name", "gender", "fixed_duties", "max_duties", "max_weekends", "mixed_gender_allowed", "busy_days", "off_dates", "fixed_dates", "duty_count"]],
            column_config={
                "name": t["name"],
                "gender": st.column_config.SelectboxColumn(t["gender"], options=["M", "F"], required=True),
                "fixed_duties": st.column_config.NumberColumn(t["fixed_duties"], min_value=0, step=1, help=t["fixed_duties_help"]),
                "max_duties": st.column_config.NumberColumn(t["max_duties"], min_value=0, step=1),
                "max_weekends": st.column_config.NumberColumn(t["max_wknd"], min_value=0, step=1),
                "mixed_gender_allowed": st.column_config.CheckboxColumn(t["mixed_ok"]),
                "busy_days": st.column_config.TextColumn(t["busy_days"], help=t["col_busy_help"]),
                "off_dates": st.column_config.TextColumn(t["off_dates"], help=t["col_off_help"]),
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
        c_dl, c_db, c_ul, c_cl = st.columns([1, 1, 2, 1])
        
        with c_dl:
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(t["save_csv"], csv, "nobet_list.csv", "text/csv")
            
        with c_db:
            if st.button(t["save_db"]):
                save_db(st.session_state.personnel, st.session_state.get('username'))
                st.success(t["db_saved"])

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
            'require_two_rest_days': require_two_rest
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
            
            # Show Table
            st.dataframe(df_res, use_container_width=True)
            
            # Show Stats
            st.subheader(t["stats"])
            stats = []
            for p in st.session_state.personnel:
                stats.append({
                    t["name"]: p['name'],
                    t["col_assigned"]: p['duty_count'],
                    t["type_wknd"]: p['weekend_duty_count']
                })
            st.dataframe(pd.DataFrame(stats))
            
            # --- Export Section ---
            st.divider()
            c_ex1, c_ex2 = st.columns(2)
            
            # 1. Excel Export
            buffer_excel = BytesIO()
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
