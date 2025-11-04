import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from home_components import cleaning_data
from home_components import api_sales as api
import streamlit as st
from utils_theme import apply_theme
from datetime import datetime
from dateutil.relativedelta import relativedelta
import base64
from pathlib import Path

@st.cache_data  # Buena práctica para cachear la imagen
def img_to_base64(image_path):
    """Convierte una imagen local a formato Base64."""
    try:
        # Usamos pathlib para asegurar compatibilidad de rutas
        path_obj = Path(image_path)
        with open(path_obj, "rb") as img_file:
            # Codifica a base64 y decodifica a UTF-8
            return base64.b64encode(img_file.read()).decode('utf-8')
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo de icono en '{image_path}'")
        return None

def app(periodo, categoria, comparacion):
    


    st.set_page_config(
        page_title="Gardú La Polar",
        page_icon="images/gardu_logo.jpg",
        layout="wide",
        initial_sidebar_state="expanded"
        
    )


    # 1. Define la ruta a tu icono
    ICON_PATH = "images/gardu_logo.jpg"  # ¡Reemplaza esto con la ruta a tu imagen!

    # 2. Carga la imagen como Base64
    icon_base64 = img_to_base64(ICON_PATH)

# 3. Muestra el título usando st.markdown
    st.markdown(
            f"""
        <div style="display: flex; align-items: center; gap: 15px;">
        <img src="data:image/png;base64,{icon_base64}" alt="Icono personalizado" style="width: 40px; height: 40px;">
        <h1 class="main-header">Gardú La Polar</h1>
        </div>
        """,
            unsafe_allow_html=True
    )
    notificaciones = [
    "⚠️ Se agotará la Coca-Cola 600 ml mañana.",
    "🔻 Tortas de pierna bajaron 25% esta semana.",
    ]   


    for nota in notificaciones:
        st.toast("- " + nota)

    apply_theme()

    reference = 'Total'
    label1 = "💰 Ingresos Totales"
    label2 = "👥 Ticket Promedio"
    titleLineChart = "Evolución de Ingresos"
    titlePieChart = "Distribución de Ventas por Categoria"
    titleBarChart = "Ventas Totales por Producto"
    if categoria == 'Devolución':
        label1 = "📦 Devoluciones"
        label2 = "🔙 Numero de devoluciones"
        titleLineChart = "📦 Evolución de Devoluciones"
        titlePieChart = "Devoluciones por Producto"
        titleBarChart = "Devoluciones Totales por Producto"
        reference = 'TotalRefound'
    
    #Recoleccionn de los datos
    with st.spinner(text = f"Cargando datos para '{periodo}'...", width="content"):
        df = pd.read_csv('./ventas_restaurante.csv')
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df_today, df_past = cleaning_data.filter_csv(df, periodo, comparacion)
        #df_sales = cleaning_data.load_data('./data_base/mi_archivo.parquet')
        dfSalesToday, dfPastSales = df_today, df_past 


        # KPIs
    st.markdown("## 📈 Resumen del Negocio")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        today_total = df_today[reference].sum()
        past_total = df_past[reference].sum()    
        # --- FIX: Check if past_total is zero before dividing ---
        if past_total != 0:
            percentChange = (today_total - past_total) / past_total * 100
        else:
            percentChange = 0.0  # Or handle as you see fit when there's no past data
            
        st.metric(label1 , f"${today_total:,.0f}", f"{2.8:.1f}%")

    with col2:
        if categoria == 'Devolución':
            cat_prom = (df_today['SaleReturned'] == True).sum()
            pastCatProm = (df_past['SaleReturned'] == True).sum()
            
            # --- FIX: Check for zero ---
            if pastCatProm != 0:
                changeCatProm = (cat_prom - pastCatProm) / pastCatProm * 100
            else:
                changeCatProm = 0.0
                
            st.metric(label2, f"{cat_prom:,.0f}", f"{3.2:.1f}%")
        else:
            cat_prom = df_today[reference].mean()
            pastCatProm = df_past[reference].mean()
            
            # --- FIX: Check for zero ---
            if pastCatProm != 0:
                changeCatProm = (cat_prom - pastCatProm) / pastCatProm * 100
            else:
                changeCatProm = 0.0
                
            st.metric(label2, f"${cat_prom:,.0f}", f"{4.2:.1f}%")
            
    with col3:
        grossIncome = dfSalesToday['Total'].sum() * 0.4
        pastGrossIncome = dfPastSales['Total'].sum() * 0.4
        
        # --- FIX: Check for zero ---
        if pastGrossIncome != 0:
            changeGrossIncome = (grossIncome - pastGrossIncome) / pastGrossIncome * 100
        else:
            changeGrossIncome = 0.0
            
        st.metric("💸 Venta Hoy ", f"${grossIncome:,.0f}", f"{3.2:.1f}%")

    with col4:
        netIncome = dfSalesToday['Total'].sum() * 0.25
        pastNetIncome = dfPastSales['Total'].sum() * 0.25
        
        # --- FIX: Check for zero ---
        if pastNetIncome != 0:
            changeNetIncome = (netIncome - pastNetIncome) / pastNetIncome * 100
        else:
            changeNetIncome = 0.0
            
        st.metric("💵 Utilidad Estimada", f"${netIncome:,.0f}", f"{5.6:.1f}%")

    # Gráficosd
    df_suc = df_today.groupby(['Sucursal', 'Fecha'])[reference].sum().reset_index()
    df = df_today.groupby('Fecha')[reference].sum().reset_index()
    df_suc[reference] = df_suc[reference].abs().astype(int)
    df[reference] = df[reference].abs().astype(int)
    # Gráficosd
    st.markdown("## 📊 Análisis de Tendencias")
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Fecha'], y=df[reference], mode='lines', name= categoria, line=dict(color='#1f4e79')))
        z = np.polyfit(range(len(df)), df[reference], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(x=df['Fecha'], y=p(range(len(df))), mode='lines', name='Rate', line=dict(color='red', dash='dash')))
        fig.update_layout(title= titleLineChart, height=350, margin=dict(r=62))
        
        

        if comparacion =='Mismo período año pasado':
            df_suc_past = df_past.groupby(['Sucursal', 'Fecha'])[reference].sum().reset_index()
            df_copy = df_past.groupby('Fecha')[reference].sum().reset_index()
            df_suc_past[reference] = df_suc[reference].abs().astype(int)
            df_copy[reference] = df_copy[reference].abs().astype(int)
            
            df_copy['Fecha'] = df_copy['Fecha']+pd.Timedelta(days=365)
            fig.add_trace(go.Scatter(x=df_copy['Fecha'], y=df_copy[reference], mode='lines', name= 'Venta pasada', line=dict(color="#A47DD6")))

            peaks = (df_copy[reference].shift(1) < df_copy[reference]) & (df_copy[reference].shift(-1) < df_copy[reference])
                # Get peak values and dates
            peak_dates = df_copy['Fecha'][peaks]
            peak_values = df_copy[reference][peaks]
            # Peaks as markers
            fig.add_trace(go.Scatter(
                x=peak_dates,
                y=peak_values,
                mode='markers+text',              # ← texto + marcador
                name='Picos past',
                marker=dict(color='orange', size=6, symbol='circle'),
                text=[f"${v:,.0f}" for v in peak_values],  # etiqueta
                texttemplate="%{text}",
                textposition="top center",        # arriba del punto
                cliponaxis=False                  # evita que se recorte el texto
            ))
        
        
        
        fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=25, r=100, t=50, b=40),
        height=350,
        legend=dict(orientation="v", xanchor="right", x=1.3)
        )
        peaks = (df[reference].shift(1) < df[reference]) & (df[reference].shift(-1) < df[reference])
        # Get peak values and dates
        peak_dates = df['Fecha'][peaks]
        peak_values = df[reference][peaks]
        # Peaks as markers
        fig.add_trace(go.Scatter(
            x=peak_dates,
            y=peak_values,
            mode='markers+text',              # ← texto + marcador
            name='Picos',
            marker=dict(color='red', size=6, symbol='circle'),
            text=[f"${v:,.0f}" for v in peak_values],  # etiqueta
            texttemplate="%{text}",
            textposition="top center",        # arriba del punto
            cliponaxis=False                  # evita que se recorte el texto
        ))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Agrupar por sucursal y sumar totales
        df_totales = df_suc.groupby("Sucursal")[reference].sum().reset_index()

        # Diccionario original
        data = {
            "Platillos": 55000,
            "Bebidas": 20000,
            "Combos": 35000,
            "Postres": 10000
        }

        # Crear DataFrame
        df_pie = pd.DataFrame(list(data.items()), columns=["Categoria", "Monto"])


        # Crear gráfica de pastel
        fig = px.pie(
            df_pie,
            names="Categoria",
            values="Monto",
            title=titlePieChart,
            hole=0.3  # 0 para pastel, >0 para tipo dona
        )
        fig.update_traces(textinfo="value + percent")
        fig.update_layout(
            margin=dict(l=10, r=170, t=50, b=40),   # más espacio para la leyenda
            legend=dict(
            orientation="v",
            x=0.95, xanchor="left",            # fuera del gráfico, a la derecha
            y=0.5,  yanchor="middle"           # centrada verticalmente
            ),
            height=350,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, use_container_width=True)



    st.markdown("## 📈 Top Mejores productos")
    mostrar_barras = st.toggle("Gráfica de Barras", value = True)
    if mostrar_barras:
            # Crear gráfica de barras
        fig = px.bar(
            df_totales,
            x="Sucursal",
            y=reference,
            title=titleBarChart,
            text_auto='.2s',  # Muestra valores en las barras
            color="Sucursal"  # Colores distintos por tienda
        )

        fig.update_layout(
            xaxis_title="Sucursal",
            yaxis_title=f"Total de {categoria} (MXN)",
            showlegend=False,
            margin=dict(r=62)
        )
    else:
        # Lista de sucursales (texto para mostrar, nombre en DataFrame)
        sucursales = [
        "TIENDA NORMA",
        "TIENDA VILLA IZCALLI",
        "TIENDA ARMERIA",
        "TIENDA MEN",
        "MATRIZ",
        "TIENDA BENITO JUAREZ",
        "TIENDA SANTIAGO",
        "TIENDA ARTURO",
        "TIENDA VIRU",
        "TIENDA LADY",
        "TIENDA PATY",
        "DIEGO"
        ]

        fig = go.Figure()

      # Agregar líneas para sucursales activadas
        st.markdown(f"#### {titleBarChart} ")
        for sucursal in sucursales:
            df_filtrado = df_suc[df_suc['Sucursal'] == sucursal]
            fig.add_trace(go.Scatter(
                x=df_filtrado['Fecha'],
                y=df_filtrado[reference],
                mode='lines',
                name=sucursal,
                line=dict(width=2)
            ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    # Mostrar el gráfico
    st.plotly_chart(fig, use_container_width=True)
