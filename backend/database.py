"""
Ma'lumotlar bazasi boshqaruvi (SQLite)
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "restaurant.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Bazani yaratish va jadvallarni to'ldirish."""
    conn = get_connection()
    cur  = conn.cursor()

    # ── Kategoriyalar ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            icon        TEXT    DEFAULT '🍽️',
            description TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Menyu ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT    NOT NULL,
            price            REAL    NOT NULL,
            category_id      INTEGER NOT NULL,
            description      TEXT    DEFAULT '',
            image_url        TEXT    DEFAULT '',
            is_available     INTEGER DEFAULT 1,
            preparation_time INTEGER DEFAULT 10,
            calories         INTEGER DEFAULT 0,
            allergens        TEXT    DEFAULT '[]',
            created_at       TEXT    DEFAULT (datetime('now')),
            updated_at       TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # ── Stollar ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tables (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            number     INTEGER NOT NULL UNIQUE,
            capacity   INTEGER NOT NULL,
            location   TEXT    DEFAULT 'Zal',
            status     TEXT    DEFAULT 'free',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Buyurtmalar ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id      INTEGER NOT NULL,
            customer_name TEXT    DEFAULT 'Mehmon',
            notes         TEXT    DEFAULT '',
            status        TEXT    DEFAULT 'pending',
            subtotal      REAL    DEFAULT 0,
            tax           REAL    DEFAULT 0,
            service_fee   REAL    DEFAULT 0,
            total         REAL    DEFAULT 0,
            created_at    TEXT    DEFAULT (datetime('now')),
            updated_at    TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (table_id) REFERENCES tables(id)
        )
    """)

    # ── Buyurtma elementlari ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id       INTEGER NOT NULL,
            menu_item_id   INTEGER NOT NULL,
            menu_item_name TEXT    NOT NULL,
            quantity       INTEGER NOT NULL DEFAULT 1,
            unit_price     REAL    NOT NULL,
            notes          TEXT    DEFAULT '',
            subtotal       REAL    NOT NULL,
            FOREIGN KEY (order_id)     REFERENCES orders(id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
        )
    """)

    # ── To'lovlar ──
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id       INTEGER NOT NULL UNIQUE,
            amount         REAL    NOT NULL,
            tip            REAL    DEFAULT 0,
            total_paid     REAL    NOT NULL,
            method         TEXT    NOT NULL,
            transaction_id TEXT    NOT NULL,
            status         TEXT    DEFAULT 'pending',
            created_at     TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    conn.commit()

    # ── Demo ma'lumotlar (agar bo'sh bo'lsa) ──
    _seed_data(conn)
    conn.close()


def _seed_data(conn):
    cur = conn.cursor()

    # Kategoriyalar
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] > 0:
        return   # Allaqachon bor

    categories = [
        ("Salatlar",    "🥗", "Yangi salatlar"),
        ("Sho'rvalar",  "🍲", "Issiq sho'rvalar"),
        ("Asosiy taom","🍖", "Asosiy taomlar"),
        ("Grilllar",   "🔥", "Grill taomlar"),
        ("Pitstsa",    "🍕", "Italyan pitstsasi"),
        ("Ichimliklar","🥤", "Sovuq va issiq ichimliklar"),
        ("Desertlar",  "🍰", "Shirinliklar"),
        ("Nonlar",     "🫓", "Turli non mahsulotlari"),
    ]
    cur.executemany(
        "INSERT INTO categories (name, icon, description) VALUES (?,?,?)",
        categories
    )

    # Menyu
    menu = [
        # Salatlar (cat 1)
        ("Toshkent salati",    28000, 1, "Yangi sabzavotlar bilan", "", 1, 10, 120),
        ("Cezar salati",       35000, 1, "Tovuq va krekerlar bilan", "", 1, 12, 280),
        ("Grek salati",        30000, 1, "Fetali va zaytunli", "", 1, 8,  200),
        # Sho'rvalar (cat 2)
        ("Mastava",            32000, 2, "An'anaviy o'zbek oshi", "", 1, 20, 350),
        ("Lagʻmon",            36000, 2, "Uy qo'li lagʻmoni", "", 1, 25, 480),
        ("Moshxo'rda",         30000, 2, "Mosh va guruchli", "", 1, 20, 320),
        # Asosiy (cat 3)
        ("Osh (plov)",         45000, 3, "Farg'ona usuli", "", 1, 40, 650),
        ("Manti",              38000, 3, "Qo'y go'shtli", "", 1, 30, 450),
        ("Dimlama",            42000, 3, "Qozon dimlamasi", "", 1, 35, 520),
        # Grill (cat 4)
        ("Shashlik (mol)",     55000, 4, "Mol go'shti shashlik", "", 1, 25, 580),
        ("Shashlik (qo'y)",    58000, 4, "Qo'y go'shti shashlik", "", 1, 25, 600),
        ("Tovuq shashlik",     48000, 4, "Tovuq shashlik", "", 1, 20, 420),
        ("Kebab",              52000, 4, "Qiyma kabob", "", 1, 20, 500),
        # Pitsa (cat 5)
        ("Margarita",          65000, 5, "Tomat va mocarella", "", 1, 20, 750),
        ("Pepperoni",          75000, 5, "Kolbasa va pishloq", "", 1, 20, 900),
        ("Sabzavotli",         60000, 5, "Yangi sabzavotlar", "", 1, 20, 650),
        # Ichimliklar (cat 6)
        ("Kompot",             12000, 6, "Meva kompoti", "", 1, 5,  80),
        ("Choy (ko'k)",        8000,  6, "Ko'k choy", "", 1, 3,  5),
        ("Choy (qora)",        8000,  6, "Qora choy", "", 1, 3,  5),
        ("Limonad",            18000, 6, "Uy limonadi", "", 1, 5,  120),
        ("Kola",               15000, 6, "Coca-Cola", "", 1, 2,  140),
        # Desertlar (cat 7)
        ("Chak-chak",          22000, 7, "An'anaviy tatli", "", 1, 5,  400),
        ("Tort",               35000, 7, "Kreml torti", "", 1, 5,  550),
        ("Muzqaymoq",          18000, 7, "Vanil muzqaymoq", "", 1, 3,  250),
        # Nonlar (cat 8)
        ("Non (tandir)",       8000,  8, "Yangi tandir non", "", 1, 10, 220),
        ("Patir",              10000, 8, "Farg'ona patiri", "", 1, 10, 280),
    ]
    cur.executemany(
        """INSERT INTO menu_items
           (name,price,category_id,description,image_url,is_available,preparation_time,calories)
           VALUES (?,?,?,?,?,?,?,?)""",
        menu
    )

    # Stollar
    tables = [(i, cap, loc) for i, cap, loc in [
        (1,  4,  "Zal"),   (2,  4,  "Zal"),   (3,  2,  "Zal"),
        (4,  6,  "Zal"),   (5,  4,  "Zal"),   (6,  8,  "VIP"),
        (7,  4,  "Veranda"),(8,  4,  "Veranda"),(9,  6,  "Veranda"),
        (10, 2,  "Bar"),
    ]]
    cur.executemany(
        "INSERT INTO tables (number, capacity, location) VALUES (?,?,?)",
        tables
    )

    conn.commit()
