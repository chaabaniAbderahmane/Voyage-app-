"""
Couche base de données (SQLite) pour l'app Voyages en Bus.
Toutes les fonctions d'accès aux données passent par ici.
"""
import sqlite3
import os
import uuid
import unicodedata
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "voyages.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT,
            app_url TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            rows INTEGER NOT NULL DEFAULT 12,
            seats_per_row INTEGER NOT NULL DEFAULT 4,
            FOREIGN KEY(trip_id) REFERENCES trips(id)
        );

        CREATE TABLE IF NOT EXISTS groups_tbl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            name TEXT,
            type TEXT DEFAULT 'solo',
            FOREIGN KEY(trip_id) REFERENCES trips(id)
        );

        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            bus_id INTEGER,
            group_id INTEGER,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            gender TEXT DEFAULT 'NA',
            phone TEXT,
            username TEXT UNIQUE,
            password TEXT,
            token TEXT UNIQUE,
            seat TEXT,
            checked_in INTEGER DEFAULT 0,
            checkin_time TEXT,
            checkin_by TEXT,
            points INTEGER DEFAULT 0,
            free_trip_available INTEGER DEFAULT 0,
            created_at TEXT,
            FOREIGN KEY(trip_id) REFERENCES trips(id),
            FOREIGN KEY(bus_id) REFERENCES buses(id),
            FOREIGN KEY(group_id) REFERENCES groups_tbl(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            sender TEXT NOT NULL,        -- 'client' ou 'admin'
            text TEXT NOT NULL,
            timestamp TEXT,
            read_by_admin INTEGER DEFAULT 0,
            read_by_client INTEGER DEFAULT 0,
            FOREIGN KEY(client_id) REFERENCES clients(id)
        );
        """
    )
    conn.commit()
    conn.close()


# ---------- Helpers ----------

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.strip().lower().replace(" ", "-")
    return "".join(ch for ch in text if ch.isalnum() or ch == "-")


def cap_first(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    return text[0].upper() + text[1:].lower()


def generate_credentials(conn, first_name: str, last_name: str):
    base_username = slugify(f"{last_name}-{first_name}")
    username = base_username
    c = conn.cursor()
    i = 1
    while c.execute("SELECT 1 FROM clients WHERE username = ?", (username,)).fetchone():
        i += 1
        username = f"{base_username}{i}"
    password = cap_first(last_name)
    token = uuid.uuid4().hex[:12]
    return username, password, token


# ---------- Trips ----------

def create_trip(name, date, app_url=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO trips (name, date, app_url, created_at) VALUES (?, ?, ?, ?)",
        (name, date, app_url, datetime.now().isoformat()),
    )
    conn.commit()
    tid = c.lastrowid
    conn.close()
    return tid


def get_trips():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM trips ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def get_trip(trip_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    conn.close()
    return row


def update_trip_url(trip_id, app_url):
    conn = get_conn()
    conn.execute("UPDATE trips SET app_url = ? WHERE id = ?", (app_url, trip_id))
    conn.commit()
    conn.close()


# ---------- Buses ----------

def create_bus(trip_id, name, rows=12, seats_per_row=4):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO buses (trip_id, name, rows, seats_per_row) VALUES (?, ?, ?, ?)",
        (trip_id, name, rows, seats_per_row),
    )
    conn.commit()
    bid = c.lastrowid
    conn.close()
    return bid


def get_buses(trip_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM buses WHERE trip_id = ? ORDER BY id", (trip_id,)).fetchall()
    conn.close()
    return rows


def get_bus(bus_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM buses WHERE id = ?", (bus_id,)).fetchone()
    conn.close()
    return row


# ---------- Groups ----------

def create_group(trip_id, name, gtype="solo"):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO groups_tbl (trip_id, name, type) VALUES (?, ?, ?)", (trip_id, name, gtype))
    conn.commit()
    gid = c.lastrowid
    conn.close()
    return gid


def get_groups(trip_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM groups_tbl WHERE trip_id = ?", (trip_id,)).fetchall()
    conn.close()
    return rows


# ---------- Clients ----------

def add_client(trip_id, bus_id, first_name, last_name, gender="NA", phone="", group_id=None,
                existing_points=0):
    conn = get_conn()
    username, password, token = generate_credentials(conn, first_name, last_name)
    c = conn.cursor()
    c.execute(
        """INSERT INTO clients
           (trip_id, bus_id, group_id, first_name, last_name, gender, phone,
            username, password, token, points, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trip_id, bus_id, group_id, first_name.strip(), last_name.strip(), gender, phone,
         username, password, token, existing_points, datetime.now().isoformat()),
    )
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid, username, password


