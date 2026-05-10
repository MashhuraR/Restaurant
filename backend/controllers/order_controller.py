"""
Buyurtma kontrolleri
"""
from typing import List, Optional, Dict
from backend.models.order import Order, OrderItem, OrderStatus, OrderType
from backend.database.db_manager import DatabaseManager


class OrderController:
    """Buyurtmalarni boshqarish kontrolleri"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, status: Optional[str] = None) -> List[Dict]:
        """Barcha buyurtmalarni olish"""
        orders = list(self.db.get_all_orders().values())
        if status:
            orders = [o for o in orders if o.get("status") == status]
        return sorted(orders, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_by_id(self, order_id: str) -> Optional[Dict]:
        """ID bo'yicha buyurtmani olish"""
        return self.db.get_order(order_id)

    def create(self, data: Dict) -> Dict:
        """Yangi buyurtma yaratish"""
        # Menyu elementlarini tekshirish
        menu_items_db = self.db.get_all_menu_items()

        order = Order(
            customer_name=data["customer_name"],
            order_type=data.get("order_type", OrderType.DINE_IN),
            table_number=data.get("table_number"),
            special_instructions=data.get("special_instructions", ""),
            discount_percent=float(data.get("discount_percent", 0.0))
        )

        for item_data in data.get("items", []):
            menu_item = menu_items_db.get(item_data["menu_item_id"])
            if not menu_item:
                raise ValueError(f"Menyu elementi topilmadi: {item_data['menu_item_id']}")
            if not menu_item.get("is_available", True):
                raise ValueError(f"{menu_item['name']} hozir mavjud emas!")

            order_item = OrderItem(
                menu_item_id=menu_item["id"],
                menu_item_name=menu_item["name"],
                quantity=int(item_data.get("quantity", 1)),
                unit_price=menu_item["price"],
                notes=item_data.get("notes", "")
            )
            order.add_item(order_item)

        if not order.items:
            raise ValueError("Buyurtmada kamida bitta element bo'lishi kerak!")

        self.db.save_order(order.id, order.to_dict())
        return order.to_dict()

    def update_status(self, order_id: str, new_status: str) -> Optional[Dict]:
        """Buyurtma statusini yangilash"""
        order_data = self.db.get_order(order_id)
        if not order_data:
            return None
        order = Order.from_dict(order_data)
        if not order.change_status(new_status):
            raise ValueError(f"'{order.status}' dan '{new_status}' ga o'tish mumkin emas!")
        self.db.save_order(order_id, order.to_dict())
        return order.to_dict()

    def cancel(self, order_id: str, reason: str = "") -> Optional[Dict]:
        """Buyurtmani bekor qilish"""
        order_data = self.db.get_order(order_id)
        if not order_data:
            return None
        order = Order.from_dict(order_data)
        if not order.cancel(reason):
            raise ValueError("Bu buyurtmani bekor qilish mumkin emas!")
        self.db.save_order(order_id, order.to_dict())
        return order.to_dict()

    def add_item(self, order_id: str, item_data: Dict) -> Optional[Dict]:
        """Mavjud buyurtmaga element qo'shish"""
        order_data = self.db.get_order(order_id)
        if not order_data:
            return None

        if order_data.get("status") not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise ValueError("Faqat kutilayotgan yoki tasdiqlangan buyurtmalarga element qo'shish mumkin!")

        menu_item = self.db.get_menu_item(item_data["menu_item_id"])
        if not menu_item:
            raise ValueError("Menyu elementi topilmadi!")

        order = Order.from_dict(order_data)
        new_item = OrderItem(
            menu_item_id=menu_item["id"],
            menu_item_name=menu_item["name"],
            quantity=int(item_data.get("quantity", 1)),
            unit_price=menu_item["price"],
            notes=item_data.get("notes", "")
        )
        order.add_item(new_item)
        self.db.save_order(order_id, order.to_dict())
        return order.to_dict()

    def remove_item(self, order_id: str, menu_item_id: str) -> Optional[Dict]:
        """Buyurtmadan element o'chirish"""
        order_data = self.db.get_order(order_id)
        if not order_data:
            return None

        if order_data.get("status") not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise ValueError("Faqat kutilayotgan yoki tasdiqlangan buyurtmalardan element o'chirish mumkin!")

        order = Order.from_dict(order_data)
        order.remove_item(menu_item_id)
        self.db.save_order(order_id, order.to_dict())
        return order.to_dict()

    def get_active_orders(self) -> List[Dict]:
        """Faol buyurtmalar"""
        active_statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PREPARING, OrderStatus.READY]
        orders = list(self.db.get_all_orders().values())
        return [o for o in orders if o.get("status") in active_statuses]

    def get_statistics(self) -> Dict:
        return self.db.get_statistics()
