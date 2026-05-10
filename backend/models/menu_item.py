"""
MenuItem modeli - Menyu elementini ifodalaydi
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


class Category:
    """Menyu kategoriyalari"""
    APPETIZER = "Salatlar"
    MAIN_COURSE = "Asosiy taomlar"
    SOUP = "Sho'rvalar"
    DESSERT = "Shirinliklar"
    DRINK = "Ichimliklar"
    FAST_FOOD = "Tez taomlar"

    ALL = [APPETIZER, MAIN_COURSE, SOUP, DESSERT, DRINK, FAST_FOOD]


@dataclass
class MenuItem:
    """Menyu elementi sinfi"""
    name: str
    price: float
    category: str
    description: str = ""
    is_available: bool = True
    image_url: str = ""
    preparation_time: int = 15  # daqiqalarda
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Narx manfiy bo'lishi mumkin emas!")
        if self.category not in Category.ALL:
            raise ValueError(f"Noto'g'ri kategoriya: {self.category}")

    def apply_discount(self, percent: float) -> float:
        """Chegirma qo'llash"""
        if not (0 <= percent <= 100):
            raise ValueError("Chegirma 0-100% oralig'ida bo'lishi kerak!")
        discounted = self.price * (1 - percent / 100)
        return round(discounted, 2)

    def toggle_availability(self):
        """Mavjudlikni o'zgartirish"""
        self.is_available = not self.is_available
        return self.is_available

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "description": self.description,
            "is_available": self.is_available,
            "image_url": self.image_url,
            "preparation_time": self.preparation_time,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MenuItem':
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data["name"],
            price=data["price"],
            category=data["category"],
            description=data.get("description", ""),
            is_available=data.get("is_available", True),
            image_url=data.get("image_url", ""),
            preparation_time=data.get("preparation_time", 15),
            created_at=data.get("created_at", datetime.now().isoformat())
        )

    def __str__(self):
        status = "✅" if self.is_available else "❌"
        return f"{status} [{self.id}] {self.name} - {self.price:,.0f} so'm ({self.category})"

    def __repr__(self):
        return f"MenuItem(id={self.id!r}, name={self.name!r}, price={self.price})"
