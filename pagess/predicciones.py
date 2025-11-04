import streamlit as st
import pandas as pd
def app():
    st.set_page_config(page_title="Predicción de Inventario", layout="wide")

    st.title("📦 Predicción de Inventario Semanal")

    # ------------------------
    # Datos simulados
    # ------------------------
    inventario_actual = {
        "Refresco Coca-Cola 600ml": 45,
        "Telera (pieza)": 120,
        "Carne de cerdo (kg)": 18,
        "Crema (L)": 7,
        "Mayonesa (kg)": 5,
        "Tortillas (kg)": 25,
        "Carne de res (kg)": 10,
    }

    consumo_diario_estimado = {
        "Refresco Coca-Cola 600ml": 12,
        "Telera (pieza)": 40,
        "Carne de cerdo (kg)": 4,
        "Crema (L)": 1.2,
        "Mayonesa (kg)": 0.8,
        "Tortillas (kg)": 7,
        "Carne de res (kg)": 3,
    }

    # ------------------------
    # Cálculo de predicción
    # ------------------------
    dias_semana_actual = 7
    dias_semanas = {
        "Semana Actual": dias_semana_actual,
        "Próxima Semana": dias_semana_actual * 2
    }

    filas = []
    for producto in inventario_actual:
        stock = inventario_actual[producto]
        consumo_dia = consumo_diario_estimado[producto]
        
        consumo_semana = consumo_dia * dias_semana_actual
        consumo_dos_semanas = consumo_dia * dias_semanas["Próxima Semana"]
        
        stock_fin_semana = stock - consumo_semana
        stock_fin_dos_semanas = stock - consumo_dos_semanas
        
        filas.append([
            producto,
            stock,
            consumo_semana,
            stock_fin_semana,
            consumo_dos_semanas,
            stock_fin_dos_semanas
        ])

    df = pd.DataFrame(filas, columns=[
        "Producto", "Inventario Actual",
        "Consumo Esperado Semana Actual", "Faltante",
        "Consumo Dos Semanas", "Faltante Prox Semana"
    ])

    st.dataframe(df, use_container_width=True)

    # ------------------------
    # Alertas
    # ------------------------
    st.subheader("🔔 Alertas de Inventario")

    for _, row in df.iterrows():
        if row["Faltante"] <= 0:
            st.warning(f"⚠️ *{row['Producto']}* se agotará **esta semana**. Reabastecer pronto.")
        elif row["Faltante Prox Semana"] <= 0:
            st.info(f"ℹ️ *{row['Producto']}* alcanzará esta semana, pero se agotará la próxima.")
