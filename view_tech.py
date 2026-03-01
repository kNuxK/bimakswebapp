import streamlit as st
import config
import db_engine
import math_engine
import ai_engine
import pdf_engine
import os

def t(key): return config.LANGUAGES.get(st.session_state.get('lang', 'TR'), config.LANGUAGES['TR']).get(key, key)
def _(tr, en, ru, ar, fr, es):
    l = st.session_state.get('lang', 'TR')
    if l == 'EN': return en
    if l == 'RU': return ru
    if l == 'AR': return ar
    if l == 'FR': return fr
    if l == 'ES': return es
    return tr

def render():
    perms = str(st.session_state.get('permissions', ''))
    is_admin = str(st.session_state.get('role', '')).lower() == 'admin'

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
    if "tech_sds_gen" in perms or is_admin: nav_tabs.append(_("Sıfırdan SDS/TDS Üretici", "SDS/TDS Generator", "Генератор SDS/TDS", "منشئ SDS/TDS", "Générateur FDS/FT", "Generador HDS/HT")); tab_keys.append('SDS_Gen')
    
    if not nav_tabs:
        st.warning("Bu modülün hiçbir alt başlığına yetkiniz bulunmamaktadır.")
        st.stop()
        
    if st.session_state.get('bimaks_sub_tab') not in tab_keys:
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
            db_engine.ping_online(st.session_state['current_user'])
            lsi_val, rsi_val = math_engine.calculate_lsi(sy_ph, sy_tds, sy_temp, sy_ca, sy_alk)
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
                res = ai_engine.get_gemini_response_from_manual(p_solver, st.session_state['settings_db']["genai_key"])
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
            db_engine.ping_online(st.session_state['current_user'])
            res = math_engine.calculate_advanced_roi(bd, hours, coc_curr, coc_targ, cost_w, cost_e, scale, cost_c)
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
            db_engine.ping_online(st.session_state['current_user'])
            lang_name = config.LANGUAGES.get(st.session_state['lang'], config.LANGUAGES['TR'])['name']
            ocr_prompt = f"""
            ACT AS: Senior Water Treatment Engineer.
            MISSION: Read, analyze and interpret this water analysis report. Point out any critical out-of-spec values and suggest corrective actions.
            CRITICAL LANGUAGE RULE: TRANSLATE YOUR THOUGHTS AND WRITE YOUR ENTIRE RESPONSE STRICTLY AND NATIVELY IN {lang_name.upper()}.
            """
            with st.spinner(_("Okunuyor...", "Reading...", "Чтение...", "قراءة...", "Lecture en cours...", "Leyendo...")):
                res = ai_engine.analyze_image_with_gemini(ocr_file.getvalue(), ocr_prompt, st.session_state['settings_db']["genai_key"])
                st.markdown(res)

    # D. Mevzuat
    elif st.session_state['bimaks_sub_tab'] == 'REG':
        st.subheader(t('reg_title')); q_reg = st.text_input(_("Soru:", "Question:", "Вопрос:", "سؤال:", "Question:", "Pregunta:"), placeholder=t('reg_ph'))
        if st.button(_("Araştır", "Search", "Поиск", "بحث", "Rechercher", "Buscar")):
            db_engine.ping_online(st.session_state['current_user'])
            lang_name = config.LANGUAGES.get(st.session_state['lang'], config.LANGUAGES['TR'])['name']
            reg_prompt = f"ACT AS: Regulatory Expert. QUESTION: {q_reg}. CRITICAL LANGUAGE RULE: YOU MUST WRITE YOUR ENTIRE RESPONSE STRICTLY IN {lang_name.upper()}."
            res = ai_engine.get_gemini_response_from_manual(reg_prompt, st.session_state['settings_db']["genai_key"])
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
                db_engine.ping_online(st.session_state['current_user'])
                pdf = pdf_engine.create_pdf(qi, qs, qp, qpy, qb, st.session_state['quote_items'], qc, q_show_total, q_note, st.session_state['lang'])
                st.download_button(_("İndir", "Download", "Скачать", "تحميل", "Télécharger", "Descargar"), data=pdf, file_name="Teklif.pdf", mime="application/pdf")

    # F. BAYİ SDS/TDS ÜRETİCİ
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
                        old_tds_phone = st.text_input("Eski Telefon", value="0 850 522 71 04")
                        
                    with c_t2:
                        new_tds_prod = st.text_input("Yeni Ürün Adı", placeholder="Örn: YENİ ÜRÜN")
                        new_tds_type = st.text_input("Yeni Ürün Tipi", placeholder="Örn: YENİ ANTİSKALANT")
                        new_tds_sup = st.text_input("Yeni Tedarikçi", placeholder="Örn: YENİ FİRMA")
                        new_tds_phone = st.text_input("Yeni Telefon", placeholder="Örn: 0 555 555 55 55")
                        
                    new_tds_add = st.text_area("Tedarikçi Adresi (Tüm Sayfaların Altına)", placeholder="Örn: Yeni Mah. Sokak No:1\nİlçe / Şehir", height=68)
                        
                    if new_tds_prod: exact_replacements.append((old_tds_prod, new_tds_prod, True, True))
                    if new_tds_type: exact_replacements.append((old_tds_type, new_tds_type, True, True))
                    if new_tds_sup: exact_replacements.append((old_tds_sup, new_tds_sup, True, False))
                    if new_tds_phone: exact_replacements.append((old_tds_phone, new_tds_phone, True, False))

            with st.expander("🛠️ Gelişmiş Konumlandırma Ayarları (Advanced Positioning)", expanded=False):
                st.caption("Logonun, Adresin ve İsteğe Bağlı Beyaz Maskelerin yerini X ve Y olarak ayarlayın.")
                
                st.markdown("**1. Üst Beyaz Maske (Eski Logoyu Gizler)**")
                ct1, ct2, ct3, ct4 = st.columns(4)
                top_mask_x = ct1.slider("X (Sağ-Sol)", 0, 595, 357, key=f"{doc_type}_tm_x")
                top_mask_y = ct2.slider("Y (Yukarı-Aşağı)", 0, 300, 0, key=f"{doc_type}_tm_y")
                top_mask_w = ct3.slider("Genişlik", 0, 595, 595, key=f"{doc_type}_tm_w")
                top_mask_h = ct4.slider("Yükseklik", 0, 300, 46, key=f"{doc_type}_tm_h")
                
                st.markdown("**2. Alt Beyaz Maske (Kapatmak isterseniz)**")
                cb1, cb2, cb3, cb4 = st.columns(4)
                bot_mask_x = cb1.slider("X (Sağ-Sol)", 0, 595, 0, key=f"{doc_type}_bm_x")
                bot_mask_y = cb2.slider("Y (Yukarı-Aşağı)", 500, 842, 786, key=f"{doc_type}_bm_y")
                bot_mask_w = cb3.slider("Genişlik", 0, 595, 595, key=f"{doc_type}_bm_w")
                bot_mask_h = cb4.slider("Yükseklik", 0, 300, 56, key=f"{doc_type}_bm_h")
                
                st.markdown("**3. Yeni Logo Konumu**")
                c_l1, c_l2, c_l3 = st.columns(3)
                logo_x = c_l1.slider("Logo X (Sağ-Sol)", 0, 500, 386, key=f"{doc_type}_lx")
                logo_y = c_l2.slider("Logo Y (Yukarı-Aşağı)", 0, 300, 8, key=f"{doc_type}_ly")
                logo_w = c_l3.slider("Logo Büyüklüğü", 50, 400, 174, key=f"{doc_type}_lw")

                st.markdown("**4. Alt Bilgi / Adres Konumu (Tüm Sayfalar İçin)**")
                c_a1, c_a2 = st.columns(2)
                addr_x = c_a1.slider("Adres X (Sağ-Sol)", 0, 500, 80, key=f"{doc_type}_ax")
                addr_y = c_a2.slider("Adres Y (Yukarı-Aşağı)", 500, 842, 800, key=f"{doc_type}_ay")

            st.markdown("---")
            
            current_addr = None
            if doc_type == "SDS":
                try: current_addr = new_add
                except: current_addr = None
            else:
                try: current_addr = new_tds_add
                except: current_addr = None
                
            if st.button(_(f"✅ Onayla ve {doc_type} Oluştur", "Generate PDF", "Создать PDF", "إنشاء PDF", f"✅ Générer {doc_type}", f"✅ Generar {doc_type}"), type="primary"):
                db_engine.ping_online(st.session_state['current_user'])
                if sds_file:
                    with st.spinner(f"{doc_type} Maskeleniyor ve Oluşturuluyor..."):
                        pdf_out = pdf_engine.create_dealer_pdf(
                            sds_file.getvalue(), 
                            d_logo.getvalue() if d_logo else None, 
                            current_addr, 
                            top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                            bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                            logo_x, logo_y, logo_w, addr_x, addr_y, 
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
            
            preview_img = pdf_engine.generate_sds_preview(
                sds_file.getvalue() if sds_file else None,
                d_logo.getvalue() if d_logo else None, 
                current_addr, 
                top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                logo_x, logo_y, logo_w, addr_x, addr_y,
                auto_data,
                exact_replacements
            )
            st.image(preview_img, caption=f"Sanal A4 Önizlemesi ({doc_type} Belgeniz)", use_container_width=True)

    # G. SIFIRDAN SDS/TDS ÜRETİCİ (V 134.0 - DİNAMİK FORM YAPISI)
    elif st.session_state['bimaks_sub_tab'] == 'SDS_Gen' and ("tech_sds_gen" in perms or is_admin):
        st.subheader(_("Sıfırdan SDS/TDS Formülasyon Motoru (AI)", "SDS/TDS Formulation Engine (AI)", "Механизм формулирования SDS/TDS (ИИ)", "محرك صياغة SDS/TDS (الذكاء الاصطناعي)", "Moteur de formulation FDS/FT (IA)", "Motor de formulación HDS/HT (IA)"))
        st.info(_("Bu modül, girdiğiniz bilgilere dayanarak uluslararası standartlarda tam teşekküllü bir Güvenlik Bilgi Formu veya TDS oluşturur. Her sayfaya logo ve adres basarak PDF üretir.", "Generates 16-section SDS based on raw materials.", "Создает SDS на основе сырья.", "يولد SDS بناءً على المواد الخام.", "Génère une FDS basée sur les matières premières.", "Genera HDS basado en materias primas."))
        
        c_top1, c_top2 = st.columns(2)
        with c_top1:
            doc_choice = st.radio("Belge Türü / Document Type", ["SDS (Güvenlik Bilgi Formu)", "TDS (Teknik Veri Bülteni)"], horizontal=True)
        with c_top2:
            lang_options = list(config.LANGUAGES.keys())
            current_lang = st.session_state.get('lang', 'TR')
            default_index = lang_options.index(current_lang) if current_lang in lang_options else 0
            gen_doc_lang = st.selectbox("Belge Dili / Document Language", lang_options, index=default_index, format_func=lambda x: config.LANGUAGES[x]['name'])
            
        st.markdown("### Belge ve Tedarikçi Detayları")
        c_g3, c_g4 = st.columns(2)
        with c_g3:
            gen_prod_name = st.text_input("Ürün Adı", placeholder="Örn: MAKS 400PD")
            if "SDS" in doc_choice:
                gen_prod_type = st.text_input("Kullanım Amacı / Ürün Tipi", placeholder="Örn: Ters Osmoz Antiskalantı")
            else:
                gen_prod_type = st.text_input("Ürün Tanımı / Kategori", placeholder="Örn: Yüksek Performanslı Polimerik Antiskalant")
                
            gen_cdate = st.text_input("Oluşturma Tarihi", placeholder="Örn: 15.06.2024")
            gen_rdate = st.text_input("Revizyon Tarihi", placeholder="Örn: 20.08.2025")
            gen_vers = st.text_input("Versiyon", placeholder="Örn: 01")
            gen_logo = st.file_uploader("Firma Logosu (PDF Sağ Üst Köşesi İçin)", type=['png', 'jpg', 'jpeg'], key="gen_logo_upl")
        with c_g4:
            gen_sup_name = st.text_input("Üretici/Tedarikçi (Firma Adı)", placeholder="Örn: BİMAKS KİMYA")
            gen_sup_tel = st.text_input("Telefon Numarası", placeholder="Örn: 0 850 522 71 04")
            gen_sup_fax = st.text_input("Faks Numarası", placeholder="Örn: 0 216 321 32 13")
            gen_sup_mail = st.text_input("E-posta", placeholder="Örn: info@bimakskimya.com")
            gen_sup_addr = st.text_input("Şirket Adresi", placeholder="Örn: Fatih Sultan Mehmet Mah...")
            gen_footer = st.text_area("Alt Bilgi (Tüm Sayfaların Altına Basılır)", placeholder="Örn: Fatih Sultan Mehmet Mah...\nTel: 0555...\nWeb: www...", height=68)

        st.markdown("### İçerik ve Formülasyon")
        # V 134.0: DİNAMİK REÇETE KUTUSU
        if "SDS" in doc_choice:
            gen_ingredients = st.text_area("Bileşenler ve Yüzdeleri (Tam Reçete - Zorunlu)", placeholder="Örn: %10 Sodyum Hidroksit (CAS: 1310-73-2)\n%5 Fosfonat\n%85 Su", height=100)
        else:
            gen_ingredients = st.text_area("Kimyasal Yapı / Temel Etken Maddeler", placeholder="Örn: Polikarboksilat bazlı kireç önleyici polimer karışımı. (Reçete vermek zorunlu değildir)", height=100)

        with st.expander("🧪 Fiziksel ve Kimyasal Özellikler (İsteğe Bağlı)"):
            st.caption("Boş bırakılırsa AI hesaplar. Özel değer girmek için doldurun. Çıkarmak için '-' yazın.")
            c_91, c_92 = st.columns(2)
            gen_p_state = c_91.text_input("Fiziksel Hali", placeholder="Örn: Sıvı")
            gen_p_color = c_92.text_input("Renk", placeholder="Örn: Şeffaf / Renksiz")
            gen_p_odor = c_91.text_input("Koku", placeholder="Örn: Kokusuz")
            gen_p_ph = c_92.text_input("pH", placeholder="Örn: > 13")
            gen_p_dens = c_91.text_input("Yoğunluk", placeholder="Örn: 1.10 - 1.12 g/cm³")
            gen_p_flash = c_92.text_input("Parlama Noktası", placeholder="Örn: Uygulanamaz")
            
        # V 134.0: DİNAMİK TDS PANELİ VE SDS BÖLÜM 16
        if "SDS" in doc_choice:
            tds_areas = tds_benefits = tds_dosage = tds_pack = ""
            with st.expander("🕒 Bölüm 16: Revizyon Bilgileri (İsteğe Bağlı)"):
                st.caption("Boş bırakılırsa yazılmaz. Çıkarmak için '-' yazın.")
                c_161, c_162 = st.columns(2)
                gen_rev_no = c_161.text_input("Revizyon No", placeholder="Örn: 02")
                gen_rev_date = c_162.text_input("Bölüm 16 Revizyon Tarihi", placeholder="Örn: 20.08.2025")
                gen_prev_date = c_161.text_input("Önceki GBF Tarihi", placeholder="Örn: 15.06.2024")
        else:
            gen_rev_no = gen_rev_date = gen_prev_date = ""
            with st.expander("📝 TDS Özel Bölümleri (İsteğe Bağlı)"):
                st.caption("Boş bırakırsanız AI kendisi ürün adına ve kimyasal yapıya göre üretecektir. Kendi metninizi yazarsanız AI doğrudan onu kullanır.")
                c_t1, c_t2 = st.columns(2)
                tds_areas = c_t1.text_area("Kullanım Alanları", placeholder="Örn: Ters osmoz sistemlerinde membran koruyucu olarak kullanılır.")
                tds_benefits = c_t2.text_area("Özellikler ve Avantajlar", placeholder="Örn: Kireçlenmeyi önler, membran ömrünü uzatır, temizlik maliyetlerini düşürür.")
                tds_dosage = c_t1.text_area("Uygulama ve Dozaj", placeholder="Örn: Sistem kapasitesine göre besleme suyuna 2-5 ppm dozlanmalıdır.")
                tds_pack = c_t2.text_area("Ambalaj ve Depolama", placeholder="Örn: 25 kg bidon ve 1000 kg IBC. Serin ve kuru yerde saklanmalıdır.")

        extra_params = {
            "c_date": gen_cdate,
            "r_date": gen_rdate,
            "vers": gen_vers,
            "sup_name": gen_sup_name,
            "sup_tel": gen_sup_tel,
            "sup_fax": gen_sup_fax,
            "sup_mail": gen_sup_mail,
            "sup_addr": gen_sup_addr,
            "p_state": gen_p_state,
            "p_color": gen_p_color,
            "p_odor": gen_p_odor,
            "p_ph": gen_p_ph,
            "p_dens": gen_p_dens,
            "p_flash": gen_p_flash,
            "rev_no": gen_rev_no,
            "rev_date": gen_rev_date,
            "prev_date": gen_prev_date,
            "tds_areas": tds_areas,
            "tds_benefits": tds_benefits,
            "tds_dosage": tds_dosage,
            "tds_pack": tds_pack
        }
            
        if st.button("AI ile Belgeyi PDF Olarak Üret", type="primary"):
            if not gen_prod_name or not gen_ingredients:
                st.warning("Lütfen Ürün Adı ve Bileşenleri (İçeriği) girin.")
            else:
                db_engine.ping_online(st.session_state['current_user'])
                with st.spinner("AI kimyasal formülü analiz ediyor ve uluslararası normlara göre PDF üretiyor... (Bu işlem 15-30 saniye sürebilir)"):
                    res_text = ai_engine.generate_sds_from_recipe_with_gemini(
                        gen_prod_name, 
                        gen_prod_type, 
                        gen_ingredients, 
                        doc_choice, 
                        st.session_state['settings_db']["genai_key"], 
                        gen_doc_lang, 
                        extra_params
                    )
                    
                    if "HATA" in res_text or "ERROR" in res_text:
                        st.error(res_text)
                    else:
                        st.session_state['generated_sds_content'] = res_text
                        
                        pdf_bytes = pdf_engine.create_generated_document_pdf(
                            text_content=res_text, 
                            logo_bytes=gen_logo.getvalue() if gen_logo else None, 
                            footer_text=gen_footer, 
                            lang_code=gen_doc_lang, 
                            header_params=extra_params
                        )
                        
                        if pdf_bytes:
                            st.session_state['generated_sds_pdf'] = pdf_bytes
                            st.success("✅ Belge başarıyla üretildi ve PDF formatına dönüştürüldü!")
                        else:
                            st.error("PDF oluşturulurken bir hata meydana geldi.")
        
        if st.session_state.get('generated_sds_pdf'):
            st.markdown("---")
            st.download_button(
                label=f"📥 {gen_prod_name} {doc_choice.split()[0]} PDF İndir",
                data=st.session_state['generated_sds_pdf'],
                file_name=f"{gen_prod_name}_{doc_choice.split()[0]}.pdf",
                mime="application/pdf",
                type="primary"
            )
            with st.expander("📄 Üretilen Ham Metni Gör (Düzenleme / Kontrol İçin)"):
                st.markdown(st.session_state.get('generated_sds_content', ''))
