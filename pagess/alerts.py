import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils_theme import apply_theme
def app():
    # Alertas inteligentes
    st.markdown("## 🚨 Centro de Alertas Inteligentes")
    alertas = []
    apply_theme()  
    alertas.append({'tipo': '⚠️ Advertencia', 'mensaje': 'Ingresos por debajo del promedio en últimos 7 días', 'color': 'orange'})
    alertas.append({'tipo': '⚠️ Advertencia', 'mensaje': 'Inventario en numeros criticos', 'color': 'red'})
    
    for alerta in alertas:
        st.markdown(f"""
        <div style="padding: 1rem; margin: 0.5rem 0; background-color: {alerta['color']}; 
                    color: white; border-radius: 10px; font-weight: bold;">
            {alerta['tipo']}: {alerta['mensaje']}
        </div>
        """, unsafe_allow_html=True)