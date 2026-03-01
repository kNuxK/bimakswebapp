import streamlit as st
import db_engine
import time

def render():
    is_admin = str(st.session_state.get('role', '')).lower() == 'admin'
    if not is_admin:
        st.error("Yetkisiz Erişim")
        st.stop()
        
    st.header("👑 Admin Yönetim Paneli")
    
    st.subheader("🔒 Rol ve Yetki Yönetimi")
    role_defs = db_engine.get_role_definitions()
    
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
    p_tech_sds_gen = c2.checkbox("↳ Sıfırdan SDS Üretici (AI)", value="tech_sds_gen" in curr_perms)
    
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
        if p_tech_sds_gen: new_perms.append("tech_sds_gen")
        
        role_defs[sel_role] = ",".join(new_perms)
        db_engine.update_role_definitions(role_defs["Admin"], role_defs["Bimaks Üye"], role_defs["Yeni Üye"])
        st.success("Yetkiler başarıyla güncellendi! Bu role sahip tüm kullanıcıların erişimleri anında değişti.")
        if st.session_state['role'] == sel_role:
            st.session_state['permissions'] = role_defs[sel_role]
        time.sleep(1)
        st.rerun()

    st.markdown("---")
    st.subheader("👥 Kullanıcı Listesi")
    users_data = db_engine.get_all_users_status()
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
                    if db_engine.update_user_role(u['username'], selected_r):
                        st.success("✔")
                    else: st.error("X")
                    
            if cu5.button("🗑️", key=f"dl_{u['username']}", help="Kullanıcıyı Sil"):
                if u['username'] == st.session_state['current_user']:
                    st.error("!")
                else:
                    db_engine.delete_user(u['username'])
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
                    s, m = db_engine.register_user(n_u, n_p, n_r)
                    if s: st.success(f"'{n_u}' başarıyla oluşturuldu!"); time.sleep(1); st.rerun()
                    else: st.error(m)