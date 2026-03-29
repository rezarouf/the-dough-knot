"""
The Dough Knot — Admin Server
Run: python admin.py
Main site : http://localhost:3000
Admin panel: http://localhost:3000/admin
"""

from flask import Flask, request, jsonify, session, send_file, send_from_directory
import sqlite3, json, os, uuid
from functools import wraps
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'doughknot-secret-2026-change-me'

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, 'data')
DB_PATH   = os.path.join(DATA_DIR, 'doughknot.db')
CONTENT_PATH  = os.path.join(DATA_DIR, 'content.json')
UPLOADS_DIR   = os.path.join(BASE_DIR, 'brand_assets', 'uploads')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'doughknot2026')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ── DATABASE ──────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript('''
            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                phone       TEXT,
                occasion    TEXT,
                date_needed TEXT,
                details     TEXT NOT NULL,
                status      TEXT DEFAULT "new",
                notes       TEXT DEFAULT "",
                created_at  TEXT DEFAULT (CURRENT_TIMESTAMP)
            );
            CREATE TABLE IF NOT EXISTS analytics (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type  TEXT NOT NULL,
                event_data  TEXT,
                user_agent  TEXT,
                referrer    TEXT,
                created_at  TEXT DEFAULT (CURRENT_TIMESTAMP)
            );
        ''')

init_db()


# ── CONTENT JSON ──────────────────────────────────────────────────────────────

