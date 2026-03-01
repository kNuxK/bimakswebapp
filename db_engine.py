import streamlit as st
from google.oauth2.service_account import Credentials
import gspread
import json
import hashlib
import time
from datetime import datetime

def get_gsheets_client():
    try:
        creds_json = st.secrets["gcp_json"]
        creds_dict = json.loads(creds_json)
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        return None

def get_db_sheet():
    try:
        client = get_gsheets_client()
        if not client: return None
        sheet_url = st.secrets["gsheet_url"]
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_role_definitions():
    defs = {"Admin": "smy,smy_li,smy_in,tech,tech_an,tech_roi,tech_ocr,tech_reg,tech_quo,tech_sds,tech_sds_gen", 
            "Bimaks Üye": "smy,smy_li,smy_in,tech,tech_an,tech_roi,tech_ocr,tech_reg,tech_quo,tech_sds", 
            "Yeni Üye": ""}
    try:
        sheet = get_db_sheet()
        if not sheet: 
            return st.session_state.get('cached_roles', defs)
            
        rows = sheet.get_all_values()
        for r in rows:
            if len(r) > 0 and r[0] == '__ROLE_DEFS__':
                defs["Admin"] = r[1] if len(r)>1 else ""
                defs["Bimaks Üye"] = r[2] if len(r)>2 else ""
                defs["Yeni Üye"] = r[3] if len(r)>3 else ""
                st.session_state['cached_roles'] = defs
                return defs
    except: pass
    return st.session_state.get('cached_roles', defs)

def update_role_definitions(admin_p, bimaks_p, yeni_p):
    st.session_state['cached_roles'] = {"Admin": admin_p, "Bimaks Üye": bimaks_p, "Yeni Üye": yeni_p}
    sheet = get_db_sheet()
    if not sheet: return False
    try:
        users = sheet.col_values(1)
        if '__ROLE_DEFS__' in users:
            row_idx = users.index('__ROLE_DEFS__') + 1
            sheet.update_cell(row_idx, 2, admin_p)
            sheet.update_cell(row_idx, 3, bimaks_p)
            sheet.update_cell(row_idx, 4, yeni_p)
        else:
            sheet.append_row(['__ROLE_DEFS__', admin_p, bimaks_p, yeni_p])
        return True
    except: return False

def ping_online(username):
    try:
        now = time.time()
        last_ping = st.session_state.get('last_ping_time', 0)
        if now - last_ping < 60: return 
        sheet = get_db_sheet()
        if not sheet: return
        users = sheet.col_values(1)
        if username in users:
            row_idx = users.index(username) + 1
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            sheet.update_cell(row_idx, 8, now_str)
            st.session_state['last_ping_time'] = now
    except: pass 

def login_user(username, password):
    sheet = get_db_sheet()
    if not sheet: return False, "Veritabanı bağlantı hatası."
    try:
        rows = sheet.get_all_values()
        hashed_pw = hash_password(password)
        role_defs = None 
        for i, r in enumerate(rows):
            if i == 0 or (len(r)>0 and r[0] == '__ROLE_DEFS__'): continue 
            r_user = r[0] if len(r) > 0 else ""
            r_pass = r[1] if len(r) > 1 else ""
            if str(r_user) == username and str(r_pass) == hashed_pw:
                r_role = r[6] if len(r) > 6 and str(r[6]).strip() != "" else "Admin" 
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                try: sheet.update_cell(i + 1, 8, now_str)
                except: pass 
                if not role_defs: role_defs = get_role_definitions()
                r_perms = role_defs.get(r_role, "")
                if r_role.lower() == "admin" and not r_perms:
                    r_perms = "smy,smy_li,smy_in,tech,tech_an,tech_roi,tech_ocr,tech_reg,tech_quo,tech_sds,tech_sds_gen"
                data = {
                    "username": r_user,
                    "genai_key": r[2] if len(r) > 2 else "",
                    "linkedin_token": r[3] if len(r) > 3 else "",
                    "instagram_token": r[4] if len(r) > 4 else "",
                    "instagram_account_id": r[5] if len(r) > 5 else "",
                    "role": r_role,
                    "permissions": r_perms
                }
                return True, data
        return False, "Kullanıcı adı veya şifre hatalı!"
    except Exception as e:
        return False, f"Okuma hatası: {e}"

def register_user(username, password, role="Yeni Üye"):
    sheet = get_db_sheet()
    if not sheet: return False, "Veritabanı bağlantı hatası."
    try:
        rows = sheet.get_all_values()
        for r in rows:
            if len(r) > 0 and str(r[0]) == username:
                return False, "Bu kullanıcı adı zaten alınmış!"
        hashed_pw = hash_password(password)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        new_row = [username, hashed_pw, "", "", "", "", role, now_str]
        sheet.append_row(new_row)
        return True, "Kayıt başarılı!"
    except Exception as e:
        return False, f"Kayıt hatası: {e}"

def update_user_keys(username, genai, li, insta, insta_id):
    sheet = get_db_sheet()
    if not sheet: return False
    try:
        users = sheet.col_values(1) 
        if username in users:
            row_idx = users.index(username) + 1
            sheet.update_cell(row_idx, 3, genai)
            sheet.update_cell(row_idx, 4, li)
            sheet.update_cell(row_idx, 5, insta)
            sheet.update_cell(row_idx, 6, insta_id)
            return True
        return False
    except Exception as e:
        return False

def get_all_users_status():
    try:
        sheet = get_db_sheet()
        if not sheet: return st.session_state.get('cached_users', [])
        rows = sheet.get_all_values()
        if len(rows) <= 1: return []
        users = []
        for r in rows[1:]:
            u_name = r[0] if len(r) > 0 else ""
            if not u_name or u_name == '__ROLE_DEFS__': continue
            u_role = r[6] if len(r) > 6 and str(r[6]).strip() != "" else "Admin"
            u_last = r[7] if len(r) > 7 else "Hiç girmedi"
            users.append({"username": u_name, "role": u_role, "last_seen": u_last})
        st.session_state['cached_users'] = users
        return users
    except Exception as e:
        return st.session_state.get('cached_users', [])

def update_user_role(username, new_role):
    sheet = get_db_sheet()
    if not sheet: return False
    try:
        users = sheet.col_values(1)
        if username in users:
            row_idx = users.index(username) + 1
            sheet.update_cell(row_idx, 7, new_role)
            return True
        return False
    except: return False

def delete_user(target_username):
    sheet = get_db_sheet()
    if not sheet: return False, "Veritabanı bağlantı hatası."
    try:
        users = sheet.col_values(1)
        if target_username in users:
            row_idx = users.index(target_username) + 1
            if row_idx == 1: return False, "Başlık satırı silinemez!"
            try: sheet.delete_rows(row_idx)
            except AttributeError: sheet.delete_row(row_idx)
            return True, f"'{target_username}' başarıyla silindi."
        return False, "Kullanıcı bulunamadı."
    except Exception as e:
        return False, f"Silme hatası: {str(e)}"