"""
Order modeli - Buyurtmalarni boshqarish
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum
import uuid


class OrderStatus(str, Enum):
    PENDING = "pending"          # Kutilmoqda
    CONFIRMED = "confirmed"      # Tasdiqlangan
    PREPARING = "preparing"      # Tayyorlanmoqda
    READY = "ready"              # Tayyor
    DELIVERED = "delivered"      # Yetkazildi
    CANCELLED = "cancelled"      # Bekor qilindi


class OrderType(str, Enum):
    DINE_IN = "dine_in"         # Zalda
    TAKEAWAY = "takeaway"        # Olib ketish
    DELIVERY = "delivery"        # Yetkazib berish


@dataclass
class OrderItem:
    """Buyurtma elementi"""
    menu_item_id: str
    menu_item_name: str
    quantity: int
    unit_price: float
    notes: str = ""

    @property
    def subtotal(self) -> float:
        return round(self.unit_price * self.quantity, 2)

    def to_dict(self) -> dict:
        return {
            "menu_item_id": self.menu_item_id,
            "menu_item_name": self.menu_item_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'OrderItem':
        return cls(
            menu_item_id=data["menu_item_id"],
            menu_item_name=data["menu_item_name"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            notes=data.get("notes", "")
        )


@dataclass
class Order:
    """Buyurtma sinfi"""
    customer_name: str
    order_type: str = OrderType.DINE_IN
    table_number: Optional[int] = None
    items: List[OrderItem] = field(default_factory=list)
    status: str = OrderStatus.PENDING
    id: str = field(default_factory=lambda: f"ORD-{str(uuid.uuid4())[:6].upper()}")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    special_instructions: str = ""
    discount_percent: float = 0.0

    def add_item(self, order_item: OrderItem):
        """Buyurtmaga element qo'shish"""
        # Agar mavjud bo'lsa, miqdorni oshirish
        for item in self.items:
            if item.menu_item_id == order_item.menu_item_id:
                item.quantity += order_item.quantity
                self._update_timestamp()
                return
        self.items.append(order_item)
        self._update_timestamp()

    def remove_item(self, menu_item_id: str) -> bool:
        """Buyurtmadan element o'chirish"""
        original_len = len(self.items)
        self.items = [i for i in self.items if i.menu_item_id != menu_item_id]
        if len(self.items) < original_len:
            self._update_timestamp()
            return True
        return False

    def update_item_quantity(self, menu_item_id: str, quantity: int) -> bool:
        """Element miqdorini yangilash"""
        for item in self.items:
            if item.menu_item_id == menu_item_id:
                if quantity <= 0:
                    return self.remove_item(menu_item_id)
                item.quantity = quantity
                self._update_timestamp()
                return True
        return False

    @property
    def subtotal(self) -> float:
        """Chegirmасiz jami summa"""
        return round(sum(item.subtotal for item in self.items), 2)

    @property
    def discount_amount(self) -> float:
        """Chegirma summasi"""
        return round(self.subtotal * self.discount_percent / 100, 2)

    @property
    def total(self) -> float:
        """Jami summa (chegirma bilan)"""
        return round(self.subtotal - self.discount_amount, 2)

    @property
    def item_count(self) -> int:
        """Umumiy mahsulot soni"""
        return sum(item.quantity for item in self.items)

    def change_status(self, new_status: str) -> bool:
        """Statusni o'zgartirish"""
        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY, OrderStatus.CANCELLED],
            OrderStatus.READY: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: []
        }
        if new_status in valid_transitions.get(self.status, []):
            self.status = new_status
            self._update_timestamp()
            return True
        return False

    def cancel(self, reason: str = "") -> bool:
        """Buyurtmani bekor qilish"""
        if self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            return False
        self.status = OrderStatus.CANCELLED
        if reason:
            self.special_instructions += f" | Bekor qilish sababi: {reason}"
        self._update_timestamp()
        return True

    def _update_timestamp(self):
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "order_type": self.order_type,
            "table_number": self.table_number,
            "items": [item.to_dict() for item in self.items],
            "status": self.status,
            "subtotal": self.subtotal,
            "discount_percent": self.discount_percent,
            "discount_amount": self.discount_amount,
            "total": self.total,
            "item_count": self.item_count,
            "special_instructions": self.special_instructions,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Order':
        order = cls(
            id=data.get("id", f"ORD-{str(uuid.uuid4())[:6].upper()}"),
            customer_name=data["customer_name"],
            order_type=data.get("order_type", OrderType.DINE_IN),
            table_number=data.get("table_number"),
            status=data.get("status", OrderStatus.PENDING),
            special_instructions=data.get("special_instructions", ""),
            discount_percent=data.get("discount_percent", 0.0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )
        order.items = [OrderItem.from_dict(i) for i in data.get("items", [])]
        return order

    def __str__(self):
        return f"[{self.id}] {self.customer_name} - {self.status} - {self.total:,.0f} so'm"
