import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

from utils.db import (
    init_db, get_client_by_token, authenticate_client, get_client_by_id,
    checkin_client, get_trip, get_bus, send_message, get_messages, mark_read,
)

st.set_page_config(page_title="Mon espace — Voyages en Bus", page_icon="🧑‍💼", layout="centered")
init_db()

st.title("🧑‍💼 Mon espace voyageur")

# ---------- Connexion ----------
if "client_id" not in st.session_state:
    token = st.query_params.get("token")
    if token:
        client = get_client_by_token(token)
        if client:
            st.session_state["client_id"] = client["id"]
            st.rerun()
        else:
            st.error("Code d'accès invalide ou expiré.")

if "client_id" not in st.session_state:
    st.write("Connectez-vous avec l'identifiant et le mot de passe fournis par l'organisateur, "
             "ou scannez votre QR code personnel le jour du départ.")
    with st.form("client_login"):
        u = st.text_input("Identifiant")
        p = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")
    if submitted:
        client = authenticate_client(u.strip(), p.strip())
        if client:
            st.session_state["client_id"] = client["id"]
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect.")
    st.stop()

# ---------- Profil connecté ----------
client = get_client_by_id(st.session_state["client_id"])
if not client:
    st.error("Profil introuvable.")
    st.session_state.pop("client_id", None)
    st.stop()

trip = get_trip(client["trip_id"])
bus = get_bus(client["bus_id"]) if client["bus_id"] else None

st.success(f"Bienvenue, **{client['first_name']} {client['last_name']}** 👋")

col1, col2 = st.columns(2)
col1.metric("Voyage", trip["name"] if trip else "—")
col2.metric("Bus", bus["name"] if bus else "Non assigné")

col3, col4 = st.columns(2)
col3.metric("Votre place", client["seat"] or "En attente d'attribution")
col4.metric("Points de fidélité", client["points"])

if client["free_trip_available"]:
    st.balloons()
    st.success("🎁 Félicitations ! Vous avez atteint 10 voyages : votre prochain voyage est OFFERT. "
                "Présentez ceci à l'organisateur.")

st.divider()

if client["checked_in"]:
    st.info(f"✅ Votre présence a déjà été confirmée ({'par vous' if client['checkin_by']=='client' else 'par un organisateur'}).")
else:
    st.write("Merci de confirmer votre présence à l'arrivée dans le bus :")
    if st.button("✅ Je suis présent(e)", use_container_width=True, type="primary"):
        checkin_client(client["id"], by="client")
        st.rerun()

st.caption(
    "👵 Besoin d'aide ? Une personne âgée ou peu à l'aise avec l'application peut demander "
    "à l'organisateur de confirmer sa présence directement depuis l'espace admin."
)

st.divider()
st.subheader("💬 Contacter l'organisateur")
mark_read(client["id"], "client")
msgs = get_messages(client["id"])
box = st.container(height=300)
with box:
    if not msgs:
        st.caption("Aucun message pour l'instant. Écrivez-nous si vous avez une question !")
    for m in msgs:
        role = "🧑 Vous" if m["sender"] == "client" else "🛠️ Organisateur"
        st.markdown(f"**{role}** — _{m['timestamp'][:16].replace('T', ' ')}_")
        st.write(m["text"])
        st.divider()

with st.form("client_msg", clear_on_submit=True):
    text = st.text_input("Votre message")
    send = st.form_submit_button("Envoyer")
if send and text:
    send_message(client["id"], "client", text)
    st.rerun()

st.divider()
if st.button("🚪 Se déconnecter"):
    st.session_state.pop("client_id", None)
    st.rerun()
