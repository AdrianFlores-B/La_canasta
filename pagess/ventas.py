import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from home_components import cleaning_data, api_sales as api
from sales_components import sales_plots as sp
from utils_theme import apply_theme

def app():
    st.set_page_config(
        page_title="Venta Casa Renteria",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
        
    )

    st.markdown('<h1 class="main-header">💲 Analisis de Ventas</h1>', unsafe_allow_html=True)
    apply_theme()    # carga e inyecta CSS

    with st.spinner(text = f"Cargando datos...", width="content"): 
        df = pd.read_csv('./ventas_restaurante.csv')
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    #---------Columns (PeakHour, WeekdaySales, MonthSales)------------------

    top_lefT, top_center, top_right  = st.columns(3)

    with top_lefT:
        sp.plot_weekDays(df)
    with top_center:
        sp.plot_MonthSales(df)
    with top_right:
        sp.plot_MonthSales_suc(df)




    
    st.markdown("### Ventas por Producto")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    col1, col2, col3 = st.columns(3)

    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", value=pd.to_datetime("2025-08-5").date())
    with col2:
        fecha_fin = st.date_input("Fecha de fin", value=pd.to_datetime("2025-8-31").date())
    with col3:
        periodo = st.selectbox("📅 Período de análisis:", ["Dia", "Semana", "Mes"], index=1)
    fecha_inicio = pd.to_datetime(fecha_inicio)
    fecha_fin = pd.to_datetime(fecha_fin)

# Filtro correcto
    df_filtrado = df[
    (df["Fecha"] >= fecha_inicio) & (df["Fecha"] <= fecha_fin)
    ]
    if periodo == "Dia":
        df_filtrado = df_filtrado.groupby(['Sucursal', 'Fecha'])['Total'].sum().reset_index()
    elif periodo == "Semana":
        df_filtrado['Fecha'] = df_filtrado['Fecha'].dt.isocalendar().year.astype(str) + '-' + df_filtrado['Fecha'].dt.isocalendar().week.astype(str)
        df_filtrado = df_filtrado.groupby(['Sucursal', 'Fecha'])['Total'].sum().reset_index()
    elif periodo == "Mes":
        df_filtrado['Fecha'] = df_filtrado['Fecha'].dt.to_period('M').astype(str)
        df_filtrado = df_filtrado.groupby(['Sucursal', 'Fecha'])['Total'].sum().reset_index()

    df_filtrado['Etiqueta'] = df_filtrado['Total'].apply(lambda x: f"${x:,.0f} MXN")    
    fig = px.bar(
    df_filtrado,
    x="Fecha",
    y="Total",
    color="Sucursal",
    title="Ventas por Producto",
    text="Etiqueta"
    )

    # --- arreglar textos cortados arriba ---
    fig.update_traces(cliponaxis=False)  # permite que el texto salga del área del eje
    y_max = df_filtrado.groupby("Fecha")["Total"].sum().max()  # tope de cada pila
    fig.update_yaxes(range=[0, y_max * 1.12], automargin=True)  # añade “headroom” y evita recortes
    fig.update_layout(margin=dict(t=90, l=10, r=10, b=10))  # margen superior suficiente


    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(r=80),
    )
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

        
