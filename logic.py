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

# PDF Canlı Önizleme ve Metin Değiştirme Kütüphanesi
try:
    import fitz 
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# ==============================================================================
# 🧠 VERİTABANI VE KİMLİK DOĞRULAMA (V 118.1 KOTA KORUMASI EKLENDİ)
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
        # Sessizce devam et, hata patlatma
        return None

def get_db_sheet():
    # V 118.1: API koptuğunda veya limit dolduğunda uygulamanın çökmesini engelleyen kalkan
    try:
        client = get_gsheets_client()
        if not client: return None
        sheet_url = st.secrets["gsheet_url"]
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        return None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def ping_online(username):
    # V 118.1: Kullanıcının her tıklamasında API'yi boğmamak için 60 saniye bekleme süresi eklendi
    try:
        now = time.time()
        last_ping = st.session_state.get('last_ping_time', 0)
        if now - last_ping < 60: 
            return # 60 saniye geçmediyse Google'a istek atma, API'yi yorma
            
        sheet = get_db_sheet()
        if not sheet: return
        
        users = sheet.col_values(1)
        if username in users:
            row_idx = users.index(username) + 1
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            sheet.update_cell(row_idx, 8, now_str)
            st.session_state['last_ping_time'] = now
    except: 
        pass 

def login_user(username, password):
    sheet = get_db_sheet()
    if not sheet: return False, "Veritabanı bağlantı hatası."
    try:
        rows = sheet.get_all_values()
        hashed_pw = hash_password(password)
        for i, r in enumerate(rows):
            if i == 0: continue 
            r_user = r[0] if len(r) > 0 else ""
            r_pass = r[1] if len(r) > 1 else ""
            if str(r_user) == username and str(r_pass) == hashed_pw:
                r_role = r[6] if len(r) > 6 and str(r[6]).strip() != "" else "Admin" 
                r_perms = r[8] if len(r) > 8 else ""
                
                if r_role.lower() == "admin" and not r_perms:
                    r_perms = "smy,smy_li,smy_in,tech,tech_an,tech_roi,tech_ocr,tech_reg,tech_quo,tech_sds"
                
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                try: sheet.update_cell(i + 1, 8, now_str)
                except: pass 
                
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

def register_user(username, password, role="Yeni Üye", perms=""):
    sheet = get_db_sheet()
    if not sheet: return False, "Veritabanı bağlantı hatası."
    try:
        rows = sheet.get_all_values()
        for r in rows:
            if len(r) > 0 and str(r[0]) == username:
                return False, "Bu kullanıcı adı zaten alınmış!"
        
        hashed_pw = hash_password(password)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        new_row = [username, hashed_pw, "", "", "", "", role, now_str, perms]
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
        st.error(f"Güncelleme Hatası: {e}")
        return False

def get_all_users_status():
    sheet = get_db_sheet()
    if not sheet: return []
    try:
        rows = sheet.get_all_values()
        if len(rows) <= 1: return []
        users = []
        now = datetime.now()
        for r in rows[1:]:
            u_name = r[0] if len(r) > 0 else ""
            if not u_name: continue
            u_role = r[6] if len(r) > 6 and str(r[6]).strip() != "" else "Admin"
            u_last = r[7] if len(r) > 7 else ""
            u_perms = r[8] if len(r) > 8 else ""
            
            status = "🔴 Offline"
            if u_last:
                try:
                    last_time = datetime.strptime(u_last, "%d.%m.%Y %H:%M:%S")
                    diff = now - last_time
                    if diff.total_seconds() <= 900: 
                        status = "🟢 Online"
                except: pass
            
            users.append({
                "username": u_name,
                "role": u_role,
                "status": status,
                "last_seen": u_last if u_last else "Hiç girmedi",
                "permissions": u_perms
            })
        return users
    except Exception as e:
        return []

def update_user_role_and_perms(username, new_role, new_perms):
    sheet = get_db_sheet()
    if not sheet: return False
    try:
        users = sheet.col_values(1)
        if username in users:
            row_idx = users.index(username) + 1
            sheet.update_cell(row_idx, 7, new_role)
            sheet.update_cell(row_idx, 9, new_perms)
            return True
        return False
    except:
        return False

def delete_user(target_username):
    sheet = get_db_sheet()
    if not sheet: return False, "Veritabanı bağlantı hatası."
    try:
        users = sheet.col_values(1)
        if target_username in users:
            row_idx = users.index(target_username) + 1
            if row_idx == 1:
                return False, "Başlık satırı silinemez!"
            try:
                sheet.delete_rows(row_idx)
            except AttributeError:
                sheet.delete_row(row_idx)
            return True, f"'{target_username}' başarıyla silindi."
        return False, "Kullanıcı bulunamadı."
    except Exception as e:
        return False, f"Silme hatası: {str(e)}"

