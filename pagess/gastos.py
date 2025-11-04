import os
import streamlit as st
import pandas as pd
from datetime import date, datetime
from users_db import is_admin  # <- usamos tu helper del módulo de usuarios
import plotly.express as px
import plotly.graph_objects as go
from utils_theme import apply_theme
# ---------- Helper compatibilidad rerun ----------
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# ---------- Constantes de archivos ----------
FILE_NON_RECURRENT = "Costos_No_Recurrentes__Ejemplo_.csv"
FILE_RECURRENT     = "Costos_Recurrentes__Ejemplo_.csv"

CSV_COLUMNS = ["ID", "Concepto", "Fecha", "Categoría", "Sucursal", "Monto", "Responsable", "Tipo de Costo"]

# ---------- Utilidades CSV ----------
def ensure_csv(path: str):
    """Crea el CSV con cabecera si no existe."""
    if not os.path.exists(path):
        pd.DataFrame(columns=CSV_COLUMNS).to_csv(path, index=False)

def load_csv(path: str) -> pd.DataFrame:
    ensure_csv(path)
    df = pd.read_csv(path)
    # Asegurar columnas y tipos
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = None
    # Tipos
    if not pd.api.types.is_integer_dtype(df["ID"]):
        # Convierte a int de forma segura
        df["ID"] = pd.to_numeric(df["ID"], errors="coerce").fillna(0).astype(int)
    if not pd.api.types.is_datetime64_any_dtype(df["Fecha"]):
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    # Ordenar por fecha desc e ID desc como default
    df = df[CSV_COLUMNS].sort_values(["Fecha", "ID"], ascending=[False, False]).reset_index(drop=True)
    return df

def next_id(path: str) -> int:
    df = load_csv(path)
    if df.empty:
        return 1
    return int(df["ID"].max()) + 1

def append_row(path: str, row: dict):
    ensure_csv(path)
    df = load_csv(path)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(path, index=False)

def delete_rows_by_ids(path: str, ids_to_delete: list[int]):
    if not ids_to_delete:
        return
    df = load_csv(path)
    df = df[~df["ID"].isin(ids_to_delete)]
    df.to_csv(path, index=False)

