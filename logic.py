import google.generativeai as genai
import requests
import json
import time
import re
import os
import io
import base64
import math
import hashlib
import gspread
import textwrap
from google.oauth2.service_account import Credentials
import streamlit as st 
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
import config

# --- KÜTÜPHANE KONTROLLERİ VE PDF MOTORU ---
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfReader
        HAS_PYPDF = True
    except ImportError:
        HAS_PYPDF = False

try:
    import fitz 
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# ==============================================================================
# 🧠 VERİTABANI VE KİMLİK DOĞRULAMA 
# ==============================================================================

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

# ==============================================================================
# 🧠 MANTIK VE PDF TEMEL MOTORLARI
# ==============================================================================

def apply_theme():
    if 'settings_db' not in st.session_state: return 
    s = st.session_state['settings_db']
    st.markdown(f"""<style>
        .stApp {{ background-color: {s.get("theme_bg", "#0E1117")}; color: {s.get("theme_txt", "#FAFAFA")}; }} 
        div.stButton > button {{ background-color: {s.get("theme_btn", "#8998f3")}; color: white; border-radius: 8px; font-weight: bold; }} 
        [data-testid="stSidebar"] {{ background-color: {s.get("theme_bg", "#0E1117")}; border-right: 1px solid #333; }}
        footer {{visibility: hidden;}}
    </style>""", unsafe_allow_html=True)

def get_persona_list_for_ui():
    lang = st.session_state.get('lang', 'TR')
    lang_dict = config.LANGUAGES.get(lang, config.LANGUAGES['TR'])
    raw_list = [p.get(lang, p.get('TR')) for p in st.session_state.get('personas_db', [])]
    default_role = "Su Şartlandırma Kimyasalları ve Sistemleri Baş Mühendisi"
    final_list = []
    if default_role in raw_list:
        raw_list.remove(default_role)
        final_list.append(default_role)
    final_list.extend(sorted(raw_list, key=lambda x: x.lower()))
    final_list.insert(0, lang_dict.get('sys_manual', 'Manuel'))
    final_list.insert(0, lang_dict.get('sys_placeholder_select', 'Seçiniz'))
    return final_list

def save_history_entry(topic, role):
    if 'history_db' not in st.session_state: st.session_state['history_db'] = []
    st.session_state['history_db'].insert(0, {"date": datetime.now().strftime("%Y-%m-%d %H:%M"), "topic": topic, "role": role})

def force_clean_text(text):
    if not text or not isinstance(text, str): return "⚠️ HATA: İçerik oluşturulamadı."
    if "ACT AS:" in text.upper() or "MISSION:" in text.upper():
        if "---" in text: text = text.split("---")[-1].strip()
        else:
            match = re.search(r'FORMATTING:.*?\n(.*)', text, flags=re.IGNORECASE | re.DOTALL)
            if match: text = match.group(1).strip()
    text = re.sub(r'^(Merhaba|Ben|Sen|Biz|Bir yapay zeka|Yapay zeka|İşte makaleniz|Hazırladığım|Here is|Sure|As requested|Here\'s|I have written).*?[\.\!\?]\s*', '', text, flags=re.IGNORECASE)
    return text.strip()

def smart_trim(text, limit):
    return text

def get_gemini_response_from_manual(full_prompt, api_key):
    if not api_key: return "❌ Lütfen API anahtarını girin. / Please enter API key."
    models_to_try = ['gemini-2.5-flash', 'gemini-3-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-pro']
    genai.configure(api_key=api_key)
    last_err = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
            if response and response.text: return response.text
        except Exception as e:
            last_err = str(e)
            time.sleep(0.5) 
            continue
    return f"❌ HATA / ERROR: {last_err}"

def get_linkedin_user_urn(access_token):
    access_token = str(access_token).strip()
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        resp_info = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
        if resp_info.status_code == 200: return resp_info.json().get('sub') 
    except: pass
    try:
        resp_me = requests.get("https://api.linkedin.com/v2/me", headers=headers)
        if resp_me.status_code == 200: return resp_me.json().get('id')
    except: pass
    return None

def register_upload_image(access_token, person_urn):
    access_token = str(access_token).strip()
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": f"urn:li:person:{person_urn}",
            "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset = data['value']['asset']
            return upload_url, asset
        return None, None
    except: return None, None

