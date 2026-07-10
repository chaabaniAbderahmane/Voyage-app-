"""
Point d'entrée unique de l'application (structure à plat : tous les fichiers
.py vivent au même niveau que celui-ci, aucun sous-dossier requis).

Cloisonnement des privilèges :
- st.session_state["role"] vaut "admin" OU "client", jamais les deux.
- Tant que ce rôle n'est pas défini, seul l'écran de connexion (auth.login_screen)
  est visible.
- Une fois connecté, seule la vue correspondant au rôle est importée/rendue.
"""
import streamlit as st
from db import init_db
from auth import try_auto_login_from_qr, login_screen
from styles import inject_css

st.set_page_config(page_title="Voyages en Bus", page_icon="🚌", layout="wide")

inject_css()
init_db()

# Connexion automatique si un QR code personnel a été scanné (?token=...)
try_auto_login_from_qr()

role = st.session_state.get("role")

if role == "admin":
    from admin_view import render_admin
    render_admin()

elif role == "client":
    from client_view import render_client
    render_client()

else:
    login_screen()
