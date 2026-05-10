"""
Restoran Boshqaruv Tizimi - Backend API
Flask yordamida yaratilgan RESTful API
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from backend.database.db_manager import DatabaseManager
from backend.controllers.menu_controller import MenuController
from backend.controllers.order_controller import OrderController
from backend.controllers.payment_controller import PaymentController

# ─── App sozlamalari ──────────────────────────────────────────────
app = Flask(__name__, static_folder='frontend', static_url_path='')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
CORS(app)

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ─── Kontrollerlarni ishga tushirish ─────────────────────────────
db = DatabaseManager(db_path="database/restaurant_db.json")
menu_ctrl = MenuController(db)
order_ctrl = OrderController(db)
payment_ctrl = PaymentController(db)


# ─── Helper funksiyalar ──────────────────────────────────────────
def success(data=None, message="Muvaffaqiyatli", code=200):
    return jsonify({"success": True, "message": message, "data": data}), code

def error(message="Xato yuz berdi", code=400):
    return jsonify({"success": False, "message": message, "data": None}), code


# ─── Frontend sahifalar ──────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')


# ═══════════════════════════════════════════════════════════════
#                    MENYU API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/menu', methods=['GET'])
def get_menu():
    """Barcha menyu elementlarini olish"""
    category = request.args.get('category')
    available_only = request.args.get('available_only', 'false').lower() == 'true'
    items = menu_ctrl.get_all(category=category, available_only=available_only)
    return success(items)

@app.route('/api/menu/search', methods=['GET'])
def search_menu():
    """Menyu elementlarini qidirish"""
    query = request.args.get('q', '')
    if not query:
        return error("Qidiruv so'zi kiriting!")
    results = menu_ctrl.search(query)
    return success(results)

@app.route('/api/menu/categories', methods=['GET'])
def get_categories():
    """Kategoriyalarni olish"""
    return success(menu_ctrl.get_categories())

@app.route('/api/menu/<item_id>', methods=['GET'])
def get_menu_item(item_id):
    """Bitta menyu elementini olish"""
    item = menu_ctrl.get_by_id(item_id)
    if not item:
        return error("Menyu elementi topilmadi!", 404)
    return success(item)

@app.route('/api/menu', methods=['POST'])
def create_menu_item():
    """Yangi menyu elementi yaratish"""
    data = request.json
    if not data:
        return error("Ma'lumot yuborilmadi!")
    required = ["name", "price", "category"]
    for field in required:
        if field not in data:
            return error(f"'{field}' maydoni majburiy!")
    try:
        item = menu_ctrl.create(data)
        return success(item, "Menyu elementi yaratildi!", 201)
    except ValueError as e:
        return error(str(e))

@app.route('/api/menu/<item_id>', methods=['PUT'])
def update_menu_item(item_id):
    """Menyu elementini yangilash"""
    data = request.json
    if not data:
        return error("Ma'lumot yuborilmadi!")
    item = menu_ctrl.update(item_id, data)
    if not item:
        return error("Menyu elementi topilmadi!", 404)
    return success(item, "Yangilandi!")

@app.route('/api/menu/<item_id>/toggle', methods=['PATCH'])
def toggle_menu_item(item_id):
    """Mavjudlikni o'zgartirish"""
    item = menu_ctrl.toggle_availability(item_id)
    if not item:
        return error("Menyu elementi topilmadi!", 404)
    status = "mavjud" if item["is_available"] else "mavjud emas"
    return success(item, f"Holat o'zgartirildi: {status}")

