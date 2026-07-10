"""
Vue Client. IMPORTANT : render_client() ne doit être appelée que si
st.session_state['role'] == 'client' (vérifié dans app.py).
"""
import streamlit as st

from db import (
    get_client_by_id, checkin_client, get_trip, get_bus,
    send_message, get_messages, mark_read, unread_count_for_client,
)
from auth import logout


def _chat_section(client):
    st.subheader("💬 Discuter avec l'organisateur")
    mark_read(client["id"], "client")
    msgs = get_messages(client["id"])
    box = st.container(height=320, border=True)
    with box:
        if not msgs:
            st.caption("Aucun message pour l'instant. Écrivez-nous si vous avez une question !")
        for m in msgs:
            role = "user" if m["sender"] == "client" else "assistant"
            avatar = "🧑" if m["sender"] == "client" else "🛠️"
            with st.chat_message(role, avatar=avatar):
                st.write(m["text"])
                st.caption(m["timestamp"][:16].replace("T", " "))
    prompt = st.chat_input("Écrire un message à l'organisateur...")
    if prompt:
        send_message(client["id"], "client", prompt)
        st.rerun()


def render_client():
    if st.session_state.get("role") != "client":
        st.error("Accès refusé : cette section est réservée aux voyageurs.")
        st.stop()

    client_id = st.session_state.get("client_id")
    client = get_client_by_id(client_id) if client_id else None
    if not client:
        st.error("Profil introuvable.")
        logout()
        return

    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>🧑‍💼 {client['first_name']} {client['last_name']}</h1>
            <p>Bienvenue dans votre espace voyageur</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    unread_c = unread_count_for_client(client["id"])
    if unread_c:
        st.markdown(
            f"<div class='notif-banner'>🔔 Vous avez <b>{unread_c}</b> nouveau(x) message(s) "
            f"de l'organisateur — répondez juste en dessous 👇</div>",
            unsafe_allow_html=True,
        )
        _chat_section(client)
        st.divider()

    trip = get_trip(client["trip_id"])
    bus = get_bus(client["bus_id"]) if client["bus_id"] else None

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
        if st.button("✅ Je suis présent(e)", width='stretch', type="primary"):
            checkin_client(client["id"], by="client")
            st.rerun()

    st.caption(
        "👵 Besoin d'aide ? Une personne âgée ou peu à l'aise avec l'application peut demander "
        "à l'organisateur de confirmer sa présence directement depuis l'espace admin."
    )

    if not unread_c:
        st.divider()
        _chat_section(client)

    st.divider()
    if st.button("🚪 Se déconnecter"):
        logout()
