"""
Ma'lumotlar bazasini boshqarish - JSON fayl asosida
"""
import json
import os
from typing import Dict, Any
from datetime import datetime


class DatabaseManager:
    """JSON asosidagi ma'lumotlar bazasi"""

    def __init__(self, db_path: str = "database/restaurant_db.json"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Ma'lumotlar bazasini yaratish (agar yo'q bo'lsa)"""
        if not os.path.exists(self.db_path):
            self._write({
                "menu_items": {},
                "orders": {},
                "payments": {},
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            })
            # self._seed_default_data()

    def _read(self) -> Dict:
        """Bazani o'qish"""
        with open(self.db_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write(self, data: Dict):
        """Bazaga yozish"""
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ─── Menyu operatsiyalari ─────────────────────────────────
    def get_all_menu_items(self) -> Dict:
        return self._read().get("menu_items", {})

    def get_menu_item(self, item_id: str) -> Dict | None:
        return self._read().get("menu_items", {}).get(item_id)

    def save_menu_item(self, item_id: str, data: Dict):
        db = self._read()
        db["menu_items"][item_id] = data
        self._write(db)

    def delete_menu_item(self, item_id: str) -> bool:
        db = self._read()
        if item_id in db["menu_items"]:
            del db["menu_items"][item_id]
            self._write(db)
            return True
        return False

    # ─── Buyurtma operatsiyalari ──────────────────────────────
    def get_all_orders(self) -> Dict:
        return self._read().get("orders", {})

    def get_order(self, order_id: str) -> Dict | None:
        return self._read().get("orders", {}).get(order_id)

    def save_order(self, order_id: str, data: Dict):
        db = self._read()
        db["orders"][order_id] = data
        self._write(db)

    def delete_order(self, order_id: str) -> bool:
        db = self._read()
        if order_id in db["orders"]:
            del db["orders"][order_id]
            self._write(db)
            return True
        return False

    # ─── To'lov operatsiyalari ────────────────────────────────
    def get_all_payments(self) -> Dict:
        return self._read().get("payments", {})

    def get_payment(self, payment_id: str) -> Dict | None:
        return self._read().get("payments", {}).get(payment_id)

    def save_payment(self, payment_id: str, data: Dict):
        db = self._read()
        db["payments"][payment_id] = data
        self._write(db)

    def get_payments_by_order(self, order_id: str) -> list:
        payments = self._read().get("payments", {})
        return [p for p in payments.values() if p.get("order_id") == order_id]

    # ─── Statistika ───────────────────────────────────────────
    def get_statistics(self) -> Dict:
        db = self._read()
        orders = list(db.get("orders", {}).values())
        payments = list(db.get("payments", {}).values())

        total_revenue = sum(
            float(p.get("amount", 0)) for p in payments if p.get("status") == "completed"
        )
        completed_orders = [o for o in orders if o.get("status") == "delivered"]
        cancelled_orders = [o for o in orders if o.get("status") == "cancelled"]

        # Eng ko'p buyurtma qilingan taomlar
        item_counts = {}
        for order in orders:
            for item in order.get("items", []):
                name = item.get("menu_item_name", "")
                if name:
                    item_counts[name] = item_counts.get(name, 0) + int(item.get("quantity", 0))

        top_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        active_orders = [o for o in orders if o.get("status") not in ["delivered", "cancelled"]]
        projected_revenue = sum(float(o.get("total", 0) or 0) for o in active_orders)

        return {
            "total_orders": len(orders),
            "completed_orders": len(completed_orders),
            "cancelled_orders": len(cancelled_orders),
            "active_orders": len(active_orders),
            "total_revenue": round(total_revenue, 2),
            "active_revenue": round(projected_revenue, 2),
            "total_payments": len(payments),
            "top_items": [{"name": n, "count": c} for n, c in top_items],
            "menu_items_count": len(db.get("menu_items", {}))
        }

    def _seed_default_data(self):
        """Namunа ma'lumotlar"""
        from backend.models.menu_item import MenuItem, Category
        from backend.models.order import Order, OrderItem, OrderType, OrderStatus
        from backend.models.payment import Payment, PaymentMethod, PaymentStatus

        sample_items = [
            MenuItem("Osh", 45000, Category.MAIN_COURSE, "An'anaviy o'zbek oshi", preparation_time=30),
            MenuItem("Lag'mon", 35000, Category.MAIN_COURSE, "Qo'lda tayyorlangan lag'mon", preparation_time=25),
            MenuItem("Shurva", 28000, Category.SOUP, "Go'sht va sabzavotli shurva", preparation_time=20),
            MenuItem("Mastava", 25000, Category.SOUP, "Guruchli mastava", preparation_time=20),
            MenuItem("Chuchvara", 30000, Category.MAIN_COURSE, "Qaynatilgan chuchvara", preparation_time=20),
            MenuItem("Samsa", 8000, Category.FAST_FOOD, "Tandirda pishirilgan samsa", preparation_time=10),
            MenuItem("Non", 5000, Category.FAST_FOOD, "Tandir noni", preparation_time=5),
            MenuItem("Shirmon", 20000, Category.DESSERT, "Milliy shirmon", preparation_time=15),
            MenuItem("Ko'k choy", 8000, Category.DRINK, "Ariq suvi bilan ko'k choy", preparation_time=5),
            MenuItem("Qora choy", 8000, Category.DRINK, "Limon bilan qora choy", preparation_time=5),
            MenuItem("Coca-Cola", 12000, Category.DRINK, "Sovuq ichimlik", preparation_time=2),
            MenuItem("Shashlik", 55000, Category.MAIN_COURSE, "O'tin o'tida pishirilgan shashlik", preparation_time=35),
            MenuItem("Salat Toshkent", 22000, Category.APPETIZER, "Toshkent salati", preparation_time=10),
            MenuItem("Achiq-chuchuk", 15000, Category.APPETIZER, "Achchiq va shirin sabzavotlar", preparation_time=10),
            MenuItem("Manti", 32000, Category.MAIN_COURSE, "Bug'da pishirilgan manti", preparation_time=40),
        ]

        db = self._read()
        for item in sample_items:
            db["menu_items"][item.id] = item.to_dict()

        # Namuna buyurtmalar
        order1 = Order("Akbar Toshmatov", OrderType.DINE_IN, table_number=5)
        item1 = OrderItem(list(db["menu_items"].values())[0]["id"],
                          list(db["menu_items"].values())[0]["name"],
                          2, list(db["menu_items"].values())[0]["price"])
        item2 = OrderItem(list(db["menu_items"].values())[8]["id"],
                          list(db["menu_items"].values())[8]["name"],
                          2, list(db["menu_items"].values())[8]["price"])
        order1.add_item(item1)
        order1.add_item(item2)
        order1.status = OrderStatus.DELIVERED
        db["orders"][order1.id] = order1.to_dict()

        # Namuna to'lov
        pay1 = Payment(order1.id, order1.total, PaymentMethod.CASH)
        pay1.complete()
        pay1.status = PaymentStatus.COMPLETED
        db["payments"][pay1.id] = pay1.to_dict()

        order2 = Order("Malika Yusupova", OrderType.TAKEAWAY)
        item3 = OrderItem(list(db["menu_items"].values())[5]["id"],
                          list(db["menu_items"].values())[5]["name"],
                          4, list(db["menu_items"].values())[5]["price"])
        order2.add_item(item3)
        order2.status = OrderStatus.PREPARING
        db["orders"][order2.id] = order2.to_dict()

        self._write(db)