@app.route('/api/menu/<item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    """Menyu elementini o'chirish"""
    if menu_ctrl.delete(item_id):
        return success(None, "O'chirildi!")
    return error("Menyu elementi topilmadi!", 404)


# ═══════════════════════════════════════════════════════════════
#                    BUYURTMALAR API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Barcha buyurtmalarni olish"""
    status = request.args.get('status')
    orders = order_ctrl.get_all(status=status)
    return success(orders)

@app.route('/api/orders/active', methods=['GET'])
def get_active_orders():
    """Faol buyurtmalarni olish"""
    orders = order_ctrl.get_active_orders()
    return success(orders)

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """Bitta buyurtmani olish"""
    order = order_ctrl.get_by_id(order_id)
    if not order:
        return error("Buyurtma topilmadi!", 404)
    return success(order)

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Yangi buyurtma yaratish"""
    data = request.json
    if not data:
        return error("Ma'lumot yuborilmadi!")
    if "customer_name" not in data:
        return error("Mijoz ismi majburiy!")
    try:
        order = order_ctrl.create(data)
        return success(order, f"Buyurtma #{order['id']} yaratildi!", 201)
    except ValueError as e:
        return error(str(e))

@app.route('/api/orders/<order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    """Buyurtma statusini yangilash"""
    data = request.json
    if not data or "status" not in data:
        return error("Status yuborilmadi!")
    try:
        order = order_ctrl.update_status(order_id, data["status"])
        if not order:
            return error("Buyurtma topilmadi!", 404)
        return success(order, f"Status yangilandi: {order['status']}")
    except ValueError as e:
        return error(str(e))

@app.route('/api/orders/<order_id>/cancel', methods=['PATCH'])
def cancel_order(order_id):
    """Buyurtmani bekor qilish"""
    data = request.json or {}
    try:
        order = order_ctrl.cancel(order_id, data.get("reason", ""))
        if not order:
            return error("Buyurtma topilmadi!", 404)
        return success(order, "Buyurtma bekor qilindi!")
    except ValueError as e:
        return error(str(e))

@app.route('/api/orders/<order_id>/items', methods=['POST'])
def add_order_item(order_id):
    """Buyurtmaga element qo'shish"""
    data = request.json
    if not data or "menu_item_id" not in data:
        return error("Menyu elementi IDsi majburiy!")
    try:
        order = order_ctrl.add_item(order_id, data)
        if not order:
            return error("Buyurtma topilmadi!", 404)
        return success(order, "Element qo'shildi!")
    except ValueError as e:
        return error(str(e))

@app.route('/api/orders/<order_id>/items/<menu_item_id>', methods=['DELETE'])
def remove_order_item(order_id, menu_item_id):
    """Buyurtmadan element o'chirish"""
    try:
        order = order_ctrl.remove_item(order_id, menu_item_id)
        if not order:
            return error("Buyurtma topilmadi!", 404)
        return success(order, "Element o'chirildi!")
    except ValueError as e:
        return error(str(e))

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Statistika"""
    stats = order_ctrl.get_statistics()
    revenue = payment_ctrl.get_revenue_summary()
    stats.update(revenue)
    return success(stats)


# ═══════════════════════════════════════════════════════════════
#                    TO'LOVLAR API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/payments', methods=['GET'])
def get_payments():
    """Barcha to'lovlarni olish"""
    status = request.args.get('status')
    payments = payment_ctrl.get_all(status=status)
    return success(payments)

@app.route('/api/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    """Bitta to'lovni olish"""
    payment = payment_ctrl.get_by_id(payment_id)
    if not payment:
        return error("To'lov topilmadi!", 404)
    return success(payment)

@app.route('/api/payments/order/<order_id>', methods=['GET'])
def get_payments_by_order(order_id):
    """Buyurtma bo'yicha to'lovlarni olish"""
    payments = payment_ctrl.get_by_order(order_id)
    return success(payments)

@app.route('/api/payments', methods=['POST'])
def create_payment():
    """Yangi to'lov yaratish"""
    data = request.json
    if not data:
        return error("Ma'lumot yuborilmadi!")
    if "order_id" not in data:
        return error("Buyurtma IDsi majburiy!")
    try:
        payment = payment_ctrl.create(data)
        return success(payment, f"To'lov #{payment['id']} amalga oshirildi!", 201)
    except ValueError as e:
        return error(str(e))

@app.route('/api/payments/<payment_id>/refund', methods=['PATCH'])
def refund_payment(payment_id):
    """To'lovni qaytarish"""
    try:
        payment = payment_ctrl.refund(payment_id)
        if not payment:
            return error("To'lov topilmadi!", 404)
        return success(payment, "To'lov qaytarildi!")
    except ValueError as e:
        return error(str(e))

@app.route('/api/payments/methods', methods=['GET'])
def get_payment_methods():
    """To'lov usullarini olish"""
    return success(payment_ctrl.get_payment_methods())

@app.route('/api/payments/revenue', methods=['GET'])
def get_revenue():
    """Daromad xulosasi"""
    return success(payment_ctrl.get_revenue_summary())


# ─── Xato ishlovchilar ──────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return error("Sahifa topilmadi!", 404)

@app.errorhandler(500)
def server_error(e):
    return error("Server xatosi!", 500)


if __name__ == '__main__':
    print("Restoran Boshqaruv Tizimi ishga tushmoqda...")
    print("API: http://localhost:5000")
    print("Frontend: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
