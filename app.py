import streamlit as st
from db import init_db

st.set_page_config(
    page_title="Voyages en Bus",
    page_icon="🚌",
    layout="centered",
)

init_db()

st.markdown(
    """
    <style>
    .hero {
        text-align: center;
        padding: 2.2rem 1rem 1rem 1rem;
    }
    .hero h1 {
        font-size: 2.3rem;
        margin-bottom: 0.2rem;
    }
    .hero p {
        color: #6b7280;
        font-size: 1.05rem;
    }
    .role-card {
        border-radius: 18px;
        padding: 1.6rem;
        text-align: center;
        border: 1px solid #e5e7eb;
    }
    </style>
    <div class="hero">
        <h1>🚌 Voyages en Bus</h1>
        <p>Gestion des présences, des places et de la fidélité pour vos sorties organisées.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Auto-login client si un QR code a été scanné (token dans l'URL)
token = st.query_params.get("token")
if token:
    st.info("Code d'accès détecté — ouverture de votre espace personnel…")
    st.switch_page("pages/2_🧑‍💼_Espace_Client.py")

col1, col2 = st.columns(2)
with col1:
    st.markdown('<div class="role-card">', unsafe_allow_html=True)
    st.markdown("### 🛠️ Espace Admin")
    st.write("Créer un voyage, ajouter les voyageurs, gérer les présences, la messagerie.")
    if st.button("Accéder à l'espace admin", use_container_width=True):
        st.switch_page("pages/1_🛠️_Admin.py")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="role-card">', unsafe_allow_html=True)
    st.markdown("### 🧑‍💼 Espace Client")
    st.write("Confirmer votre présence, voir votre place, contacter l'organisateur.")
    if st.button("Accéder à mon espace", use_container_width=True):
        st.switch_page("pages/2_🧑‍💼_Espace_Client.py")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()
st.caption(
    "💡 Astuce : les clients qui arrivent le jour J scannent leur QR code personnel "
    "et arrivent directement sur leur profil, sans rien taper."
)