# ---------- Página principal ----------
def app():
    st.set_page_config(
        page_title="Costo Casa Renteria",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Verifica sesión
    if "auth_user" not in st.session_state or st.session_state.auth_user is None:
        st.error("No has iniciado sesión.")
        st.stop()

    current_user = st.session_state.auth_user
    #user_is_admin = is_admin(None, current_user) if "is_admin" in globals() else False
    # Nota: si tu is_admin del módulo requiere db, impórtalo y pásalo;
    # en el diseño anterior is_admin(db, username) usa load_db() interno en admin/app.
    # Si tu versión requiere db explícito, adapta:
    from users_db import load_db
    user_is_admin = is_admin(load_db(), current_user)
    apply_theme()
    st.markdown('<h1 class="main-header">🏭 Costo Operativo</h1>', unsafe_allow_html=True)

    # ---------------------- 1) Formulario agregar costo ----------------------
    with st.expander("➕ Agregar nuevo costo operativo", expanded=False):
        with st.form("formulario_costo_unificado", clear_on_submit=True):
            st.subheader("Detalles del Costo")

            concepto = st.text_input("Concepto")
            fecha = st.date_input("Fecha", value=date.today())
            monto = st.number_input("Monto", min_value=0.0, format="%.2f")
            tipo_costo = st.selectbox(
                "Tipo de Costo",
                ["No recurrente", "Recurrente"],
                index=0,
                help="Selecciona si el costo es un gasto único o se repite periódicamente."
            )

            col1, col2 = st.columns(2)
            with col1:
                categoria = st.selectbox("Categoría", ["Servicios", "Nomina", "Mantenimiento", "Renta", "Suministros", "Publicidad", "Honorarios"])
                # RESPONSABLE BLOQUEADO = usuario actual
                st.text_input("Responsable", value=current_user, disabled=True, help="Se asigna automáticamente y no puede cambiarse.")
                responsable = current_user
            with col2:
                sucursal = st.selectbox(
                    "Sucursal",
                    [
                        "MATRIZ"]
                )

            submitted = st.form_submit_button("✅ Agregar Costo")

            if submitted:
                if not concepto or monto <= 0:
                    st.warning("Por favor, completa Concepto y Monto > 0.")
                else:
                    target_file = FILE_RECURRENT if tipo_costo == "Recurrente" else FILE_NON_RECURRENT
                    try:
                        row = {
                            "ID": next_id(target_file),
                            "Concepto": concepto.strip(),
                            "Fecha": pd.to_datetime(fecha),
                            "Categoría": categoria,
                            "Sucursal": sucursal,
                            "Monto": float(monto),
                            "Responsable": responsable,
                            "Tipo de Costo": tipo_costo
                        }
                        append_row(target_file, row)
                        st.success(f"✅ Costo '{concepto}' agregado correctamente en '{target_file}'.")
                        safe_rerun()
                    except Exception as e:
                        st.error(f"Ocurrió un error al guardar: {e}")

    # ---------------------- 2) Visualización: No Recurrentes ----------------------
    st.markdown("---")
    st.markdown("## 📊 Costos No Recurrentes")

    try:
        df_nr = load_csv(FILE_NON_RECURRENT)

        # Filtro por permisos: si NO es admin, solo sus costos
        if not user_is_admin:
            df_nr = df_nr[df_nr["Responsable"] == current_user]

        if df_nr.empty:
            st.info("No hay costos no recurrentes para mostrar.")
        else:
            # Rango de fechas
            min_d, max_d = df_nr["Fecha"].min().date(), df_nr["Fecha"].max().date()
            col_nr1, col_nr2 = st.columns(2)
            with col_nr1:
                fecha_inicio_nr = st.date_input("Fecha de inicio (No Recurrentes)", value=min_d, key="nr_start")
            with col_nr2:
                fecha_fin_nr = st.date_input("Fecha de fin (No Recurrentes)", value=max_d, key="nr_end")

            fecha_inicio_nr = pd.to_datetime(fecha_inicio_nr)
            fecha_fin_nr = pd.to_datetime(fecha_fin_nr)  # <- respeta selección

            df_filtrado_nr = df_nr[(df_nr["Fecha"] >= fecha_inicio_nr) & (df_nr["Fecha"] <= fecha_fin_nr)]

            st.dataframe(df_filtrado_nr, use_container_width=True)
            st.metric("Total No Recurrente (periodo seleccionado)", f"${df_filtrado_nr['Monto'].sum():,.2f}")

    except Exception as e:
        st.error(f"No se pudieron cargar los costos no recurrentes: {e}")

    # ---------------------- 3) Visualización: Recurrentes ----------------------
    st.markdown("---")
    st.markdown("## 🔁 Costos Recurrentes")

    try:
        df_r = load_csv(FILE_RECURRENT)

        # Filtro por permisos: si NO es admin, solo sus costos
        if not user_is_admin:
            df_r = df_r[df_r["Responsable"] == current_user]

        if df_r.empty:
            st.info("No hay costos recurrentes para mostrar.")
        else:
            min_d, max_d = df_r["Fecha"].min().date(), df_r["Fecha"].max().date()
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                fecha_inicio_r = st.date_input("Fecha de inicio (Recurrentes)", value=min_d, key="r_start")
            with col_r2:
                fecha_fin_r = st.date_input("Fecha de fin (Recurrentes)", value=max_d, key="r_end")

            fecha_inicio_r = pd.to_datetime(fecha_inicio_r)
            fecha_fin_r = pd.to_datetime(fecha_fin_r)  # <- respeta selección

            df_filtrado_r = df_r[(df_r["Fecha"] >= fecha_inicio_r) & (df_r["Fecha"] <= fecha_fin_r)]

            st.dataframe(df_filtrado_r, use_container_width=True)
            st.metric("Total Recurrente (periodo seleccionado)", f"${df_filtrado_r['Monto'].sum():,.2f}")

    except Exception as e:
        st.error(f"No se pudieron cargar los costos recurrentes: {e}")

    
    col1, col2 = st.columns(2)
    with col1:
        df_totales = pd.concat([df_r, df_nr])
        df_totales = df_totales.groupby("Tipo de Costo")['Monto'].sum().reset_index()

        # Crear gráfica de pastel
        fig = px.pie(
            df_totales,
            names="Tipo de Costo",
            values='Monto',
            title='Costos por Tipo',
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
    
    with col2:
        df_totales = pd.concat([df_r, df_nr])
        df_totales = df_totales.groupby("Categoría")['Monto'].sum().reset_index()

        # Crear gráfica de pastel
        fig = px.pie(
            df_totales,
            names="Categoría",
            values='Monto',
            title='Costos por Categoría',
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

    # ---------------------- 4) Panel de eliminación (solo Admin) ----------------------
    if user_is_admin:
        st.markdown("---")
        st.subheader("🗑️ Panel de eliminación de costos (Admin)")

        tabs = st.tabs(["No Recurrentes", "Recurrentes"])
        with tabs[0]:
            try:
                df_nr_all = load_csv(FILE_NON_RECURRENT)
                if df_nr_all.empty:
                    st.info("No hay registros no recurrentes.")
                else:
                    st.caption("Selecciona los IDs a eliminar:")
                    ids_nr = st.multiselect(
                        "IDs No Recurrentes",
                        options=df_nr_all["ID"].tolist(),
                        format_func=lambda x: f"ID {x} | {df_nr_all.loc[df_nr_all['ID']==x, 'Concepto'].values[0]} | {df_nr_all.loc[df_nr_all['ID']==x, 'Responsable'].values[0]}",
                        key="del_nr_ids"
                    )
                    if st.button("Eliminar seleccionados (No Recurrentes)", type="primary"):
                        delete_rows_by_ids(FILE_NON_RECURRENT, ids_nr)
                        st.success(f"Eliminados {len(ids_nr)} registros no recurrentes.")
                        safe_rerun()
            except Exception as e:
                st.error(f"Error listando NR: {e}")

        with tabs[1]:
            try:
                df_r_all = load_csv(FILE_RECURRENT)
                if df_r_all.empty:
                    st.info("No hay registros recurrentes.")
                else:
                    st.caption("Selecciona los IDs a eliminar:")
                    ids_r = st.multiselect(
                        "IDs Recurrentes",
                        options=df_r_all["ID"].tolist(),
                        format_func=lambda x: f"ID {x} | {df_r_all.loc[df_r_all['ID']==x, 'Concepto'].values[0]} | {df_r_all.loc[df_r_all['ID']==x, 'Responsable'].values[0]}",
                        key="del_r_ids"
                    )
                    if st.button("Eliminar seleccionados (Recurrentes)", type="primary"):
                        delete_rows_by_ids(FILE_RECURRENT, ids_r)
                        st.success(f"Eliminados {len(ids_r)} registros recurrentes.")
                        safe_rerun()
            except Exception as e:
                st.error(f"Error listando R: {e}")



