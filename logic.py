import google.generativeai as genai
import requests
import json
import time
import re
import os
import io
import base64
import math
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
        
    # 1. YANKI (ECHO) KALKANI: AI Promptu aynen ekrana basarsa bunu bul ve imha et.
    if "ACT AS:" in text.upper() or "MISSION:" in text.upper():
        if "---" in text:
            text = text.split("---")[-1].strip()
        else:
            match = re.search(r'FORMATTING:.*?\n(.*)', text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1).strip()
    
    # 2. GEREKSİZ GİRİŞ CÜMLELERİNİ TEMİZLE
    text = re.sub(r'^(Merhaba|Ben|Sen|Biz|Bir yapay zeka|Yapay zeka|İşte makaleniz|Hazırladığım|Here is|Sure|As requested|Here\'s|I have written).*?[\.\!\?]\s*', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def smart_trim(text, limit):
    # Makas tamamen kaldırıldı, yazı kesilmez.
    return text

# --- GEMINI API ---
def get_gemini_response_from_manual(full_prompt, api_key):
    if not api_key: return "❌ Lütfen API anahtarını girin. / Please enter API key."
    
    models_to_try = [
        'gemini-2.5-flash',      
        'gemini-3-flash',        
        'gemini-2.5-flash-lite', 
        'gemini-2.5-pro',        
        'gemini-2.0-flash-exp'   
    ]
    
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

# --- MUTLAK DİL KİLİTLİ PROMPT (V 108.0) ---
def construct_prompt_text(role, topic, audience, platform, product, limit, lang_code, product_link=None):
    lang_dict = config.LANGUAGES.get(lang_code, config.LANGUAGES['TR'])
    lang_name = lang_dict['name']
    detail_lbl = lang_dict.get('detail_info', 'Detaylı Bilgi:')
    
    # 0.90 KATSAYISI: Karakteri AI'nin anlayacağı kelime kotasına çeviriyoruz (~6.5 karakter = 1 kelime).
    safe_word_limit = int((limit * 0.90) / 6.5)

    product_instruction = ""
    link_instruction = ""

    # ÜRÜN KONTROLÜ
    if product and str(product).strip() and str(product).strip() != "...":
        product_instruction = f"- 🧪 PRODUCT INTEGRATION: In your solution section, briefly explain why '{product}' should be used and how it technically solves the discussed problem."
    else:
        product_instruction = "- 🧪 NO PRODUCT: Focus entirely on the technical methodology. Do not mention or promote any commercial products."

    # LİNK KONTROLÜ
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
            c.drawString(40, y, it['name'][:40]); c.drawString(220, y, it['pkg'][:15]); c.drawString(450, y, f"{p:,.2f}")
            y -= 15
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
