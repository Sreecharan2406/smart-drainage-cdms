from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
import sqlite3, datetime, bcrypt

app = Flask(__name__)
app.secret_key = "cdms_secret_key_2025"
CORS(app, supports_credentials=True)
DB = "cdms.db"

def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with get_db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS drains (
            id TEXT PRIMARY KEY, zone TEXT, type TEXT,
            diameter INTEGER, inspected TEXT, status TEXT DEFAULT 'Active'
        );
        CREATE TABLE IF NOT EXISTS reports (
            id TEXT PRIMARY KEY, zone TEXT, drain_id TEXT,
            type TEXT, severity TEXT, status TEXT DEFAULT 'Pending',
            description TEXT, reporter TEXT, admin_note TEXT DEFAULT '',
            created_at TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS maintenance (
            id TEXT PRIMARY KEY, drain_id TEXT, zone TEXT,
            work_type TEXT, crew TEXT, scheduled_date TEXT,
            duration TEXT DEFAULT '—', status TEXT DEFAULT 'Scheduled'
        );
        CREATE TABLE IF NOT EXISTS predictions (
            drain_id TEXT PRIMARY KEY, risk_score INTEGER,
            risk_level TEXT, reason TEXT, predicted_at TEXT
        );
        CREATE TABLE IF NOT EXISTS java_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, zone TEXT,
            drain_id TEXT, message TEXT, level TEXT, triggered_at TEXT
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT DEFAULT 'public', created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT,
            action TEXT, target TEXT, detail TEXT, logged_at TEXT
        );
        """)
        # Seed admin
        if con.execute("SELECT COUNT(*) FROM users WHERE username='admin'").fetchone()[0] == 0:
            pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            con.execute("INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
                        ["admin", pw, "admin", now])
            con.commit()
        # Seed drain data
        if con.execute("SELECT COUNT(*) FROM drains").fetchone()[0] == 0:
            drains = [
                ("DR-001","Adyar","Storm Drain",900,"2025-03-12","Active"),
                ("DR-002","Velachery","Combined Sewer",600,"2025-01-08","Blocked"),
                ("DR-003","T. Nagar","Surface Channel",450,"2025-04-22","Active"),
                ("DR-004","Anna Nagar","Box Culvert",1200,"2025-02-15","Maintenance"),
                ("DR-005","Adyar","Storm Drain",750,"2025-05-01","Active"),
                ("DR-006","Tambaram","Combined Sewer",500,"2024-12-10","Blocked"),
                ("DR-007","Perambur","Storm Drain",600,"2025-03-30","Active"),
                ("DR-008","Mylapore","Surface Channel",300,"2025-04-05","Active"),
                ("DR-009","Kodambakkam","Storm Drain",800,"2025-05-10","Blocked"),
                ("DR-010","Velachery","Box Culvert",1100,"2025-01-20","Active"),
                ("DR-011","T. Nagar","Storm Drain",650,"2024-11-15","Inactive"),
                ("DR-012","Anna Nagar","Combined Sewer",700,"2025-04-18","Active"),
                ("DR-013","Adyar","Surface Channel",400,"2025-05-20","Active"),
                ("DR-014","Mylapore","Storm Drain",950,"2025-02-28","Active"),
                ("DR-015","Tambaram","Box Culvert",1300,"2024-10-05","Blocked"),
            ]
            con.executemany("INSERT INTO drains VALUES(?,?,?,?,?,?)", drains)
            reports = [
                ("RPT-001","Velachery","DR-002","Blockage","Critical","In Progress","Complete blockage causing road flooding near bus stand","public","Crew dispatched","2026-06-01 07:14","2026-06-01 09:00"),
                ("RPT-002","Adyar","DR-001","Overflow","High","Pending","Overflow during last rain, water on streets near market","public","","2026-06-02 08:30","2026-06-02 08:30"),
                ("RPT-003","Tambaram","DR-006","Debris Accumulation","Medium","Pending","Plastic waste blocking drain entry point","public","","2026-06-03 15:22","2026-06-03 15:22"),
                ("RPT-004","Kodambakkam","DR-009","Blockage","High","Pending","Drain blocked near fish market, strong odour","public","","2026-06-04 12:00","2026-06-04 12:00"),
                ("RPT-005","Tambaram","DR-015","Flooding Risk","Critical","Pending","Water level rising, risk of road flooding","public","","2026-06-05 06:45","2026-06-05 06:45"),
            ]
            con.executemany("INSERT INTO reports VALUES(?,?,?,?,?,?,?,?,?,?,?)", reports)
            maintenance = [
                ("MNT-001","DR-004","Anna Nagar","Routine Cleaning","Crew Alpha","2026-06-03","4h","Completed"),
                ("MNT-002","DR-002","Velachery","Emergency Repair","Crew Bravo","2026-06-05","—","In Progress"),
                ("MNT-003","DR-006","Tambaram","De-silting","Crew Delta","2026-06-06","—","Scheduled"),
                ("MNT-004","DR-001","Adyar","Inspection","Crew Echo","2026-06-07","—","Scheduled"),
                ("MNT-005","DR-015","Tambaram","Emergency Repair","Crew Alpha","2026-06-08","—","Scheduled"),
            ]
            con.executemany("INSERT INTO maintenance VALUES(?,?,?,?,?,?,?,?)", maintenance)
            con.commit()

def log_action(user, action, target="", detail=""):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_db() as con:
        con.execute("INSERT INTO activity_log(user,action,target,detail,logged_at) VALUES(?,?,?,?,?)",
                    [user, action, target, detail, now])
        con.commit()

def current_user(): return session.get("username")
def is_admin(): return session.get("role") == "admin"

def require_login():
    if not current_user(): return jsonify({"error":"Not logged in"}), 401
def require_admin():
    if not is_admin(): return jsonify({"error":"Admin only"}), 403

# ── AUTH ──
@app.route('/auth/login', methods=['POST'])
def login():
    d = request.json
    con = get_db()
    user = con.execute("SELECT * FROM users WHERE username=?", [d['username'].strip()]).fetchone()
    if not user or not bcrypt.checkpw(d['password'].encode(), user['password_hash'].encode()):
        return jsonify({"error":"Invalid username or password"}), 401
    session['username'] = user['username']
    session['role'] = user['role']
    log_action(user['username'], "LOGIN")
    return jsonify({"username": user['username'], "role": user['role']})

@app.route('/auth/logout', methods=['POST'])
def logout():
    if current_user(): log_action(current_user(), "LOGOUT")
    session.clear()
    return jsonify({"ok": True})

@app.route('/auth/register', methods=['POST'])
def register():
    d = request.json
    u = d.get('username','').strip()
    p = d.get('password','')
    if len(u) < 3: return jsonify({"error":"Username must be at least 3 characters"}), 400
    if len(p) < 6: return jsonify({"error":"Password must be at least 6 characters"}), 400
    pw_hash = bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    try:
        with get_db() as con:
            con.execute("INSERT INTO users(username,password_hash,role,created_at) VALUES(?,?,?,?)",
                        [u, pw_hash, "public", now])
            con.commit()
        session['username'] = u; session['role'] = "public"
        log_action(u, "REGISTER")
        return jsonify({"username": u, "role": "public"})
    except: return jsonify({"error":"Username already taken"}), 409

@app.route('/auth/me')
def me():
    if current_user(): return jsonify({"username": current_user(), "role": session.get('role')})
    return jsonify({"username": None, "role": None})

# ── DRAINS ──
@app.route('/drains', methods=['GET','POST'])
def drains():
    err = require_login()
    if err: return err
    con = get_db()
    if request.method == 'POST':
        ae = require_admin()
        if ae: return ae
        d = request.json
        try:
            con.execute("INSERT INTO drains VALUES(?,?,?,?,?,?)",
                [d['id'], d['zone'], d['type'], d['diameter'], datetime.date.today().isoformat(), 'Active'])
            con.commit()
            log_action(current_user(), "ADD_DRAIN", d['id'], f"{d['zone']} — {d['type']}")
            return jsonify({"ok": True})
        except: return jsonify({"error":"Drain ID already exists"}), 409
    return jsonify([dict(r) for r in con.execute("SELECT * FROM drains ORDER BY id")])

@app.route('/drains/<drain_id>', methods=['PATCH'])
def update_drain(drain_id):
    ae = require_admin()
    if ae: return ae
    d = request.json
    get_db().execute("UPDATE drains SET status=? WHERE id=?", [d['status'], drain_id])
    get_db().commit()
    with get_db() as con:
        con.execute("UPDATE drains SET status=? WHERE id=?", [d['status'], drain_id])
        con.commit()
    log_action(current_user(), "UPDATE_DRAIN", drain_id, f"Status → {d['status']}")
    return jsonify({"ok": True})

# ── REPORTS ──
@app.route('/reports', methods=['GET','POST'])
def reports():
    err = require_login()
    if err: return err
    con = get_db()
    if request.method == 'POST':
        d = request.json
        count = con.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        rid = f"RPT-{count+1:03d}"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        con.execute("INSERT INTO reports VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            [rid, d['zone'], d['drainId'], d['type'], d['severity'],
             'Pending', d['desc'], current_user(), '', now, now])
        con.commit()
        log_action(current_user(), "SUBMIT_REPORT", rid, f"{d['zone']} — {d['type']} ({d['severity']})")
        return jsonify({"id": rid})
    if is_admin():
        rows = con.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
    else:
        rows = con.execute("SELECT * FROM reports WHERE reporter=? ORDER BY created_at DESC", [current_user()]).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/reports/<report_id>', methods=['PATCH'])
def update_report(report_id):
    ae = require_admin()
    if ae: return ae
    d = request.json
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_db() as con:
        con.execute("UPDATE reports SET status=?, admin_note=?, updated_at=? WHERE id=?",
                    [d.get('status'), d.get('admin_note',''), now, report_id])
        con.commit()
    log_action(current_user(), "UPDATE_REPORT", report_id, f"Status → {d.get('status')}")
    return jsonify({"ok": True})

# ── MAINTENANCE ──
@app.route('/maintenance', methods=['GET','POST'])
def maintenance():
    err = require_login()
    if err: return err
    con = get_db()
    if request.method == 'POST':
        ae = require_admin()
        if ae: return ae
        d = request.json
        count = con.execute("SELECT COUNT(*) FROM maintenance").fetchone()[0]
        mid = f"MNT-{count+1:03d}"
        con.execute("INSERT INTO maintenance VALUES(?,?,?,?,?,?,?,?)",
            [mid, d['drain_id'], d['zone'], d['work_type'], d['crew'], d['scheduled_date'], '—', 'Scheduled'])
        con.commit()
        log_action(current_user(), "SCHEDULE_MAINT", mid, f"{d['drain_id']} — {d['work_type']}")
        return jsonify({"id": mid})
    return jsonify([dict(r) for r in con.execute("SELECT * FROM maintenance ORDER BY scheduled_date")])

# ── ANALYTICS ──
@app.route('/analytics')
def analytics():
    err = require_login()
    if err: return err
    con = get_db()
    def q(sql, *a): return con.execute(sql, *a).fetchall()
    status_rows = q("SELECT status, COUNT(*) as c FROM drains GROUP BY status")
    zone_rows   = q("SELECT zone, COUNT(*) as c FROM reports GROUP BY zone ORDER BY c DESC")
    sev_rows    = q("SELECT severity, COUNT(*) as c FROM reports GROUP BY severity")
    maint_rows  = q("SELECT work_type, COUNT(*) as c FROM maintenance GROUP BY work_type")
    type_rows   = q("SELECT type, COUNT(*) as c FROM drains GROUP BY type")
    time_rows   = q("SELECT substr(created_at,1,10) as day, COUNT(*) as c FROM reports GROUP BY day ORDER BY day DESC LIMIT 7")
    return jsonify({
        "status_breakdown": {r['status']:r['c'] for r in status_rows},
        "reports_by_zone":  {"labels":[r['zone'] for r in zone_rows],"values":[r['c'] for r in zone_rows]},
        "reports_by_severity": {r['severity']:r['c'] for r in sev_rows},
        "maintenance_by_type": {"labels":[r['work_type'] for r in maint_rows],"values":[r['c'] for r in maint_rows]},
        "drain_types": {"labels":[r['type'] for r in type_rows],"values":[r['c'] for r in type_rows]},
        "reports_over_time": {"labels":[r['day'] for r in reversed(time_rows)],"values":[r['c'] for r in reversed(time_rows)]},
        "totals": {
            "drains":      con.execute("SELECT COUNT(*) FROM drains").fetchone()[0],
            "reports":     con.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
            "maintenance": con.execute("SELECT COUNT(*) FROM maintenance").fetchone()[0],
            "users":       con.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        }
    })

# ── ACTIVITY LOG ──
@app.route('/activity_log')
def activity_log():
    ae = require_admin()
    if ae: return ae
    rows = get_db().execute("SELECT * FROM activity_log ORDER BY logged_at DESC LIMIT 100").fetchall()
    return jsonify([dict(r) for r in rows])

# ── USERS ──
@app.route('/users')
def users():
    ae = require_admin()
    if ae: return ae
    rows = get_db().execute("SELECT id,username,role,created_at FROM users ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows])

# ── PREDICTIONS & ALERTS ──
@app.route('/predictions')
def predictions():
    err = require_login()
    if err: return err
    rows = get_db().execute("SELECT * FROM predictions ORDER BY risk_score DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/java_alerts')
def java_alerts():
    err = require_login()
    if err: return err
    rows = get_db().execute("SELECT * FROM java_alerts ORDER BY triggered_at DESC LIMIT 30").fetchall()
    return jsonify([dict(r) for r in rows])

# ── RESET ──
@app.route('/reset', methods=['DELETE'])
def reset():
    ae = require_admin()
    if ae: return ae
    with get_db() as con:
        con.executescript("DELETE FROM drains;DELETE FROM reports;DELETE FROM maintenance;DELETE FROM predictions;DELETE FROM java_alerts;")
        con.commit()
    log_action(current_user(), "RESET_DB", "", "All operational data cleared")
    return jsonify({"ok": True})

@app.route('/')
def index(): return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)