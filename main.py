# main.py
import streamlit as st
from streamlit_option_menu import option_menu

# Importa tus páginas
import pagess.alerts as alerts
import pagess.home as home
import pagess.ventas as ventas
import pagess.gastos as gastos
import pagess.admin as admin
import pagess.predicciones as predicciones
from users_db import load_db, allowed_pages_for, is_admin, BASE_PAGES


st.set_page_config(
    page_title="Gardu",
    page_icon="images/gardu_logo.jpg",   # ruta a la imagen
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- Sin Autenticación ----------
# Forzamos usuario por defecto (ej: "admin")
st.session_state.auth_user = "admin"

# Usuario simulado cargado desde base
db = load_db()
user = {"role": "admin"}  # rol libre sin restricciones

# ---------- Sidebar ----------
with st.sidebar:
    st.image("images/gardu_logo.jpg", use_container_width=True)
    st.write(f"👤 **{st.session_state.auth_user}** ({user.get('role', 'Sin Rol')})")

    # Construir menú completo sin restricciones
    all_pages_order = BASE_PAGES + ["Admin"]
    options = all_pages_order
    
    icon_map = {
        "Home": "house",
        "Ventas": "cash",
        "Costos": "wallet",
        "Alertas": "activity",
        "Predicciones": "graph-up",
        "Admin": "gear"
    }
    icons = [icon_map.get(p, "dot") for p in options]

    selected = option_menu(
        menu_title="Menu",
        options=options,
        icons=icons,
        menu_icon="cast",
        default_index=0,
    )

    # Controles extra SOLO en Home
    if selected == "Home":
        periodo = st.selectbox("📅 Período de análisis:", ["Últimos 30 días", "Último trimestre", "Último año"])
        categoria = st.selectbox("🎯 Categoría:", ["Venta"])
        comparacion = st.selectbox("📊 Comparar con:", ["Período anterior", "Mismo período año pasado"])

# ---------- Routing / Render ----------
if selected == "Home":
    home.app(periodo, categoria, comparacion)
elif selected == "Costos":
    gastos.app()
elif selected == "Alertas":
    alerts.app()
elif selected == "Ventas":
    ventas.app()
elif selected == "Admin":
    admin.app()

elif selected == "Predicciones":
    predicciones.app()
