"""
To'lov kontrolleri
"""
from typing import List, Optional, Dict
from backend.models.payment import Payment, PaymentMethod, PaymentStatus
from backend.models.order import OrderStatus
from backend.database.db_manager import DatabaseManager


class PaymentController:
    """To'lovlarni boshqarish kontrolleri"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_all(self, status: Optional[str] = None) -> List[Dict]:
        """Barcha to'lovlarni olish"""
        payments = list(self.db.get_all_payments().values())
        if status:
            payments = [p for p in payments if p.get("status") == status]
        return sorted(payments, key=lambda x: x.get("created_at", ""), reverse=True)

    def get_by_id(self, payment_id: str) -> Optional[Dict]:
        """ID bo'yicha to'lovni olish"""
        return self.db.get_payment(payment_id)

    def get_by_order(self, order_id: str) -> List[Dict]:
        """Buyurtma bo'yicha to'lovlarni olish"""
        return self.db.get_payments_by_order(order_id)

    def create(self, data: Dict) -> Dict:
        """Yangi to'lov yaratish"""
        order_id = data["order_id"]
        order_data = self.db.get_order(order_id)

        if not order_data:
            raise ValueError(f"Buyurtma topilmadi: {order_id}")

        if order_data.get("status") == OrderStatus.CANCELLED:
            raise ValueError("Bekor qilingan buyurtma uchun to'lov qilish mumkin emas!")

        # Avvalgi to'lovlarni tekshirish
        existing = self.db.get_payments_by_order(order_id)
        already_paid = sum(
            p["amount"] for p in existing if p.get("status") == PaymentStatus.COMPLETED
        )

        amount = float(data.get("amount", order_data.get("total", 0)))

        payment = Payment(
            order_id=order_id,
            amount=amount,
            method=data.get("method", PaymentMethod.CASH),
            cashier_name=data.get("cashier_name", "Kassir"),
            notes=data.get("notes", "")
        )

        # Darhol tasdiqlash
        payment.complete()

        # Buyurtmani "yetkazildi" deb belgilash
        if order_data.get("status") not in [OrderStatus.CANCELLED, OrderStatus.DELIVERED]:
            order_data["status"] = OrderStatus.DELIVERED
            from datetime import datetime
            order_data["updated_at"] = datetime.now().isoformat()
            self.db.save_order(order_id, order_data)

        self.db.save_payment(payment.id, payment.to_dict())
        return payment.to_dict()

    def refund(self, payment_id: str) -> Optional[Dict]:
        """To'lovni qaytarish"""
        payment_data = self.db.get_payment(payment_id)
        if not payment_data:
            return None
        payment = Payment.from_dict(payment_data)
        if not payment.refund():
            raise ValueError("Bu to'lovni qaytarish mumkin emas!")
        self.db.save_payment(payment_id, payment.to_dict())
        return payment.to_dict()

    def get_payment_methods(self) -> List[Dict]:
        """To'lov usullarini olish"""
        return [
            {"value": PaymentMethod.CASH, "label": "💵 Naqd pul"},
            {"value": PaymentMethod.CARD, "label": "💳 Bank kartasi"},
            {"value": PaymentMethod.ONLINE, "label": "🌐 Online to'lov"},
            {"value": PaymentMethod.PAYME, "label": "📱 Payme"},
            {"value": PaymentMethod.CLICK, "label": "📱 Click"},
        ]

    def get_revenue_summary(self) -> Dict:
        """Daromad xulosasi"""
        payments = list(self.db.get_all_payments().values())
        completed = [p for p in payments if p.get("status") == PaymentStatus.COMPLETED]
        refunded = [p for p in payments if p.get("status") == PaymentStatus.REFUNDED]

        by_method = {}
        for p in completed:
            method = p.get("method", "cash")
            by_method[method] = by_method.get(method, 0) + p.get("amount", 0)

        return {
            "total_revenue": round(sum(p.get("amount", 0) for p in completed), 2),
            "total_refunded": round(sum(p.get("amount", 0) for p in refunded), 2),
            "total_transactions": len(completed),
            "by_method": by_method
        }
