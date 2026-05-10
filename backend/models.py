"""
Restoran Boshqaruv Tizimi - OOP Modellari
==========================================
Barcha asosiy ob'ektlar shu yerda aniqlanadi:
  - MenuItem (Menyu elementi)
  - Category (Kategoriya)
  - Table (Stol)
  - Order (Buyurtma)
  - OrderItem (Buyurtma elementi)
  - Payment (To'lov)
  - Customer (Mijoz)
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
import json


# ─────────────────────────────────────────────
# ENUMLAR
# ─────────────────────────────────────────────

class OrderStatus(Enum):
    PENDING    = "pending"      # Kutilmoqda
    PREPARING  = "preparing"   # Tayyorlanmoqda
    READY      = "ready"       # Tayyor
    SERVED     = "served"      # Berildi
    CANCELLED  = "cancelled"   # Bekor qilindi


class PaymentMethod(Enum):
    CASH       = "cash"        # Naqd
    CARD       = "card"        # Karta
    ONLINE     = "online"      # Onlayn


class PaymentStatus(Enum):
    PENDING    = "pending"     # Kutilmoqda
    COMPLETED  = "completed"   # Bajarildi
    REFUNDED   = "refunded"    # Qaytarildi


class TableStatus(Enum):
    FREE       = "free"        # Bo'sh
    OCCUPIED   = "occupied"    # Band
    RESERVED   = "reserved"    # Bron qilingan


# ─────────────────────────────────────────────
# ASOSIY SINF
# ─────────────────────────────────────────────

class BaseModel:
    """Barcha modellar uchun asosiy sinf."""

    def to_dict(self) -> dict:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.to_dict()}>"


# ─────────────────────────────────────────────
# KATEGORIYA
# ─────────────────────────────────────────────

class Category(BaseModel):
    def __init__(self, id: int, name: str, icon: str = "🍽️", description: str = ""):
        self.id          = id
        self.name        = name
        self.icon        = icon
        self.description = description
        self.created_at  = datetime.now()

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "name":        self.name,
            "icon":        self.icon,
            "description": self.description,
            "created_at":  self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────
# MENYU ELEMENTI
# ─────────────────────────────────────────────

class MenuItem(BaseModel):
    def __init__(
        self,
        id: int,
        name: str,
        price: float,
        category_id: int,
        description: str = "",
        image_url: str = "",
        is_available: bool = True,
        preparation_time: int = 10,   # daqiqa
        calories: int = 0,
        allergens: Optional[List[str]] = None,
    ):
        self.id               = id
        self.name             = name
        self.price            = price
        self.category_id      = category_id
        self.description      = description
        self.image_url        = image_url
        self.is_available     = is_available
        self.preparation_time = preparation_time
        self.calories         = calories
        self.allergens        = allergens or []
        self.created_at       = datetime.now()
        self.updated_at       = datetime.now()

    def apply_discount(self, percent: float) -> float:
        """Chegirma qo'llash."""
        if 0 < percent <= 100:
            return round(self.price * (1 - percent / 100), 2)
        return self.price

    def to_dict(self) -> dict:
        return {
            "id":               self.id,
            "name":             self.name,
            "price":            self.price,
            "category_id":      self.category_id,
            "description":      self.description,
            "image_url":        self.image_url,
            "is_available":     self.is_available,
            "preparation_time": self.preparation_time,
            "calories":         self.calories,
            "allergens":        self.allergens,
            "created_at":       self.created_at.isoformat(),
            "updated_at":       self.updated_at.isoformat(),
        }


# ─────────────────────────────────────────────
# STOL
# ─────────────────────────────────────────────

class Table(BaseModel):
    def __init__(self, id: int, number: int, capacity: int, location: str = "Zal"):
        self.id         = id
        self.number     = number
        self.capacity   = capacity
        self.location   = location
        self.status     = TableStatus.FREE
        self.created_at = datetime.now()

    def occupy(self):
        self.status = TableStatus.OCCUPIED

    def free(self):
        self.status = TableStatus.FREE

    def reserve(self):
        self.status = TableStatus.RESERVED

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "number":     self.number,
            "capacity":   self.capacity,
            "location":   self.location,
            "status":     self.status.value,
            "created_at": self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────
# BUYURTMA ELEMENTI
# ─────────────────────────────────────────────

