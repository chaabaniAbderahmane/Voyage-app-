"""Authentification admin (mot de passe unique, défini dans st.secrets)."""
import streamlit as st


def get_admin_password() -> str:
    try:
        return st.secrets["admin_password"]
    except Exception:
        return "admin123"  # mot de passe par défaut si secrets.toml non configuré


def admin_login_form():
    st.subheader("🔐 Connexion administrateur")
    with st.form("admin_login"):
        pwd = st.text_input("Mot de passe admin", type="password")
        submitted = st.form_submit_button("Se connecter")
    if submitted:
        if pwd == get_admin_password():
            st.session_state["is_admin"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")


def require_admin():
    if not st.session_state.get("is_admin"):
        admin_login_form()
        st.stop()
