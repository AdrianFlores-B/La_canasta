from pathlib import Path
import streamlit as st

THEMES = {
    "Light • Classic": "styles/theme_light_classic.css",
    "Light • Minimal": "styles/theme_light_minimal.css",
    "Light • Contrast": "styles/theme_light_contrast.css",
}

def apply_theme(name: str = "Light • Classic"):
    path = THEMES.get(name, list(THEMES.values())[0])
    css = Path(path).read_text(encoding="utf-8")
    # key fijo para reemplazar el <style> y evitar acumulación
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def theme_selector(default="Light • Classic"):
    if "theme_choice" not in st.session_state:
        st.session_state.theme_choice = default
    st.session_state.theme_choice = st.sidebar.selectbox(
        "🎨 Tema", list(THEMES.keys()),
        index=list(THEMES.keys()).index(st.session_state.theme_choice)
    )
    apply_theme(st.session_state.theme_choice)
