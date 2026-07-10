"""
Algorithme de placement automatique dans le bus (v2 — amélioré).

Idée clé : on traite chaque CÔTÉ du bus (gauche / droite) comme une colonne
continue de sièges, rangée après rangée. Deux sièges consécutifs dans cette
colonne sont donc soit dans la même rangée, soit dans deux rangées voisines
du même côté — physiquement proches dans les deux cas. Cela permet de placer
des groupes plus grands que la largeur d'une rangée (ex: famille de 4 dans un
bus 2+2) sans les séparer inutilement.

Priorités :
1. Type de groupe : famille > couple > amis (les familles ont la priorité
   sur les meilleurs blocs de sièges).
2. À type égal, les groupes les plus grands sont placés en premier (plus
   difficiles à caser).
3. Les voyageurs seuls sont regroupés par genre en "paquets" et traités
   comme des groupes.
4. On choisit, pour chaque groupe, le plus petit bloc libre (gauche ou
   droite) qui peut le contenir en entier (best-fit) afin de ne pas
   gaspiller les grands blocs. Si aucun bloc ne suffit, le groupe est
   réparti sur plusieurs blocs en minimisant le nombre de coupures.
"""

GROUP_TYPE_PRIORITY = {"famille": 0, "couple": 1, "amis": 2}


def _side_seats(rows: int, seats_per_row: int):
    """Retourne (sièges_gauche, sièges_droite), chacun ordonné rangée par rangée."""
    half = max(seats_per_row // 2, 1)
    left_letters = [chr(ord("A") + i) for i in range(half)]
    right_letters = [chr(ord("A") + half + i) for i in range(max(seats_per_row - half, 0))]
    left, right = [], []
    for r in range(1, rows + 1):
        for letter in left_letters:
            left.append(f"{r}{letter}")
        for letter in right_letters:
            right.append(f"{r}{letter}")
    return left, right


def generate_seat_map(rows: int, seats_per_row: int = 4):
    left, right = _side_seats(rows, seats_per_row)
    return left + right


def _free_runs(side_seats, occupied):
    runs, current = [], []
    for seat in side_seats:
        if seat in occupied:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(seat)
    if current:
        runs.append(current)
    return runs


def _best_fit(runs, size):
    candidates = [r for r in runs if len(r) >= size]
    if not candidates:
        return None
    return min(candidates, key=len)


def assign_seats(clients, rows: int, seats_per_row: int = 4, group_types: dict = None):
    """
    clients : liste de dicts {"id":, "group_id":, "gender":}
    group_types : dict {group_id: "famille"|"couple"|"amis"} pour la priorité de placement
    Retourne (assignment: {client_id: seat}, unassigned: [client_id], total_seats: int)
    """
    group_types = group_types or {}
    left, right = _side_seats(rows, seats_per_row)
    total_seats = len(left) + len(right)
    occupied_left, occupied_right = set(), set()
    assignment = {}

    groups = {}
    for cl in clients:
        gid = cl.get("group_id")
        key = gid if gid is not None else f"solo-{cl['id']}"
        groups.setdefault(key, []).append(cl)

    real_groups = [(key, members) for key, members in groups.items() if not str(key).startswith("solo-")]
    solos = [members[0] for key, members in groups.items() if str(key).startswith("solo-")]

    def sort_key(item):
        key, members = item
        gtype = group_types.get(key, "amis")
        return (GROUP_TYPE_PRIORITY.get(gtype, 3), -len(members))

    real_groups.sort(key=sort_key)

    # Regrouper les solos par genre en paquets de la taille d'un demi-rang (pour rester compact)
    solos_by_gender = {}
    for s in solos:
        solos_by_gender.setdefault(s.get("gender", "NA"), []).append(s)

    pack_size = max(seats_per_row // 2, 2)
    solo_packs = []
    for gender, members in solos_by_gender.items():
        for i in range(0, len(members), pack_size):
            solo_packs.append((f"solo-pack-{gender}-{i}", members[i:i + pack_size]))

    to_place = real_groups + solo_packs

    for _key, members in to_place:
        size = len(members)
        runs_left = _free_runs(left, occupied_left)
        runs_right = _free_runs(right, occupied_right)
        best_left = _best_fit(runs_left, size)
        best_right = _best_fit(runs_right, size)

        chosen_run, chosen_occupied = None, None
        if best_left and best_right:
            if len(best_left) <= len(best_right):
                chosen_run, chosen_occupied = best_left, occupied_left
            else:
                chosen_run, chosen_occupied = best_right, occupied_right
        elif best_left:
            chosen_run, chosen_occupied = best_left, occupied_left
        elif best_right:
            chosen_run, chosen_occupied = best_right, occupied_right

        if chosen_run is not None:
            chosen = chosen_run[:size]
            for cl, seat in zip(members, chosen):
                assignment[cl["id"]] = seat
                chosen_occupied.add(seat)
        else:
            # Aucun bloc unique assez grand : on répartit en minimisant le nb de coupures
            idx = 0
            pool = sorted(runs_left + runs_right, key=len, reverse=True)
            for run in pool:
                if idx >= size:
                    break
                take_n = min(len(run), size - idx)
                take = run[:take_n]
                for seat in take:
                    (occupied_left if seat in left else occupied_right).add(seat)
                for cl, seat in zip(members[idx:idx + take_n], take):
                    assignment[cl["id"]] = seat
                idx += take_n

    unassigned = [cl["id"] for cl in clients if cl["id"] not in assignment]
    return assignment, unassigned, total_seats
