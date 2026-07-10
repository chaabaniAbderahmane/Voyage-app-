"""
Vue Admin. IMPORTANT : render_admin() ne doit être appelée que si
st.session_state['role'] == 'admin' (vérifié dans app.py).
"""
import streamlit as st
import pandas as pd
from datetime import date

from config import GROUP_TYPES, GROUP_TYPE_LABELS
from db import (
    create_trip, get_trips, get_trip, update_trip, delete_trip,
    create_bus, get_buses, get_bus, update_bus, delete_bus, count_clients_in_bus,
    create_group, get_groups, get_group, update_group, delete_group, count_clients_in_group,
    add_client, find_returning_client, get_clients, get_client_by_id,
    update_client, delete_client, regenerate_credentials,
    set_client_seat, clear_bus_seats, checkin_client, undo_checkin, use_free_trip,
    send_message, get_messages, mark_read, unread_count_for_admin, get_conversations_summary,
)
from seating import assign_seats
from qr_utils import build_client_link, make_qr_image_bytes
from auth import logout

SECTIONS = [
    "🏠 Tableau de bord",
    "🚌 Voyage & bus",
    "👥 Groupes",
    "➕ Voyageurs",
    "🧩 Placement",
    "✅ Présences",
    "📱 QR codes",
    "💬 Messagerie",
    "⭐ Fidélité",
]


