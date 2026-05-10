from dataclasses import dataclass, field
from typing import List, Optional
from backend.database.db import DatabaseManager


@dataclass
class Category:
    id: Optional[int]
    name: str
    description: str
    icon: str = '🍽️'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
        }


@dataclass
class MenuItem:
    id: Optional[int]
    category_id: int
    name: str
    description: str
    price: float
    is_available: bool = True
    preparation_time: int = 15
    calories: Optional[int] = None
    image_url: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'is_available': self.is_available,
            'preparation_time': self.preparation_time,
            'calories': self.calories,
            'image_url': self.image_url,
        }


class MenuRepository:
    """Menyu bilan ishlash uchun repository pattern"""

    def __init__(self):
        self.db = DatabaseManager()

    # ── Category CRUD ──────────────────────────────────────────────────────
    def get_all_categories(self) -> List[Category]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM categories ORDER BY name"
            ).fetchall()
        return [Category(**dict(r)) for r in rows]

    def create_category(self, name: str, description: str, icon: str = '🍽️') -> Category:
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)",
                (name, description, icon)
            )
            return Category(id=cur.lastrowid, name=name, description=description, icon=icon)

    # ── MenuItem CRUD ──────────────────────────────────────────────────────
    def get_all_items(self, category_id: Optional[int] = None) -> List[dict]:
        with self.db.get_connection() as conn:
            if category_id:
                rows = conn.execute(
                    """SELECT m.*, c.name as category_name, c.icon as category_icon
                       FROM menu_items m JOIN categories c ON m.category_id = c.id
                       WHERE m.category_id = ? ORDER BY m.name""",
                    (category_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT m.*, c.name as category_name, c.icon as category_icon
                       FROM menu_items m JOIN categories c ON m.category_id = c.id
                       ORDER BY c.name, m.name"""
                ).fetchall()
        return [dict(r) for r in rows]

    def get_item_by_id(self, item_id: int) -> Optional[dict]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM menu_items WHERE id = ?", (item_id,)
            ).fetchone()
        return dict(row) if row else None

    def create_item(self, data: dict) -> dict:
        with self.db.get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO menu_items
                   (category_id, name, description, price, is_available, preparation_time, calories)
                   VALUES (:category_id, :name, :description, :price,
                           :is_available, :preparation_time, :calories)""",
                data
            )
            data['id'] = cur.lastrowid
        return data

    def update_item(self, item_id: int, data: dict) -> Optional[dict]:
        fields = ', '.join(f"{k} = ?" for k in data)
        values = list(data.values()) + [item_id]
        with self.db.get_connection() as conn:
            conn.execute(f"UPDATE menu_items SET {fields} WHERE id = ?", values)
        return self.get_item_by_id(item_id)

    def delete_item(self, item_id: int) -> bool:
        with self.db.get_connection() as conn:
            cur = conn.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
        return cur.rowcount > 0

    def toggle_availability(self, item_id: int) -> Optional[dict]:
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE menu_items SET is_available = NOT is_available WHERE id = ?",
                (item_id,)
            )
        return self.get_item_by_id(item_id)
