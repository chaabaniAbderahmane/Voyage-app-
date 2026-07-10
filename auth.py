"""
Authentification et séparation stricte des privilèges Admin / Client.

- st.session_state["role"] ne peut valoir que "admin" ou "client".
- Tant qu'aucun rôle n'est fixé, seul l'écran de connexion est affiché.
- Un client ne peut jamais accéder aux fonctions admin, et inversement :
  chaque vue vérifie le rôle avant de s'afficher (voir admin_view.py / client_view.py).
"""
import streamlit as st
from db import authenticate_client, get_client_by_token


def get_admin_password() -> str:
    try:
        return st.secrets["admin_password"]
    except Exception:
        return "admin123"  # à changer avant tout usage réel (voir README)


def try_auto_login_from_qr():
    """Si l'URL contient ?token=..., connecte automatiquement le client
    (utilisé quand quelqu'un scanne son QR code personnel)."""
    if st.session_state.get("role"):
        return
    token = st.query_params.get("token")
    if token:
        client = get_client_by_token(token)
        if client:
            st.session_state["role"] = "client"
            st.session_state["client_id"] = client["id"]
            st.rerun()


def login_screen():
    st.markdown(
        """
        <div style="text-align:center; padding: 1.5rem 0 0.5rem 0;">
            <h1>🚌 Voyages en Bus</h1>
            <p style="color:#6b7280;">Connectez-vous à votre espace</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_client, tab_admin = st.tabs(["🧑‍💼 Espace Client", "🛠️ Espace Admin"])

    with tab_client:
        st.caption("Connexion avec l'identifiant et le mot de passe fournis par l'organisateur, "
                    "ou en scannant votre QR code personnel.")
        with st.form("client_login_form"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
        if submitted:
            client = authenticate_client(u.strip(), p.strip())
            if client:
                st.session_state["role"] = "client"
                st.session_state["client_id"] = client["id"]
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")

    with tab_admin:
        st.caption("Réservé à l'organisateur du voyage.")
        with st.form("admin_login_form"):
            pwd = st.text_input("Mot de passe admin", type="password")
            submitted_admin = st.form_submit_button("Se connecter", use_container_width=True)
        if submitted_admin:
            if pwd == get_admin_password():
                st.session_state["role"] = "admin"
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")


def logout():
    for key in ("role", "client_id"):
        st.session_state.pop(key, None)
    st.rerun()