# ==============================================================================
# 🧠 MANTIK
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
    if not text or not isinstance(text, str):
        return "⚠️ HATA: İçerik oluşturulamadı. Lütfen API kotanızı kontrol edin."
        
    if "ACT AS:" in text.upper() or "MISSION:" in text.upper():
        if "---" in text:
            text = text.split("---")[-1].strip()
        else:
            match = re.search(r'FORMATTING:.*?\n(.*)', text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1).strip()
    
    text = re.sub(r'^(Merhaba|Ben|Sen|Biz|Bir yapay zeka|Yapay zeka|İşte makaleniz|Hazırladığım|Here is|Sure|As requested|Here\'s|I have written).*?[\.\!\?]\s*', '', text, flags=re.IGNORECASE)
    return text.strip()

def smart_trim(text, limit):
    return text

# --- GEMINI API ---
def get_gemini_response_from_manual(full_prompt, api_key):
    if not api_key: return "❌ Lütfen API anahtarını girin. / Please enter API key."
    
    models_to_try = ['gemini-2.5-flash', 'gemini-3-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-pro']
    genai.configure(api_key=api_key)
    
    last_err = ""
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(full_prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = str(e)
            time.sleep(0.5) 
            continue
            
    return f"❌ HATA / ERROR: {last_err}"

# --- GERÇEK LINKEDIN API ENTEGRASYONU ---
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
    
    share_content = {
        "shareCommentary": {"text": text},
        "shareMediaCategory": "NONE"
    }
    
    if asset_urn:
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [{
            "status": "READY",
            "description": {"text": "Bimaks App Auto Post"},
            "media": asset_urn,
            "title": {"text": "Bimaks Visual"}
        }]
        
    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": share_content
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    
    try:
        response = requests.post(post_url, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            return "✅ BAŞARILI: Paylaşım LinkedIn'de yayında!"
        else:
            return f"❌ HATA: LinkedIn reddetti. Kod: {response.status_code} - Mesaj: {response.text}"
    except Exception as e:
        return f"❌ HATA: Bağlantı sorunu: {str(e)}"

# --- GELİŞMİŞ ROI HESAPLAMA ---
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
            "w_curr": float(blowdown_curr) * float(hours),
            "w_new": blowdown_new * float(hours),
            "w_save": water_saved_total,
            "w_money": water_saved_total * float(water_cost),
            "e_save": energy_saved,
            "total_gain": (water_saved_total * float(water_cost)) + energy_saved - float(chem_cost)
        }
    except: return None

# --- OCR VE GÖRSEL ANALİZ ---
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

# --- LSI HESAPLAMA ---
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

# --- PROMPT MİMARİSİ ---
def construct_prompt_text(role, topic, audience, platform, product, limit, lang_code, product_link=None):
    lang_dict = config.LANGUAGES.get(lang_code, config.LANGUAGES['TR'])
    lang_name = lang_dict['name']
    detail_lbl = lang_dict.get('detail_info', 'Detaylı Bilgi:')
    
    safe_word_limit = int((limit * 0.90) / 6.5)

    product_instruction = ""
    link_instruction = ""

    if product and str(product).strip() and str(product).strip() != "...":
        product_instruction = f"- 🧪 PRODUCT INTEGRATION: In your solution section, briefly explain why '{product}' should be used and how it technically solves the discussed problem."
    else:
        product_instruction = "- 🧪 NO PRODUCT: Focus entirely on the technical methodology. Do not mention or promote any commercial products."

    if product_link and str(product_link).strip():
        link_instruction = f"- 🔗 CONCLUSION: End the article with a strong technical summary, then on the absolute final line add exactly this text (DO NOT translate this line):\n{detail_lbl} {product_link}"
    else:
        link_instruction = "- 🚀 CONCLUSION: End the article with a strong technical summary. Stop writing immediately after the summary."

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
        if isinstance(template_bytes, bytes) and b'%PDF' in template_bytes[:50]:
            is_pdf_template = True
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
    
    amb_text = {"TR":"Ambalaj", "EN":"Package", "RU":"Упаковка", "AR":"التعبئة"}.get(lang_code, "Ambalaj")
    
    c.drawString(40, y, t('q_prod_name')); c.drawString(220, y, amb_text); c.drawString(450, y, f"{t('q_price')} ({currency})")
    
    y -= 20; grand_total = 0
    for it in items:
        try:
            p = float(it.get('price', 0))
            q = float(it.get('qty', 1))
            line_total = p * q
            grand_total += line_total
            
            name_text = str(it.get('name', ''))
            wrapped_name = textwrap.wrap(name_text, width=35) 
            if not wrapped_name: wrapped_name = [""]
            
            c.drawString(40, y, wrapped_name[0])
            c.drawString(220, y, str(it.get('pkg', ''))[:15])
            c.drawString(450, y, f"{p:,.2f}")
            y -= 15
            
            if len(wrapped_name) > 1:
                for extra_line in wrapped_name[1:]:
                    c.drawString(40, y, extra_line)
                    y -= 15
                    
            y -= 5 
        except: continue
    
    if show_total: 
        c.setFont(f_reg, 11); c.line(40, y, 560, y)
        c.drawString(350, y-20, f"{t('q_total')}: {grand_total:,.2f} {currency}")
    
    bank_y = 100; c.setFont(f_reg, 9); c.drawString(50, bank_y, t('q_bank_lbl'))
    c.drawString(140, bank_y, bank_info.replace('\n', ' | '))
    
    c.save(); buffer.seek(0)
    
    if is_pdf_template and HAS_PYPDF:
        try:
            text_pdf = PdfReader(buffer)
            template_pdf = PdfReader(io.BytesIO(template_bytes))
            writer = PdfWriter()
            
            template_page = template_pdf.pages[0]
            text_page = text_pdf.pages[0]
            
            if hasattr(template_page, "merge_page"):
                template_page.merge_page(text_page)
            elif hasattr(template_page, "mergePage"):
                template_page.mergePage(text_page)
                
            writer.add_page(template_page)
            
            merged_buffer = io.BytesIO()
            writer.write(merged_buffer)
            merged_buffer.seek(0)
            return merged_buffer
        except Exception as e:
            return buffer
            
    return buffer

def resize_for_instagram(image):
    base_width = 1080
    w_percent = (base_width / float(image.size[0]))
    h_size = int((float(image.size[1]) * float(w_percent)))
    img = image.resize((base_width, h_size), Image.Resampling.LANCZOS)
    if h_size > 1350: img = img.crop((0, (h_size-1350)/2, 1080, (h_size+1350)/2))
    return img

def replace_text_in_pdf_bytes(pdf_bytes, exact_replacements=None, smart_replacements=None):
    if not HAS_PYMUPDF or not pdf_bytes:
        return pdf_bytes
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in doc:
            try:
                for link in page.get_links():
                    page.delete_link(link)
            except:
                pass
                
            if smart_replacements:
                blocks = page.get_text("dict")["blocks"]
                for b in blocks:
                    if b.get('type') == 0: 
                        for l in b.get("lines", []):
                            line_text = "".join([s["text"] for s in l.get("spans", [])])
                            for prefix, new_text in smart_replacements:
                                if prefix and new_text and str(prefix) in line_text:
                                    bbox = fitz.Rect(l["bbox"])
                                    page.add_redact_annot(bbox, fill=(1, 1, 1))
                                    page.apply_redactions()
                                    
                                    if l.get("spans"):
                                        font_sz = l["spans"][0]["size"] * 0.90
                                    else:
                                        font_sz = 9
                                    page.insert_text((bbox.x0, bbox.y1 - (bbox.height * 0.2)), str(new_text), fontsize=font_sz, color=(0,0,0), fontname="helv")

            if exact_replacements:
                for old_text, new_text in exact_replacements:
                    if old_text and new_text and str(old_text).strip() != "" and str(new_text).strip() != "":
                        text_instances = page.search_for(str(old_text))
                        for inst in text_instances:
                            page.add_redact_annot(inst, fill=(1, 1, 1))
                            page.apply_redactions()
                            
                            font_sz = inst.height * 0.85
                            page.insert_text((inst.x0, inst.y1 - (inst.height * 0.15)), str(new_text), fontsize=font_sz, color=(0,0,0), fontname="helv")
        
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
                      exact_replacements=None, smart_replacements=None):
    if not HAS_PYPDF or not HAS_REPORTLAB: return None
    
    if exact_replacements or smart_replacements:
        original_pdf_bytes = replace_text_in_pdf_bytes(original_pdf_bytes, exact_replacements, smart_replacements)
        
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
            if hasattr(page, "merge_page"):
                page.merge_page(overlay_page)
            elif hasattr(page, "mergePage"):
                page.mergePage(overlay_page)
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
                         exact_replacements=None, smart_replacements=None):
    width, height = 595, 842 
    img = None
    
    if original_pdf_bytes and HAS_PYMUPDF:
        if exact_replacements or smart_replacements:
            original_pdf_bytes = replace_text_in_pdf_bytes(original_pdf_bytes, exact_replacements, smart_replacements)
            
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
