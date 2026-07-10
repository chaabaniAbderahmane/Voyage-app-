"""
Algorithme d'attribution des places dans le bus.

Critères pris en compte, dans cet ordre de priorité :
1. Les membres d'un même groupe (famille, couple, amis) sont placés cote à cote /
   sur des sièges contigus, si possible dans la même rangée.
2. Les voyageurs seuls (solo) sont regroupés par genre quand c'est pertinent
   (ex : groupe de filles seules ensemble, groupe de garçons seuls ensemble).
3. Les groupes les plus grands sont placés en premier (plus difficiles à caser).
4. Le reste des places est rempli dans l'ordre.

Plan de bus : rangées de `seats_per_row` sièges avec une allée simulée entre les
sièges de gauche (A, B, ...) et de droite (..., C, D) pour éviter de considérer
un siège côté couloir opposé comme "adjacent".
"""


def generate_seat_map(rows: int, seats_per_row: int = 4):
    """Retourne une liste ordonnée de codes sièges, avec des marqueurs 'AISLE'
    entre le bloc gauche et le bloc droit de chaque rangée."""
    half = seats_per_row // 2
    letters = [chr(ord("A") + i) for i in range(seats_per_row)]
    seat_map = []
    for r in range(1, rows + 1):
        for i, letter in enumerate(letters):
            if i == half and half > 0:
                seat_map.append(f"AISLE-{r}")
            seat_map.append(f"{r}{letter}")
    return seat_map


def _free_runs(seat_map, occupied_seats):
    """Retourne la liste des séquences contiguës de sièges libres (séparées par
    les marqueurs AISLE ou par des sièges déjà occupés)."""
    runs = []
    current = []
    for seat in seat_map:
        if seat.startswith("AISLE") or seat in occupied_seats:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(seat)
    if current:
        runs.append(current)
    return runs


def _best_fit_run(runs, size):
    """Trouve la plus petite séquence libre qui peut contenir `size` personnes."""
    candidates = [r for r in runs if len(r) >= size]
    if not candidates:
        return None
    return min(candidates, key=len)


def assign_seats(clients, rows: int, seats_per_row: int = 4):
    """
    clients : liste de dicts avec au minimum
        {"id": int, "group_id": int|None, "gender": "H"/"F"/"NA"}
    Retourne un dict {client_id: seat_code}.
    """
    seat_map = generate_seat_map(rows, seats_per_row)
    total_seats = len([s for s in seat_map if not s.startswith("AISLE")])
    occupied = set()
    assignment = {}

    # 1) Regrouper par group_id (None -> solo, un groupe par personne)
    groups = {}
    for cl in clients:
        gid = cl.get("group_id")
        key = gid if gid is not None else f"solo-{cl['id']}"
        groups.setdefault(key, []).append(cl)

    real_groups = [members for key, members in groups.items() if not str(key).startswith("solo-")]
    solos = [members[0] for key, members in groups.items() if str(key).startswith("solo-")]

    # 2) Trier les vrais groupes du plus grand au plus petit
    real_groups.sort(key=len, reverse=True)

    # 3) Regrouper les solos par genre pour les rapprocher (paquets de 2 à 4)
    solos_by_gender = {}
    for s in solos:
        solos_by_gender.setdefault(s.get("gender", "NA"), []).append(s)

    solo_packs = []
    for gender, members in solos_by_gender.items():
        pack_size = 4 if seats_per_row >= 4 else 2
        for i in range(0, len(members), pack_size):
            solo_packs.append(members[i:i + pack_size])

    all_groups_to_place = real_groups + solo_packs

    # 4) Placement : best-fit, sinon découpage en sous-blocs
    for members in all_groups_to_place:
        size = len(members)
        runs = _free_runs(seat_map, occupied)
        run = _best_fit_run(runs, size)
        if run is not None:
            chosen = run[:size]
        else:
            # Pas de bloc assez grand : on découpe le groupe sur plusieurs runs
            chosen = []
            remaining = size
            for r in sorted(runs, key=len, reverse=True):
                if remaining <= 0:
                    break
                take = r[:remaining]
                chosen.extend(take)
                remaining -= len(take)
            if remaining > 0:
                # Plus assez de place dans le bus
                chosen = chosen  # on placera ce qu'on peut, le reste restera sans siège
        for cl, seat in zip(members, chosen):
            assignment[cl["id"]] = seat
            occupied.add(seat)

    unassigned = [cl["id"] for cl in clients if cl["id"] not in assignment]
    return assignment, unassigned, total_seats
