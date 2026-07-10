"""
Vue Admin. IMPORTANT : render_admin() ne doit être appelée que si
st.session_state['role'] == 'admin' (vérifié dans app.py). Cette page ne
contient aucune fonction utilisable par un client.
"""
import streamlit as st
import pandas as pd
from datetime import date

from db import (
    create_trip, get_trips, get_trip, update_trip_url,
    create_bus, get_buses, get_bus,
    create_group, get_groups,
    add_client, find_returning_client, get_clients,
    set_client_seat, checkin_client, undo_checkin,
    send_message, get_messages, mark_read, unread_count_for_admin,
)
from seating import assign_seats
from qr_utils import build_client_link, make_qr_image_bytes
from auth import logout


def render_admin():
    # --- Garde-fou de rôle : double sécurité en plus du contrôle dans app.py ---
    if st.session_state.get("role") != "admin":
        st.error("Accès refusé : cette section est réservée à l'administrateur.")
        st.stop()

    st.title("🛠️ Espace Administrateur")

    trips = get_trips()
    trip_names = {f"{t['name']} — {t['date']}": t["id"] for t in trips}

    with st.sidebar:
        st.header("Voyage en cours")
        current_trip_id = None
        if trip_names:
            choice = st.selectbox("Sélectionner un voyage", list(trip_names.keys()))
            current_trip_id = trip_names[choice]
        else:
            st.info("Aucun voyage pour l'instant. Créez-en un ci-dessous.")

        with st.expander("➕ Nouveau voyage"):
            with st.form("new_trip"):
                name = st.text_input("Nom du voyage (ex : Sortie Saïdia)")
                d = st.date_input("Date", value=date.today())
                submitted = st.form_submit_button("Créer le voyage")
            if submitted and name:
                create_trip(name, str(d))
                st.success(f"Voyage « {name} » créé.")
                st.rerun()

        st.divider()
        if st.button("🚪 Se déconnecter"):
            logout()

    if not current_trip_id:
        st.stop()

    trip = get_trip(current_trip_id)
    buses = get_buses(current_trip_id)
    bus_names = {b["name"]: b["id"] for b in buses}

    tabs = st.tabs([
        "🚌 Bus & lien de l'app",
        "➕ Ajouter des voyageurs",
        "🧩 Placement automatique",
        "✅ Présences",
        "📱 QR codes",
        "💬 Messagerie",
        "⭐ Fidélité",
    ])

    # ================= Bus & lien app =================
    with tabs[0]:
        st.subheader("Configurer les bus du voyage")
        with st.form("new_bus"):
            c1, c2, c3 = st.columns(3)
            bname = c1.text_input("Nom du bus (ex : Bus 1)")
            brows = c2.number_input("Nombre de rangées", min_value=1, value=12)
            bspr = c3.selectbox("Sièges par rangée", [2, 4], index=1)
            add_bus_submit = st.form_submit_button("Ajouter ce bus")
        if add_bus_submit and bname:
            create_bus(current_trip_id, bname, brows, bspr)
            st.success(f"Bus « {bname} » ajouté.")
            st.rerun()

        if buses:
            st.dataframe(
                pd.DataFrame([{"Bus": b["name"], "Rangées": b["rows"], "Sièges/rangée": b["seats_per_row"]} for b in buses]),
                use_container_width=True, hide_index=True,
            )
        else:
            st.info("Ajoutez au moins un bus pour pouvoir affecter des voyageurs.")

        st.divider()
        st.subheader("Lien public de l'application (pour générer les QR codes)")
        st.caption("Collez ici l'URL de votre app une fois déployée sur Streamlit Cloud, ex : https://mon-voyage.streamlit.app")
        url = st.text_input("URL de l'application", value=trip["app_url"] or "")
        if st.button("Enregistrer l'URL"):
            update_trip_url(current_trip_id, url)
            st.success("URL enregistrée.")
            st.rerun()

    # ================= Ajouter des voyageurs =================
    with tabs[1]:
        st.subheader("Ajouter des voyageurs")
        st.caption(
            "Un identifiant et un mot de passe sont générés automatiquement pour chaque voyageur "
            "(identifiant = nom-prenom, mot de passe = Nom avec majuscule). "
            "Si la personne a déjà voyagé avec vous, ses points de fidélité sont automatiquement repris."
        )

        if not buses:
            st.warning("Créez d'abord un bus dans l'onglet précédent.")
        else:
            mode = st.radio("Mode d'ajout", ["Formulaire (un par un)", "Texte / dictée en masse"], horizontal=True)

            if mode == "Formulaire (un par un)":
                with st.form("add_one_client", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    fn = c1.text_input("Prénom")
                    ln = c2.text_input("Nom")
                    c3, c4, c5 = st.columns(3)
                    gender = c3.selectbox("Genre", ["NA", "F", "H"], format_func=lambda x: {"NA": "Non précisé", "F": "Femme", "H": "Homme"}[x])
                    phone = c4.text_input("Téléphone (optionnel)")
                    bus_choice = c5.selectbox("Bus", list(bus_names.keys()))
                    group_name = st.text_input("Groupe (famille / amis — laissez vide si seul(e))")
                    group_type = st.selectbox("Type de groupe", ["famille", "amis", "couple"]) if group_name else None
                    submitted = st.form_submit_button("Ajouter le voyageur")
                if submitted and fn and ln:
                    existing = find_returning_client(fn, ln)
                    pts = existing["points"] if existing else 0
                    gid = None
                    if group_name:
                        groups = get_groups(current_trip_id)
                        match = next((g for g in groups if g["name"] == group_name), None)
                        gid = match["id"] if match else create_group(current_trip_id, group_name, group_type)
                    cid, uname, pwd = add_client(
                        current_trip_id, bus_names[bus_choice], fn, ln, gender, phone, gid, pts
                    )
                    st.success(f"✅ {fn} {ln} ajouté(e). Identifiant : `{uname}` — Mot de passe : `{pwd}`")

            else:
                st.write(
                    "Collez ou dictez une ligne par personne, format libre recommandé :\n\n"
                    "`Prénom Nom, genre(F/H), groupe(optionnel)`\n\n"
                    "Exemple :\n```\nSara Amrani, F, Famille Amrani\nYoussef Amrani, H, Famille Amrani\nKarim Idrissi, H\n```"
                )
                bulk_bus = st.selectbox("Bus pour ce lot", list(bus_names.keys()), key="bulk_bus")
                bulk_text = st.text_area("Liste des voyageurs", height=200,
                                          help="Astuce : utilisez le micro 🎤 du clavier de votre téléphone pour dicter la liste directement ici.")
                if st.button("Importer la liste"):
                    lines = [l.strip() for l in bulk_text.splitlines() if l.strip()]
                    added = []
                    for line in lines:
                        parts = [p.strip() for p in line.split(",")]
                        name_part = parts[0]
                        gender = "NA"
                        group_name = None
                        if len(parts) > 1 and parts[1].upper() in ("F", "H"):
                            gender = parts[1].upper()
                        if len(parts) > 2:
                            group_name = parts[2]
                        name_tokens = name_part.split()
                        if len(name_tokens) < 2:
                            continue
                        fn, ln = name_tokens[0], " ".join(name_tokens[1:])
                        gid = None
                        if group_name:
                            groups = get_groups(current_trip_id)
                            match = next((g for g in groups if g["name"] == group_name), None)
                            gid = match["id"] if match else create_group(current_trip_id, group_name, "famille")
                        existing = find_returning_client(fn, ln)
                        pts = existing["points"] if existing else 0
                        cid, uname, pwd = add_client(current_trip_id, bus_names[bulk_bus], fn, ln, gender, "", gid, pts)
                        added.append({"Nom": f"{fn} {ln}", "Identifiant": uname, "Mot de passe": pwd})
                    if added:
                        st.success(f"{len(added)} voyageur(s) importé(s).")
                        st.dataframe(pd.DataFrame(added), use_container_width=True, hide_index=True)
                    else:
                        st.warning("Aucune ligne valide détectée (il faut au moins Prénom + Nom).")

        st.divider()
        st.subheader("Liste des voyageurs de ce voyage")
        clients = get_clients(current_trip_id)
        if clients:
            df = pd.DataFrame([{
                "Nom": f"{c['first_name']} {c['last_name']}",
                "Bus": next((b["name"] for b in buses if b["id"] == c["bus_id"]), "—"),
                "Genre": c["gender"],
                "Identifiant": c["username"],
                "Mot de passe": c["password"],
                "Place": c["seat"] or "—",
                "Points": c["points"],
            } for c in clients])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun voyageur ajouté pour le moment.")

    # ================= Placement automatique =================
    with tabs[2]:
        st.subheader("Attribution automatique des places")
        st.caption(
            "L'algorithme place en priorité les groupes (familles, amis, couples) côte à côte, "
            "puis regroupe les voyageurs seuls par genre, puis remplit le reste du bus."
        )
        if not buses:
            st.warning("Créez d'abord un bus.")
        else:
            target_bus = st.selectbox("Bus à placer", list(bus_names.keys()), key="assign_bus")
            bus_id = bus_names[target_bus]
            bus_row = get_bus(bus_id)
            bus_clients = get_clients(current_trip_id, bus_id)

            if st.button("🧩 Lancer le placement automatique"):
                client_dicts = [{"id": c["id"], "group_id": c["group_id"], "gender": c["gender"]} for c in bus_clients]
                assignment, unassigned, total_seats = assign_seats(client_dicts, bus_row["rows"], bus_row["seats_per_row"])
                for cid, seat in assignment.items():
                    set_client_seat(cid, seat)
                st.success(f"{len(assignment)} place(s) attribuée(s) sur {total_seats} sièges disponibles.")
                if unassigned:
                    st.warning(f"⚠️ {len(unassigned)} voyageur(s) n'ont pas pu être placés — le bus est complet.")
                st.rerun()

            bus_clients = get_clients(current_trip_id, bus_id)
            if bus_clients:
                df = pd.DataFrame([{
                    "Nom": f"{c['first_name']} {c['last_name']}",
                    "Genre": c["gender"],
                    "Place": c["seat"] or "Non attribuée",
                } for c in bus_clients])
                st.dataframe(df, use_container_width=True, hide_index=True)

    # ================= Présences =================
    with tabs[3]:
        st.subheader("Suivi des présences en temps réel")
        if not buses:
            st.warning("Créez d'abord un bus.")
        else:
            pres_bus = st.selectbox("Filtrer par bus", ["Tous"] + list(bus_names.keys()), key="pres_bus")
            bus_id = None if pres_bus == "Tous" else bus_names[pres_bus]
            clients = get_clients(current_trip_id, bus_id)

            present = sum(1 for c in clients if c["checked_in"])
            st.metric("Présents", f"{present} / {len(clients)}")
            st.progress(present / len(clients) if clients else 0)

            for c in clients:
                cols = st.columns([3, 2, 2, 2])
                status = "✅ Présent" if c["checked_in"] else "⏳ En attente"
                cols[0].write(f"**{c['first_name']} {c['last_name']}**  \nPlace : {c['seat'] or '—'}")
                cols[1].write(status)
                if c["checked_in"]:
                    cols[2].caption(f"par {c['checkin_by']}")
                    if cols[3].button("Annuler", key=f"undo_{c['id']}"):
                        undo_checkin(c["id"])
                        st.rerun()
                else:
                    if cols[2].button("Confirmer pour lui/elle", key=f"chk_{c['id']}"):
                        checkin_client(c["id"], by="admin")
                        st.rerun()

    # ================= QR codes =================
    with tabs[4]:
        st.subheader("QR codes personnels")
        st.caption(
            "Imprimez ou envoyez ces QR codes aux voyageurs. En le scannant, l'application "
            "s'ouvre directement sur leur profil personnel — aucune saisie nécessaire."
        )
        clients = get_clients(current_trip_id)
        if not clients:
            st.info("Aucun voyageur pour l'instant.")
        else:
            selected = st.selectbox(
                "Voyageur", [f"{c['first_name']} {c['last_name']}" for c in clients], key="qr_select"
            )
            client = next(c for c in clients if f"{c['first_name']} {c['last_name']}" == selected)
            link = build_client_link(trip["app_url"], client["token"])
            qr_bytes = make_qr_image_bytes(link)
            col1, col2 = st.columns([1, 2])
            col1.image(qr_bytes, caption=f"{client['first_name']} {client['last_name']}", width=220)
            col2.write(f"**Identifiant :** `{client['username']}`")
            col2.write(f"**Mot de passe :** `{client['password']}`")
            col2.write(f"**Lien direct :** {link}")
            col2.download_button("⬇️ Télécharger le QR code", data=qr_bytes,
                                  file_name=f"qr_{client['username']}.png", mime="image/png")

            with st.expander("📄 Générer tous les QR codes du bus sélectionné"):
                if buses:
                    bulk_bus = st.selectbox("Bus", list(bus_names.keys()), key="qr_bulk_bus")
                    bulk_clients = get_clients(current_trip_id, bus_names[bulk_bus])
                    if bulk_clients:
                        ncols = 4
                        rows_ui = [bulk_clients[i:i + ncols] for i in range(0, len(bulk_clients), ncols)]
                        for row_ui in rows_ui:
                            cols = st.columns(ncols)
                            for col, c in zip(cols, row_ui):
                                link_c = build_client_link(trip["app_url"], c["token"])
                                col.image(make_qr_image_bytes(link_c), caption=f"{c['first_name']} {c['last_name']}", use_container_width=True)

    # ================= Messagerie =================
    with tabs[5]:
        st.subheader("💬 Messagerie avec les voyageurs")
        unread = unread_count_for_admin(current_trip_id)
        if unread:
            st.warning(f"{unread} nouveau(x) message(s) non lu(s)")

        clients = get_clients(current_trip_id)
        if not clients:
            st.info("Aucun voyageur pour l'instant.")
        else:
            chat_client = st.selectbox(
                "Conversation avec", [f"{c['first_name']} {c['last_name']}" for c in clients], key="chat_select"
            )
            client = next(c for c in clients if f"{c['first_name']} {c['last_name']}" == chat_client)
            mark_read(client["id"], "admin")
            msgs = get_messages(client["id"])
            box = st.container(height=350)
            with box:
                for m in msgs:
                    role = "🧑 Client" if m["sender"] == "client" else "🛠️ Admin"
                    st.markdown(f"**{role}** — _{m['timestamp'][:16].replace('T', ' ')}_")
                    st.write(m["text"])
                    st.divider()
            with st.form(f"admin_reply_{client['id']}", clear_on_submit=True):
                reply = st.text_input("Votre réponse")
                send = st.form_submit_button("Envoyer")
            if send and reply:
                send_message(client["id"], "admin", reply)
                st.rerun()

    # ================= Fidélité =================
    with tabs[6]:
        st.subheader("⭐ Programme de fidélité")
        st.caption("1 point par voyage effectué (confirmé le jour J). Le 10e voyage est offert.")
        clients = get_clients(current_trip_id)
        if clients:
            df = pd.DataFrame([{
                "Nom": f"{c['first_name']} {c['last_name']}",
                "Points": c["points"],
                "Voyage offert disponible": "🎁 Oui" if c["free_trip_available"] else "Non",
            } for c in clients]).sort_values("Points", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun voyageur pour l'instant.")
