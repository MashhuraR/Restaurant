"""
Restoran Boshqaruv Tizimi - Asosiy Flask Ilovasi
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
from pathlib import Path

from database import get_connection, init_db, DB_PATH
from models import (
    OrderStatus, PaymentMethod, PaymentStatus,
    Order, OrderItem, Payment
)

# ─────────────────────────────────────────────
# ILOVANI SOZLASH
# ─────────────────────────────────────────────

BASE_DIR    = Path(__file__).parent
STATIC_DIR  = BASE_DIR.parent / "frontend"

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="")
CORS(app)

# ─────────────────────────────────────────────
# YORDAMCHI FUNKSIYALAR
# ─────────────────────────────────────────────

def ok(data=None, msg="Muvaffaqiyatli", code=200):
    return jsonify({"success": True,  "message": msg, "data": data}), code

def err(msg="Xatolik yuz berdi", code=400):
    return jsonify({"success": False, "message": msg, "data": None}), code

def row_to_dict(row):
    return dict(row) if row else None

def rows_to_list(rows):
    return [dict(r) for r in rows]

def recalc_order(conn, order_id):
    """Buyurtma summalarini qayta hisoblash."""
    TAX = 0.12; SVC = 0.05
    cur = conn.cursor()
    cur.execute("SELECT SUM(subtotal) FROM order_items WHERE order_id=?", (order_id,))
    sub = cur.fetchone()[0] or 0
    tax  = round(sub * TAX, 2)
    svc  = round(sub * SVC, 2)
    tot  = round(sub + tax + svc, 2)
    cur.execute(
        "UPDATE orders SET subtotal=?, tax=?, service_fee=?, total=?, updated_at=? WHERE id=?",
        (sub, tax, svc, tot, datetime.now().isoformat(), order_id)
    )
    return {"subtotal": sub, "tax": tax, "service_fee": svc, "total": tot}

# ─────────────────────────────────────────────
# FRONTEND
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(STATIC_DIR), "index.html")

# ─────────────────────────────────────────────
# KATEGORIYALAR
# ─────────────────────────────────────────────

@app.route("/api/categories", methods=["GET"])
def get_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY id").fetchall()
    conn.close()
    return ok(rows_to_list(rows))

@app.route("/api/categories", methods=["POST"])
def create_category():
    d = request.json or {}
    name = d.get("name","").strip()
    if not name:
        return err("Kategoriya nomi kerak")
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO categories (name, icon, description) VALUES (?,?,?)",
        (name, d.get("icon","🍽️"), d.get("description",""))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM categories WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Kategoriya qo'shildi", 201)

@app.route("/api/categories/<int:cid>", methods=["PUT"])
def update_category(cid):
    d = request.json or {}
    conn = get_connection()
    conn.execute(
        "UPDATE categories SET name=?, icon=?, description=? WHERE id=?",
        (d.get("name"), d.get("icon"), d.get("description"), cid)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM categories WHERE id=?", (cid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Yangilandi")

@app.route("/api/categories/<int:cid>", methods=["DELETE"])
def delete_category(cid):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id=?", (cid,))
    conn.commit()
    conn.close()
    return ok(msg="Kategoriya o'chirildi")

# ─────────────────────────────────────────────
# MENYU
# ─────────────────────────────────────────────

@app.route("/api/menu", methods=["GET"])
def get_menu():
    cat_id = request.args.get("category_id")
    avail  = request.args.get("available")
    q      = "SELECT m.*, c.name as category_name, c.icon as category_icon FROM menu_items m JOIN categories c ON m.category_id=c.id WHERE 1=1"
    params = []
    if cat_id:
        q += " AND m.category_id=?"; params.append(int(cat_id))
    if avail:
        q += " AND m.is_available=?"; params.append(1 if avail=="1" else 0)
    q += " ORDER BY m.category_id, m.name"
    conn = get_connection()
    rows = conn.execute(q, params).fetchall()
    conn.close()
    items = []
    for r in rows:
        d = dict(r)
        try:    d["allergens"] = json.loads(d["allergens"] or "[]")
        except: d["allergens"] = []
        items.append(d)
    return ok(items)

@app.route("/api/menu/<int:mid>", methods=["GET"])
def get_menu_item(mid):
    conn = get_connection()
    row  = conn.execute(
        "SELECT m.*, c.name as category_name FROM menu_items m JOIN categories c ON m.category_id=c.id WHERE m.id=?",
        (mid,)
    ).fetchone()
    conn.close()
    if not row: return err("Topilmadi", 404)
    d = dict(row)
    try:    d["allergens"] = json.loads(d["allergens"] or "[]")
    except: d["allergens"] = []
    return ok(d)

@app.route("/api/menu", methods=["POST"])
def create_menu_item():
    d = request.json or {}
    required = ["name", "price", "category_id"]
    for f in required:
        if not d.get(f):
            return err(f"'{f}' maydoni kerak")
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """INSERT INTO menu_items
           (name,price,category_id,description,image_url,is_available,preparation_time,calories,allergens)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            d["name"], float(d["price"]), int(d["category_id"]),
            d.get("description",""), d.get("image_url",""),
            1 if d.get("is_available", True) else 0,
            int(d.get("preparation_time", 10)),
            int(d.get("calories", 0)),
            json.dumps(d.get("allergens", []))
        )
    )
    conn.commit()
    row = conn.execute(
        "SELECT m.*, c.name as category_name FROM menu_items m JOIN categories c ON m.category_id=c.id WHERE m.id=?",
        (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Menyu elementi qo'shildi", 201)

@app.route("/api/menu/<int:mid>", methods=["PUT"])
def update_menu_item(mid):
    d = request.json or {}
    conn = get_connection()
    conn.execute(
        """UPDATE menu_items SET
           name=?, price=?, category_id=?, description=?, image_url=?,
           is_available=?, preparation_time=?, calories=?, allergens=?, updated_at=?
           WHERE id=?""",
        (
            d.get("name"), float(d.get("price",0)), int(d.get("category_id",1)),
            d.get("description",""), d.get("image_url",""),
            1 if d.get("is_available", True) else 0,
            int(d.get("preparation_time", 10)),
            int(d.get("calories", 0)),
            json.dumps(d.get("allergens",[])),
            datetime.now().isoformat(), mid
        )
    )
    conn.commit()
    row = conn.execute("SELECT * FROM menu_items WHERE id=?", (mid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Yangilandi")

@app.route("/api/menu/<int:mid>", methods=["DELETE"])
def delete_menu_item(mid):
    conn = get_connection()
    conn.execute("DELETE FROM menu_items WHERE id=?", (mid,))
    conn.commit()
    conn.close()
    return ok(msg="Menyu elementi o'chirildi")

@app.route("/api/menu/<int:mid>/toggle", methods=["POST"])
def toggle_availability(mid):
    conn = get_connection()
    row  = conn.execute("SELECT is_available FROM menu_items WHERE id=?", (mid,)).fetchone()
    if not row: return err("Topilmadi", 404)
    new_val = 0 if row["is_available"] else 1
    conn.execute("UPDATE menu_items SET is_available=? WHERE id=?", (new_val, mid))
    conn.commit()
    conn.close()
    return ok({"is_available": bool(new_val)}, "Holat yangilandi")

# ─────────────────────────────────────────────
# STOLLAR
# ─────────────────────────────────────────────

@app.route("/api/tables", methods=["GET"])
def get_tables():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tables ORDER BY number").fetchall()
    conn.close()
    return ok(rows_to_list(rows))

@app.route("/api/tables/<int:tid>", methods=["GET"])
def get_table(tid):
    conn = get_connection()
    row  = conn.execute("SELECT * FROM tables WHERE id=?", (tid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row)) if row else err("Topilmadi", 404)

@app.route("/api/tables", methods=["POST"])
def create_table():
    d = request.json or {}
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO tables (number, capacity, location) VALUES (?,?,?)",
        (d.get("number"), d.get("capacity",4), d.get("location","Zal"))
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tables WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Stol qo'shildi", 201)

@app.route("/api/tables/<int:tid>/status", methods=["PUT"])
def update_table_status(tid):
    d      = request.json or {}
    status = d.get("status","free")
    conn   = get_connection()
    conn.execute("UPDATE tables SET status=? WHERE id=?", (status, tid))
    conn.commit()
    row = conn.execute("SELECT * FROM tables WHERE id=?", (tid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Stol holati yangilandi")

# ─────────────────────────────────────────────
# BUYURTMALAR
# ─────────────────────────────────────────────

@app.route("/api/orders", methods=["GET"])
def get_orders():
    status   = request.args.get("status")
    table_id = request.args.get("table_id")
    q        = "SELECT o.*, t.number as table_number FROM orders o JOIN tables t ON o.table_id=t.id WHERE 1=1"
    params   = []
    if status:
        q += " AND o.status=?"; params.append(status)
    if table_id:
        q += " AND o.table_id=?"; params.append(int(table_id))
    q += " ORDER BY o.created_at DESC LIMIT 200"
    conn  = get_connection()
    rows  = conn.execute(q, params).fetchall()
    result = []
    for r in rows:
        od = dict(r)
        items = conn.execute(
            "SELECT * FROM order_items WHERE order_id=?", (od["id"],)
        ).fetchall()
        od["items"] = rows_to_list(items)
        result.append(od)
    conn.close()
    return ok(result)

@app.route("/api/orders/<int:oid>", methods=["GET"])
def get_order(oid):
    conn = get_connection()
    row  = conn.execute(
        "SELECT o.*, t.number as table_number FROM orders o JOIN tables t ON o.table_id=t.id WHERE o.id=?",
        (oid,)
    ).fetchone()
    if not row:
        conn.close(); return err("Topilmadi", 404)
    od    = dict(row)
    items = conn.execute("SELECT * FROM order_items WHERE order_id=?", (oid,)).fetchall()
    od["items"] = rows_to_list(items)
    # to'lov
    pay   = conn.execute("SELECT * FROM payments WHERE order_id=?", (oid,)).fetchone()
    od["payment"] = row_to_dict(pay)
    conn.close()
    return ok(od)

@app.route("/api/orders", methods=["POST"])
def create_order():
    d = request.json or {}
    table_id = d.get("table_id")
    if not table_id:
        return err("Stol ID kerak")
    conn = get_connection()
    # Stol mavjudligini tekshirish
    tbl = conn.execute("SELECT * FROM tables WHERE id=?", (table_id,)).fetchone()
    if not tbl:
        conn.close(); return err("Stol topilmadi", 404)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (table_id, customer_name, notes, status) VALUES (?,?,?,?)",
        (table_id, d.get("customer_name","Mehmon"), d.get("notes",""), "pending")
    )
    order_id = cur.lastrowid

    # Buyurtma elementlari
    items = d.get("items", [])
    for it in items:
        menu_row = conn.execute(
            "SELECT * FROM menu_items WHERE id=? AND is_available=1", (it["menu_item_id"],)
        ).fetchone()
        if not menu_row: continue
        qty  = int(it.get("quantity", 1))
        sub  = round(qty * menu_row["price"], 2)
        cur.execute(
            """INSERT INTO order_items
               (order_id, menu_item_id, menu_item_name, quantity, unit_price, notes, subtotal)
               VALUES (?,?,?,?,?,?,?)""",
            (order_id, menu_row["id"], menu_row["name"], qty, menu_row["price"],
             it.get("notes",""), sub)
        )

    recalc_order(conn, order_id)
    # Stolni band deb belgilash
    conn.execute("UPDATE tables SET status='occupied' WHERE id=?", (table_id,))
    conn.commit()

    row  = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    od   = dict(row)
    irows = conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    od["items"] = rows_to_list(irows)
    conn.close()
    return ok(od, "Buyurtma yaratildi", 201)

@app.route("/api/orders/<int:oid>/items", methods=["POST"])
def add_order_item(oid):
    d = request.json or {}
    conn = get_connection()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not order:
        conn.close(); return err("Buyurtma topilmadi", 404)
    if order["status"] in ("served","cancelled"):
        conn.close(); return err("Bu buyurtmaga element qo'shib bo'lmaydi")
    menu_row = conn.execute(
        "SELECT * FROM menu_items WHERE id=? AND is_available=1", (d.get("menu_item_id"),)
    ).fetchone()
    if not menu_row:
        conn.close(); return err("Menyu elementi topilmadi yoki mavjud emas", 404)
    qty = int(d.get("quantity", 1))
    sub = round(qty * menu_row["price"], 2)
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO order_items
           (order_id, menu_item_id, menu_item_name, quantity, unit_price, notes, subtotal)
           VALUES (?,?,?,?,?,?,?)""",
        (oid, menu_row["id"], menu_row["name"], qty, menu_row["price"],
         d.get("notes",""), sub)
    )
    recalc_order(conn, oid)
    conn.commit()
    row = conn.execute("SELECT * FROM order_items WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Element qo'shildi", 201)

@app.route("/api/orders/<int:oid>/items/<int:iid>", methods=["DELETE"])
def remove_order_item(oid, iid):
    conn = get_connection()
    conn.execute("DELETE FROM order_items WHERE id=? AND order_id=?", (iid, oid))
    recalc_order(conn, oid)
    conn.commit()
    conn.close()
    return ok(msg="Element o'chirildi")

@app.route("/api/orders/<int:oid>/status", methods=["PUT"])
def update_order_status(oid):
    d      = request.json or {}
    status = d.get("status")
    valid  = [s.value for s in OrderStatus]
    if status not in valid:
        return err(f"Noto'g'ri holat. To'g'ri qiymatlar: {valid}")
    conn = get_connection()
    conn.execute(
        "UPDATE orders SET status=?, updated_at=? WHERE id=?",
        (status, datetime.now().isoformat(), oid)
    )
    # Buyurtma yopilsa yoki bekor bo'lsa stol bo'shatiladi
    if status in ("served", "cancelled"):
        row = conn.execute("SELECT table_id FROM orders WHERE id=?", (oid,)).fetchone()
        if row:
            conn.execute("UPDATE tables SET status='free' WHERE id=?", (row["table_id"],))
    conn.commit()
    row = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "Holat yangilandi")

@app.route("/api/orders/<int:oid>", methods=["DELETE"])
def cancel_order(oid):
    conn = get_connection()
    row  = conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not row:
        conn.close(); return err("Topilmadi", 404)
    conn.execute(
        "UPDATE orders SET status='cancelled', updated_at=? WHERE id=?",
        (datetime.now().isoformat(), oid)
    )
    conn.execute("UPDATE tables SET status='free' WHERE id=?", (row["table_id"],))
    conn.commit()
    conn.close()
    return ok(msg="Buyurtma bekor qilindi")

# ─────────────────────────────────────────────
# TO'LOVLAR
# ─────────────────────────────────────────────

@app.route("/api/payments", methods=["GET"])
def get_payments():
    conn  = get_connection()
    rows  = conn.execute(
        """SELECT p.*, o.customer_name, t.number as table_number
           FROM payments p
           JOIN orders o ON p.order_id=o.id
           JOIN tables  t ON o.table_id=t.id
           ORDER BY p.created_at DESC LIMIT 200"""
    ).fetchall()
    conn.close()
    return ok(rows_to_list(rows))

@app.route("/api/payments/<int:pid>", methods=["GET"])
def get_payment(pid):
    conn = get_connection()
    row  = conn.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row)) if row else err("Topilmadi", 404)

@app.route("/api/payments", methods=["POST"])
def create_payment():
    d        = request.json or {}
    order_id = d.get("order_id")
    method   = d.get("method","cash")
    if not order_id:
        return err("Buyurtma ID kerak")
    valid_methods = [m.value for m in PaymentMethod]
    if method not in valid_methods:
        return err(f"Noto'g'ri to'lov usuli: {valid_methods}")

    conn  = get_connection()
    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        conn.close(); return err("Buyurtma topilmadi", 404)
    # To'lov allaqachon mavjudmi?
    exist = conn.execute("SELECT id FROM payments WHERE order_id=?", (order_id,)).fetchone()
    if exist:
        conn.close(); return err("Bu buyurtma uchun to'lov allaqachon amalga oshirilgan")

    tip        = float(d.get("tip", 0))
    amount     = float(order["total"])
    total_paid = round(amount + tip, 2)
    txn_id     = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"

    cur = conn.cursor()
    cur.execute(
        """INSERT INTO payments (order_id, amount, tip, total_paid, method, transaction_id, status)
           VALUES (?,?,?,?,?,?,?)""",
        (order_id, amount, tip, total_paid, method, txn_id, "completed")
    )
    # Buyurtma holatini yangilash
    conn.execute(
        "UPDATE orders SET status='served', updated_at=? WHERE id=?",
        (datetime.now().isoformat(), order_id)
    )
    # Stolni bo'shatish
    conn.execute("UPDATE tables SET status='free' WHERE id=?", (order["table_id"],))
    conn.commit()
    row = conn.execute("SELECT * FROM payments WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "To'lov muvaffaqiyatli amalga oshirildi", 201)

@app.route("/api/payments/<int:pid>/refund", methods=["POST"])
def refund_payment(pid):
    conn = get_connection()
    row  = conn.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not row:
        conn.close(); return err("Topilmadi", 404)
    if row["status"] == "refunded":
        conn.close(); return err("Bu to'lov allaqachon qaytarilgan")
    conn.execute("UPDATE payments SET status='refunded' WHERE id=?", (pid,))
    conn.execute(
        "UPDATE orders SET status='cancelled', updated_at=? WHERE id=?",
        (datetime.now().isoformat(), row["order_id"])
    )
    conn.commit()
    row = conn.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    conn.close()
    return ok(row_to_dict(row), "To'lov qaytarildi")

# ─────────────────────────────────────────────
# STATISTIKA / DASHBOARD
# ─────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_connection()
    today = datetime.now().strftime("%Y-%m-%d")

    total_orders    = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    active_orders   = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE status NOT IN ('served','cancelled')"
    ).fetchone()[0]
    today_revenue   = conn.execute(
        "SELECT COALESCE(SUM(total_paid),0) FROM payments WHERE status='completed' AND date(created_at)=?",
        (today,)
    ).fetchone()[0]
    total_revenue   = conn.execute(
        "SELECT COALESCE(SUM(total_paid),0) FROM payments WHERE status='completed'"
    ).fetchone()[0]
    free_tables     = conn.execute("SELECT COUNT(*) FROM tables WHERE status='free'").fetchone()[0]
    occupied_tables = conn.execute("SELECT COUNT(*) FROM tables WHERE status='occupied'").fetchone()[0]
    menu_count      = conn.execute("SELECT COUNT(*) FROM menu_items WHERE is_available=1").fetchone()[0]
    today_orders    = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE date(created_at)=?", (today,)
    ).fetchone()[0]

    # Top 5 mahsulot
    top_items = conn.execute(
        """SELECT oi.menu_item_name, SUM(oi.quantity) as total_qty, SUM(oi.subtotal) as total_rev
           FROM order_items oi
           JOIN orders o ON oi.order_id=o.id
           WHERE o.status='served'
           GROUP BY oi.menu_item_id
           ORDER BY total_qty DESC LIMIT 5"""
    ).fetchall()

    # So'nggi buyurtmalar
    recent_orders = conn.execute(
        """SELECT o.id, o.customer_name, o.status, o.total, t.number as table_number, o.created_at
           FROM orders o JOIN tables t ON o.table_id=t.id
           ORDER BY o.created_at DESC LIMIT 10"""
    ).fetchall()

    # Kunlik daromad (oxirgi 7 kun)
    daily_rev = conn.execute(
        """SELECT date(created_at) as day, SUM(total_paid) as revenue
           FROM payments WHERE status='completed'
           GROUP BY day ORDER BY day DESC LIMIT 7"""
    ).fetchall()

    conn.close()
    return ok({
        "total_orders":    total_orders,
        "active_orders":   active_orders,
        "today_orders":    today_orders,
        "today_revenue":   round(today_revenue, 2),
        "total_revenue":   round(total_revenue, 2),
        "free_tables":     free_tables,
        "occupied_tables": occupied_tables,
        "menu_count":      menu_count,
        "top_items":       rows_to_list(top_items),
        "recent_orders":   rows_to_list(recent_orders),
        "daily_revenue":   rows_to_list(daily_rev),
    })

# ─────────────────────────────────────────────
# ISHGA TUSHIRISH
# ─────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("=" * 55)
    print("  🍽️  Restoran Boshqaruv Tizimi ishga tushdi!")
    print("  🌐  http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, host="0.0.0.0", port=5000)
