# pagess/admin.py
import streamlit as st
from users_db import load_db, save_db, upsert_user, delete_user, BASE_PAGES

def app():
    st.title("🛡️ Panel de Administración")
    st.caption("Crear/editar usuarios, asignar páginas y cambiar contraseñas.")

    db = load_db()
    users = db.get("users", {})

    st.subheader("Usuarios actuales")
    # Tabla simple
    st.dataframe(
        [
            {
                "usuario": u,
                "rol": info.get("role"),
                "páginas": ", ".join(info.get("pages", [])),
                "requiere cambio de contraseña": info.get("must_change_password", False),
            }
            for u, info in sorted(users.items())
        ],
        use_container_width=True
    )

    st.divider()
    st.subheader("Crear / Editar usuario")

    with st.form("user_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Usuario", placeholder="p. ej. juan")
            role = st.selectbox("Rol", ["user", "admin"], index=0)
        with col2:
            pages = st.multiselect(
                "Páginas permitidas",
                BASE_PAGES + ["Admin"],
                default=(BASE_PAGES + ["Admin"] if role == "admin" else BASE_PAGES[:1])
            )
        new_password = st.text_input(
            "Nueva contraseña (opcional para editar)",
            type="password",
            help="Déjalo vacío para no cambiarla si el usuario ya existe."
        )
        must_change = st.checkbox(
            "Forzar cambio de contraseña al iniciar",
            value=(new_password != "")
        )
        submitted = st.form_submit_button("Guardar / Actualizar")

    if submitted:
        if not username.strip():
            st.error("Debes indicar un nombre de usuario.")
        elif role != "admin" and "Admin" in pages:
            st.error("Un usuario no admin no puede tener acceso a 'Admin'.")
        else:
            upsert_user(load_db(), username.strip(), role, pages, 
                        new_password=(new_password or None),
                        must_change_password=must_change)
            st.success(f"Usuario '{username}' guardado/actualizado.")
            st.rerun()

    st.divider()
    st.subheader("Acciones")
    colA, colB = st.columns(2)
    with colA:
        user_to_delete = st.selectbox("Eliminar usuario", ["(elige)"] + sorted([u for u in users.keys() if u != "admin"]))
        if st.button("Eliminar usuario seleccionado"):
            if user_to_delete == "(elige)":
                st.warning("Elige un usuario.")
            else:
                try:
                    delete_user(load_db(), user_to_delete)
                    st.success(f"Usuario '{user_to_delete}' eliminado.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with colB:
        st.info("Para cambiar tu propia contraseña, usa la sección de cambio de contraseña en el login (aparece cuando es requerido).")
