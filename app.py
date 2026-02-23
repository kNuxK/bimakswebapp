import streamlit as st
import config
import logic
import os
from PIL import Image, ImageDraw, ImageFont 
import io
import time 
try: from pypdf import PdfWriter, PdfReader 
except: pass

st.set_page_config(page_title="BİMAKS APP V 1.0", layout="wide", page_icon="💧", initial_sidebar_state="expanded")

# --- KİMLİK DOĞRULAMA (LOGIN) SİSTEMİ ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = ""
if 'role' not in st.session_state:
    st.session_state['role'] = "Yeni Üye"
if 'permissions' not in st.session_state:
    st.session_state['permissions'] = ""

def t(key): return config.LANGUAGES.get(st.session_state.get('lang', 'TR'), config.LANGUAGES['TR']).get(key, key)
def _(tr, en, ru, ar, fr, es):
    l = st.session_state.get('lang', 'TR')
    if l == 'EN': return en
    if l == 'RU': return ru
    if l == 'AR': return ar
    if l == 'FR': return fr
    if l == 'ES': return es
    return tr

# LOGIN EKRANI
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>💧 BİMAKS APP GİRİŞ</h1>", unsafe_allow_html=True)
        st.markdown("---")
        tab1, tab2 = st.tabs(["🔑 Giriş Yap", "📝 Kayıt Ol"])
        
        with tab1:
            log_user = st.text_input("Kullanıcı Adı", key="log_user")
            log_pass = st.text_input("Şifre", type="password", key="log_pass")
            if st.button("Giriş", type="primary", use_container_width=True):
                with st.spinner("Doğrulanıyor..."):
                    success, data = logic.login_user(log_user, log_pass)
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['current_user'] = log_user
                        st.session_state['role'] = data.get('role', 'Yeni Üye')
                        st.session_state['permissions'] = data.get('permissions', '')
                        st.session_state['settings_db'] = {
                            "genai_key": data.get('genai_key', ''), 
                            "linkedin_token": data.get('linkedin_token', ''), 
                            "instagram_token": data.get('instagram_token', ''), 
                            "instagram_account_id": data.get('instagram_account_id', ''), 
                            "theme_bg": "#0E1117", "theme_txt": "#FAFAFA", "theme_btn": "#8998f3", 
                            "app_title": "BİMAKS APP", "app_footer": "Created by Ogün Gümüşay",
                            "enable_quote": True, "enable_social_media": True, "enable_linkedin": True, "enable_instagram": False, "enable_problem_solver": True,
                            "enable_dealer_sds": False 
                        }
                        st.success("Giriş Başarılı! Yönlendiriliyorsunuz...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(data)

        with tab2:
            reg_user = st.text_input("Yeni Kullanıcı Adı", key="reg_user")
            reg_pass = st.text_input("Yeni Şifre", type="password", key="reg_pass")
            if st.button("Kayıt Ol", use_container_width=True):
                if len(reg_user) < 3 or len(reg_pass) < 3:
                    st.warning("Kullanıcı adı ve şifre en az 3 karakter olmalıdır.")
                else:
                    with st.spinner("Kayıt yapılıyor..."):
                        success, msg = logic.register_user(reg_user, reg_pass, "Yeni Üye")
                        if success: st.success(msg)
                        else: st.error(msg)
    st.stop()

# ==========================================
# GİRİŞ YAPILDIKTAN SONRAKİ UYGULAMA KODLARI
# ==========================================

if 'personas_db' not in st.session_state: st.session_state['personas_db'] = config.DEFAULT_PERSONAS
if 'history_db' not in st.session_state: st.session_state['history_db'] = []
if 'lang' not in st.session_state: st.session_state['lang'] = 'TR'
if 'bimaks_sub_tab' not in st.session_state: st.session_state['bimaks_sub_tab'] = 'Analysis'

for k in ['logo_data', 'template_data', 'quote_items', 'insta_tags_list', 'active_tab', 'linkedin_editor', 'insta_editor', 'ocr_result', 'linkedin_warning', 'insta_warning']:
    if k not in st.session_state: st.session_state[k] = None if k in ['logo_data', 'template_data', 'active_tab'] else ([] if 'list' in k or 'quote' in k else "")

logic.apply_theme()

perms = str(st.session_state.get('permissions', ''))
is_admin = str(st.session_state.get('role', '')).lower() == 'admin'

# --- SIDEBAR ---
with st.sidebar:
    st.success(f"👤 Hoşgeldin, **{st.session_state['current_user']}**")
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()
    
    if st.session_state.get('logo_data'): st.image(st.session_state['logo_data'], use_container_width=True)
    elif os.path.exists("logo.jpg"): st.image("logo.jpg", use_container_width=True)
    st.markdown(f"<h1 style='text-align: center;'>{st.session_state['settings_db'].get('app_title')}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    if ("smy" in perms or is_admin) and st.session_state['settings_db'].get("enable_social_media"):
        is_soc = st.session_state['active_tab'] in [t('btn_social_main'), t('btn_linkedin'), t('btn_instagram')]
        if st.button(t('btn_social_main'), use_container_width=True, type="primary" if is_soc else "secondary"):
            st.session_state['active_tab'] = t('btn_social_main'); st.rerun()
        if is_soc:
            if ("smy_li" in perms or is_admin) and st.session_state['settings_db'].get("enable_linkedin") and st.button(t('btn_linkedin'), use_container_width=True): st.session_state['active_tab'] = t('btn_linkedin'); st.rerun()
            if ("smy_in" in perms or is_admin) and st.session_state['settings_db'].get("enable_instagram") and st.button(t('btn_instagram'), use_container_width=True): st.session_state['active_tab'] = t('btn_instagram'); st.rerun()

    if ("tech" in perms or is_admin) and st.session_state['settings_db'].get("enable_problem_solver") and st.button(t('btn_bimaks_tech'), use_container_width=True, type="primary" if st.session_state['active_tab'] == t('btn_bimaks_tech') else "secondary"):
        st.session_state['active_tab'] = t('btn_bimaks_tech'); st.rerun()

    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True); st.markdown("---")
    
    is_settings_active = st.session_state.get('show_settings', False) and st.session_state.get('active_tab') != 'Admin Paneli'
    if st.button(t('settings'), use_container_width=True, type="primary" if is_settings_active else "secondary"): 
        st.session_state['show_settings'] = True
        st.session_state['active_tab'] = None
        st.rerun()

    if (st.session_state.get('show_settings') or st.session_state.get('active_tab') == 'Admin Paneli') and is_admin:
        if st.button("↳ 👑 Admin Paneli", use_container_width=True, type="primary" if st.session_state.get('active_tab') == 'Admin Paneli' else "secondary"):
            st.session_state['active_tab'] = 'Admin Paneli'
            st.session_state['show_settings'] = False
            st.rerun()

    st.markdown("---"); st.markdown("### 🌐 Language")
    r1c1, r1c2, r1c3 = st.columns(3)
    if r1c1.button("TR", use_container_width=True): st.session_state['lang'] = 'TR'; st.rerun()
    if r1c2.button("EN", use_container_width=True): st.session_state['lang'] = 'EN'; st.rerun()
    if r1c3.button("RU", use_container_width=True): st.session_state['lang'] = 'RU'; st.rerun()
    r2c1, r2c2, r2c3 = st.columns(3)
    if r2c1.button("AR", use_container_width=True): st.session_state['lang'] = 'AR'; st.rerun()
    if r2c2.button("FR", use_container_width=True): st.session_state['lang'] = 'FR'; st.rerun()
    if r2c3.button("ES", use_container_width=True): st.session_state['lang'] = 'ES'; st.rerun()
    st.caption(st.session_state['settings_db'].get('app_footer'))

# --- ANA EKRAN ---

# 1. BİMAKS TEKNİK
if st.session_state.get('active_tab') == t('btn_bimaks_tech') and not st.session_state.get('show_settings'):
    st.header(t('btn_bimaks_tech'))
    if not st.session_state['settings_db'].get("genai_key"): 
        st.info(_("👋 API Anahtarı Gerekli. Lütfen Ayarlar'dan API girin.", "👋 API Key Required.", "👋 Требуется ключ API", "👋 مفتاح API مطلوب", "👋 Clé API requise.", "👋 Se requiere clave API."))
        st.stop()
    
    nav_tabs = []
    tab_keys = []
    
    if "tech_an" in perms or is_admin: nav_tabs.append(t('nav_analysis')); tab_keys.append('Analysis')
    if "tech_roi" in perms or is_admin: nav_tabs.append(t('nav_roi')); tab_keys.append('ROI')
    if "tech_ocr" in perms or is_admin: nav_tabs.append(t('nav_ocr')); tab_keys.append('OCR')
    if "tech_reg" in perms or is_admin: nav_tabs.append(t('nav_reg')); tab_keys.append('REG')
    if "tech_quo" in perms or is_admin: 
        nav_tabs.append(_("Teklif Oluştur", "Quote Generator", "Генератор предложений", "مولد الاقتباس", "Créer un devis", "Crear cotización"))
        tab_keys.append('Teklif')
    if "tech_sds" in perms or is_admin: nav_tabs.append("SDS/TDS"); tab_keys.append('SDS')
    
    if not nav_tabs:
        st.warning("Bu modülün hiçbir alt başlığına yetkiniz bulunmamaktadır.")
        st.stop()
        
    if st.session_state['bimaks_sub_tab'] not in tab_keys:
        st.session_state['bimaks_sub_tab'] = tab_keys[0]
        
    nav_cols = st.columns(len(nav_tabs))
    for i, n_tab in enumerate(nav_tabs):
        if nav_cols[i].button(n_tab, use_container_width=True, type="primary" if st.session_state['bimaks_sub_tab'] == tab_keys[i] else "secondary"):
            st.session_state['bimaks_sub_tab'] = tab_keys[i]; st.rerun()
    
    st.divider()

    # A. Sistem Analizi
    if st.session_state['bimaks_sub_tab'] == 'Analysis':
        st.subheader(t('solver_title'))
        user_problem = st.text_area(_("Problem:", "Problem:", "Проблема:", "مشكلة:", "Problème:", "Problema:"), height=100, placeholder=t('solver_ph'))
        st.info(t('lsi_info'))
        
        col_mk, col_sy = st.columns(2)
        with col_mk:
            st.markdown(f"**{t('mk_water')}**")
            mk_ph = st.text_input(t('ph_req'), key="mk_ph")
            mk_tds = st.text_input(t('tds_req'), key="mk_tds")
            mk_temp = st.text_input(t('temp_req'), key="mk_temp")
            mk_ca = st.text_input(t('ca_req'), key="mk_ca")
            mk_alk = st.text_input(t('alk_req'), key="mk_alk")
            mk_cond = st.text_input(t('cond_opt'), key="mk_cond")
            mk_cl = st.text_input(t('cl_opt'), key="mk_cl")
            mk_so4 = st.text_input(t('so4_opt'), key="mk_so4")
            mk_fe = st.text_input(t('fe_opt'), key="mk_fe")
            mk_sio2 = st.text_input(t('sio2_opt'), key="mk_sio2")
        with col_sy:
            st.markdown(f"**{t('sy_water')}**")
            sy_ph = st.text_input(t('ph_req'), key="sy_ph")
            sy_tds = st.text_input(t('tds_req'), key="sy_tds")
            sy_temp = st.text_input(t('temp_req'), key="sy_temp")
            sy_ca = st.text_input(t('ca_req'), key="sy_ca")
            sy_alk = st.text_input(t('alk_req'), key="sy_alk")
            sy_cond = st.text_input(t('cond_opt'), key="sy_cond")
            sy_cl = st.text_input(t('cl_opt'), key="sy_cl")
            sy_so4 = st.text_input(t('so4_opt'), key="sy_so4")
            sy_fe = st.text_input(t('fe_opt'), key="sy_fe")
            sy_sio2 = st.text_input(t('sio2_opt'), key="sy_sio2")

        if st.button(t('btn_analyze'), type="primary"):
            logic.ping_online(st.session_state['current_user'])
            lsi_val, rsi_val = logic.calculate_lsi(sy_ph, sy_tds, sy_temp, sy_ca, sy_alk)
            an_txt = f"""
            MAKEUP SUYU: pH:{mk_ph}, TDS:{mk_tds}, Ca:{mk_ca}, Alk:{mk_alk}, İletkenlik:{mk_cond}, Cl:{mk_cl}, SO4:{mk_so4}, Fe:{mk_fe}, SiO2:{mk_sio2}
            SİSTEM SUYU: pH:{sy_ph}, TDS:{sy_tds}, Ca:{sy_ca}, Alk:{sy_alk}, İletkenlik:{sy_cond}, Cl:{sy_cl}, SO4:{sy_so4}, Fe:{sy_fe}, SiO2:{sy_sio2}
            """
            lsi_msg = f"\nLSI: {lsi_val:.2f} | RSI: {rsi_val:.2f}" if lsi_val is not None else ""
            if lsi_val is not None: st.success(t('lsi_result') + lsi_msg)
            
            lang_name = config.LANGUAGES.get(st.session_state['lang'], config.LANGUAGES['TR'])['name']
            
            p_solver = f"""
            ACT AS: Senior Water Treatment Engineer.
            PROBLEM: {user_problem}
            SYSTEM DATA: {an_txt}
            {lsi_msg}
            MISSION: Provide a detailed technical solution, chemical recommendations, and operational adjustments.
            CRITICAL LANGUAGE RULE: TRANSLATE YOUR THOUGHTS AND WRITE YOUR ENTIRE RESPONSE STRICTLY, NATIVELY, AND FLUENTLY IN {lang_name.upper()}. DO NOT MIX LANGUAGES.
            """
            with st.spinner(_("Analiz ediliyor...", "Analyzing...", "Анализируется...", "جارٍ التحليل...", "Analyse en cours...", "Analizando...")):
                res = logic.get_gemini_response_from_manual(p_solver, st.session_state['settings_db']["genai_key"])
                st.markdown(res)

    # B. ROI
    elif st.session_state['bimaks_sub_tab'] == 'ROI':
        st.subheader(t('roi_title'))
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**{t('roi_subtitle_inputs')}**")
            bd = st.number_input(t('roi_blowdown'), value=2.0)
            hours = st.number_input(t('roi_hours'), value=8000)
            coc_curr = st.number_input(t('roi_coc_curr'), value=2.5)
            scale = st.number_input(t('roi_scale'), value=1.0)
        with c2:
            st.markdown(f"**{t('roi_subtitle_costs')}**")
            cost_w = st.number_input(t('roi_cost_water'), value=2.0)
            cost_e = st.number_input(t('roi_cost_energy'), value=50000.0)
            cost_c = st.number_input(t('roi_cost_chem'), value=2000.0)
        with c3:
            st.markdown(f"**{t('roi_subtitle_bimaks')}**")
            coc_targ = st.number_input(t('roi_coc_target'), value=4.0)
            dose = st.number_input(t('roi_dose'), value=50.0)
            price = st.number_input(t('roi_price'), value=5.0)
        
        st.markdown("---")
        if st.button(t('roi_calc_btn'), type="primary"):
            logic.ping_online(st.session_state['current_user'])
            res = logic.calculate_advanced_roi(bd, hours, coc_curr, coc_targ, cost_w, cost_e, scale, cost_c)
            if res:
                new_chem_cost = res['w_new'] * (dose / 1000) * price 
                total_gain = res['w_money'] + res['e_save'] + (cost_c - new_chem_cost)
                st.subheader(_("📊 Karşılaştırmalı Maliyet Analizi", "📊 Comparative Cost Analysis", "📊 Сравнительный анализ затрат", "📊 تحليل التكلفة المقارن", "📊 Analyse comparative des coûts", "📊 Análisis de costos comparativo"))
                col_data = {
                    t('tbl_param'): [t('row_water'), t('row_energy'), t('row_chem'), t('row_total')],
                    t('tbl_curr'): [f"{res['w_curr']:.0f} m³", f"{cost_e:,.0f} €", f"{cost_c:,.0f} €", f"{(res['w_curr']*cost_w + cost_e + cost_c):,.0f} €"],
                    t('tbl_bimaks'): [f"{res['w_new']:.0f} m³", f"{(cost_e - res['e_save']):,.0f} €", f"{new_chem_cost:,.0f} €", f"{(res['w_new']*cost_w + cost_e - res['e_save'] + new_chem_cost):,.0f} €"],
                    t('tbl_save'): [f"✅ {res['w_save']:.0f} m³", f"✅ {res['e_save']:,.0f} €", f"{'✅' if cost_c > new_chem_cost else '❌'} {(cost_c - new_chem_cost):,.0f} €", f"🔥 {total_gain:,.0f} €"]
                }
                st.table(col_data)
            else: st.error(_("Hesaplama hatası.", "Calculation error.", "Ошибка расчета.", "خطأ في الحساب.", "Erreur de calcul.", "Error de cálculo."))

    # C. OCR
    elif st.session_state['bimaks_sub_tab'] == 'OCR':
        st.subheader(t('ocr_title')); st.info(t('ocr_desc'))
        ocr_file = st.file_uploader(_("Rapor Fotoğrafı", "Report Photo", "Фото отчета", "صورة التقرير", "Photo du rapport", "Foto del informe"), type=['jpg', 'png', 'jpeg'])
        if ocr_file and st.button(t('ocr_btn')):
            logic.ping_online(st.session_state['current_user'])
            lang_name = config.LANGUAGES.get(st.session_state['lang'], config.LANGUAGES['TR'])['name']
            ocr_prompt = f"""
            ACT AS: Senior Water Treatment Engineer.
            MISSION: Read, analyze and interpret this water analysis report. Point out any critical out-of-spec values and suggest corrective actions.
            CRITICAL LANGUAGE RULE: TRANSLATE YOUR THOUGHTS AND WRITE YOUR ENTIRE RESPONSE STRICTLY AND NATIVELY IN {lang_name.upper()}.
            """
            with st.spinner(_("Okunuyor...", "Reading...", "Чтение...", "قراءة...", "Lecture en cours...", "Leyendo...")):
                res = logic.analyze_image_with_gemini(ocr_file.getvalue(), ocr_prompt, st.session_state['settings_db']["genai_key"])
                st.markdown(res)

    # D. Mevzuat
    elif st.session_state['bimaks_sub_tab'] == 'REG':
        st.subheader(t('reg_title')); q_reg = st.text_input(_("Soru:", "Question:", "Вопрос:", "سؤال:", "Question:", "Pregunta:"), placeholder=t('reg_ph'))
        if st.button(_("Araştır", "Search", "Поиск", "بحث", "Rechercher", "Buscar")):
            logic.ping_online(st.session_state['current_user'])
            lang_name = config.LANGUAGES.get(st.session_state['lang'], config.LANGUAGES['TR'])['name']
            reg_prompt = f"ACT AS: Regulatory Expert. QUESTION: {q_reg}. CRITICAL LANGUAGE RULE: YOU MUST WRITE YOUR ENTIRE RESPONSE STRICTLY IN {lang_name.upper()}."
            res = logic.get_gemini_response_from_manual(reg_prompt, st.session_state['settings_db']["genai_key"])
            st.markdown(res)
            
    # E. TEKLİF OLUŞTUR
    elif st.session_state['bimaks_sub_tab'] == 'Teklif':
        st.subheader(t('quote_title'))
        
        with st.expander(_("📄 Antetli Kağıt Ayarı", "📄 Letterhead Setup", "📄 Настройка бланка", "📄 إعداد الترويسة", "📄 Config. En-tête", "📄 Config. Membrete"), expanded=True):
            default_antet = "antetlikagit.pdf"
            
            ut = st.file_uploader(_("Yeni Antet Yükle:", "Upload New Letterhead:", "Загрузить новый бланк:", "تحميل ترويسة جديدة:", "Nouveau En-tête :", "Nuevo Membrete:"), type=['png', 'jpg', 'jpeg', 'pdf'], key="quote_antet")
            
            if ut: 
                st.session_state['template_data'] = ut.getvalue()
                st.success(_("✅ Yeni antet kullanılıyor!", "✅ New letterhead applied!", "✅ Используется новый бланк!", "✅ تم تطبيق ترويسة جديدة!", "✅ Nouvel en-tête appliqué !", "✅ ¡Nuevo membrete aplicado!"))
            else:
                if os.path.exists(default_antet):
                    with open(default_antet, "rb") as f: 
                        st.session_state['template_data'] = f.read()
                    st.info(f"✅ {default_antet} aktif.")
                else:
                    st.session_state['template_data'] = None
                    st.warning("⚠️ Antet bulunamadı. / Letterhead not found.")

        c1, c2 = st.columns(2)
        qi, qs = c1.text_area(t('q_invoice_info'), height=100), c1.text_area(t('q_shipping_addr'), height=100)
        qp, qpy = c2.text_input(t('q_period'), "15"), c2.text_input(t('q_payment'), "Peşin / Cash")
        qb, qc = c2.text_area(t('q_bank_lbl'), value=t('q_bank_def'), height=100), c2.selectbox(_("Birim", "Currency", "Валюта", "العملة", "Devise", "Moneda"), ["₺","$","€"])
        
        st.divider()
        
        c_qn, c_qk, c_qs, c_qq, c_qu, c_qp = st.columns([3, 1.5, 1.5, 1, 1, 1.5])
        qn = c_qn.text_input(t('q_prod_name'))
        qk = c_qk.text_input(_("Ambalaj", "Pkg", "Упак.", "تعبئة", "Emb.", "Paq."))
        qs = c_qs.selectbox(t('q_shipping_opt'), [t('q_inc'), t('q_exc')])
        qq = c_qq.number_input(_("Adet", "Qty", "Кол.", "كمية", "Qté", "Cant."), 1, 10000, 1)
        qu = c_qu.text_input(_("Birim", "Unit", "Ед.", "وحدة", "Unité", "Unidad"), value="kg")
        qp_val = c_qp.number_input(_("Fiyat", "Price", "Цена", "السعر", "Prix", "Precio"), 0.0, 1000000.0, 0.0)
        
        if st.button(_("Ekle", "Add", "Добавить", "إضافة", "Ajouter", "Añadir")): 
            new_item = {
                "name": qn,
                "pkg": qk,
                "ship": qs,
                "qty": qq,
                "unit": qu,
                "price": qp_val
            }
            st.session_state['quote_items'].append(new_item)
            st.rerun()
        
        if st.session_state['quote_items']:
            st.markdown("---")
            st.markdown(_("**📝 Eklenen Ürünler (Düzenleyebilirsiniz)**", "**📝 Added Items (Editable)**", "**📝 Добавленные товары (можно редактировать)**", "**📝 العناصر المضافة (قابلة للتعديل)**", "**📝 Articles ajoutés (Modifiables)**", "**📝 Artículos agregados (Editables)**"))
            
            for i, it in enumerate(st.session_state['quote_items']):
                c_ed1, c_ed2, c_ed3, c_ed4, c_ed5, c_ed6 = st.columns([3, 1.5, 1, 1, 1.5, 0.5])
                
                st.session_state['quote_items'][i]['name'] = c_ed1.text_input("Ürün", value=it['name'], key=f"ed_n_{i}", label_visibility="collapsed")
                st.session_state['quote_items'][i]['pkg'] = c_ed2.text_input("Ambalaj", value=it['pkg'], key=f"ed_k_{i}", label_visibility="collapsed")
                st.session_state['quote_items'][i]['qty'] = c_ed3.number_input("Adet", value=float(it['qty']), key=f"ed_q_{i}", label_visibility="collapsed")
                st.session_state['quote_items'][i]['unit'] = c_ed4.text_input("Birim", value=it['unit'], key=f"ed_u_{i}", label_visibility="collapsed")
                st.session_state['quote_items'][i]['price'] = c_ed5.number_input("Fiyat", value=float(it['price']), key=f"ed_p_{i}", label_visibility="collapsed")
                
                if c_ed6.button("X", key=f"del_{i}"):
                    st.session_state['quote_items'].pop(i)
                    st.rerun()
                    
            q_show_total = st.checkbox(t('q_show_total'), value=True)
            q_note = st.text_area(t('q_note_label'))
            if st.button(t('q_create')):
                logic.ping_online(st.session_state['current_user'])
                pdf = logic.create_pdf(qi, qs, qp, qpy, qb, st.session_state['quote_items'], qc, q_show_total, q_note, st.session_state['lang'])
                st.download_button(_("İndir", "Download", "Скачать", "تحميل", "Télécharger", "Descargar"), data=pdf, file_name="Teklif.pdf", mime="application/pdf")

    # F. BAYİ SDS/TDS ÜRETİCİ (V 126.1 - ACİL TELEFON 16 MADDELİ JİLET EDİTÖR)
    elif st.session_state['bimaks_sub_tab'] == 'SDS' and ("tech_sds" in perms or is_admin):
        st.subheader(_("Bayi SDS/TDS Oluşturucu", "Dealer SDS/TDS Generator", "Генератор SDS/TDS дилера", "منشئ SDS/TDS للوكيل", "Générateur FDS/FT du distributeur", "Generador HDS/HT del distribuidor"))
        doc_type = st.radio(_("Belge Türünü Seçin:", "Select Document Type:", "Выберите тип документа:", "حدد نوع المستند:", "Sélectionnez le type de document:", "Seleccione el tipo de documento:"), ["SDS", "TDS"], horizontal=True)
        st.info(_("Sisteme bir PDF yüklediğinizde sağ tarafta orijinal PDF'in canlı görüntüsü belirecektir. Sol taraftaki gelişmiş araçlarla yeni logonuzu, adresinizi ve gizleme maskelerini istediğiniz yere milimetrik olarak kaydırabilirsiniz.", "Live Preview and advanced positioning added.", "Предварительный просмотр.", "معاينة حية.", "Un aperçu en direct du PDF s'affichera à droite.", "Se mostrará una vista previa en vivo del PDF a la derecha."))
        
        st.markdown("""
            <style>
            div[data-testid="column"]:nth-of-type(2) {
                position: -webkit-sticky;
                position: sticky;
                top: 3rem;
                z-index: 10;
                align-self: flex-start;
            }
            </style>
        """, unsafe_allow_html=True)
        
        c_p1, c_p2 = st.columns([1, 1])
        
        with c_p1:
            sds_file = st.file_uploader(_(f"1. Orijinal {doc_type} (PDF)", f"1. Original {doc_type} (PDF)", f"1. Оригинальный {doc_type}", f"1. {doc_type} الأصلي", f"1. {doc_type} original (PDF)", f"1. {doc_type} original (PDF)"), type=['pdf'])
            d_logo = st.file_uploader(_("2. Bayi Logosu (PNG/JPG)", "2. Dealer Logo", "2. Логотип дилера", "2. شعار الوكيل", "2. Logo du distributeur", "2. Logo del distribuidor"), type=['png', 'jpg', 'jpeg'])
            
            auto_data = {}
            exact_replacements = []
            
            if doc_type == "SDS":
                # V 126.1 - ACİL TELEFON 16 MADDE
                with st.expander("🧠 Akıllı Belge Düzenleyici (SDS Otonom)", expanded=True):
                    st.caption("Sadece yeni değerleri girin. Sistem eski yazıları bulup hizalarını ve arka plan çizgilerini hiç bozmadan milimetrik olarak yenisiyle değiştirir. Eski değeri bilmenize gerek yoktur!")
                    
                    c_s1, c_s2 = st.columns(2)
                    
                    with c_s1:
                        new_prod = st.text_input("1. Yeni Ürün Adı", placeholder="Örn: YENİ ÜRÜN (Tüm sayfalarda değiştirir)")
                        new_cdate = st.text_input("2. Oluşturma Tarihi", placeholder="Örn: 15.06.2024")
                        new_rdate = st.text_input("3. Revizyon Tarihi", placeholder="Örn: 20.08.2025")
                        new_vers = st.text_input("4. Versiyon Numarası", placeholder="Örn: 01")
                        new_chem = st.text_input("5. Kimyasal Adı", placeholder="Örn: TEMİZLEYİCİ")
                        new_sup = st.text_input("6. Tedarikçi Firma", placeholder="Örn: YENİ FİRMA LTD. ŞTİ.")
                        new_add = st.text_area("7. Tedarikçi Adresi", placeholder="Örn: Yeni Mah. Sokak No:1\nİlçe / Şehir", height=68)
                        new_tel = st.text_input("8. Tedarikçi Telefonu", placeholder="Örn: 0 555 555 55 55")
                    
                    with c_s2:
                        new_fax = st.text_input("9. Tedarikçi Fax", placeholder="Örn: 0 212 123 45 67")
                        new_mail = st.text_input("10. Tedarikçi Email", placeholder="Örn: info@bayi.com")
                        new_web = st.text_input("11. Tedarikçi Web Adresi", placeholder="Örn: www.bayi.com")
                        new_emer = st.text_input("12. Acil Durum Telefonu", placeholder="Örn: 112")
                        new_contact = st.text_input("13. Başvurulacak Kişi (Tablo)", placeholder="Örn: ALİ VELİ")
                        new_gbf = st.text_input("14. GBF Yetkili Kişi (Son Sayfa)", placeholder="Örn: YENİ İSİM")
                        new_cert_date = st.text_input("15. Sertifika Geçerlilik Süresi", placeholder="Örn: 01.01.2028")
                        new_cert_no = st.text_input("16. Sertifika No", placeholder="Örn: YENİ-NO")

                    # Motora gönderilecek Lazer Kesim Komutları
                    auto_data = {
                        "ÜRÜN ADI": ("", new_prod),
                        "Oluşturma Tarihi:": (" ", new_cdate),
                        "Oluşturma Tarihi": (": ", new_cdate),
                        "Revizyon Tarihi:": (" ", new_rdate),
                        "Revizyon Tarihi": (": ", new_rdate),
                        "Versiyon:": (" ", new_vers),
                        "Versiyon": (": ", new_vers),
                        "KİMYASAL ADI": ("", new_chem),
                        "TEDARİKÇİ": ("", new_sup),
                        "ADDRESS": ("", new_add),
                        "Tel:": (" ", new_tel),
                        "Fax:": (" ", new_fax),
                        "E-mail:": (" ", new_mail),
                        "E-mail": (": ", new_mail),
                        "Web:": (" ", new_web),
                        "Web": (": ", new_web),
                        "BAŞVURULACAK KİŞİ": ("", new_contact),
                        "ACİL DURUM TELEFONU": ("", new_emer),
                        "ACİL DURUM TEL:": (" ", new_emer),
                        "ACİL DURUM TEL": ("", new_emer),
                        "ACİL DURUM TELEFON NUMARALARI:": (" ", new_emer),
                        "GBF Yetkili Kişi:": (" ", new_gbf),
                        "GBF Yetkili Kişi": (": ", new_gbf),
                        "Sertifika Geçerlilik Süresi:": (" ", new_cert_date),
                        "Sertifika Geçerlilik Süresi": (": ", new_cert_date),
                        "Sertifika No:": (" ", new_cert_no),
                        "Sertifika No": (": ", new_cert_no)
                    }

            elif doc_type == "TDS":
                with st.expander("🧠 TDS Akıllı Belge Düzenleyici (Lazer Tarama)", expanded=True):
                    st.caption("TDS belgelerinde 'Ürün Adı:' gibi sabit başlıklar olmadığından, değiştirmek istediğiniz eski kelimeleri tam olarak girmeniz gerekir. Sistem bu kelimeleri bulup TDS'in her yerinde yenisiyle değiştirecektir.")
                    
                    c_t1, c_t2 = st.columns(2)
                    with c_t1:
                        old_tds_prod = st.text_input("Eski Ürün Adı", value="MAKS 400PD")
                        old_tds_type = st.text_input("Eski Ürün Tipi", value="TERS OSMOZ ANTİSKALANTI")
                        old_tds_sup = st.text_input("Eski Tedarikçi", value="BİMAKS")
                        
                    with c_t2:
                        new_tds_prod = st.text_input("Yeni Ürün Adı", placeholder="Örn: YENİ ÜRÜN")
                        new_tds_type = st.text_input("Yeni Ürün Tipi", placeholder="Örn: YENİ ANTİSKALANT")
                        new_tds_sup = st.text_input("Yeni Tedarikçi", placeholder="Örn: YENİ FİRMA")
                        
                    if new_tds_prod: exact_replacements.append((old_tds_prod, new_tds_prod))
                    if new_tds_type: exact_replacements.append((old_tds_type, new_tds_type))
                    if new_tds_sup: exact_replacements.append((old_tds_sup, new_tds_sup))

            with st.expander("🛠️ Gelişmiş Konumlandırma Ayarları (Advanced Positioning)", expanded=False):
                st.caption("Logonun ve İsteğe Bağlı Beyaz Maskelerin yerini X ve Y olarak ayarlayın.")
                
                st.markdown("**1. Üst Beyaz Maske (Eski Logoyu Gizler)**")
                ct1, ct2, ct3, ct4 = st.columns(4)
                top_mask_x = ct1.slider("X (Sağ-Sol)", 0, 595, 357, key=f"{doc_type}_tm_x")
                top_mask_y = ct2.slider("Y (Yukarı-Aşağı)", 0, 300, 0, key=f"{doc_type}_tm_y")
                top_mask_w = ct3.slider("Genişlik", 0, 595, 595, key=f"{doc_type}_tm_w")
                top_mask_h = ct4.slider("Yükseklik", 0, 300, 46, key=f"{doc_type}_tm_h")
                
                st.markdown("**2. Alt Beyaz Maske (Kapatmak isterseniz)**")
                cb1, cb2, cb3, cb4 = st.columns(4)
                bot_mask_x = cb1.slider("X (Sağ-Sol)", 0, 595, 0, key=f"{doc_type}_bm_x")
                bot_mask_y = cb2.slider("Y (Yukarı-Aşağı)", 500, 842, 842, key=f"{doc_type}_bm_y")
                bot_mask_w = cb3.slider("Genişlik", 0, 595, 595, key=f"{doc_type}_bm_w")
                bot_mask_h = cb4.slider("Yükseklik", 0, 300, 0, key=f"{doc_type}_bm_h")
                
                st.markdown("**3. Yeni Logo Konumu**")
                c_l1, c_l2, c_l3 = st.columns(3)
                logo_x = c_l1.slider("Logo X (Sağ-Sol)", 0, 500, 386, key=f"{doc_type}_lx")
                logo_y = c_l2.slider("Logo Y (Yukarı-Aşağı)", 0, 300, 8, key=f"{doc_type}_ly")
                logo_w = c_l3.slider("Logo Büyüklüğü", 50, 400, 174, key=f"{doc_type}_lw")

            st.markdown("---")
            if st.button(_(f"✅ Onayla ve {doc_type} Oluştur", "Generate PDF", "Создать PDF", "إنشاء PDF", f"✅ Générer {doc_type}", f"✅ Generar {doc_type}"), type="primary"):
                logic.ping_online(st.session_state['current_user'])
                if sds_file:
                    with st.spinner(f"{doc_type} Maskeleniyor ve Oluşturuluyor..."):
                        pdf_out = logic.create_dealer_pdf(
                            sds_file.getvalue(), 
                            d_logo.getvalue() if d_logo else None, 
                            None, 
                            top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                            bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                            logo_x, logo_y, logo_w, 0, 0, 
                            st.session_state['lang'],
                            auto_data,
                            exact_replacements
                        )
                        if pdf_out:
                            st.success(f"İşlem Başarılı! {doc_type} bütün sayfalara uygulandı.")
                            st.download_button(_("İndir", "Download", "Скачать", "تحميل", "Télécharger", "Descargar"), data=pdf_out, file_name=f"Bayi_{doc_type}.pdf", mime="application/pdf")
                        else:
                            st.error("HATA: PDF işlenemedi. Orijinal belgede bir sorun olabilir.")
                else:
                    st.warning(f"Lütfen orijinal {doc_type} dosyasını yükleyin.")
                    
        with c_p2:
            st.markdown(_(f"**👀 Canlı Önizleme (Yüklediğiniz {doc_type})**", "**👀 Live Preview**", "**👀 Предварительный просмотр**", "**👀 معاينة حية**", f"**👀 Aperçu en direct ({doc_type})**", f"**👀 Vista previa en vivo ({doc_type})**"))
            
            preview_img = logic.generate_sds_preview(
                sds_file.getvalue() if sds_file else None,
                d_logo.getvalue() if d_logo else None, 
                None, 
                top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                logo_x, logo_y, logo_w, 0, 0,
                auto_data,
                exact_replacements
            )
            st.image(preview_img, caption=f"Sanal A4 Önizlemesi ({doc_type} Belgeniz)", use_container_width=True)

# 2. LINKEDIN
elif st.session_state.get('active_tab') == t('btn_linkedin') and not st.session_state.get('show_settings'):
    with st.expander(t('step1_linkedin_title'), expanded=False):
        ui_personas = logic.get_persona_list_for_ui()
        sel_p = st.selectbox(t('sys_select'), ui_personas, index=0, key="li_p")
        role_c = st.text_input(t('sys_manual'), key="li_m") if sel_p == t('sys_manual') else sel_p
        
        m_topic = st.text_input(t('topic'), placeholder=_("Konu...", "Topic...", "Тема...", "الموضوع...", "Sujet...", "Tema..."))
        t_aud = st.text_input(t('target_audience'), t('target_def'))
        t_plat = st.text_input(t('target_plat'), t('plat_def'))
        
        p_ref = st.text_input(t('prod_ref'), placeholder=_("Örn: BİMAKS Atık Su Kimyasalları", "e.g., BIMAKS Waste Water Chemicals", "напр., Химикаты BIMAKS", "مثال: بيمكس للمواد الكيميائية", "ex. Produits chimiques pour eaux usées", "ej. Productos químicos para aguas residuales"))
        p_link = st.text_input(t('prod_link_lbl'), placeholder=_("Örn: https://www.bimaks...", "e.g., https://www.bimaks...", "напр., https://www.bimaks...", "مثال: https://www.bimaks...", "ex. https://www.bimaks...", "ej. https://www.bimaks...")) 
        
        c_lim = st.number_input(t('prompt_limit'), 500, 10000, 3000, 100)
        
        if st.button(t('btn_create'), type="primary"):
            logic.ping_online(st.session_state['current_user'])
            clean_prod = None if not p_ref or p_ref.strip() == "" else p_ref
            
            prompt = logic.construct_prompt_text(role_c, m_topic, t_aud, t_plat, clean_prod, c_lim, st.session_state.get('lang', 'TR'), p_link)
            
            with st.spinner(_("AI Yazıyor...", "AI is writing...", "ИИ пишет...", "الذكاء الاصطناعي يكتب...", "L'IA écrit...", "La IA está escribiendo...")):
                res = logic.get_gemini_response_from_manual(prompt, st.session_state['settings_db']["genai_key"])
                if "HATA" in res or "ERROR" in res: st.error(res)
                else:
                    cleaned_res = logic.force_clean_text(res)
                    
                    if len(cleaned_res) > c_lim:
                        w_tr = f"⚠️ SİSTEM UYARISI: Üretilen metin ({len(cleaned_res)} karakter) sınırınızı ({c_lim}) aştı. Kesilmedi, aşağıdan düzenleyebilirsiniz."
                        w_en = f"⚠️ WARNING: Generated text ({len(cleaned_res)} chars) exceeded limit ({c_lim}). It was NOT cut, edit below."
                        w_ru = f"⚠️ ВНИМАНИЕ: Текст ({len(cleaned_res)} симв.) превысил лимит ({c_lim}). Он не был обрезан."
                        w_ar = f"⚠️ تحذير: النص ({len(cleaned_res)} حرف) تجاوز الحد ({c_lim}). لم يتم قصه."
                        w_fr = f"⚠️ AVERTISSEMENT : Le texte généré ({len(cleaned_res)} caractères) a dépassé la limite ({c_lim}). Il n'a PAS été coupé."
                        w_es = f"⚠️ ADVERTENCIA: El texto generado ({len(cleaned_res)} caracteres) superó el límite ({c_lim}). NO fue cortado."
                        st.session_state['linkedin_warning'] = _(w_tr, w_en, w_ru, w_ar, w_fr, w_es)
                    else:
                        st.session_state['linkedin_warning'] = ""
                        
                    yeni_makale = logic.smart_trim(cleaned_res, c_lim)
                    st.session_state['linkedin_editor'] = yeni_makale
                    st.session_state['linkedin_editor_area'] = yeni_makale 
                        
                    st.rerun()

    if st.session_state.get('linkedin_editor'):
        c1, c2 = st.columns(2)
        with c1: 
            st.subheader(t('editor'))
            if st.session_state.get('linkedin_warning'):
                st.warning(st.session_state['linkedin_warning'])
                
            val = st.text_area("", value=st.session_state['linkedin_editor'], height=600, key="linkedin_editor_area")
            st.caption(f"📊 {t('char_count')} {len(val)}") 
            
        with c2:
            st.subheader(t('visual')); up = st.file_uploader(_("Medya", "Media", "Медиа", "وسائط", "Médias", "Medios"), type=['jpg','png','mp4','mov'], key="li_up")
            if up:
                if "image" in up.type: st.image(up, use_container_width=True)
                else: st.video(up)
            st.markdown("---")
            if st.button(t('publish'), type="primary"): 
                logic.ping_online(st.session_state['current_user'])
                r = logic.post_to_linkedin_real(val, up.getvalue() if up else None, up.type if up else "", st.session_state['settings_db']["linkedin_token"])
                if "✅" in r: logic.save_history_entry(m_topic, role_c); st.balloons(); st.success(r)
                else: st.error(r)
    
    with st.expander("📜 History"):
        if not st.session_state['history_db']: st.caption(_("Kayıt yok.", "No records.", "Нет записей.", "لا توجد سجلات.", "Aucun enregistrement.", "Sin registros."))
        else: [st.text(f"{h['date']} | {h['topic']} | {h['role']}") for h in st.session_state['history_db']]

# 3. INSTAGRAM
elif st.session_state.get('active_tab') == t('btn_instagram') and not st.session_state.get('show_settings'):
    if not st.session_state['settings_db'].get("genai_key"): st.warning(f"⚠️ {t('guide_title_main')}"); st.rerun()
    with st.expander(t('step1_linkedin_title'), expanded=False):
        ui_personas = logic.get_persona_list_for_ui()
        sel_p = st.selectbox(t('sys_select'), ui_personas, key="in_p")
        role_c = st.text_input(t('sys_manual'), key="in_m") if sel_p == t('sys_manual') else sel_p
        m_topic = st.text_input(t('topic'), placeholder=_("Konuyu yazın...", "Write the topic...", "Напишите тему...", "اكتب الموضوع...", "Écrivez le sujet...", "Escribe el tema..."))
        c_lim = st.number_input(t('prompt_limit'), 500, 2200, 2000, 100, key="in_l")
        
        if st.button(t('btn_create'), type="primary", key="in_btn"):
            logic.ping_online(st.session_state['current_user'])
            st.session_state['draft_prompt'] = logic.construct_prompt_text(role_c, m_topic, "Followers", "Instagram", None, c_lim, st.session_state['lang'])
            with st.spinner(_("AI Yazıyor...", "AI is writing...", "ИИ пишет...", "الذكاء الاصطناعي يكتب...", "L'IA écrit...", "La IA está escribiendo...")):
                res = logic.get_gemini_response_from_manual(st.session_state['draft_prompt'], st.session_state['settings_db']["genai_key"])
                if "HATA" in res or "ERROR" in res: st.error(res)
                else: 
                    cleaned_res = logic.force_clean_text(res)
                    if len(cleaned_res) > c_lim:
                        w_tr = f"⚠️ SİSTEM UYARISI: Metin ({len(cleaned_res)} karakter) sınırı aştı."
                        w_en = f"⚠️ WARNING: Text ({len(cleaned_res)} chars) exceeded limit."
                        w_ru = f"⚠️ ВНИМАНИЕ: Текст ({len(cleaned_res)} симв.) превысил лимит."
                        w_ar = f"⚠️ تحذير: النص ({len(cleaned_res)} حرف) تجاوز الحد."
                        w_fr = f"⚠️ AVERTISSEMENT : Le texte généré ({len(cleaned_res)} caractères) a dépassé la limite."
                        w_es = f"⚠️ ADVERTENCIA: El texto generado ({len(cleaned_res)} caracteres) superó el límite."
                        st.session_state['insta_warning'] = _(w_tr, w_en, w_ru, w_ar, w_fr, w_es)
                    else:
                        st.session_state['insta_warning'] = ""
                        
                    yeni_makale = logic.smart_trim(cleaned_res, c_lim)
                    st.session_state['insta_editor'] = yeni_makale
                    st.session_state['insta_editor_area'] = yeni_makale
                    st.rerun()

    col1, col2 = st.columns([1, 1])
    with col1: 
        st.subheader(t('editor'))
        if st.session_state.get('insta_warning'):
            st.warning(st.session_state['insta_warning'])
        st.text_area(_("İçerik:", "Caption:", "Подпись:", "التسمية التوضيحية:", "Légende:", "Leyenda:"), value=st.session_state.get('insta_editor', ''), height=300, key="insta_editor_area")
            
    with col2:
        st.subheader(t('visual')); uploaded_file = st.file_uploader(_("Resim Yükle", "Upload Image", "Загрузить изображение", "تحميل الصورة", "Télécharger l'image", "Subir imagen"), type=['jpg', 'png'])
        if uploaded_file: im = Image.open(uploaded_file).convert("RGB"); im = logic.resize_for_instagram(im); st.session_state['original_image'] = im
        if 'original_image' in st.session_state:
            with st.expander(_("🏷️ Etiketle", "🏷️ Tagging", "🏷️ Теги", "🏷️ وسم", "🏷️ Étiqueter", "🏷️ Etiquetar"), expanded=True):
                tag_color = st.color_picker(_("Etiket Rengi", "Tag Color", "Цвет тега", "لون العلامة", "Couleur de l'étiquette", "Color de etiqueta"), "#FFFF00")
                tag_u = st.text_input(_("Kullanıcı Adı", "Username", "Имя пользователя", "اسم المستخدم", "Nom d'utilisateur", "Nombre de usuario"))
                t_x, t_y = st.slider(_("X Konumu", "X Pos", "Позиция X", "موضع X", "Pos X", "Pos X"), 0, 100, 50), st.slider(_("Y Konumu", "Y Pos", "Позиция Y", "موضع Y", "Pos Y", "Pos Y"), 0, 100, 50)
                if st.button(_("Ekle", "Add", "Добавить", "إضافة", "Ajouter", "Añadir")): st.session_state['insta_tags_list'].append({'u': tag_u, 'x': t_x/100, 'y': t_y/100, 'c': tag_color}); st.rerun()
            preview_img = st.session_state['original_image'].copy(); draw = ImageDraw.Draw(preview_img); w, h = preview_img.size
            for t_tag in st.session_state['insta_tags_list']: draw.text((t_tag['x']*w, t_tag['y']*h), f"@{t_tag['u']}", fill=t_tag.get('c', '#FFFF00'))
            if tag_u: draw.text((t_x/100*w, t_y/100*h), f"@{tag_u}", fill=tag_color)
            st.image(preview_img, caption=_("Önizleme (Canlı)", "Live Preview", "Предпросмотр", "معاينة حية", "Aperçu (en direct)", "Vista previa (en vivo)"), use_container_width=True)
            if st.button(t('publish_insta'), type="primary"): logic.ping_online(st.session_state['current_user']); st.warning("⚠️ Web API Simulasyon Modundadır.")

# 4. ADMIN PANELİ
elif st.session_state.get('active_tab') == 'Admin Paneli' and is_admin:
    st.header("👑 Admin Yönetim Paneli")
    
    st.subheader("🔒 Rol ve Yetki Yönetimi")
    role_defs = logic.get_role_definitions()
    
    sel_role = st.selectbox("Yetkilerini Düzenle:", ["Bimaks Üye", "Yeni Üye", "Admin"])
    curr_perms = role_defs.get(sel_role, "")
    
    st.markdown(f"**{sel_role}** rolü için erişim izinleri:")
    c1, c2 = st.columns(2)
    p_smy = c1.checkbox("Sosyal Medya Yönetimi (Ana Menü)", value="smy" in curr_perms)
    p_smy_li = c1.checkbox("↳ LinkedIn", value="smy_li" in curr_perms)
    p_smy_in = c1.checkbox("↳ Instagram", value="smy_in" in curr_perms)
    
    p_tech = c2.checkbox("BİMAKS TEKNİK (Ana Menü)", value="tech" in curr_perms)
    p_tech_an = c2.checkbox("↳ Sistem Analizi", value="tech_an" in curr_perms)
    p_tech_roi = c2.checkbox("↳ ROI", value="tech_roi" in curr_perms)
    p_tech_ocr = c2.checkbox("↳ OCR Analiz", value="tech_ocr" in curr_perms)
    p_tech_reg = c2.checkbox("↳ Global Mevzuat", value="tech_reg" in curr_perms)
    p_tech_quo = c2.checkbox("↳ Teklif Oluştur", value="tech_quo" in curr_perms)
    p_tech_sds = c2.checkbox("↳ SDS/TDS", value="tech_sds" in curr_perms)
    
    if st.button(f"💾 {sel_role} Yetkilerini Kaydet", type="primary"):
        new_perms = []
        if p_smy: new_perms.append("smy")
        if p_smy_li: new_perms.append("smy_li")
        if p_smy_in: new_perms.append("smy_in")
        if p_tech: new_perms.append("tech")
        if p_tech_an: new_perms.append("tech_an")
        if p_tech_roi: new_perms.append("tech_roi")
        if p_tech_ocr: new_perms.append("tech_ocr")
        if p_tech_reg: new_perms.append("tech_reg")
        if p_tech_quo: new_perms.append("tech_quo")
        if p_tech_sds: new_perms.append("tech_sds")
        
        role_defs[sel_role] = ",".join(new_perms)
        logic.update_role_definitions(role_defs["Admin"], role_defs["Bimaks Üye"], role_defs["Yeni Üye"])
        st.success("Yetkiler başarıyla güncellendi! Bu role sahip tüm kullanıcıların erişimleri anında değişti.")
        if st.session_state['role'] == sel_role:
            st.session_state['permissions'] = role_defs[sel_role]
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    st.subheader("👥 Kullanıcı Listesi")
    users_data = logic.get_all_users_status()
    if users_data:
        c_h1, c_h2, c_h3, c_h4 = st.columns([3, 3, 3, 2])
        c_h1.markdown("**Kullanıcı**")
        c_h2.markdown("**Son Giriş**")
        c_h3.markdown("**Rol**")
        c_h4.markdown("**İşlem**")
        st.markdown("---")
        
        for u in users_data:
            cu1, cu2, cu3, cu4, cu5 = st.columns([3, 3, 2, 1, 1])
            cu1.code(u['username'])
            cu2.caption(u['last_seen'])
            
            role_options = ["Yeni Üye", "Bimaks Üye", "Admin"]
            idx = role_options.index(u['role']) if u['role'] in role_options else 0
            selected_r = cu3.selectbox("Rol", role_options, index=idx, key=f"sel_r_{u['username']}", label_visibility="collapsed")
            
            if cu4.button("💾", key=f"sv_{u['username']}", help="Rolü Kaydet"):
                with st.spinner("..."):
                    if logic.update_user_role(u['username'], selected_r):
                        st.success("✔")
                    else: st.error("X")
                    
            if cu5.button("🗑️", key=f"dl_{u['username']}", help="Kullanıcıyı Sil"):
                if u['username'] == st.session_state['current_user']:
                    st.error("!")
                else:
                    logic.delete_user(u['username'])
                    st.rerun()
    else:
        st.info("Sistem bilgileri yükleniyor... Lütfen bekleyin veya sayfayı yenileyin.")
        
    st.markdown("---")
    with st.expander("➕ Yeni Kullanıcı Ekle"):
        n_u = st.text_input("Kullanıcı Adı", key="admin_add_u")
        n_p = st.text_input("Şifre", key="admin_add_p")
        n_r = st.selectbox("Kullanıcı Rolü", ["Yeni Üye", "Bimaks Üye", "Admin"], key="admin_add_r")
        if st.button("Hesap Oluştur", type="primary"):
            if len(n_u) < 3 or len(n_p) < 3:
                st.warning("Kullanıcı adı ve şifre en az 3 karakter olmalı.")
            else:
                with st.spinner("Ekleniyor..."):
                    s, m = logic.register_user(n_u, n_p, n_r)
                    if s: st.success(f"'{n_u}' başarıyla oluşturuldu!"); time.sleep(1); st.rerun()
                    else: st.error(m)

# 5. KİŞİSEL AYARLAR (Tüm Üyeler İçin)
elif st.session_state.get('show_settings'):
    st.header(t('settings_title'))
    c1, c2 = st.columns(2)
    
    with c1:
        if is_admin:
            st.subheader(t('set_role_mgmt'))
            np = st.text_input(t('set_add_role'))
            if st.button(_("Ekle", "Add", "Добавить", "إضافة", "Ajouter", "Añadir")): 
                st.session_state['personas_db'].append({"TR": np, "EN": np, "RU": np, "AR": np, "FR": np, "ES": np}); st.rerun()
            dp = st.selectbox(t('set_del_role'), logic.get_persona_list_for_ui())
            if st.button(_("Sil", "Delete", "Удалить", "حذف", "Supprimer", "Eliminar")): 
                st.session_state['personas_db'] = [p for p in st.session_state['personas_db'] if p.get(st.session_state['lang']) != dp]; st.rerun()
            
            st.markdown("---")
            st.subheader(t('set_logo'))
            ul = st.file_uploader(t('set_logo_btn'), type=['png', 'jpg', 'jpeg'])
            if ul: st.session_state['logo_data'] = ul.getvalue(); st.success(_("Logo Güncellendi!", "Logo Updated!", "Логотип обновлен!", "تم تحديث الشعار!", "Logo mis à jour !", "¡Logo actualizado!"))
            
            st.markdown("---")
            st.subheader(t('set_theme'))
            nbg = st.color_picker(t('set_bg'), st.session_state['settings_db'].get("theme_bg"))
            ntxt = st.color_picker(t('set_txt'), st.session_state['settings_db'].get("theme_txt"))
            nbtn = st.color_picker(t('set_btn'), st.session_state['settings_db'].get("theme_btn"))
            
            st.markdown("---")
            nt = st.text_input(_("Başlık", "Title", "Заголовок", "عنوان", "Titre", "Título"), st.session_state['settings_db'].get("app_title"))
            nf = st.text_input(_("Alt Bilgi", "Footer", "Нижний колонтитул", "تذييل", "Pied de page", "Pie de página"), st.session_state['settings_db'].get("app_footer"))
            st.markdown(f"**{t('set_modules')}**")
            se = st.checkbox(_("Sosyal Medya", "Social Media", "Соцсети", "وسائل التواصل الاجتماعي", "Médias sociaux", "Redes sociales"), st.session_state['settings_db'].get("enable_social_media"))
            li = st.checkbox(" > LinkedIn", st.session_state['settings_db'].get("enable_linkedin"))
            ins = st.checkbox(" > Instagram", st.session_state['settings_db'].get("enable_instagram"))
            pe = st.checkbox(_("Problem Çözücü", "Problem Solver", "Решатель проблем", "حل المشكلات", "Résolveur de problèmes", "Solucionador de problemas"), st.session_state['settings_db'].get("enable_problem_solver"))
            sds_cb = st.checkbox(" > Bayi SDS/TDS", st.session_state['settings_db'].get("enable_dealer_sds", False))
            qe = st.checkbox(_("Teklif", "Quote", "Коммерческое предложение", "اقتباس", "Devis", "Cotización"), st.session_state['settings_db'].get("enable_quote"))
            
            if st.button(_("Tema Kaydet", "Save Theme", "Сохранить тему", "حفظ السمة", "Enregistrer le thème", "Guardar tema")): 
                st.session_state['settings_db'].update({
                    "app_title": nt, "app_footer": nf, "enable_social_media": se, 
                    "enable_linkedin": li, "enable_instagram": ins, "enable_problem_solver": pe, 
                    "enable_dealer_sds": sds_cb, "enable_quote": qe, "theme_bg": nbg, "theme_txt": ntxt, "theme_btn": nbtn
                })
                st.success("Tema güncellendi!"); time.sleep(1); st.rerun()
        else:
            st.info("Tema ve Sistem ayarları sadece Adminler içindir.")
                
    with c2:
        st.subheader(_("Kişisel API Ayarların", "Personal API Settings", "Ваши настройки API", "إعدادات API الشخصية", "Paramètres d'API personnels", "Configuración personal de API"))
        st.info(_("Buraya girdiğiniz anahtarlar veritabanında güvenle sadece sizin hesabınıza kaydedilir.", "Keys entered here are securely saved to your account in the DB.", "Эти ключи сохраняются в БД только для вашего аккаунта.", "يتم حفظ هذه المفاتيح في قاعدة البيانات لحسابك فقط.", "Les clés saisies ici sont enregistrées en toute sécurité.", "Las claves ingresadas aquí se guardan de forma segura."))
        
        k1 = st.text_input("Gemini API", st.session_state['settings_db'].get("genai_key", ""), type="password")
        k2 = st.text_input("LinkedIn Token", st.session_state['settings_db'].get("linkedin_token", ""), type="password")
        k3 = st.text_input("Instagram Token", st.session_state['settings_db'].get("instagram_token", ""), type="password")
        k4 = st.text_input("Instagram Account ID", st.session_state['settings_db'].get("instagram_account_id", ""))
        
        if st.button(t('set_save'), type="primary"):
            st.session_state['settings_db'].update({"genai_key": k1, "linkedin_token": k2, "instagram_token": k3, "instagram_account_id": k4})
            
            with st.spinner("Veritabanına kaydediliyor..."):
                is_saved = logic.update_user_keys(st.session_state['current_user'], k1, k2, k3, k4)
                if is_saved:
                    st.success(_("Veritabanına Kaydedildi!", "Saved to DB!", "Сохранено в БД!", "تم الحفظ в قاعدة البيانات!", "Enregistré dans la BD !", "¡Guardado en la BD!"))
                else:
                    st.error("Veritabanına kaydedilirken bir hata oluştu.")
            time.sleep(1); st.rerun()
    
    st.markdown("---")
    with st.expander(t('guide_btn'), expanded=True):
        st.info(t('guide_gemini_title')); st.markdown(t('guide_gemini_text'))
        st.warning(t('guide_linkedin_title')); st.markdown(t('guide_linkedin_text'))
        st.error(t('guide_instagram_title')); st.markdown(t('guide_instagram_text'))
    if st.button(t('back_btn'), type="secondary"): st.session_state['show_settings'] = False; st.rerun()