def render_admin():
    if st.session_state.get("role") != "admin":
        st.error("Accès refusé : cette section est réservée à l'administrateur.")
        st.stop()

    st.markdown(
        """
        <div class="hero-banner" style="padding:1.3rem;">
            <h1 style="font-size:1.6rem;">🛠️ Espace Administrateur</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        if st.button("🚪 Se déconnecter", width='stretch'):
            logout()

    if not current_trip_id:
        st.info("Créez un voyage dans la barre latérale pour commencer.")
        st.stop()

    trip = get_trip(current_trip_id)
    buses = get_buses(current_trip_id)
    bus_names = {b["name"]: b["id"] for b in buses}
    groups = get_groups(current_trip_id)

    # ---------------- Barre de notification (toujours visible, en haut) ----------------
    unread_total = unread_count_for_admin(current_trip_id)
    if unread_total:
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(
                f"<div class='notif-banner'>🔔 <b>{unread_total}</b> nouveau(x) message(s) "
                f"de voyageur(s) en attente de réponse.</div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.write("")
            if st.button("Voir les messages", key="goto_msgs", width='stretch'):
                st.session_state["admin_section"] = "💬 Messagerie"
                st.rerun()

    # ---------------- Navigation ----------------
    if "admin_section" not in st.session_state:
        st.session_state["admin_section"] = SECTIONS[0]
    section = st.radio("Navigation", SECTIONS, horizontal=True, key="admin_section", label_visibility="collapsed")
    st.divider()

    # ================= TABLEAU DE BORD =================
    if section == "🏠 Tableau de bord":
        clients = get_clients(current_trip_id)
        present = sum(1 for c in clients if c["checked_in"])
        total_seats = sum((b["rows"] * b["seats_per_row"]) for b in buses)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Voyageurs inscrits", len(clients))
        c2.metric("Présents", f"{present}/{len(clients)}" if clients else "0/0")
        c3.metric("Bus", len(buses))
        c4.metric("Capacité totale", total_seats)

        if buses:
            st.subheader("Occupation par bus")
            data = []
            for b in buses:
                n = count_clients_in_bus(b["id"])
                capacity = b["rows"] * b["seats_per_row"]
                data.append({"Bus": b["name"], "Occupés": n, "Libres": max(capacity - n, 0)})
            df = pd.DataFrame(data).set_index("Bus")
            st.bar_chart(df)
        else:
            st.info("Créez un bus dans l'onglet « Voyage & bus » pour voir les statistiques.")

        if groups:
            st.subheader("Groupes")
            gdata = [{"Groupe": g["name"], "Type": GROUP_TYPE_LABELS.get(g["type"], g["type"]),
                      "Membres": count_clients_in_group(g["id"])} for g in groups]
            st.dataframe(pd.DataFrame(gdata), width='stretch', hide_index=True)

    # ================= VOYAGE & BUS =================
    elif section == "🚌 Voyage & bus":
        st.subheader("Informations du voyage")
        with st.form("edit_trip"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("Nom du voyage", value=trip["name"])
            new_date = c2.text_input("Date", value=trip["date"] or "")
            save_trip = st.form_submit_button("💾 Enregistrer")
        if save_trip:
            update_trip(current_trip_id, new_name, new_date)
            st.success("Voyage mis à jour.")
            st.rerun()

        with st.expander("🗑️ Supprimer ce voyage (irréversible)"):
            st.warning("Cela supprime aussi tous les bus, groupes, voyageurs et messages liés à ce voyage.")
            confirm = st.checkbox("Je confirme vouloir supprimer définitivement ce voyage")
            if st.button("Supprimer le voyage", disabled=not confirm):
                delete_trip(current_trip_id)
                st.success("Voyage supprimé.")
                st.rerun()

        st.divider()
        st.subheader("Bus")
        with st.form("new_bus"):
            c1, c2, c3 = st.columns(3)
            bname = c1.text_input("Nom du bus (ex : Bus 1)")
            brows = c2.number_input("Nombre de rangées", min_value=1, value=12)
            bspr = c3.selectbox("Sièges par rangée", [2, 4], index=1)
            add_bus_submit = st.form_submit_button("➕ Ajouter ce bus")
        if add_bus_submit and bname:
            create_bus(current_trip_id, bname, brows, bspr)
            st.success(f"Bus « {bname} » ajouté.")
            st.rerun()

        for b in buses:
            with st.expander(f"✏️ {b['name']} — {b['rows']} rangées × {b['seats_per_row']} sièges"):
                with st.form(f"edit_bus_{b['id']}"):
                    c1, c2, c3 = st.columns(3)
                    ename = c1.text_input("Nom", value=b["name"], key=f"ename_{b['id']}")
                    erows = c2.number_input("Rangées", min_value=1, value=b["rows"], key=f"erows_{b['id']}")
                    espr = c3.selectbox("Sièges/rangée", [2, 4], index=[2, 4].index(b["seats_per_row"]), key=f"espr_{b['id']}")
                    save_bus = st.form_submit_button("💾 Enregistrer")
                if save_bus:
                    update_bus(b["id"], ename, erows, espr)
                    clear_bus_seats(b["id"])
                    st.success("Bus mis à jour. Relancez le placement automatique (les places ont été réinitialisées).")
                    st.rerun()

                n_clients = count_clients_in_bus(b["id"])
                confirm_del = st.checkbox(f"Confirmer la suppression de {b['name']}", key=f"confdel_{b['id']}")
                if st.button(f"🗑️ Supprimer {b['name']}", key=f"delbus_{b['id']}", disabled=not confirm_del):
                    if n_clients:
                        st.warning(f"{n_clients} voyageur(s) seront désassignés (bus et place remis à vide).")
                    delete_bus(b["id"])
                    st.success("Bus supprimé.")
                    st.rerun()

    # ================= GROUPES =================
    elif section == "👥 Groupes":
        st.subheader("Familles, couples, amis")
        st.caption("Créez ici les groupes. Vous les retrouverez ensuite dans une liste déroulante "
                    "au moment d'ajouter les voyageurs, pour être sûr de bien les regrouper dans le bus.")

        with st.form("new_group"):
            c1, c2 = st.columns([2, 1])
            gname = c1.text_input("Nom du groupe (ex : Famille Amrani)")
            gtype = c2.selectbox("Type", GROUP_TYPES, format_func=lambda t: GROUP_TYPE_LABELS[t])
            add_group_submit = st.form_submit_button("➕ Créer le groupe")
        if add_group_submit and gname:
            create_group(current_trip_id, gname, gtype)
            st.success(f"Groupe « {gname} » créé.")
            st.rerun()

        if not groups:
            st.info("Aucun groupe pour l'instant.")
        for g in groups:
            n_members = count_clients_in_group(g["id"])
            with st.expander(f"{GROUP_TYPE_LABELS.get(g['type'], g['type'])} — {g['name']} ({n_members} membre(s))"):
                with st.form(f"edit_group_{g['id']}"):
                    c1, c2 = st.columns([2, 1])
                    egname = c1.text_input("Nom", value=g["name"], key=f"egname_{g['id']}")
                    egtype = c2.selectbox("Type", GROUP_TYPES, index=GROUP_TYPES.index(g["type"]) if g["type"] in GROUP_TYPES else 0,
                                           format_func=lambda t: GROUP_TYPE_LABELS[t], key=f"egtype_{g['id']}")
                    save_group = st.form_submit_button("💾 Enregistrer")
                if save_group:
                    update_group(g["id"], egname, egtype)
                    st.success("Groupe mis à jour.")
                    st.rerun()
                if st.button(f"🗑️ Supprimer ce groupe", key=f"delgrp_{g['id']}"):
                    delete_group(g["id"])
                    st.success("Groupe supprimé (les membres redeviennent voyageurs seuls).")
                    st.rerun()

    # ================= VOYAGEURS =================
    elif section == "➕ Voyageurs":
        st.subheader("Ajouter des voyageurs")
        st.caption(
            "Un identifiant et un mot de passe sont générés automatiquement pour chaque voyageur "
            "(identifiant = nom-prenom, mot de passe = Nom avec majuscule). "
            "Si la personne a déjà voyagé avec vous, ses points de fidélité sont automatiquement repris."
        )

        if not buses:
            st.warning("Créez d'abord un bus dans l'onglet « Voyage & bus ».")
        else:
            group_options = ["Aucun (voyageur seul)"] + [g["name"] for g in groups]

            mode = st.radio("Mode d'ajout", ["Formulaire (un par un)", "Liste (plusieurs personnes)"], horizontal=True)

            if mode == "Formulaire (un par un)":
                with st.form("add_one_client", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    fn = c1.text_input("Prénom")
                    ln = c2.text_input("Nom")
                    c3, c4, c5 = st.columns(3)
                    gender = c3.selectbox("Genre", ["NA", "F", "H"], format_func=lambda x: {"NA": "Non précisé", "F": "Femme", "H": "Homme"}[x])
                    phone = c4.text_input("Téléphone (optionnel)")
                    bus_choice = c5.selectbox("Bus", list(bus_names.keys()))
                    group_choice = st.selectbox(
                        "Groupe (famille / amis / couple)", group_options,
                        help="Choisissez dans la liste à quel groupe appartient ce voyageur, pour que le placement automatique les mette ensemble."
                    )
                    submitted = st.form_submit_button("Ajouter le voyageur", type="primary")
                if submitted and fn and ln:
                    existing = find_returning_client(fn, ln)
                    pts = existing["points"] if existing else 0
                    gid = None
                    if group_choice != "Aucun (voyageur seul)":
                        match = next((g for g in groups if g["name"] == group_choice), None)
                        gid = match["id"] if match else None
                    cid, uname, pwd = add_client(
                        current_trip_id, bus_names[bus_choice], fn, ln, gender, phone, gid, pts
                    )
                    st.success(f"✅ {fn} {ln} ajouté(e). Identifiant : `{uname}` — Mot de passe : `{pwd}`")

            else:
                st.write("Ajoutez une ligne par personne. Choisissez le genre, le groupe et le bus "
                          "directement dans les listes déroulantes de chaque ligne.")
                default_bus = list(bus_names.keys())[0]
                base_df = pd.DataFrame({
                    "Prénom": [""], "Nom": [""], "Genre": ["NA"],
                    "Groupe": ["Aucun (voyageur seul)"], "Bus": [default_bus],
                })
                edited_df = st.data_editor(
                    base_df,
                    num_rows="dynamic",
                    width='stretch',
                    column_config={
                        "Genre": st.column_config.SelectboxColumn(options=["NA", "F", "H"], required=True),
                        "Groupe": st.column_config.SelectboxColumn(options=group_options, required=True),
                        "Bus": st.column_config.SelectboxColumn(options=list(bus_names.keys()), required=True),
                    },
                    key="bulk_editor",
                )
                if st.button("Importer la liste", type="primary"):
                    added = []
                    for _, row in edited_df.iterrows():
                        fn, ln = str(row["Prénom"]).strip(), str(row["Nom"]).strip()
                        if not fn or not ln or fn == "nan" or ln == "nan":
                            continue
                        gid = None
                        if row["Groupe"] != "Aucun (voyageur seul)":
                            match = next((g for g in groups if g["name"] == row["Groupe"]), None)
                            gid = match["id"] if match else None
                        existing = find_returning_client(fn, ln)
                        pts = existing["points"] if existing else 0
                        cid, uname, pwd = add_client(
                            current_trip_id, bus_names[row["Bus"]], fn, ln, row["Genre"], "", gid, pts
                        )
                        added.append({"Nom": f"{fn} {ln}", "Identifiant": uname, "Mot de passe": pwd})
                    if added:
                        st.success(f"{len(added)} voyageur(s) importé(s).")
                        st.dataframe(pd.DataFrame(added), width='stretch', hide_index=True)
                    else:
                        st.warning("Aucune ligne valide détectée (Prénom + Nom requis).")

        st.divider()
        st.subheader("Liste des voyageurs de ce voyage")
        clients = get_clients(current_trip_id)
        search = st.text_input("🔎 Rechercher un voyageur", placeholder="Tapez un nom...")
        filtered = [c for c in clients if search.lower() in f"{c['first_name']} {c['last_name']}".lower()] if search else clients

        if filtered:
            df = pd.DataFrame([{
                "Nom": f"{c['first_name']} {c['last_name']}",
                "Bus": next((b["name"] for b in buses if b["id"] == c["bus_id"]), "—"),
                "Groupe": next((g["name"] for g in groups if g["id"] == c["group_id"]), "—"),
                "Genre": c["gender"],
                "Identifiant": c["username"],
                "Mot de passe": c["password"],
                "Place": c["seat"] or "—",
                "Points": c["points"],
            } for c in filtered])
            st.dataframe(df, width='stretch', hide_index=True)
            st.download_button(
                "⬇️ Exporter la liste (CSV)",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=f"voyageurs_{trip['name']}.csv",
                mime="text/csv",
            )

            st.markdown("##### Modifier ou supprimer un voyageur")
            names = [f"{c['first_name']} {c['last_name']}" for c in filtered]
            sel = st.selectbox("Voyageur à modifier", names, key="edit_client_select")
            client = next(c for c in filtered if f"{c['first_name']} {c['last_name']}" == sel)
            with st.form("edit_client_form"):
                c1, c2 = st.columns(2)
                efn = c1.text_input("Prénom", value=client["first_name"])
                eln = c2.text_input("Nom", value=client["last_name"])
                c3, c4, c5 = st.columns(3)
                egender = c3.selectbox("Genre", ["NA", "F", "H"], index=["NA", "F", "H"].index(client["gender"]))
                ephone = c4.text_input("Téléphone", value=client["phone"] or "")
                ebus = c5.selectbox("Bus", list(bus_names.keys()),
                                     index=list(bus_names.values()).index(client["bus_id"]) if client["bus_id"] in bus_names.values() else 0)
                egroup = st.selectbox("Groupe", group_options,
                                       index=(group_options.index(next((g["name"] for g in groups if g["id"] == client["group_id"]), "Aucun (voyageur seul)"))
                                              if client["group_id"] else 0))
                save_client = st.form_submit_button("💾 Enregistrer les modifications", type="primary")
            if save_client:
                gid = None
                if egroup != "Aucun (voyageur seul)":
                    match = next((g for g in groups if g["name"] == egroup), None)
                    gid = match["id"] if match else None
                update_client(client["id"], efn, eln, egender, ephone, bus_names[ebus], gid)
                st.success("Voyageur mis à jour.")
                st.rerun()

            cdel1, cdel2 = st.columns(2)
            if cdel1.button("🔑 Régénérer identifiant/mot de passe"):
                uname, pwd = regenerate_credentials(client["id"])
                st.success(f"Nouveaux identifiants : `{uname}` / `{pwd}`")
            if cdel2.button("🗑️ Supprimer ce voyageur"):
                delete_client(client["id"])
                st.success("Voyageur supprimé.")
                st.rerun()
        else:
            st.info("Aucun voyageur trouvé.")

    # ================= PLACEMENT =================
    elif section == "🧩 Placement":
        st.subheader("Attribution automatique des places")
        st.caption(
            "Priorité : 1) familles ensemble, 2) couples ensemble, 3) amis ensemble, "
            "4) voyageurs seuls regroupés par genre, 5) reste du bus rempli automatiquement."
        )
        if not buses:
            st.warning("Créez d'abord un bus.")
        else:
            target_bus = st.selectbox("Bus à placer", list(bus_names.keys()), key="assign_bus")
            bus_id = bus_names[target_bus]
            bus_row = get_bus(bus_id)
            bus_clients = get_clients(current_trip_id, bus_id)
            group_types = {g["id"]: g["type"] for g in groups}

            if st.button("🧩 Lancer le placement automatique", type="primary"):
                client_dicts = [{"id": c["id"], "group_id": c["group_id"], "gender": c["gender"]} for c in bus_clients]
                assignment, unassigned, total_seats = assign_seats(client_dicts, bus_row["rows"], bus_row["seats_per_row"], group_types)
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
                    "Groupe": next((g["name"] for g in groups if g["id"] == c["group_id"]), "—"),
                    "Genre": c["gender"],
                    "Place": c["seat"] or "Non attribuée",
                } for c in bus_clients])
                st.dataframe(df, width='stretch', hide_index=True)

    # ================= PRÉSENCES =================
    elif section == "✅ Présences":
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
                cols[0].write(f"**{c['first_name']} {c['last_name']}**  \nPlace : {c['seat'] or '—'}")
                if c["checked_in"]:
                    cols[1].markdown("<span class='success-chip'>✅ Présent</span>", unsafe_allow_html=True)
                    cols[2].caption(f"confirmé par {c['checkin_by']}")
                    if cols[3].button("Annuler", key=f"undo_{c['id']}"):
                        undo_checkin(c["id"])
                        st.rerun()
                else:
                    cols[1].markdown("<span class='pending-chip'>⏳ En attente</span>", unsafe_allow_html=True)
                    if cols[2].button("Confirmer pour lui/elle", key=f"chk_{c['id']}"):
                        checkin_client(c["id"], by="admin")
                        st.rerun()

    # ================= QR CODES =================
    elif section == "📱 QR codes":
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
            link = build_client_link(client["token"])
            qr_bytes = make_qr_image_bytes(link)
            col1, col2 = st.columns([1, 2])
            col1.image(qr_bytes, caption=f"{client['first_name']} {client['last_name']}", width=220)
            col2.write(f"**Identifiant :** `{client['username']}`")
            col2.write(f"**Mot de passe :** `{client['password']}`")
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
                                link_c = build_client_link(c["token"])
                                col.image(make_qr_image_bytes(link_c), caption=f"{c['first_name']} {c['last_name']}", width='stretch')

    # ================= MESSAGERIE =================
    elif section == "💬 Messagerie":
        st.subheader("💬 Messagerie")
        summaries = get_conversations_summary(current_trip_id)
        if not summaries:
            st.info("Aucun voyageur pour l'instant.")
        else:
            options = [f"{'🔴 ' if s['unread'] else '⚪ '}{s['name']} — {s['preview']}" for s in summaries]
            idx = st.selectbox("Conversation", range(len(options)), format_func=lambda i: options[i])
            convo = summaries[idx]
            mark_read(convo["id"], "admin")
            msgs = get_messages(convo["id"])

            chat_box = st.container(height=420, border=True)
            with chat_box:
                if not msgs:
                    st.caption("Aucun message pour l'instant dans cette conversation.")
                for m in msgs:
                    role = "user" if m["sender"] == "client" else "assistant"
                    avatar = "🧑" if m["sender"] == "client" else "🛠️"
                    with st.chat_message(role, avatar=avatar):
                        st.write(m["text"])
                        st.caption(m["timestamp"][:16].replace("T", " "))

            prompt = st.chat_input(f"Répondre à {convo['name']}...")
            if prompt:
                send_message(convo["id"], "admin", prompt)
                st.rerun()

    # ================= FIDÉLITÉ =================
    elif section == "⭐ Fidélité":
        st.subheader("⭐ Programme de fidélité")
        st.caption("1 point par voyage effectué (confirmé le jour J). Le 10e voyage est offert.")
        clients = get_clients(current_trip_id)
        if clients:
            for c in sorted(clients, key=lambda c: -c["points"]):
                cols = st.columns([3, 2, 2])
                cols[0].write(f"**{c['first_name']} {c['last_name']}**")
                cols[1].write(f"⭐ {c['points']} point(s)")
                if c["free_trip_available"]:
                    if cols[2].button("🎁 Marquer le voyage gratuit utilisé", key=f"free_{c['id']}"):
                        use_free_trip(c["id"])
                        st.rerun()
                else:
                    cols[2].caption(f"{10 - (c['points'] % 10)} voyage(s) avant le prochain gratuit")
        else:
            st.info("Aucun voyageur pour l'instant.")
