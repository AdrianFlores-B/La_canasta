import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date
from home_components import cleaning_data, api_sales as api


def plot_weekDays(df):
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

    # 1) Día de la semana en número (lunes=0, domingo=6)
    df['dia_num'] = df['Fecha'].dt.dayofweek

    # 2) Cambiar número por nombre en español
    dias_es = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
    df['Day'] = df['dia_num'].map(dias_es)
    orden = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
    df['Day'] = pd.Categorical(df['Day'], categories=orden, ordered=True)
    df['Year'] = df['Fecha'].dt.year 
    df.Total = df.Total.fillna(0).abs().astype(float)
    df  = df.groupby(['Day', 'Year'])['Total'].mean().reset_index()


    fig = px.line(
        df,
        x="Day",
        y="Total",
        markers=True,
        color="Year",
        title="Ventas por Dia",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=25, r=62, t=50, b=60),
        height=250,
        legend=dict(orientation="h", yanchor="top", xanchor="right", y=2, x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_MonthSales(df):
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df["Month"] = df['Fecha'].dt.month

    # 2) Remapeo a nombre del mes en español
    month_map = {
        1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
        7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
    }
    df["Month"] = df["Month"].map(month_map)
    df['Year'] = df['Fecha'].dt.year 
    orden = ["Enero","Febrero", "Marzo", "Abril", "Mayo","Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre","Diciembre"]
    df['Month'] = pd.Categorical(df['Month'], categories=orden, ordered=True)

    df  = df.groupby(['Month', 'Year'])['Total'].sum().reset_index()
    df.Total = df.Total.abs().astype(int)

    
    fig = px.line(
        df,
        x="Month",
        y="Total",
        markers=True,
        color="Year",
        title="Ventas por Mes",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=25, r=62, t=95, b=60),
        height=250,
        legend=dict(orientation="h", yanchor="top", xanchor="right", y=2, x=1.2)
    )
    st.plotly_chart(fig, use_container_width=True)




def plot_MonthSales_suc(df):
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df["Month"] = df['Fecha'].dt.month

    # 2) Remapeo a nombre del mes en español
    month_map = {
        1:"Enero", 2:"Febrero", 3:"Marzo", 4:"Abril", 5:"Mayo", 6:"Junio",
        7:"Julio", 8:"Agosto", 9:"Septiembre", 10:"Octubre", 11:"Noviembre", 12:"Diciembre"
    }
    df["Month"] = df["Month"].map(month_map)
    df['Year'] = df['Fecha'].dt.year 
    orden = ["Enero","Febrero", "Marzo", "Abril", "Mayo","Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre","Diciembre"]
    df['Month'] = pd.Categorical(df['Month'], categories=orden, ordered=True)
    df.Total = df.Total.fillna(0).abs().astype(float)
    df  = df.groupby(['Month', 'Sucursal'])['Total'].mean().reset_index()


    
    fig = px.line(
        df,
        x="Month",
        y="Total",
        markers=True,
        color="Sucursal",
        title="Ventas por Sucursal",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=25, r=62, t=50, b=60),
        height=250,
        legend=dict(orientation="v", yanchor="bottom", xanchor="right", y=0.001, x=0.005),
        showlegend = False
    )
    st.plotly_chart(fig, use_container_width=True)


@st.cache_data(ttl=82000) 
def load_all_data():

    df_old = pd.read_csv('./data_base/Old_sales.csv')
    # Limpiar la columna 'total'
    df_old['total'] = (
        df_old['total']
        .astype(str)              # Asegura que todos los valores sean cadenas
        .str.replace('$', '', regex=False)  # Quita el símbolo de dólar
        .str.replace(',', '', regex=False)  # Quita comas (si hay miles)
        .str.strip()              # Elimina espacios en blanco
        .astype(float)            # Convierte a número flotante
    )
 
    df_new = api.sales_period(pd.to_datetime("2023-01-1"),pd.to_datetime("today"))
    df_new = cleaning_data.cleaning(df_new)
    df_new.rename(columns={'Name': 'Sucursal'}, inplace=True)
    df_list = [df_new, df_old]

    df = pd.concat(df_list)
    df.rename(columns={'fecha':'Fecha', 'total': 'Total'}, inplace=True)
    return df