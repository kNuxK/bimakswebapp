import google.generativeai as genai
import time
import re
from PIL import Image
import io
import config

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
    5. FORMATTING: Use short paragraphs for readability, and relevant industrial emojis (e.g., ⚗️, 🏭, 💧, 📊) to structure the data.
    """
    return prompt.strip()

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
        1. Calculate the hazard classifications (H-codes, P-codes).
        2. Determine the UN Number for Section 14.
        3. Structure the output strictly into the standard 16 SDS sections.
        
        STRICT TEMPLATE RULES (YOU MUST FOLLOW THESE OR FAIL):
        
        For SECTION 1 (Identification), you MUST exactly include this information WITHOUT altering or omitting any line:
        {sec1_block}

        For SECTION 2 (Hazard Identification), if the substance has a hazard, YOU MUST INCLUDE THE PICTOGRAM MARKDOWN LINK exactly as written below in your response:
        - Corrosive/Aşındırıcı: ![GHS05](https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/GHS-pictogram-corrosion.svg/120px-GHS-pictogram-corrosion.svg.png)
        - Flammable/Yanıcı: ![GHS02](https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/GHS-pictogram-flamme.svg/120px-GHS-pictogram-flamme.svg.png)
        - Toxic/Sağlık Tehlikesi: ![GHS08](https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/GHS-pictogram-silhouete.svg/120px-GHS-pictogram-silhouete.svg.png)
        - Irritant/Tahriş Edici: ![GHS07](https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/GHS-pictogram-exclam.svg/120px-GHS-pictogram-exclam.svg.png)
        - Environmental/Çevre: ![GHS09](https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/GHS-pictogram-pollu.svg/120px-GHS-pictogram-pollu.svg.png)

        For SECTION 3 (Composition), you MUST output the ingredients as a STRICT Markdown table. 
        EVERY SINGLE ROW MUST START WITH THE '|' CHARACTER AND END WITH THE '|' CHARACTER. Do not break this format.
        Example:
        | Kimyasal Adı | EC No | CAS No | Konsantrasyon | GHS Sınıflandırması |
        |---|---|---|---|---|
        | Su | 231-791-2 | 7732-18-5 | %80 | Sınıflandırılmamış |

        For SECTION 9 (Physical Properties), YOU ARE FORBIDDEN FROM ADDING EXTRA TEXT OR PARENTHESES. 
        If a value is provided below, output it EXACTLY as written. DO NOT add explanations in parentheses.
        If it says '[AI_ESTIMATE]', ONLY THEN should you replace that specific tag entirely with your scientific estimation. Do not print the tag "[AI_ESTIMATE]".
        {sec9_block}

        For SECTION 16 (Other Info), append these exact revision lines at the end if provided:
        {sec16_block}
        
        DO NOT write "Oluşturma Tarihi" or "Revizyon Tarihi" at the very beginning of the document. Start directly with "BÖLÜM 1".
        
        CRITICAL LANGUAGE RULE: 
        You MUST output the ENTIRE document strictly, fluently, and natively in {lang_name.upper()}.
        """
    else:
        # V 134.0: TDS ÖZEL DİNAMİK İÇERİK BLOĞU
        tds_areas = extra_params.get('tds_areas', '')
        tds_benefits = extra_params.get('tds_benefits', '')
        tds_dosage = extra_params.get('tds_dosage', '')
        tds_pack = extra_params.get('tds_pack', '')

        tds_block = ""
        if tds_areas: tds_block += f"\nUSER PROVIDED APPLICATION AREAS (Must include): {tds_areas}"
        if tds_benefits: tds_block += f"\nUSER PROVIDED FEATURES & BENEFITS (Must include): {tds_benefits}"
        if tds_dosage: tds_block += f"\nUSER PROVIDED APPLICATION & DOSAGE (Must include): {tds_dosage}"
        if tds_pack: tds_block += f"\nUSER PROVIDED PACKAGING & STORAGE (Must include): {tds_pack}"

        prompt = f"""
        ACT AS: A Senior Chemical Engineer and Product Manager.
        MISSION: Generate a professional Technical Data Sheet (TDS) based on the provided product info.
        
        PRODUCT NAME: {product_name}
        PRODUCT INTENDED USE: {product_type}
        CHEMICAL NATURE / INGREDIENTS:
        {ingredients}
        {tds_block}
        
        REQUIREMENTS:
        1. Provide a strong 'Product Description'.
        2. List 'Application Areas' (Use user provided text if available, otherwise suggest professionally).
        3. List 'Features & Benefits' (Use user provided text if available, otherwise suggest professionally).
        4. Suggest 'Application & Dosage' (Use user provided text if available, otherwise suggest professionally).
        5. Include 'Packaging & Storage' (Use user provided text if available, otherwise suggest professionally).
        
        STRICT TEMPLATE RULES:
        For SECTION 1 (Identification), you MUST exactly include this information WITHOUT altering or omitting:
        {sec1_block}

        For SECTION 9 (Physical Properties), YOU ARE FORBIDDEN FROM ADDING EXTRA TEXT. 
        If a value is provided below, output it EXACTLY as written. DO NOT add explanations in parentheses.
        If it says '[AI_ESTIMATE]', ONLY THEN replace it entirely with your scientific estimation. Do not print "[AI_ESTIMATE]".
        {sec9_block}
        
        DO NOT use markdown tables ('|' character). Use bullet points instead.
        DO NOT write header dates like "Oluşturma Tarihi". Start directly with the main content.
        
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
