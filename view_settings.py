import streamlit as st
import config
import db_engine
import ui_engine
import time

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
    is_admin = str(st.session_state.get('role', '')).lower() == 'admin'
    st.header(t('settings_title'))
    c1, c2 = st.columns(2)
    
    with c1:
        if is_admin:
            st.subheader(t('set_role_mgmt'))
            np = st.text_input(t('set_add_role'))
            if st.button(_("Ekle", "Add", "Добавить", "إضافة", "Ajouter", "Añadir")): 
                st.session_state['personas_db'].append({"TR": np, "EN": np, "RU": np, "AR": np, "FR": np, "ES": np}); st.rerun()
            dp = st.selectbox(t('set_del_role'), ui_engine.get_persona_list_for_ui())
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
                is_saved = db_engine.update_user_keys(st.session_state['current_user'], k1, k2, k3, k4)
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