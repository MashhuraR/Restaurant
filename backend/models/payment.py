"""
Payment modeli - To'lovlarni boshqarish
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class PaymentMethod(str, Enum):
    CASH = "cash"               # Naqd
    CARD = "card"               # Karta
    ONLINE = "online"           # Online to'lov
    PAYME = "payme"             # Payme
    CLICK = "click"             # Click


class PaymentStatus(str, Enum):
    PENDING = "pending"         # Kutilmoqda
    COMPLETED = "completed"     # Amalga oshirildi
    FAILED = "failed"           # Muvaffaqiyatsiz
    REFUNDED = "refunded"       # Qaytarildi


@dataclass
class Payment:
    """To'lov sinfi"""
    order_id: str
    amount: float
    method: str = PaymentMethod.CASH
    status: str = PaymentStatus.PENDING
    id: str = field(default_factory=lambda: f"PAY-{str(uuid.uuid4())[:6].upper()}")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    transaction_id: Optional[str] = None
    notes: str = ""
    cashier_name: str = "Kassir"

    def complete(self, transaction_id: Optional[str] = None) -> bool:
        """To'lovni tasdiqlash"""
        if self.status != PaymentStatus.PENDING:
            return False
        self.status = PaymentStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        if transaction_id:
            self.transaction_id = transaction_id
        else:
            self.transaction_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"
        return True

    def fail(self, reason: str = "") -> bool:
        """To'lovni rad etish"""
        if self.status != PaymentStatus.PENDING:
            return False
        self.status = PaymentStatus.FAILED
        if reason:
            self.notes += f" | Xato: {reason}"
        return True

    def refund(self) -> bool:
        """To'lovni qaytarish"""
        if self.status != PaymentStatus.COMPLETED:
            return False
        self.status = PaymentStatus.REFUNDED
        return True

    @property
    def is_completed(self) -> bool:
        return self.status == PaymentStatus.COMPLETED

    @property
    def method_display(self) -> str:
        labels = {
            PaymentMethod.CASH: "💵 Naqd",
            PaymentMethod.CARD: "💳 Karta",
            PaymentMethod.ONLINE: "🌐 Online",
            PaymentMethod.PAYME: "📱 Payme",
            PaymentMethod.CLICK: "📱 Click"
        }
        return labels.get(self.method, self.method)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "amount": self.amount,
            "method": self.method,
            "method_display": self.method_display,
            "status": self.status,
            "transaction_id": self.transaction_id,
            "notes": self.notes,
            "cashier_name": self.cashier_name,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Payment':
        return cls(
            id=data.get("id", f"PAY-{str(uuid.uuid4())[:6].upper()}"),
            order_id=data["order_id"],
            amount=data["amount"],
            method=data.get("method", PaymentMethod.CASH),
            status=data.get("status", PaymentStatus.PENDING),
            transaction_id=data.get("transaction_id"),
            notes=data.get("notes", ""),
            cashier_name=data.get("cashier_name", "Kassir"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at")
        )

    def __str__(self):
        return f"[{self.id}] {self.order_id} - {self.amount:,.0f} so'm ({self.method_display}) - {self.status}"