DEFAULT_CONTENT = {
    "hero": {
        "eyebrow": "Cakes, Desserts & More · Dubai, UAE",
        "body": "Every bite handcrafted with love — from showstopping celebration cakes to the perfect everyday indulgence.",
        "cta": "View Our Menu",
        "image": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.01%20PM.jpeg",
        "slides": [
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.01%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.12%20PM%20(4).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.11%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.09%20PM.jpeg"
        ]
    },
    "about": {
        "label": "Our Story",
        "heading": "Made from scratch,\nbaked with heart",
        "body": "The Dough Knot started as a passion project in a home kitchen and grew into something much sweeter. Every cake, cookie, and pastry is handcrafted to order using the finest ingredients — because you deserve nothing less than the best.",
        "image1": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.09%20PM.jpeg",
        "image2": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.04%20PM.jpeg"
    },
    "hours": {
        "row1_label": "Monday – Friday", "row1_value": "9:00 AM – 8:00 PM",
        "row2_label": "Saturday",         "row2_value": "9:00 AM – 9:00 PM",
        "row3_label": "Sunday",           "row3_value": "10:00 AM – 6:00 PM"
    },
    "fullbleed": {
        "image": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.12%20PM.jpeg"
    },
    "gallery": {
        "images": [
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.01%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.04%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.05%20PM%20(2).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.11%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.02%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.01%20PM%20(4).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.05%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.06%20PM%20(3).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.10%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.04%20PM%20(4).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.12%20PM.jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.06%20PM%20(1).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.12%20PM%20(3).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.12%20PM%20(4).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.01%20PM%20(2).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.01%20PM%20(3).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.03%20PM%20(2).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.03%20PM%20(3).jpeg",
            "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.06%20PM%20(2).jpeg"
        ]
    },
    "menu": {
        "note": "All items baked fresh daily. Custom orders available with 48 hours notice.",
        "brownies": [
            {"name":"Nutella Brownies","desc":"Rich fudgy brownies swirled with creamy Nutella — an irresistible chocolate fix","price6":50,"priceSlab":120},
            {"name":"Fudge Brownies","desc":"Ultimate chocolate indulgence — intensely chocolatey, timeless, and never fails to delight","price6":40,"priceSlab":110},
            {"name":"Red Velvet Cheesecake Brownies","desc":"Moist red velvet base topped with silky smooth cheesecake — visually stunning and delicious","price6":50,"priceSlab":120},
            {"name":"Hazelnut Brownies","desc":"Rich fudgy brownies packed with crunchy hazelnuts — a perfect balance of texture and flavour","price6":60,"priceSlab":130},
            {"name":"Roasted Almond Brownies","desc":"Fudgy brownies loaded with roasted almonds — a sophisticated twist on a classic","price6":40,"priceSlab":110},
            {"name":"Chocolate Cheesecake Brownies","desc":"Rich fudgy brownies layered with decadent chocolate cheesecake — pure indulgence","price6":60,"priceSlab":130},
            {"name":"Lotus Biscoff Brownies","desc":"Sweet caramelised Lotus Biscoff swirled into rich fudgy brownies — a delightfully unexpected treat","price6":50,"priceSlab":120}
        ],
        "cakes": [
            {"name":"White Chocolate Raspberry Cake","desc":"Vanilla sponge, white chocolate ganache, tangy raspberry compote, finished with fresh raspberries","price":180},
            {"name":"Belgian Chocolate Cake","desc":"Dense, fudgy sponge with premium Belgian chocolate enveloped in velvety chocolate ganache","price":200},
            {"name":"Ferrero Rocher Cake","desc":"Hazelnut-chocolate sponge, Nutella cream, roasted hazelnuts, coated in decadent chocolate ganache","price":160},
            {"name":"Cookies & Cream Cake","desc":"Oreo-infused frosting, crushed cookies, and white Oreos — a nostalgic favourite","price":140},
            {"name":"Reese's Chocolate Cake","desc":"Chocolate cake, creamy peanut butter filling, rich chocolate ganache, topped with Reese's Pieces","price":180},
            {"name":"Almond Nutella Cake","desc":"Almond sponge, Nutella filling, roasted almonds, and Nutella buttercream — sweet and crunchy","price":140},
            {"name":"Truffle Chocolate Cake","desc":"Dense chocolate layers, glossy chocolate glaze adorned with hand-rolled chocolate truffles","price":120},
            {"name":"Matilda Chocolate Cake","desc":"Rich moist chocolate sponge, luscious chocolate fudge filling, thick chocolate frosting — every chocoholic's fantasy","price":150},
            {"name":"Lotus Biscoff Cake","desc":"Vanilla sponge layered with Biscoff spread and buttercream, topped with crushed Biscoff","price":140},
            {"name":"Rafaello White Chocolate Cake","desc":"Light coconut sponge, white chocolate-almond filling, white chocolate frosting — elegant and refined","price":140},
            {"name":"Tiramisu Cake","desc":"Coffee-soaked sponge, creamy mascarpone filling, dusted with cocoa — a decadent Italian classic","price":150},
            {"name":"Salted Caramel Cake","desc":"Vanilla sponge, rich salted caramel filling, caramel drizzle — the perfect sweet and savoury balance","price":110},
            {"name":"Caramel Crunch Cake","desc":"Caramel sponge, crunchy caramel pieces, caramel cream and sugar shards — a sweet, crunchy indulgence","price":130},
            {"name":"Hazelnut Praline Cake","desc":"Hazelnut sponge, smooth praline filling, chocolate ganache, topped with toasted hazelnuts","price":150},
            {"name":"Victoria Sandwich Cake","desc":"Classic light vanilla sponge, strawberry jam, vanilla cream, dusted with powdered sugar","price":100}
        ],
        "cookies": [
            {"name":"Chocolate Chip Filled Cookies","desc":"Gooey melted chocolate chip centre that will tantalize your taste buds","price":30},
            {"name":"Double Chocolate Filled Cookies","desc":"Rich, irresistible cookies packed with a double dose of decadent chocolate","price":35},
            {"name":"Brookies","desc":"The best of both worlds — fudgy brownie meets chewy cookie in one heavenly treat","price":25},
            {"name":"Dulce De Leche Cookies","desc":"Creamy caramelised dulce de leche filling — perfect paired with a sweet latte","price":30},
            {"name":"Red Velvet Cookies","desc":"Soft chewy red velvet cookies with a hint of cocoa and white chocolate","price":15},
            {"name":"Butter Cookies","desc":"Timeless, classic — perfectly crisp and buttery, melts in your mouth with every bite","price":15},
            {"name":"Salted Caramel Pecan Cookies","desc":"Irresistible sweet-salty cookies filled with luscious caramel and crunchy pecans","price":35}
        ]
    },
    "contact": {
        "whatsapp": "971567894758",
        "instagram": "thedoughknot.ae"
    },
    "baker": {
        "name": "Naurah\nNafeesa",
        "title": "Pastry Chef &amp; Founder",
        "bio": "Naurah Nafeesa is a passionate and experienced baker whose love for pastry turned into a lifelong craft. A graduate of the prestigious Lavonne Academy of Baking Science and Pastry Arts in Bangalore, India, she has been creating extraordinary baked goods professionally since 2017 — first in India, and now bringing her expertise and heart to Dubai through The Dough Knot.",
        "since": "2017",
        "school": "Lavonne Academy of Baking Science and Pastry Arts",
        "lavonne_logo": "https://www.lavonne.in/wp-content/uploads/2018/03/lavonne-logo-white.png",
        "photo": ""
    },
    "testimonials": [],
    "bestsellers": [
        {"name": "Brownies", "desc": "Rich, fudgy, and indulgent — available in Nutella, Hazelnut, Lotus Biscoff & more.", "badge": "Best Seller", "image": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.03%20PM%20(2).jpeg"},
        {"name": "Cookies", "desc": "Gooey centres, perfectly crisp edges — chocolate chip, double choc, red velvet & more.", "badge": "Best Seller", "image": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.06%20PM.jpeg"},
        {"name": "Berliners", "desc": "Pillowy soft filled doughnuts, rolled in sugar, topped with cream and fresh fruit.", "badge": "Customer Fave", "image": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.09%20PM.jpeg"},
        {"name": "Dream Cake", "desc": "Dreamy white cream, rose petals & pistachio — elegant, light, and utterly irresistible.", "badge": "Signature", "image": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.12%20PM%20(2).jpeg"},
        {"name": "White Chocolate Raspberry Cake", "desc": "Vanilla sponge, white chocolate ganache & fresh raspberries — the showstopper.", "badge": "Signature", "image": "/brand_assets/Images/WhatsApp%20Image%202026-03-26%20at%205.14.01%20PM.jpeg"}
    ]
}

def load_content():
    if not os.path.exists(CONTENT_PATH):
        save_content(DEFAULT_CONTENT)
        return DEFAULT_CONTENT
    with open(CONTENT_PATH, encoding='utf-8') as f:
        return json.load(f)

def save_content(data):
    with open(CONTENT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if not os.path.exists(CONTENT_PATH):
    save_content(DEFAULT_CONTENT)


# ── AUTH ──────────────────────────────────────────────────────────────────────

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


# ── STATIC FILES ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'index.html'))

@app.route('/admin')
@app.route('/admin/')
def admin_panel():
    return send_file(os.path.join(BASE_DIR, 'admin', 'index.html'))

@app.route('/brand_assets/<path:filename>')
def brand_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'brand_assets'), filename)

@app.route('/<path:filename>')
def static_files(filename):
    filepath = os.path.join(BASE_DIR, filename)
    if os.path.isfile(filepath):
        return send_from_directory(BASE_DIR, filename)
    return 'Not found', 404


# ── AUTH API ──────────────────────────────────────────────────────────────────

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    if data.get('password') == ADMIN_PASSWORD:
        session['admin'] = True
        return jsonify({'ok': True})
    return jsonify({'error': 'Incorrect password'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/auth/check')
def auth_check():
    return jsonify({'ok': bool(session.get('admin'))})


# ── CONTENT API ───────────────────────────────────────────────────────────────

@app.route('/api/content')
def get_content():
    return jsonify(load_content())

@app.route('/api/content', methods=['PUT'])
@requires_auth
def put_content():
    save_content(request.get_json())
    return jsonify({'ok': True})

@app.route('/api/content/<section>', methods=['PATCH'])
@requires_auth
def patch_section(section):
    content = load_content()
    updates = request.get_json()
    if section not in content:
        content[section] = {}
    content[section].update(updates)
    save_content(content)
    return jsonify({'ok': True})


@app.route('/api/testimonials', methods=['GET'])
def get_testimonials():
    c = load_content()
    return jsonify(c.get('testimonials', []))

@app.route('/api/testimonials', methods=['PUT'])
@requires_auth
def put_testimonials():
    items = request.get_json()
    content = load_content()
    content['testimonials'] = items
    save_content(content)
    return jsonify({'ok': True})

@app.route('/api/testimonials/<int:idx>', methods=['DELETE'])
@requires_auth
def delete_testimonial(idx):
    content = load_content()
    items = content.get('testimonials', [])
    if idx >= len(items):
        return jsonify({'error': 'Not found'}), 404
    items.pop(idx)
    save_content(content)
    return jsonify({'ok': True})


@app.route('/api/bestsellers', methods=['GET'])
def get_bestsellers():
    c = load_content()
    return jsonify(c.get('bestsellers', []))

@app.route('/api/bestsellers', methods=['PUT'])
@requires_auth
def put_bestsellers():
    items = request.get_json()
    content = load_content()
    content['bestsellers'] = items
    save_content(content)
    return jsonify({'ok': True})

@app.route('/api/bestsellers/<int:idx>', methods=['DELETE'])
@requires_auth
def delete_bestseller(idx):
    content = load_content()
    items = content.get('bestsellers', [])
    if idx >= len(items):
        return jsonify({'error': 'Not found'}), 404
    items.pop(idx)
    save_content(content)
    return jsonify({'ok': True})


# ── WORKSHOPS ──
@app.route('/api/workshops', methods=['GET'])
def get_workshops():
    c = load_content()
    return jsonify(c.get('workshops', []))

@app.route('/api/workshops', methods=['PUT'])
@requires_auth
def put_workshops():
    data = request.get_json(silent=True) or []
    c = load_content()
    c['workshops'] = data
    save_content(c)
    return jsonify({'ok': True})

@app.route('/api/workshops/<int:idx>', methods=['DELETE'])
@requires_auth
def delete_workshop(idx):
    c = load_content()
    items = c.get('workshops', [])
    if 0 <= idx < len(items):
        items.pop(idx)
    c['workshops'] = items
    save_content(c)
    return jsonify({'ok': True})

# ── REGISTRATIONS ──
def init_registrations_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS workshop_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workshop_name TEXT,
        name TEXT,
        phone TEXT,
        email TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )''')
    conn.commit()
    conn.close()

init_registrations_db()

@app.route('/api/registrations', methods=['GET'])
@requires_auth
def get_registrations():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM workshop_registrations ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/registrations', methods=['POST'])
def post_registration():
    d = request.get_json(silent=True) or {}
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO workshop_registrations (workshop_name, name, phone, email, notes) VALUES (?,?,?,?,?)',
        (d.get('workshop_name',''), d.get('name',''), d.get('phone',''), d.get('email',''), d.get('notes','')))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/registrations/<int:reg_id>', methods=['DELETE'])
@requires_auth
def delete_registration(reg_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM workshop_registrations WHERE id=?', (reg_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    c = load_content()
    g = c.get('gallery', {})
    if isinstance(g, dict) and 'images' in g:
        return jsonify(g['images'])
    return jsonify([])

@app.route('/api/gallery', methods=['PUT'])
@requires_auth
def put_gallery():
    imgs = request.get_json()
    content = load_content()
    content['gallery'] = {'images': imgs}
    save_content(content)
    return jsonify({'ok': True})


# ── MENU API ──────────────────────────────────────────────────────────────────

@app.route('/api/menu/categories', methods=['GET'])
def get_menu_categories():
    content = load_content()
    menu = content.get('menu', {})
    cats = [k for k in menu if k != 'note' and isinstance(menu[k], list)]
    return jsonify(cats)

@app.route('/api/menu/categories', methods=['POST'])
@requires_auth
def add_menu_category():
    data = request.get_json()
    name = (data.get('name') or '').strip().lower().replace(' ', '_')
    if not name or not name.replace('_','').isalnum():
        return jsonify({'error': 'Invalid category name'}), 400
    content = load_content()
    if 'menu' not in content:
        content['menu'] = {}
    if name in content['menu']:
        return jsonify({'error': 'Category already exists'}), 409
    content['menu'][name] = []
    save_content(content)
    return jsonify({'ok': True, 'name': name})

@app.route('/api/menu/categories/<name>', methods=['DELETE'])
@requires_auth
def delete_menu_category(name):
    content = load_content()
    menu = content.get('menu', {})
    if name not in menu or name == 'note':
        return jsonify({'error': 'Not found'}), 404
    if menu[name]:
        return jsonify({'error': 'Category is not empty. Delete all items first.'}), 400
    del menu[name]
    save_content(content)
    return jsonify({'ok': True})

@app.route('/api/menu/<category>', methods=['POST'])
@requires_auth
def add_item(category):
    content = load_content()
    if category not in content['menu']:
        return jsonify({'error': 'Unknown category'}), 400
    item = request.get_json()
    content['menu'][category].append(item)
    save_content(content)
    return jsonify({'ok': True, 'index': len(content['menu'][category]) - 1})

@app.route('/api/menu/<category>/<int:idx>', methods=['PUT'])
@requires_auth
def update_item(category, idx):
    content = load_content()
    items = content['menu'].get(category, [])
    if idx >= len(items):
        return jsonify({'error': 'Not found'}), 404
    items[idx] = request.get_json()
    save_content(content)
    return jsonify({'ok': True})

@app.route('/api/menu/<category>/<int:idx>', methods=['DELETE'])
@requires_auth
def delete_item(category, idx):
    content = load_content()
    items = content['menu'].get(category, [])
    if idx >= len(items):
        return jsonify({'error': 'Not found'}), 404
    items.pop(idx)
    save_content(content)
    return jsonify({'ok': True})

@app.route('/api/menu/<category>/reorder', methods=['POST'])
@requires_auth
def reorder_items(category):
    content = load_content()
    content['menu'][category] = request.get_json()
    save_content(content)
    return jsonify({'ok': True})


# ── IMAGE API ─────────────────────────────────────────────────────────────────

ALLOWED = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

@app.route('/api/upload', methods=['POST'])
@requires_auth
def upload():
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({'error': 'No file'}), 400
    ext = f.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED:
        return jsonify({'error': 'File type not allowed'}), 400
    filename = uuid.uuid4().hex + '.' + ext
    f.save(os.path.join(UPLOADS_DIR, filename))
    return jsonify({'ok': True, 'url': '/brand_assets/uploads/' + filename})

@app.route('/api/images')
@requires_auth
def list_images():
    imgs = []
    for folder, prefix in [('Images', '/brand_assets/Images/'), ('uploads', '/brand_assets/uploads/')]:
        d = os.path.join(BASE_DIR, 'brand_assets', folder)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.lower().split('.')[-1] in ALLOWED:
                    imgs.append(prefix + fn)
    return jsonify(imgs)


# ── ORDERS API ────────────────────────────────────────────────────────────────

@app.route('/api/orders', methods=['POST'])
def submit_order():
    d = request.get_json(silent=True) or {}
    with get_db() as db:
        db.execute(
            'INSERT INTO orders (name,phone,occasion,date_needed,details) VALUES (?,?,?,?,?)',
            (d.get('name',''), d.get('phone',''), d.get('occasion',''), d.get('date_needed',''), d.get('details',''))
        )
    _track('order', {'name': d.get('name','')})
    return jsonify({'ok': True})

@app.route('/api/orders')
@requires_auth
def get_orders():
    status = request.args.get('status')
    with get_db() as db:
        if status:
            rows = db.execute('SELECT * FROM orders WHERE status=? ORDER BY created_at DESC', (status,)).fetchall()
        else:
            rows = db.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/orders/<int:oid>', methods=['PATCH'])
@requires_auth
def patch_order(oid):
    d = request.get_json()
    fields = []
    vals = []
    for key in ('status', 'notes'):
        if key in d:
            fields.append(f'{key}=?')
            vals.append(d[key])
    if not fields:
        return jsonify({'error': 'Nothing to update'}), 400
    vals.append(oid)
    with get_db() as db:
        db.execute(f'UPDATE orders SET {", ".join(fields)} WHERE id=?', vals)
    return jsonify({'ok': True})

@app.route('/api/orders/<int:oid>', methods=['DELETE'])
@requires_auth
def delete_order(oid):
    with get_db() as db:
        db.execute('DELETE FROM orders WHERE id=?', (oid,))
    return jsonify({'ok': True})


# ── ANALYTICS API ─────────────────────────────────────────────────────────────

def _track(event_type, data=None):
    try:
        with get_db() as db:
            db.execute(
                'INSERT INTO analytics (event_type,event_data,user_agent,referrer) VALUES (?,?,?,?)',
                (event_type, json.dumps(data or {}),
                 request.headers.get('User-Agent',''), request.referrer or '')
            )
    except Exception:
        pass

@app.route('/api/analytics/event', methods=['POST'])
def track_event():
    d = request.get_json(silent=True) or {}
    _track(d.get('type', 'event'), d.get('data'))
    return jsonify({'ok': True})

@app.route('/api/analytics')
@requires_auth
def get_analytics():
    with get_db() as db:
        by_type = db.execute(
            'SELECT event_type, COUNT(*) as count FROM analytics GROUP BY event_type ORDER BY count DESC'
        ).fetchall()
        daily = db.execute(
            "SELECT substr(created_at,1,10) as day, COUNT(*) as count "
            "FROM analytics WHERE event_type='pageview' "
            "GROUP BY day ORDER BY day DESC LIMIT 30"
        ).fetchall()
        pv = db.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN substr(created_at,1,10)=date('now','localtime') THEN 1 ELSE 0 END) as today "
            "FROM analytics WHERE event_type='pageview'"
        ).fetchone()
        oc = db.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN status='new' THEN 1 ELSE 0 END) as new_c "
            "FROM orders"
        ).fetchone()
        clicks = db.execute(
            "SELECT event_data, COUNT(*) as c FROM analytics "
            "WHERE event_type='click' GROUP BY event_data ORDER BY c DESC LIMIT 20"
        ).fetchall()
    return jsonify({
        'by_type':        [dict(r) for r in by_type],
        'daily_pageviews':[dict(r) for r in daily],
        'total_pageviews': pv['total'] if pv else 0,
        'today_pageviews': pv['today'] if pv else 0,
        'total_orders':    oc['total'] if oc else 0,
        'new_orders':      oc['new_c'] if oc else 0,
        'top_clicks':     [dict(r) for r in clicks],
    })


# ── RUN ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('\n  The Dough Knot - Admin Server')
    print('  Main site : http://localhost:3000')
    print('  Admin     : http://localhost:3000/admin')
    print(f'  Password  : {ADMIN_PASSWORD}\n')
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