def post_to_linkedin_real(text, media_bytes, media_type, access_token):
    if not access_token: return "❌ HATA: LinkedIn Token girilmemiş."
    access_token = str(access_token).strip()
    person_id = get_linkedin_user_urn(access_token)
    if not person_id: return "❌ HATA: Token geçersiz veya erişim izni yok."
    person_urn = f"urn:li:person:{person_id}"
    asset_urn = None
    if media_bytes and "image" in media_type:
        upload_url, asset = register_upload_image(access_token, person_id)
        if upload_url:
            try:
                put_headers = {'Authorization': f'Bearer {access_token}'}
                put_resp = requests.put(upload_url, data=media_bytes, headers=put_headers)
                if put_resp.status_code in [200, 201]: asset_urn = asset
                else: return f"❌ HATA: Resim yüklenemedi. Kod: {put_resp.status_code}"
            except Exception as e: return f"❌ HATA: Resim upload sorunu: {str(e)}"
        else: return "❌ HATA: Resim kaydı başarısız."
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'X-Restli-Protocol-Version': '2.0.0'}
    share_content = {"shareCommentary": {"text": text}, "shareMediaCategory": "NONE"}
    if asset_urn:
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [{"status": "READY", "description": {"text": "Bimaks App Auto Post"}, "media": asset_urn, "title": {"text": "Bimaks Visual"}}]
    payload = {
        "author": person_urn, "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    try:
        response = requests.post(post_url, headers=headers, json=payload)
        if response.status_code in [200, 201]: return "✅ BAŞARILI: Paylaşım LinkedIn'de yayında!"
        else: return f"❌ HATA: LinkedIn reddetti. Kod: {response.status_code} - Mesaj: {response.text}"
    except Exception as e: return f"❌ HATA: Bağlantı sorunu: {str(e)}"

def calculate_advanced_roi(blowdown_curr, hours, coc_curr, coc_target, water_cost, energy_bill_total, scale_mm, chem_cost):
    try:
        coc_curr = float(coc_curr)
        coc_target = float(coc_target)
        if coc_curr <= 1 or coc_target <= 1: return None 
        evaporation = float(blowdown_curr) * (coc_curr - 1)
        blowdown_new = evaporation / (coc_target - 1)
        water_saved_total = (float(blowdown_curr) - blowdown_new) * float(hours)
        scale_loss_ratio = min(float(scale_mm) * 0.10, 0.50) 
        energy_saved = float(energy_bill_total) * scale_loss_ratio
        return {
            "w_curr": float(blowdown_curr) * float(hours), "w_new": blowdown_new * float(hours),
            "w_save": water_saved_total, "w_money": water_saved_total * float(water_cost),
            "e_save": energy_saved, "total_gain": (water_saved_total * float(water_cost)) + energy_saved - float(chem_cost)
        }
    except: return None

def analyze_image_with_gemini(image_bytes, prompt_text, api_key):
    if not api_key: return "❌ API Key Missing."
    models_to_try = ['gemini-2.5-flash', 'gemini-3-flash', 'gemini-2.5-pro']
    genai.configure(api_key=api_key)
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            img = Image.open(io.BytesIO(image_bytes))
            response = model.generate_content([prompt_text, img])
            if response and response.text: return response.text
        except: continue
    return "❌ OCR Error."

def calculate_lsi(ph, tds, temp_c, ca_hard, alk):
    try:
        ph, tds, temp_c, ca_hard, alk = float(ph), float(tds), float(temp_c), float(ca_hard), float(alk)
        A = (math.log10(tds) - 1) / 10
        B = -13.12 * math.log10(temp_c + 273) + 34.55
        C = math.log10(ca_hard) - 0.4
        D = math.log10(alk)
        pHs = (9.3 + A + B) - (C + D)
        return ph - pHs, 2 * pHs - ph
    except: return None, None

def construct_prompt_text(role, topic, audience, platform, product, limit, lang_code, product_link=None):
    lang_dict = config.LANGUAGES.get(lang_code, config.LANGUAGES['TR'])
    lang_name = lang_dict['name']
    detail_lbl = lang_dict.get('detail_info', 'Detaylı Bilgi:')
    safe_word_limit = int((limit * 0.90) / 6.5)
    product_instruction = f"- 🧪 PRODUCT INTEGRATION: In your solution section, briefly explain why '{product}' should be used and how it technically solves the discussed problem." if product and str(product).strip() and str(product).strip() != "..." else "- 🧪 NO PRODUCT: Focus entirely on the technical methodology. Do not mention or promote any commercial products."
    link_instruction = f"- 🔗 CONCLUSION: End the article with a strong technical summary, then on the absolute final line add exactly this text (DO NOT translate this line):\n{detail_lbl} {product_link}" if product_link and str(product_link).strip() else "- 🚀 CONCLUSION: End the article with a strong technical summary. Stop writing immediately after the summary."

    prompt = f"""
    [CRITICAL SYSTEM COMMAND: YOUR ENTIRE OUTPUT MUST BE EXCLUSIVELY WRITTEN IN {lang_name.upper()}!]
    ACT AS: A World-Class '{role}' and industry thought leader with 20+ years of hands-on engineering, operational, and technical experience.
    MISSION: Write a highly authoritative, deeply technical, and viral professional article.
    TOPIC TO WRITE ABOUT: '{topic}' (IGNORE the language of this topic. You MUST write the article in {lang_name.upper()}).
    TARGET AUDIENCE: {audience}. Assume the audience consists of plant managers, technical directors, engineers, and industry professionals. Do NOT speak to them like beginners.
    PLATFORM: {platform}.
    CRITICAL LANGUAGE RULE (MUTLAK İTAAT): 
    The requested topic or product name might be given to you in Turkish, English, or another language. YOU MUST COMPLETELY IGNORE THE INPUT LANGUAGE. 
    You MUST output your ENTIRE final response strictly, fluently, and natively in {lang_name.upper()}. Do not mix languages. TRANSLATE all your thoughts into {lang_name.upper()} before generating the text.
    STRICT CONSTRAINTS & TONE:
    1. AVOID FLUFF: Absolutely NO generic motivational phrases, superficial business jargon, or cliché introductions. Get straight to the technical reality, root causes, and scientific/engineering facts.
    2. SAFE LENGTH LIMIT: You are strictly limited to a MAXIMUM of {safe_word_limit} words. Your entire response must easily fit within {limit} characters. Do NOT write long essays. Keep it extremely concise, punchy, and highly informative.
    3. NO PROMPT ECHOING: DO NOT repeat, translate, or copy any part of these instructions. DO NOT write "ACT AS:" or "MISSION:". Start your output DIRECTLY with the article in {lang_name.upper()}.
    4. STRUCTURE: 
       - 🎣 Viral Technical Hook (Immediately state a critical operational inefficiency, risk, or advanced industry challenge)
       - 💡 Deep Insight (Analyze the root cause using engineering, chemistry, or process-driven context)
       - ✅ Actionable Solution (Provide concrete, technical steps or metrics - Use Bullet Points)
       {product_instruction}
       {link_instruction}
    5. FORMATTING: Use short paragraphs for readability, and relevant industrial emojis (e.g., ⚗️, ⚙️, 🏭, 💧, 📊) to structure the data.
    """
    return prompt.strip()

def register_embedded_font():
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(font_path, "wb") as f: f.write(r.content)
        except: return None
    if os.path.exists(font_path):
        try: pdfmetrics.registerFont(TTFont('TrFont', font_path)); return "TrFont"
        except: return None
    return None

def create_pdf(invoice_info, shipping_addr, period, payment, bank_info, items, currency, show_total, custom_note, lang_code):
    if not HAS_REPORTLAB: return None
    t = lambda k: config.LANGUAGES.get(lang_code, config.LANGUAGES['TR']).get(k, k)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    f_reg = register_embedded_font() or "Helvetica"
    
    is_pdf_template = False
    template_bytes = st.session_state.get('template_data')
    if template_bytes:
        if isinstance(template_bytes, bytes) and b'%PDF' in template_bytes[:50]: is_pdf_template = True
        else:
            try: c.drawImage(ImageReader(io.BytesIO(template_bytes)), 0, 0, width=width, height=height)
            except: pass

    start_y = height - 190
    c.setFont(f_reg, 10); c.drawString(50, start_y, t('q_invoice_info'))
    txt = c.beginText(50, start_y - 15); txt.setFont(f_reg, 10)
    for l in invoice_info.split('\n'): txt.textLine(l[:50])
    c.drawText(txt)
    
    c.setFont(f_reg, 10); c.drawString(350, start_y, f"{t('q_date')}: {datetime.now().strftime('%d.%m.%Y')}")
    c.drawString(350, start_y - 20, f"{t('q_period')} {period}")
    c.drawString(350, start_y - 35, f"{t('q_payment')} {payment}")
    
    y = start_y - 120; c.line(40, y+15, 560, y+15); c.setFont(f_reg, 9)
    amb_text = {"TR":"Ambalaj", "EN":"Package", "RU":"Упаковка", "AR":"التعبئة", "FR":"Emballage", "ES":"Paquete"}.get(lang_code, "Ambalaj")
    c.drawString(40, y, t('q_prod_name')); c.drawString(220, y, amb_text); c.drawString(450, y, f"{t('q_price')} ({currency})")
    
    y -= 20; grand_total = 0
    for it in items:
        try:
            p = float(it.get('price', 0)); q = float(it.get('qty', 1)); line_total = p * q; grand_total += line_total
            name_text = str(it.get('name', '')); wrapped_name = textwrap.wrap(name_text, width=35) 
            if not wrapped_name: wrapped_name = [""]
            c.drawString(40, y, wrapped_name[0]); c.drawString(220, y, str(it.get('pkg', ''))[:15]); c.drawString(450, y, f"{p:,.2f}"); y -= 15
            if len(wrapped_name) > 1:
                for extra_line in wrapped_name[1:]: c.drawString(40, y, extra_line); y -= 15
            y -= 5 
        except: continue
    
    if show_total: 
        c.setFont(f_reg, 11); c.line(40, y, 560, y); c.drawString(350, y-20, f"{t('q_total')}: {grand_total:,.2f} {currency}")
    
    bank_y = 100; c.setFont(f_reg, 9); c.drawString(50, bank_y, t('q_bank_lbl')); c.drawString(140, bank_y, bank_info.replace('\n', ' | '))
    c.save(); buffer.seek(0)
    
    if is_pdf_template and HAS_PYPDF:
        try:
            text_pdf = PdfReader(buffer); template_pdf = PdfReader(io.BytesIO(template_bytes)); writer = PdfWriter()
            template_page = template_pdf.pages[0]; text_page = text_pdf.pages[0]
            if hasattr(template_page, "merge_page"): template_page.merge_page(text_page)
            elif hasattr(template_page, "mergePage"): template_page.mergePage(text_page)
            writer.add_page(template_page); merged_buffer = io.BytesIO(); writer.write(merged_buffer); merged_buffer.seek(0); return merged_buffer
        except Exception as e: return buffer
    return buffer

def resize_for_instagram(image):
    base_width = 1080
    w_percent = (base_width / float(image.size[0]))
    h_size = int((float(image.size[1]) * float(w_percent)))
    img = image.resize((base_width, h_size), Image.Resampling.LANCZOS)
    if h_size > 1350: img = img.crop((0, (h_size-1350)/2, 1080, (h_size+1350)/2))
    return img

# ==============================================================================
# 🧠 V 132.1 - AI SIFIRDAN BELGE ÜRETİM MOTORU VE KATI ŞABLON YÖNETİMİ
# ==============================================================================
def generate_sds_from_recipe_with_gemini(product_name, product_type, ingredients, doc_type, api_key, lang_code, extra_params=None):
    if not api_key: return "❌ Lütfen API anahtarını girin. / Please enter API key."
    lang_dict = config.LANGUAGES.get(lang_code, config.LANGUAGES['TR'])
    lang_name = lang_dict.get('name', 'Turkish')
    
    s1_lines = []
    if extra_params:
        if extra_params.get('sup_name') != '-': s1_lines.append(f"- Üretici/Tedarikçi: {extra_params.get('sup_name') or '[Şirket Adı]'}")
        if extra_params.get('sup_addr') != '-': s1_lines.append(f"- Adres: {extra_params.get('sup_addr') or '[Şirket Adresi]'}")
        if extra_params.get('sup_tel') != '-': s1_lines.append(f"- Telefon Numarası: {extra_params.get('sup_tel') or '[Telefon Numarası]'}")
        if extra_params.get('sup_fax') != '-': s1_lines.append(f"- Faks Numarası: {extra_params.get('sup_fax') or '[Faks Numarası]'}")
        if extra_params.get('sup_mail') != '-': s1_lines.append(f"- E-posta: {extra_params.get('sup_mail') or '[E-posta Adresi]'}")
    sec1_block = "\n".join(s1_lines)

    s9_lines = []
    if extra_params:
        def add_s9(key, label):
            val = extra_params.get(key, '')
            if val == '-': return
            if not val: 
                s9_lines.append(f"- {label}: [AI_ESTIMATE]")
            else:
                s9_lines.append(f"- {label}: {val}")
            
        add_s9('p_state', 'Fiziksel Hali')
        add_s9('p_color', 'Renk')
        add_s9('p_odor', 'Koku')
        add_s9('p_ph', 'pH')
        add_s9('p_dens', 'Bağıl Yoğunluk')
        add_s9('p_flash', 'Parlama Noktası')
    sec9_block = "\n".join(s9_lines)

    s16_lines = []
    if extra_params:
        def add_s16(key, label):
            val = extra_params.get(key, '')
            if val == '-': return
            if val: s16_lines.append(f"- {label}: {val}")
        add_s16('rev_no', 'Revizyon No')
        add_s16('rev_date', 'Revizyon Tarihi')
        add_s16('prev_date', 'Önceki GBF Tarihi')
    sec16_block = "\n".join(s16_lines)

    if "SDS" in doc_type:
        prompt = f"""
        ACT AS: A Senior Chemical Regulatory Expert and Toxicologist.
        MISSION: Generate a comprehensive 16-section Safety Data Sheet (SDS / GBF) according to GHS/CLP and REACH regulations based on the provided recipe.
        
        PRODUCT NAME: {product_name}
        PRODUCT INTENDED USE: {product_type}
        INGREDIENTS & COMPOSITION:
        {ingredients}
        
        REQUIREMENTS:
        1. Calculate or estimate the hazard classifications (H-codes, P-codes).
        2. Determine the UN Number for Section 14.
        3. Structure the output strictly into the standard 16 SDS sections.
        
        STRICT TEMPLATE RULES (YOU MUST FOLLOW THESE OR FAIL):
        For SECTION 1 (Identification), you MUST exactly include this information WITHOUT altering or omitting any line:
        {sec1_block}

        For SECTION 3 (Composition), you MUST output the ingredients as a Markdown table with EXACTLY these 5 columns:
        | Kimyasal Adı | EC No | CAS No | Konsantrasyon | GHS Sınıflandırması |
        (Fill the rows below the header based on the recipe provided).

        For SECTION 9 (Physical Properties), YOU MUST STRICTLY USE THE EXACT VALUES PROVIDED BELOW. 
        DO NOT append your own estimates in parentheses next to the provided values. ONLY output the value given.
        If a value says '[AI_ESTIMATE]', ONLY THEN should you replace that specific tag with a scientific estimation. 
        If a physical property is not in this list, do not invent it.
        {sec9_block}

        For SECTION 16 (Other Info), append these exact revision lines at the end if provided:
        {sec16_block}
        
        DO NOT write "Oluşturma Tarihi" or "Revizyon Tarihi" at the very beginning of the document. Start directly with "BÖLÜM 1".
        
        CRITICAL LANGUAGE RULE: 
        You MUST output the ENTIRE document strictly, fluently, and natively in {lang_name.upper()}.
        """
    else:
        prompt = f"""
        ACT AS: A Senior Chemical Engineer and Product Manager.
        MISSION: Generate a professional Technical Data Sheet (TDS) based on the provided product recipe.
        
        PRODUCT NAME: {product_name}
        PRODUCT INTENDED USE: {product_type}
        INGREDIENTS & COMPOSITION:
        {ingredients}
        
        REQUIREMENTS:
        1. Provide a strong 'Product Description'.
        2. List 'Application Areas'.
        3. List 'Features & Benefits'.
        4. Suggest 'Application & Dosage'.
        
        STRICT TEMPLATE RULES:
        For SECTION 1 (Identification), you MUST exactly include this information WITHOUT altering or omitting:
        {sec1_block}

        For SECTION 9 (Physical Properties), YOU MUST STRICTLY USE THE EXACT VALUES PROVIDED BELOW. 
        DO NOT append your own estimates in parentheses next to the provided values. ONLY output the value given.
        If a value says '[AI_ESTIMATE]', ONLY THEN should you replace that specific tag with a scientific estimation. 
        {sec9_block}
        
        DO NOT use markdown tables ('|' character). Use bullet points instead.
        DO NOT write header dates. Start directly with the main content.
        
        CRITICAL LANGUAGE RULE: 
        You MUST output the ENTIRE document strictly, fluently, and natively in {lang_name.upper()}.
        """
    
    models_to_try = ['gemini-2.5-flash', 'gemini-3-flash', 'gemini-2.5-pro']
    genai.configure(api_key=api_key)
    
    last_err = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = str(e)
            time.sleep(0.5)
            continue
    return f"❌ HATA / ERROR: API Bağlantı Sorunu. Detay: {last_err}"

def create_generated_document_pdf(text_content, logo_bytes=None, footer_text=None, lang_code="TR", header_params=None):
    if not HAS_REPORTLAB: return None
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    font_name = register_embedded_font() or "Helvetica"
    
    def draw_bg(canvas_obj, page_num):
        if logo_bytes:
            try:
                logo_img = ImageReader(io.BytesIO(logo_bytes))
                pil_img = Image.open(io.BytesIO(logo_bytes))
                aspect = pil_img.height / float(pil_img.width)
                w = 120
                h = w * aspect
                if h > 50:
                    h = 50
                    w = h / aspect
                canvas_obj.drawImage(logo_img, width - w - 40, height - h - 20, width=w, height=h, preserveAspectRatio=True, mask='auto')
            except: pass
            
        # V 132.1 - Header'da sağa dayalı (drawRightString) olan kısımları sola dayalı (drawString) yapıldı!
        if header_params and page_num == 1:
            canvas_obj.setFont(font_name, 9)
            canvas_obj.setFillColorRGB(0, 0, 0)
            hy = height - 25
            if header_params.get('c_date') and header_params.get('c_date') != '-':
                canvas_obj.drawString(40, hy, f"Oluşturma Tarihi: {header_params['c_date']}")
                hy -= 12
            if header_params.get('r_date') and header_params.get('r_date') != '-':
                canvas_obj.drawString(40, hy, f"Revizyon Tarihi: {header_params['r_date']}")
                hy -= 12
            if header_params.get('vers') and header_params.get('vers') != '-':
                canvas_obj.drawString(40, hy, f"Versiyon: {header_params['vers']}")
        
        canvas_obj.setStrokeColorRGB(0.7, 0.7, 0.7)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40, height - 80, width - 40, height - 80) 
        canvas_obj.line(40, 60, width - 40, 60) 
        
        if footer_text:
            canvas_obj.setFont(font_name, 8)
            canvas_obj.setFillColorRGB(0.3, 0.3, 0.3)
            lines = footer_text.split('\n')
            y_start = 48
            for l in lines:
                canvas_obj.drawString(40, y_start, l.strip()[:150])
                y_start -= 10
        
        canvas_obj.setFont(font_name, 8)
        canvas_obj.setFillColorRGB(0.3, 0.3, 0.3)
        canvas_obj.drawRightString(width - 40, 48, f"Sayfa {page_num}")
        canvas_obj.setFillColorRGB(0, 0, 0)
    
    page_num = 1
    draw_bg(c, page_num)
    text_y = height - 110
    
    if text_content:
        for p in text_content.split('\n'):
            p = p.strip()
            if not p:
                text_y -= 8
                continue
                
            is_header = p.startswith('#')
            clean_p = p.replace('#', '').replace('**', '').replace('*', '').replace('|', ' ').strip()
            
            # V 132.0: ÖZEL TABLO ÇİZİM MOTORU (Boş bırakıyoruz çünkü tabloları ayıklaması lazım)
            if clean_p.startswith('|'):
                if clean_p.replace('|', '').replace('-', '').replace(':', '').replace(' ', '') == '':
                    continue 
                
                cols = [col.strip() for col in clean_p.strip('|').split('|')]
                col_bounds = [40, 160, 230, 310, 390, 555] 
                
                c.setLineWidth(0.5)
                c.setStrokeColorRGB(0.5, 0.5, 0.5)
                c.line(40, text_y + 10, 555, text_y + 10) 
                
                col_wrapped = []
                for i, col_txt in enumerate(cols):
                    if i < len(col_bounds) - 1:
                        col_w = col_bounds[i+1] - col_bounds[i]
                        char_w = max(5, int(col_w / 5.5))
                        wrapped = textwrap.wrap(col_txt, width=char_w) if col_txt else [""]
                    else:
                        wrapped = [col_txt[:20]]
                    col_wrapped.append(wrapped)
                    
                max_lines = max([len(w) for w in col_wrapped]) if col_wrapped else 1
                row_start_y = text_y + 10
                
                for line_idx in range(max_lines):
                    if text_y < 85: 
                        c.line(40, text_y + 10, 555, text_y + 10)
                        for b in col_bounds: c.line(b, row_start_y, b, text_y + 10)
                        c.showPage()
                        page_num += 1
                        draw_bg(c, page_num)
                        text_y = height - 110
                        c.setFont(font_name, 9)
                        row_start_y = text_y + 10
                        c.line(40, text_y + 10, 555, text_y + 10)
                    
                    for i, cw_list in enumerate(col_wrapped):
                        if i < len(col_bounds) - 1 and line_idx < len(cw_list):
                            c.drawString(col_bounds[i] + 5, text_y, cw_list[line_idx])
                    text_y -= 12
                    
                c.line(40, text_y + 10, 555, text_y + 10) 
                for b in col_bounds:
                    c.line(b, row_start_y, b, text_y + 10) 
                
                text_y -= 4
                continue
            
            if is_header:
                c.setFont(font_name, 12)
                text_y -= 6
            else:
                c.setFont(font_name, 9)
                
            wrapped = textwrap.wrap(clean_p, width=105) if clean_p else [""]
            
            for wl in wrapped:
                if text_y < 85: 
                    c.showPage()
                    page_num += 1
                    draw_bg(c, page_num)
                    text_y = height - 110
                    c.setFont(font_name, 12 if is_header else 9)
                    
                c.drawString(40, text_y, wl)
                text_y -= 12
            text_y -= 4 
            
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# ==============================================================================
# 🧠 V 126.1 - LAZER KESİM REDAKSİYON (ESKİ SİSTEMLER İÇİN)
# ==============================================================================
def replace_text_in_pdf_bytes(pdf_bytes, auto_data, exact_replacements=None):
    if not HAS_PYMUPDF or not pdf_bytes: return pdf_bytes
    if not auto_data and not exact_replacements: return pdf_bytes
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        old_prod = ""
        table_prod_x0 = 150 
        if auto_data:
            try:
                for page in doc:
                    insts = page.search_for("ÜRÜN ADI")
                    if insts:
                        words = page.get_text("words")
                        tw = [w for w in words if w[1] < insts[0].y1+2 and w[3] > insts[0].y0-2 and w[0] >= insts[0].x1-2]
                        if tw:
                            tw.sort(key=lambda x: x[0])
                            old_prod = " ".join([w[4] for w in tw])
                            table_prod_x0 = tw[0][0] 
                            break
            except: pass

        for page in doc:
            try:
                for link in page.get_links(): 
                    page.delete_link(link)
            except: pass
            
            if auto_data and old_prod and auto_data.get("ÜRÜN ADI") and auto_data["ÜRÜN ADI"][1]:
                new_prod = str(auto_data["ÜRÜN ADI"][1])
                o_insts = page.search_for(old_prod)
                for inst in o_insts:
                    rect = fitz.Rect(inst.x0 - 1, inst.y0 - 2, inst.x1 + 1, inst.y1 + 2)
                    page.add_redact_annot(rect, fill=(1,1,1))
                    page.apply_redactions()
                    if page.number == 0: fsz = (inst.y1 - inst.y0) * 0.75
                    else: fsz = (inst.y1 - inst.y0) * 0.60 
                    if fsz < 5: fsz = 8
                    page.insert_text((inst.x0, inst.y1 - 1.5), new_prod, fontsize=fsz, color=(0,0,0), fontname="helv")

            if page.number == 0 and auto_data:
                if auto_data.get("ADDRESS") and auto_data["ADDRESS"][1]:
                    new_add = auto_data["ADDRESS"][1]
                    inst_ted = page.search_for("TEDARİKÇİ")
                    inst_tel = page.search_for("Tel:")
                    if not inst_tel: inst_tel = page.search_for("Tel :")
                    if not inst_tel: inst_tel = page.search_for("Tel")
                    if inst_ted and inst_tel:
                        ted = inst_ted[0]
                        valid_tels = [t for t in inst_tel if t.y0 > ted.y1]
                        if valid_tels:
                            valid_tels.sort(key=lambda t: t.y0)
                            tel = valid_tels[0]
                            if (tel.y0 - ted.y1) < 150: 
                                words_pg0 = page.get_text("words")
                                t_words = [w for w in words_pg0 if w[1] < ted.y1+3 and w[3] > ted.y0-3 and w[0] >= ted.x1-2]
                                addr_x = min(w[0] for w in t_words) if t_words else ted.x1 + 10
                                addr_y0 = ted.y1 + 2
                                addr_y1 = min(tel.y0 - 2, addr_y0 + 60)
                                if addr_y1 > addr_y0:
                                    rect = fitz.Rect(addr_x - 2, addr_y0, page.rect.width - 20, addr_y1)
                                    page.add_redact_annot(rect, fill=(1,1,1))
                                    page.apply_redactions()
                                    y_cursor = addr_y0 + 10
                                    for line in new_add.split('\n'):
                                        page.insert_text((addr_x, y_cursor), line.strip(), fontsize=9, color=(0,0,0), fontname="helv")
                                        y_cursor += 12

            if auto_data:
                words = page.get_text("words")
                processed_keys = set()
                for key, (separator, new_val) in auto_data.items():
                    if not new_val or key == "ADDRESS" or key == "ÜRÜN ADI": continue 
                    base_key = key.replace(":", "").strip()
                    if base_key in processed_keys: continue
                    insts = page.search_for(key)
                    if insts:
                        processed_keys.add(base_key)
                        for inst in insts:
                            tw = [w for w in words if w[1] < inst.y1+3 and w[3] > inst.y0-3 and w[0] >= inst.x1-2]
                            if tw:
                                min_x = min(w[0] for w in tw)
                                max_x = max(w[2] for w in tw)
                                if base_key in ["KİMYASAL ADI", "TEDARİKÇİ", "BAŞVURULACAK KİŞİ", "ACİL DURUM TELEFONU", "ACİL DURUM TEL"]:
                                    start_x = table_prod_x0 
                                elif base_key in ["Tel", "Fax", "E-mail", "Web"]:
                                    start_x = inst.x0 + 40  
                                elif base_key in ["Oluşturma Tarihi", "Revizyon Tarihi", "Versiyon"]:
                                    start_x = inst.x0 + 90  
                                else:
                                    start_x = inst.x1 + 4
                                safe_left_bound = inst.x1 + 2
                                start_x = max(start_x, safe_left_bound)
                                wipe_x = min(min_x, start_x) - 2
                                wipe_x = max(wipe_x, safe_left_bound)
                                rect = fitz.Rect(wipe_x, inst.y0, max_x + 5, inst.y1)
                                page.add_redact_annot(rect, fill=(1,1,1))
                                page.apply_redactions()
                                fsz = (inst.y1 - inst.y0) * 0.75
                                if fsz < 6: fsz = 9
                                final_text = f"{separator}{new_val}"
                                page.insert_text((start_x, inst.y1 - 1.5), final_text, fontsize=fsz, color=(0,0,0), fontname="helv")

            if exact_replacements:
                for item in exact_replacements:
                    if len(item) == 4: old_text, new_text, is_bold, is_center = item
                    else: old_text, new_text, is_bold, is_center = item[0], item[1], False, False
                    if old_text and new_text and str(old_text).strip() != "" and str(new_text).strip() != "":
                        text_instances = page.search_for(str(old_text))
                        for inst in text_instances:
                            will_center = False
                            if is_center and inst.y1 < 150: will_center = True
                            rect = fitz.Rect(inst.x0 - 1, inst.y0 - 2, inst.x1 + 1, inst.y1 + 2)
                            page.add_redact_annot(rect, fill=(1, 1, 1))
                            page.apply_redactions()
                            fsz = (inst.y1 - inst.y0) * 0.75
                            if fsz < 6: fsz = 9
                            font_to_use = "hebo" if is_bold else "helv"
                            if will_center:
                                try:
                                    font = fitz.Font(font_to_use)
                                    text_width = font.text_length(str(new_text), fontsize=fsz)
                                    target_x = (page.rect.width - text_width) / 2
                                except: target_x = inst.x0
                            else: target_x = inst.x0 
                            page.insert_text((target_x, inst.y1 - 1.5), str(new_text), fontsize=fsz, color=(0,0,0), fontname=font_to_use)
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output.read()
    except Exception as e:
        return pdf_bytes

