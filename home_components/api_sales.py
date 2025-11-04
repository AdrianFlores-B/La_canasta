import requests
import pandas as pd
from datetime import datetime, date, timedelta
import streamlit as st
from home_components import cleaning_data as cd
import os
import sqlite3
import pandas as pd
import streamlit as st

# ========================
# Configuración
# ========================
DB_PATH = "data_base/data.db"
CSV_LOCAL_PATH = "data_base/full.csv"  # backup local opcional
DRIVE_URL = "data_base/full.csv"
TABLE_NAME = "ventas"
os.makedirs("data_base", exist_ok=True)

# ========================
# Conexión cacheada a SQLite
# ========================
@st.cache_resource
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# ========================
# Crear tabla con tus columnas
# ========================
def ensure_table(conn):
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            "Unnamed: 0" INTEGER,
            SaleId TEXT,
            fecha_hora TEXT,
            BranchID TEXT,
            Total REAL,
            TerminalNumber REAL,
            TotalRefound REAL,
            SaleReturned TEXT,
            Sucursal TEXT,
            Fecha TEXT,
            hora TEXT
        );
    """)
    conn.commit()

# ========================
# Función principal
# ========================
@st.cache_data(ttl=82800)
def update_data():
    conn = get_connection()
    ensure_table(conn)  # ✅ 1) crea/asegura la tabla ANTES de consultar

    # ¿La tabla está vacía?
    count = pd.read_sql(f"SELECT COUNT(*) AS n FROM {TABLE_NAME}", conn).loc[0, "n"]

    if count == 0:
        from sales_components import sales_plots as sp
        # ✅ Bootstrap: se lee de Drive SOLO una vez
        df_boot = sp.load_all_data()

        df_to_db = df_boot.copy()

        # ✅ Normaliza columnas de fecha/fecha-hora
        if 'Fecha' in df_to_db.columns:
            df_to_db['Fecha'] = pd.to_datetime(df_to_db['Fecha'], errors='coerce') \
                                .dt.strftime('%Y-%m-%d')

        if 'fecha_hora' in df_to_db.columns:
            df_to_db['fecha_hora'] = pd.to_datetime(df_to_db['fecha_hora'], errors='coerce') \
                                    .dt.strftime('%Y-%m-%d %H:%M:%S')

        # (opcional) si tienes una columna 'hora' separada y llega como Timestamp:
        if 'hora' in df_to_db.columns and pd.api.types.is_datetime64_any_dtype(df_to_db['hora']):
            df_to_db['hora'] = pd.to_datetime(df_to_db['hora'], errors='coerce') \
                                .dt.strftime('%H:%M:%S')

        # ✅ Reemplaza NaN por None para que se inserten como NULL en SQLite
        df_to_db = df_to_db.where(pd.notnull(df_to_db), None)

        # Asegura columnas esperadas (como ya tenías)
        cols = [
            "Unnamed: 0","SaleId","fecha_hora","BranchID","Total",
            "TerminalNumber","TotalRefound","SaleReturned","Sucursal","Fecha","hora"
        ]
        for c in cols:
            if c not in df_to_db.columns:
                df_to_db[c] = None

        # Inserta
        df_to_db[cols].to_sql(TABLE_NAME, conn, if_exists="append", index=False, method=None)
        df_current = df_boot 
        # retornamos el estado inicial cargado
    else:
        # ✅ Flujo normal: leer SIEMPRE desde SQLite
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)

        # Preparar fechas para incrementales
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        last_date = df["Fecha"].max()
        fecha_actual = pd.to_datetime("today")

        # Traer NUEVOS datos desde tu API
        df_new = sales_period(last_date, fecha_actual)   # <-- tu función
        df_new = cd.cleaning(df_new)                     # <-- tu limpieza
        df_new.rename(columns={"Name": "Sucursal", "fecha": "Fecha", "total": "Total"}, inplace=True)
        df_new["Fecha"] = pd.to_datetime(df_new["Fecha"], errors="coerce")

        # Filtrar duplicados por SaleId con isin
        df["SaleId"] = df["SaleId"].astype(str)
        df_new["SaleId"] = df_new["SaleId"].astype(str)
        mask_new = ~df_new["SaleId"].isin(df["SaleId"])
        df_new_only = df_new[mask_new]

        # Insertar SOLO lo nuevo en SQLite
        if not df_new_only.empty:
            df_to_db = df_new_only.copy()
            df_to_db["Fecha"] = pd.to_datetime(df_to_db["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")

            cols = [
                "Unnamed: 0","SaleId","fecha_hora","BranchID","Total",
                "TerminalNumber","TotalRefound","SaleReturned","Sucursal","Fecha","hora"
            ]
            for c in cols:
                if c not in df_to_db.columns:
                    df_to_db[c] = None

            df_to_db[cols].to_sql(TABLE_NAME, conn, if_exists="append", index=False)

            # Construimos df_current actualizado (df + nuevos)
            df_current = pd.concat([df, df_new_only], ignore_index=True)
        else:
            df_current = df  # no hubo nuevos

        # Opcional: mantener backup CSV local sincronizado
        df_current.to_csv(CSV_LOCAL_PATH, index=False)
        df_current['Fecha'] = pd.to_datetime(df_current["Fecha"], errors="coerce")
    return df_current


@st.cache_data(ttl=82800) 
def sales(BRANCHID='a0167c49-80b9-4e97-a38c-29243eb5735a', date_from=date.today() - timedelta(days=250), date_to=date.today() - timedelta(days=1)):
    """
    Se conecta a la API, obtiene un token y descarga las ventas para una sucursal y rango de fechas.
    Devuelve un DataFrame de pandas con los datos o un DataFrame vacío si ocurre un error.
    """
    BASE_URL = "http://85.31.225.50:5000/"  # PRUEBAS
    USER = "admin"
    PASSWORD = "#ERHz1417"

    login_url = f"{BASE_URL.rstrip('/')}/auth/login"

    login_payload = {
        "variables": {
            "user": USER,
            "pass": PASSWORD,
            "branch": BRANCHID
        }
    }

    print(f"Iniciando login para sucursal: {BRANCHID}...")
    try:
        resp = requests.post(login_url, json=login_payload, timeout=30)
        resp.raise_for_status()  # Lanza un error para respuestas 4xx o 5xx
        login_data = resp.json()
        print(f"Login para {BRANCHID} exitoso (Status: {resp.status_code})")
        
        token = login_data.get("access_token")
        if not token:
            print(f"Error: Login para {BRANCHID} no devolvió un access_token.")
            raise RuntimeError("Login sin access_token")

        # ----------  VENTAS ----------
        # Asegurarse que las fechas tienen el formato correcto
        if isinstance(date_from, datetime):
            from_str = date_from.strftime("%d/%m/%Y")
        else: # asume que es un objeto date
            from_str = date_from.strftime("%d/%m/%Y")

        if isinstance(date_to, datetime):
            to_str = date_to.strftime("%d/%m/%Y")
        else: # asume que es un objeto date
            to_str = date_to.strftime("%d/%m/%Y")

        sales_url = f"{BASE_URL.rstrip('/')}/branches/{BRANCHID}/sales/full?from={from_str}&to={to_str}"
        print(f"Solicitando ventas de {BRANCHID} desde {from_str} hasta {to_str}")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        sales_resp = requests.get(sales_url, headers=headers, timeout=120) # Timeout aumentado para ventas
        sales_resp.raise_for_status()
        sales_json = sales_resp.json()
        print(f"Datos de ventas para {BRANCHID} recibidos.")

        # ---------- CREACION DATAFRAMES ----------
        ventas_rows = []
        for item in sales_json.get("Sales", []):
            s = item.get("Sale", {})
            ventas_rows.append({
                "SaleId": s.get("SaleId"),
                "fecha_hora": s.get("Date"),
                "BranchID": s.get("BranchId"),
                "total": s.get("Total"),
                "TerminalNumber": s.get("TerminalNumber"),
                "TotalRefound": s.get("TotalRefound"),
                "SaleReturned": s.get("SaleReturned"),
            })

        df_sales = pd.DataFrame(ventas_rows)
        print(f"Se procesaron {len(df_sales)} registros de ventas para {BRANCHID}.")
        return df_sales

    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP para {BRANCHID}: {http_err} - Respuesta: {http_err.response.text[:500]}")
        return pd.DataFrame() # Devuelve un DataFrame vacío en caso de error
    except requests.exceptions.RequestException as req_err:
        print(f"Error de conexión/timeout para {BRANCHID}: {req_err}")
        return pd.DataFrame() # Devuelve un DataFrame vacío
    except Exception as e:
        print(f"Un error inesperado ocurrió para {BRANCHID}: {e}")
        return pd.DataFrame() # Devuelve un DataFrame vacío

@st.cache_data(ttl=82800) 
def sales_period(date_from, date_to):
        # --- Load local data ---

    df_IDstores = pd.read_csv('./data_emilio/Tiendas_id.csv')[['BranchID', 'Name']]

    # --- Build branches list (exclude specific IDs) ---
    exclude_ids = {
        '7d538af4-1336-4e55-ac62-4c692398731a'

    }
    branches = [
        b for b in df_IDstores['BranchID'].dropna().unique().tolist()
        if b not in exclude_ids
    ]

    df_list = []

    for i, branch in enumerate(branches, start=1):
        try:
            df1 = sales(branch, date_from, date_to)
            if not df1.empty:
                df_list.append(df1)
        except Exception as e:
            print(f"Error requesting sales for branch {branch}: {e}")


    
    return pd.concat(df_list, ignore_index=True)

@st.cache_data(ttl=82800)
def load_data(path: str):
    # Parquet es súper rápido y columnar
    return pd.read_parquet('../data_base/all_data.parquet')
