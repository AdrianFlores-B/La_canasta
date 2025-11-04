import streamlit as st
import pandas as pd
def app():
    st.set_page_config(page_title="Predicción de Inventario", layout="wide")

    st.title("📦 Predicción de Inventario Semanal")

    # ------------------------
    # Datos simulados
    # ------------------------
    inventario_actual = {
        "Bolsa Plana 10x20": 45,
        "Bolsa Plana 10x20": 120,
        "Jabon Roma 1kg": 18,
        "Electrolit varios": 7,
        "Bolsa 60x90": 5,
        "Camiseta Mediana": 25,
        "Vaso #12": 10,
    }
    consumo_diario_estimado = {
        "Bolsa Plana 10x20": 5,
        "Bolsa Plana 10x20": 12,
        "Jabon Roma 1kg": 7,
        "Electrolit varios": 2,
        "Bolsa 60x90": 10,
        "Camiseta Mediana": 10,
        "Vaso #12": 20,
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
