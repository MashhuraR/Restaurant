import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'restaurant.db')


class DatabaseManager:
    """Singleton pattern bilan SQLite database boshqaruvchisi"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_path = DB_PATH
            self.initialized = True
            self.create_tables()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def create_tables(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    icon TEXT DEFAULT '🍽️',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    image_url TEXT,
                    is_available INTEGER DEFAULT 1,
                    preparation_time INTEGER DEFAULT 15,
                    calories INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_number INTEGER NOT NULL,
                    customer_name TEXT,
                    status TEXT DEFAULT 'pending',
                    total_amount REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    menu_item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit_price REAL NOT NULL,
                    special_request TEXT,
                    FOREIGN KEY (order_id) REFERENCES orders(id),
                    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL UNIQUE,
                    amount REAL NOT NULL,
                    method TEXT NOT NULL,
                    status TEXT DEFAULT 'completed',
                    discount_percent REAL DEFAULT 0,
                    tip_amount REAL DEFAULT 0,
                    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders(id)
                );
            """)
            self._seed_data(conn)

    def _seed_data(self, conn):
        count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        if count > 0:
            return

        categories = [
            ('Salatlar', 'Yangi va foydali salatlar', '🥗'),
            ('Sho\'rvalar', 'Issiq va mazali sho\'rvalar', '🍲'),
            ('Asosiy taomlar', 'Milliy va Yevropa taomlari', '🍖'),
            ('Ichimliklar', 'Sovuq va issiq ichimliklar', '🥤'),
            ('Desertlar', 'Shirin taomlar', '🍰'),
        ]
        conn.executemany(
            "INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)",
            categories
        )

        menu_items = [
            (1, 'Toshkent salati', 'Mol go\'shti, tarvuz, rediska', 35000, 1, 10, 180),
            (1, 'Cezar salati', 'Tovuq, krouton, parmezan', 42000, 1, 10, 320),
            (1, 'Achichuk', 'Pomidor, piyoz, zira', 18000, 1, 5, 95),
            (2, 'Mastava', 'Guruch, sabzavotlar, mol go\'shti', 28000, 1, 20, 420),
            (2, 'Lag\'mon sho\'rvasi', 'Uy qo\'li lag\'mon, sabzavotlar', 32000, 1, 25, 510),
            (2, 'Bo\'za sho\'rvasi', 'Tovuq, limon, zira', 25000, 1, 15, 280),
            (3, 'Palov', 'O\'zbek milliy taomi, mol go\'shti', 55000, 1, 40, 680),
            (3, 'Manti', '6 dona, qo\'y go\'shti, piyoz', 48000, 1, 30, 590),
            (3, 'Shashlik', '5 ta tayoqcha, mol go\'shti', 65000, 1, 25, 750),
            (3, 'Qovurdoq', 'Mol go\'shti, sabzavotlar', 58000, 1, 35, 620),
            (4, 'Choy', 'Ko\'k yoki qora choy', 8000, 1, 5, 5),
            (4, 'Limonad', 'Tabiiy meva sharbati', 15000, 1, 5, 120),
            (4, 'Kompot', 'Quritilgan mevalar', 12000, 1, 5, 95),
            (4, 'Kofe', 'Espresso yoki kapuchino', 22000, 1, 10, 15),
            (5, 'Halvo', 'Uy halvoasi', 20000, 1, 5, 380),
            (5, 'Tort', 'Qatlama tort, bir bo\'lak', 28000, 1, 5, 450),
            (5, 'Samsa (shirali)', 'Shirin samsa, 2 dona', 18000, 1, 15, 320),
        ]
        conn.executemany(
            """INSERT INTO menu_items 
               (category_id, name, description, price, is_available, preparation_time, calories)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            menu_items
        )
