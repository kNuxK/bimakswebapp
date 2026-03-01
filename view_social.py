import streamlit as st
import config
import db_engine
import ai_engine
import social_engine
import ui_engine
from PIL import Image, ImageDraw

def t(key): return config.LANGUAGES.get(st.session_state.get('lang', 'TR'), config.LANGUAGES['TR']).get(key, key)
def _(tr, en, ru, ar, fr, es):
    l = st.session_state.get('lang', 'TR')
    if l == 'EN': return en
    if l == 'RU': return ru
    if l == 'AR': return ar
    if l == 'FR': return fr
    if l == 'ES': return es
    return tr

def render_linkedin():
    if not st.session_state['settings_db'].get("genai_key"): 
        st.warning(f"⚠️ {t('guide_title_main')}"); st.stop()
    with st.expander(t('step1_linkedin_title'), expanded=False):
        ui_personas = ui_engine.get_persona_list_for_ui()
        sel_p = st.selectbox(t('sys_select'), ui_personas, index=0, key="li_p")
        role_c = st.text_input(t('sys_manual'), key="li_m") if sel_p == t('sys_manual') else sel_p
        
        m_topic = st.text_input(t('topic'), placeholder=_("Konu...", "Topic...", "Тема...", "الموضوع...", "Sujet...", "Tema..."))
        t_aud = st.text_input(t('target_audience'), t('target_def'))
        t_plat = st.text_input(t('target_plat'), t('plat_def'))
        
        p_ref = st.text_input(t('prod_ref'), placeholder=_("Örn: BİMAKS Atık Su Kimyasalları", "e.g., BIMAKS Waste Water Chemicals", "напр., Химикаты BIMAKS", "مثال: بيمكس للمواد الكيميائية", "ex. Produits chimiques pour eaux usées", "ej. Productos químicos para aguas residuales"))
        p_link = st.text_input(t('prod_link_lbl'), placeholder=_("Örn: https://www.bimaks...", "e.g., https://www.bimaks...", "напр., https://www.bimaks...", "مثال: https://www.bimaks...", "ex. https://www.bimaks...", "ej. https://www.bimaks...")) 
        
        c_lim = st.number_input(t('prompt_limit'), 500, 10000, 3000, 100)
        
        if st.button(t('btn_create'), type="primary"):
            db_engine.ping_online(st.session_state['current_user'])
            clean_prod = None if not p_ref or p_ref.strip() == "" else p_ref
            
            prompt = ai_engine.construct_prompt_text(role_c, m_topic, t_aud, t_plat, clean_prod, c_lim, st.session_state.get('lang', 'TR'), p_link)
            
            with st.spinner(_("AI Yazıyor...", "AI is writing...", "ИИ пишет...", "الذكاء الاصطناعي يكتب...", "L'IA écrit...", "La IA está escribiendo...")):
                res = ai_engine.get_gemini_response_from_manual(prompt, st.session_state['settings_db']["genai_key"])
                if "HATA" in res or "ERROR" in res: st.error(res)
                else:
                    cleaned_res = ai_engine.force_clean_text(res)
                    
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
                        
                    yeni_makale = ai_engine.smart_trim(cleaned_res, c_lim)
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
                db_engine.ping_online(st.session_state['current_user'])
                r = social_engine.post_to_linkedin_real(val, up.getvalue() if up else None, up.type if up else "", st.session_state['settings_db']["linkedin_token"])
                if "✅" in r: ui_engine.save_history_entry(m_topic, role_c); st.balloons(); st.success(r)
                else: st.error(r)
    
    with st.expander("📜 History"):
        if not st.session_state['history_db']: st.caption(_("Kayıt yok.", "No records.", "Нет записей.", "لا توجد سجلات.", "Aucun enregistrement.", "Sin registros."))
        else: [st.text(f"{h['date']} | {h['topic']} | {h['role']}") for h in st.session_state['history_db']]

def render_instagram():
    if not st.session_state['settings_db'].get("genai_key"): st.warning(f"⚠️ {t('guide_title_main')}"); st.stop()
    with st.expander(t('step1_linkedin_title'), expanded=False):
        ui_personas = ui_engine.get_persona_list_for_ui()
        sel_p = st.selectbox(t('sys_select'), ui_personas, key="in_p")
        role_c = st.text_input(t('sys_manual'), key="in_m") if sel_p == t('sys_manual') else sel_p
        m_topic = st.text_input(t('topic'), placeholder=_("Konuyu yazın...", "Write the topic...", "Напишите тему...", "اكتب الموضوع...", "Écrivez le sujet...", "Escribe el tema..."))
        c_lim = st.number_input(t('prompt_limit'), 500, 2200, 2000, 100, key="in_l")
        
        if st.button(t('btn_create'), type="primary", key="in_btn"):
            db_engine.ping_online(st.session_state['current_user'])
            st.session_state['draft_prompt'] = ai_engine.construct_prompt_text(role_c, m_topic, "Followers", "Instagram", None, c_lim, st.session_state['lang'])
            with st.spinner(_("AI Yazıyor...", "AI is writing...", "ИИ пишет...", "الذكاء الاصطناعي يكتب...", "L'IA écrit...", "La IA está escribiendo...")):
                res = ai_engine.get_gemini_response_from_manual(st.session_state['draft_prompt'], st.session_state['settings_db']["genai_key"])
                if "HATA" in res or "ERROR" in res: st.error(res)
                else: 
                    cleaned_res = ai_engine.force_clean_text(res)
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
                        
                    yeni_makale = ai_engine.smart_trim(cleaned_res, c_lim)
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
        if uploaded_file: im = Image.open(uploaded_file).convert("RGB"); im = social_engine.resize_for_instagram(im); st.session_state['original_image'] = im
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
            if st.button(t('publish_insta'), type="primary"): db_engine.ping_online(st.session_state['current_user']); st.warning("⚠️ Web API Simulasyon Modundadır.")