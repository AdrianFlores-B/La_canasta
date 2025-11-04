import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
from home_components import api_sales as api

@st.cache_data(ttl=82800) 
def filter(rango,periodo):

    fecha_actual = pd.to_datetime("today") - pd.Timedelta(days=1)
    year = pd.Timedelta(days=365)

    df_old = pd.read_csv('./data_base/Old_sales.csv')
    df_old['fecha'] = pd.to_datetime(df_old['fecha'], errors='coerce')
    df_old['total'] = (
        df_old['total']
        .astype(str)              # Asegura que todos los valores sean cadenas
        .str.replace('$', '', regex=False)  # Quita el símbolo de dólar
        .str.replace(',', '', regex=False)  # Quita comas (si hay miles)
        .str.strip()              # Elimina espacios en blanco
        .astype(float)            # Convierte a número flotante
    )

    if rango == "Últimos 30 días":
        lapso = pd.Timedelta(days=30)
        fecha_inicio = fecha_actual - lapso
        df_today  = api.sales_period(fecha_inicio, fecha_actual)
        if periodo == 'Período anterior':
            df_past = api.sales_period(fecha_inicio-lapso, fecha_inicio)
            df_old_past = df_old[(df_old['fecha'] >= fecha_inicio-lapso) & (df_old['fecha'] <= fecha_inicio)]
        else:
            df_past = api.sales_period(fecha_inicio-year, fecha_actual-year)
            df_old_past = df_old[(df_old['fecha'] >= fecha_inicio-year) & (df_old['fecha'] <= fecha_actual- year)]
    
    elif rango == "Último trimestre":
        lapso = pd.Timedelta(days=90)
        fecha_inicio = fecha_actual - lapso
        df_today  = api.sales_period(fecha_inicio, fecha_actual)
        

        if periodo == 'Período anterior':
            df_past = api.sales_period(fecha_inicio-lapso, fecha_inicio)
            df_old_past = df_old[(df_old['fecha'] >= fecha_inicio-lapso) & (df_old['fecha'] <= fecha_inicio)]
        else:
            df_past = df_past = api.sales_period(fecha_inicio-year, fecha_actual-year)
            df_old_past = df_old[(df_old['fecha'] >= fecha_inicio-year) & (df_old['fecha'] <= fecha_actual- year)]
    
   
    elif rango == "Último año":
        lapso = pd.Timedelta(days=365)
        fecha_inicio = fecha_actual - lapso
        df_today  = api.sales_period(fecha_inicio, fecha_actual)
        if periodo == 'Período anterior':
            df_past = api.sales_period(fecha_inicio-lapso, fecha_inicio)
            df_old_past = df_old[(df_old['fecha'] >= fecha_inicio-lapso) & (df_old['fecha'] <= fecha_inicio)]
        else:
            df_past = df_past = api.sales_period(fecha_inicio-year, fecha_actual-year)
            df_old_past = df_old[(df_old['fecha'] >= fecha_inicio-year) & (df_old['fecha'] <= fecha_actual- year)]
    
    df_today = cleaning(df_today)
    df_today.rename(columns={'Name': 'Sucursal'}, inplace=True)
    df_old_today = df_old[(df_old['fecha'] >= fecha_inicio) & (df_old['fecha'] <= fecha_actual)]
    if not df_old_today.empty:
        df_today = pd.concat([df_today,df_old_today])

    df_past = cleaning(df_past)
    df_past.rename(columns={'Name': 'Sucursal'}, inplace=True)
    if not df_old_past.empty:
        df_past = pd.concat([df_past,df_old_past])

    df_today.rename(columns={'fecha':'Fecha', 'total': 'Total'}, inplace=True)
    df_past.rename(columns={'fecha':'Fecha', 'total': 'Total'}, inplace=True)
    df_past.TotalRefound = df_past.TotalRefound.astype(float)
    df_today.TotalRefound =df_today.TotalRefound.astype(float)
    return df_today, df_past

            
# cachea 1 hora; ajusta según actualizaciones


def cleaning(df_sales):
    #Merging id stores en sales to know the name
    df_IDstores = pd.read_csv('./data_emilio/Tiendas_id.csv')
    df_IDstores = df_IDstores[['BranchID', 'Name']]
    df_IDstores.BranchID = df_IDstores['BranchID'].str.upper()
    df_sales = df_sales.merge(df_IDstores, on = 'BranchID', how='left')

    #Cleaning data with quantiles and eliminated returns
    df_sales = df_sales[df_sales.TerminalNumber != 999 ]
    df_sales = df_sales[df_sales.total <= df_sales.total.quantile(0.999)]
    df_sales = df_sales.fillna(0)

    #Adjust date/time
    df_sales['fecha_hora'] = pd.to_datetime(df_sales['fecha_hora'], errors='coerce')
    # Solo la fecha (AAAA-MM-DD)
    df_sales['fecha'] = df_sales['fecha_hora'].dt.date
    df_sales["fecha"] = pd.to_datetime(df_sales["fecha"])
    # Solo la hora (HH:MM:SS)
    df_sales['hora'] = df_sales['fecha_hora'].dt.time

    return df_sales

@st.cache_data(ttl=82800) 
def filter_csv(df,rango,periodo):
    fecha_actual = pd.to_datetime("today")
    year = pd.Timedelta(days=365)
    if rango == "Últimos 30 días":
        lapso = pd.Timedelta(days=30)
        fecha_inicio = fecha_actual - lapso
            
    elif rango == "Último trimestre":
        lapso = pd.Timedelta(days=90)
        fecha_inicio = fecha_actual - lapso
       
   
    elif rango == "Último año":
        lapso = pd.Timedelta(days=365)
        fecha_inicio = fecha_actual - lapso
    
    df_today = df[(df['Fecha'] >= fecha_inicio) & (df['Fecha'] <= fecha_actual)]
    
    if periodo == 'Período anterior':
        df_past = df[(df['Fecha'] >= fecha_inicio-lapso) & (df['Fecha'] <= fecha_inicio)]
    else:
        df_past = df[(df['Fecha'] >= fecha_inicio-year) & (df['Fecha'] <= fecha_actual-year)]

    df_past.TotalRefound = df_past.TotalRefound.astype(float)
    df_today.TotalRefound =df_today.TotalRefound.astype(float)
    
    return df_today, df_past