def find_returning_client(first_name, last_name):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM clients WHERE lower(first_name)=lower(?) AND lower(last_name)=lower(?) "
        "ORDER BY id DESC LIMIT 1",
        (first_name.strip(), last_name.strip()),
    ).fetchone()
    conn.close()
    return row


def get_clients(trip_id, bus_id=None):
    conn = get_conn()
    if bus_id:
        rows = conn.execute(
            "SELECT * FROM clients WHERE trip_id = ? AND bus_id = ? ORDER BY seat", (trip_id, bus_id)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM clients WHERE trip_id = ? ORDER BY last_name", (trip_id,)).fetchall()
    conn.close()
    return rows


def get_client_by_id(client_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
    conn.close()
    return row


def get_client_by_token(token):
    conn = get_conn()
    row = conn.execute("SELECT * FROM clients WHERE token = ?", (token,)).fetchone()
    conn.close()
    return row


def authenticate_client(username, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM clients WHERE username = ? AND password = ?", (username, password)
    ).fetchone()
    conn.close()
    return row


def set_client_seat(client_id, seat):
    conn = get_conn()
    conn.execute("UPDATE clients SET seat = ? WHERE id = ?", (seat, client_id))
    conn.commit()
    conn.close()


def checkin_client(client_id, by="client"):
    conn = get_conn()
    c = conn.cursor()
    row = c.execute("SELECT checked_in, points FROM clients WHERE id = ?", (client_id,)).fetchone()
    if row and row["checked_in"] == 1:
        conn.close()
        return False
    new_points = (row["points"] or 0) + 1
    free_trip = 1 if new_points > 0 and new_points % 10 == 0 else 0
    c.execute(
        "UPDATE clients SET checked_in = 1, checkin_time = ?, checkin_by = ?, points = ?, "
        "free_trip_available = ? WHERE id = ?",
        (datetime.now().isoformat(), by, new_points, free_trip, client_id),
    )
    conn.commit()
    conn.close()
    return True


def undo_checkin(client_id):
    conn = get_conn()
    conn.execute(
        "UPDATE clients SET checked_in = 0, checkin_time = NULL, checkin_by = NULL WHERE id = ?",
        (client_id,),
    )
    conn.commit()
    conn.close()


def use_free_trip(client_id):
    conn = get_conn()
    conn.execute("UPDATE clients SET free_trip_available = 0 WHERE id = ?", (client_id,))
    conn.commit()
    conn.close()


# ---------- Messages ----------

def send_message(client_id, sender, text):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (client_id, sender, text, timestamp, read_by_admin, read_by_client) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (client_id, sender, text, datetime.now().isoformat(),
         1 if sender == "admin" else 0, 1 if sender == "client" else 0),
    )
    conn.commit()
    conn.close()


def get_messages(client_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE client_id = ? ORDER BY id", (client_id,)
    ).fetchall()
    conn.close()
    return rows


def mark_read(client_id, reader):
    conn = get_conn()
    col = "read_by_admin" if reader == "admin" else "read_by_client"
    conn.execute(f"UPDATE messages SET {col} = 1 WHERE client_id = ?", (client_id,))
    conn.commit()
    conn.close()


def unread_count_for_admin(trip_id):
    conn = get_conn()
    row = conn.execute(
        """SELECT COUNT(*) as n FROM messages m
           JOIN clients c ON c.id = m.client_id
           WHERE c.trip_id = ? AND m.sender = 'client' AND m.read_by_admin = 0""",
        (trip_id,),
    ).fetchone()
    conn.close()
    return row["n"] if row else 0
