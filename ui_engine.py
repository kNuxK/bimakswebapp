import streamlit as st
from datetime import datetime
import config

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