class OrderItem(BaseModel):
    def __init__(
        self,
        id: int,
        order_id: int,
        menu_item_id: int,
        menu_item_name: str,
        quantity: int,
        unit_price: float,
        notes: str = "",
    ):
        self.id             = id
        self.order_id       = order_id
        self.menu_item_id   = menu_item_id
        self.menu_item_name = menu_item_name
        self.quantity       = quantity
        self.unit_price     = unit_price
        self.notes          = notes
        self.subtotal       = round(quantity * unit_price, 2)

    def update_quantity(self, qty: int):
        self.quantity = qty
        self.subtotal = round(qty * self.unit_price, 2)

    def to_dict(self) -> dict:
        return {
            "id":             self.id,
            "order_id":       self.order_id,
            "menu_item_id":   self.menu_item_id,
            "menu_item_name": self.menu_item_name,
            "quantity":       self.quantity,
            "unit_price":     self.unit_price,
            "notes":          self.notes,
            "subtotal":       self.subtotal,
        }


# ─────────────────────────────────────────────
# BUYURTMA
# ─────────────────────────────────────────────

class Order(BaseModel):
    TAX_RATE     = 0.12   # 12% soliq
    SERVICE_FEE  = 0.05   # 5% xizmat haqi

    def __init__(
        self,
        id: int,
        table_id: int,
        customer_name: str = "Mehmon",
        notes: str = "",
    ):
        self.id            = id
        self.table_id      = table_id
        self.customer_name = customer_name
        self.notes         = notes
        self.status        = OrderStatus.PENDING
        self.items: List[OrderItem] = []
        self.created_at    = datetime.now()
        self.updated_at    = datetime.now()

    # ── Hisob-kitob ──

    @property
    def subtotal(self) -> float:
        return round(sum(i.subtotal for i in self.items), 2)

    @property
    def tax(self) -> float:
        return round(self.subtotal * self.TAX_RATE, 2)

    @property
    def service_fee(self) -> float:
        return round(self.subtotal * self.SERVICE_FEE, 2)

    @property
    def total(self) -> float:
        return round(self.subtotal + self.tax + self.service_fee, 2)

    # ── Holat o'zgartirish ──

    def update_status(self, new_status: OrderStatus):
        self.status     = new_status
        self.updated_at = datetime.now()

    def add_item(self, item: OrderItem):
        self.items.append(item)
        self.updated_at = datetime.now()

    def remove_item(self, item_id: int):
        self.items = [i for i in self.items if i.id != item_id]
        self.updated_at = datetime.now()

    def cancel(self):
        self.update_status(OrderStatus.CANCELLED)

    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "table_id":      self.table_id,
            "customer_name": self.customer_name,
            "notes":         self.notes,
            "status":        self.status.value,
            "items":         [i.to_dict() for i in self.items],
            "subtotal":      self.subtotal,
            "tax":           self.tax,
            "service_fee":   self.service_fee,
            "total":         self.total,
            "created_at":    self.created_at.isoformat(),
            "updated_at":    self.updated_at.isoformat(),
        }


# ─────────────────────────────────────────────
# TO'LOV
# ─────────────────────────────────────────────

class Payment(BaseModel):
    def __init__(
        self,
        id: int,
        order_id: int,
        amount: float,
        method: PaymentMethod,
        tip: float = 0.0,
        transaction_id: str = "",
    ):
        self.id             = id
        self.order_id       = order_id
        self.amount         = amount
        self.method         = method
        self.tip            = tip
        self.transaction_id = transaction_id or f"TXN{id:06d}"
        self.status         = PaymentStatus.PENDING
        self.created_at     = datetime.now()

    @property
    def total_paid(self) -> float:
        return round(self.amount + self.tip, 2)

    def complete(self):
        self.status = PaymentStatus.COMPLETED

    def refund(self):
        self.status = PaymentStatus.REFUNDED

    def to_dict(self) -> dict:
        return {
            "id":             self.id,
            "order_id":       self.order_id,
            "amount":         self.amount,
            "tip":            self.tip,
            "total_paid":     self.total_paid,
            "method":         self.method.value,
            "transaction_id": self.transaction_id,
            "status":         self.status.value,
            "created_at":     self.created_at.isoformat(),
        }