def create_dealer_pdf(original_pdf_bytes, dealer_logo_bytes, dealer_address, 
                      top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                      bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                      logo_x, logo_y, logo_w, addr_x, addr_y, lang_code, 
                      auto_data=None, exact_replacements=None):
    if not HAS_PYPDF or not HAS_REPORTLAB: return None
    if auto_data or exact_replacements:
        original_pdf_bytes = replace_text_in_pdf_bytes(original_pdf_bytes, auto_data, exact_replacements)
    try:
        original_pdf = PdfReader(io.BytesIO(original_pdf_bytes))
        writer = PdfWriter()
        packet = io.BytesIO()
        width, height = 595.27, 841.89
        try:
            first_page = original_pdf.pages[0] if hasattr(original_pdf, "pages") else original_pdf.getPage(0)
            mbox = first_page.mediabox if hasattr(first_page, "mediabox") else first_page.mediaBox
            width = float(mbox.width) if hasattr(mbox, "width") else (float(mbox.getWidth()) if hasattr(mbox, "getWidth") else float(mbox[2]))
            height = float(mbox.height) if hasattr(mbox, "height") else (float(mbox.getHeight()) if hasattr(mbox, "getHeight") else float(mbox[3]))
        except: pass
        c = canvas.Canvas(packet, pagesize=(width, height))
        if top_mask_h > 0 and top_mask_w > 0:
            c.setFillColorRGB(1, 1, 1)
            c.rect(top_mask_x, height - top_mask_y - top_mask_h, top_mask_w, top_mask_h, fill=1, stroke=0)
        if bot_mask_h > 0 and bot_mask_w > 0:
            c.setFillColorRGB(1, 1, 1)
            c.rect(bot_mask_x, height - bot_mask_y - bot_mask_h, bot_mask_w, bot_mask_h, fill=1, stroke=0)
        if dealer_logo_bytes:
            try:
                logo_img = ImageReader(io.BytesIO(dealer_logo_bytes))
                pil_img = Image.open(io.BytesIO(dealer_logo_bytes))
                aspect = pil_img.height / pil_img.width
                logo_h = logo_w * aspect
                c.drawImage(logo_img, logo_x, height - logo_y - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
            except: pass
        if dealer_address:
            try:
                f_reg = register_embedded_font() or "Helvetica"
                c.setFont(f_reg, 9)
                c.setFillColorRGB(0, 0, 0) 
                txt = c.beginText(addr_x, height - addr_y) 
                for line in dealer_address.split('\n'):
                    txt.textLine(line[:150])
                c.drawText(txt)
            except: pass
        c.save()
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0] if hasattr(overlay_pdf, "pages") else overlay_pdf.getPage(0)
        pages_list = original_pdf.pages if hasattr(original_pdf, "pages") else [original_pdf.getPage(i) for i in range(original_pdf.getNumPages())]
        for page in pages_list:
            if hasattr(page, "merge_page"): page.merge_page(overlay_page)
            elif hasattr(page, "mergePage"): page.mergePage(overlay_page)
            writer.add_page(page)
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output
    except Exception as e:
        return None

