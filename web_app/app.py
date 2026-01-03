from flask import Flask, render_template, request, jsonify, g, redirect, url_for
import sqlite3
import os
import json
import random
import string
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'app.db')

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'static'), template_folder='templates')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY, name TEXT, price INTEGER, stock INTEGER, meta TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, data TEXT)''')
    cur.execute('''CREATE TABLE IF NOT EXISTS payment_codes(code TEXT PRIMARY KEY, order_id TEXT, issued_at TEXT, expires_at TEXT, status TEXT)''')
    cur.execute('SELECT COUNT(1) FROM products')
    if cur.fetchone()[0] == 0:
        defaults = [
            ('APP-001','Tシャツ（ホワイト）',3000,120,''),
            ('APP-002','Tシャツ（ブラック）',3000,110,''),
            ('APP-003','ロングスリーブT',3800,80,''),
            ('APP-004','パーカー（グレー）',6000,60,''),
            ('APP-005','パーカー（ネイビー）',6000,60,''),
            ('APP-006','デニムパンツ',7500,40,''),
            ('APP-007','キャップ（刺繍）',2200,90,''),
            ('APP-008','トートバッグ',1800,150,''),
            ('APP-009','ソックス（3足セット）',1200,200,''),
            ('APP-010','ジャケット（ライト）',12000,30,'')
        ]
        cur.executemany('INSERT INTO products(id,name,price,stock,meta) VALUES(?,?,?,?,?)', defaults)
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_conn(exc):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def generate_code():
    return 'PC' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Init DB on import
init_db()

@app.route('/')
def index():
    db = get_db(); cur = db.cursor()
    cur.execute('SELECT id, name, price, stock FROM products LIMIT 6')
    featured = [dict(r) for r in cur.fetchall()]
    return render_template('index.html', featured=featured)

@app.route('/goods')
def goods():
    db = get_db(); cur = db.cursor()
    cur.execute('SELECT id, name, price, stock FROM products')
    products = [dict(r) for r in cur.fetchall()]
    return render_template('goods.html', products=products)


@app.route('/news')
def news():
    # Simple news/events list derived from req.md (static for now)
    items = [
        {'id': 'EVENT-A', 'title': 'Event A: 新作リリース', 'date': '2026-01-10', 'summary': '限定グッズの発売とポップアップ開催のお知らせ。'},
        {'id': 'EVENT-B', 'title': 'Event B: 再入荷情報', 'date': '2026-02-01', 'summary': '人気アイテムの再入荷を予定しています。'},
        {'id': 'EVENT-C', 'title': 'Event C: セール情報', 'date': '2026-03-15', 'summary': '期間限定セールを開催します。'}
    ]
    return render_template('news.html', news=items)


@app.route('/cart')
def cart():
    # Cart is client-side (localStorage). Render an empty page shell that the client JS will populate.
    return render_template('cart.html')


@app.route('/checkout')
def checkout_page():
    # Render checkout form page
    return render_template('checkout.html')


@app.route('/history')
def history():
    # User order history page (no auth implemented yet)
    # For now show a simple page; admin can view all orders at /admin/orders
    return render_template('history.html')


@app.route('/account')
def account():
    # Account / My Page (login not implemented)
    # Render a placeholder that explains account features will be available.
    return render_template('account.html')

@app.route('/product/<product_id>')
def product_detail(product_id):
    db = get_db(); cur = db.cursor()
    cur.execute('SELECT id, name, price, stock FROM products WHERE id=?', (product_id,))
    row = cur.fetchone()
    if not row:
        return 'Product not found', 404
    return render_template('product.html', product=dict(row))

@app.route('/api/products')
def api_products():
    db = get_db(); cur = db.cursor()
    cur.execute('SELECT id, name, price, stock FROM products')
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify(rows)

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    data = request.get_json() or {}
    cart = data.get('cart') or []
    name = data.get('name')
    email = data.get('email')
    chain = data.get('chain')
    store_code = data.get('store_code')
    if not cart or not name or not email:
        return jsonify({'error':'invalid payload'}), 400
    total = sum((item.get('qty',1) * item.get('price',0)) for item in cart)
    order_id = 'ORD' + datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    issued_at = datetime.utcnow()
    expires_at = issued_at + timedelta(hours=72)
    code = generate_code()
    order = {
        'id': order_id,
        'name': name,
        'email': email,
        'chain': chain,
        'store_code': store_code,
        'cart': cart,
        'total': total,
        'payment_code': code,
        'issued_at': issued_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'status': 'pending'
    }
    db = get_db(); cur = db.cursor()
    cur.execute('INSERT INTO orders(id,data) VALUES(?,?)', (order_id, json.dumps(order)))
    cur.execute('INSERT INTO payment_codes(code,order_id,issued_at,expires_at,status) VALUES(?,?,?,?,?)', (code, order_id, issued_at.isoformat(), expires_at.isoformat(), 'unpaid'))
    db.commit()
    return jsonify(order)

@app.route('/payment/<code>')
def payment_page(code):
    db = get_db(); cur = db.cursor()
    cur.execute('SELECT * FROM payment_codes WHERE code=?', (code,))
    row = cur.fetchone()
    if not row:
        return 'Code not found', 404
    cur.execute('SELECT data FROM orders WHERE id=?', (row['order_id'],))
    orow = cur.fetchone()
    order = json.loads(orow['data']) if orow else None
    return render_template('payment.html', order=order, code=row['code'], status=row['status'])

@app.route('/api/payments/simulate', methods=['POST'])
def simulate_payment():
    data = request.get_json() or {}
    code = data.get('code')
    if not code:
        return jsonify({'error':'code required'}), 400
    db = get_db(); cur = db.cursor()
    cur.execute('SELECT * FROM payment_codes WHERE code=?', (code,))
    row = cur.fetchone()
    if not row:
        return jsonify({'error':'not found'}), 404
    cur.execute('UPDATE payment_codes SET status=? WHERE code=?', ('paid', code))
    cur.execute('SELECT data FROM orders WHERE id=?', (row['order_id'],))
    orow = cur.fetchone()
    if orow:
        order = json.loads(orow['data'])
        order['status'] = 'paid'
        cur.execute('UPDATE orders SET data=? WHERE id=?', (json.dumps(order), row['order_id']))
    db.commit()
    return jsonify({'ok':True})

@app.route('/admin/orders')
def admin_orders():
    db = get_db(); cur = db.cursor()
    cur.execute('SELECT data FROM orders ORDER BY ROWID DESC')
    rows = cur.fetchall()
    orders = [json.loads(r['data']) for r in rows]
    return render_template('admin.html', orders=orders)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
