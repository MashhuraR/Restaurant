"""
Menyu kontrolleri - CRUD operatsiyalari
"""
from typing import List, Optional, Dict
from backend.models.menu_item import MenuItem, Category
from backend.database.db_manager import DatabaseManager


class MenuController:
    """Menyuni boshqarish kontrolleri"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, category: Optional[str] = None, available_only: bool = False) -> List[Dict]:
        """Barcha menyu elementlarini olish"""
        items = list(self.db.get_all_menu_items().values())
        if category:
            items = [i for i in items if i.get("category") == category]
        if available_only:
            items = [i for i in items if i.get("is_available", True)]
        return sorted(items, key=lambda x: x.get("category", ""))

    def get_by_id(self, item_id: str) -> Optional[Dict]:
        """ID bo'yicha menyu elementini olish"""
        return self.db.get_menu_item(item_id)

    def create(self, data: Dict) -> Dict:
        """Yangi menyu elementi yaratish"""
        item = MenuItem(
            name=data["name"],
            price=float(data["price"]),
            category=data["category"],
            description=data.get("description", ""),
            is_available=data.get("is_available", True),
            preparation_time=int(data.get("preparation_time", 15))
        )
        self.db.save_menu_item(item.id, item.to_dict())
        return item.to_dict()

    def update(self, item_id: str, data: Dict) -> Optional[Dict]:
        """Menyu elementini yangilash"""
        existing = self.db.get_menu_item(item_id)
        if not existing:
            return None
        existing.update({k: v for k, v in data.items() if k != "id"})
        self.db.save_menu_item(item_id, existing)
        return existing

    def delete(self, item_id: str) -> bool:
        """Menyu elementini o'chirish"""
        return self.db.delete_menu_item(item_id)

    def toggle_availability(self, item_id: str) -> Optional[Dict]:
        """Mavjudlikni o'zgartirish"""
        item_data = self.db.get_menu_item(item_id)
        if not item_data:
            return None
        item_data["is_available"] = not item_data.get("is_available", True)
        self.db.save_menu_item(item_id, item_data)
        return item_data

    def get_categories(self) -> List[str]:
        """Barcha kategoriyalarni olish"""
        return Category.ALL

    def search(self, query: str) -> List[Dict]:
        """Menyu elementlarini qidirish"""
        query_lower = query.lower()
        items = list(self.db.get_all_menu_items().values())
        return [
            i for i in items
            if query_lower in i.get("name", "").lower()
            or query_lower in i.get("description", "").lower()
            or query_lower in i.get("category", "").lower()
        ]