def generate_sds_preview(original_pdf_bytes, dealer_logo_bytes, dealer_address, 
                         top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                         bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                         logo_x, logo_y, logo_w, addr_x, addr_y, 
                         auto_data=None, exact_replacements=None):
    width, height = 595, 842 
    img = None
    if original_pdf_bytes and HAS_PYMUPDF:
        if auto_data or exact_replacements:
            original_pdf_bytes = replace_text_in_pdf_bytes(original_pdf_bytes, auto_data, exact_replacements)
        try:
            doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.resize((width, height), Image.Resampling.LANCZOS) 
        except: pass
    if img is None:
        img = Image.new('RGB', (width, height), color=(240, 240, 240)) 
        draw = ImageDraw.Draw(img)
        draw.text((40, 400), "ORIJINAL PDF GORUNTUSU ICIN LUTFEN 'PyMuPDF' KUTUPHANESINI YUKLEYIN", fill=(150, 150, 150))
    draw = ImageDraw.Draw(img)
    if top_mask_h > 0 and top_mask_w > 0:
        draw.rectangle([top_mask_x, top_mask_y, top_mask_x + top_mask_w, top_mask_y + top_mask_h], fill=(255, 255, 255), outline=(200, 0, 0)) 
    if bot_mask_h > 0 and bot_mask_w > 0:
        draw.rectangle([bot_mask_x, bot_mask_y, bot_mask_x + bot_mask_w, bot_mask_y + bot_mask_h], fill=(255, 255, 255), outline=(200, 0, 0)) 
    if dealer_logo_bytes:
        try:
            logo = Image.open(io.BytesIO(dealer_logo_bytes)).convert("RGBA")
            aspect = logo.height / logo.width
            logo_h = int(logo_w * aspect)
            logo = logo.resize((int(logo_w), logo_h), Image.Resampling.LANCZOS)
            img.paste(logo, (int(logo_x), int(logo_y)), logo)
        except: pass
    if dealer_address:
        try:
            font = ImageFont.load_default()
            y_text = addr_y 
            for line in dealer_address.split('\n'):
                draw.text((addr_x, y_text), line[:150], fill=(0, 0, 0), font=font)
                y_text += 12 
        except: pass
    return img
