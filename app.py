from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3
from pathlib import Path
from datetime import date

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "hostel.db"
app = Flask(__name__)
CORS(app)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY, name TEXT NOT NULL, department TEXT NOT NULL,
            year INTEGER NOT NULL, email TEXT UNIQUE, phone TEXT
        );
        CREATE TABLE IF NOT EXISTS hostels (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, gender TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT, room_no TEXT NOT NULL,
            hostel_id TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(capacity > 0),
            FOREIGN KEY(hostel_id) REFERENCES hostels(id)
        );
        CREATE TABLE IF NOT EXISTS allotments (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_roll TEXT UNIQUE,
            room_id INTEGER NOT NULL, payment_amount REAL NOT NULL DEFAULT 0,
            payment_date TEXT, FOREIGN KEY(student_roll) REFERENCES students(roll_no),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        );
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_roll TEXT,
            room_id INTEGER, category TEXT NOT NULL, description TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium', status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_roll) REFERENCES students(roll_no),
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        );
        """)
        count = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count == 0:
            con.executemany("INSERT INTO students VALUES(?,?,?,?,?,?)", [
                ("24CS001","Aarav Sharma","CSE",2,"aarav@example.com","9876500001"),
                ("24CH014","Meera Rao","Chemical",2,"meera@example.com","9876500002"),
                ("25EE022","Ishaan Das","Electrical",1,"ishaan@example.com","9876500003"),
                ("23ME031","Ananya Sen","Mechanical",3,"ananya@example.com","9876500004"),
                ("24CS044","Kabir Nair","CSE",2,"kabir@example.com","9876500005"),
            ])
            con.executemany("INSERT INTO hostels VALUES(?,?,?)", [
                ("H01","Maple Hall","Mixed"),("H02","Cedar House","Mixed")
            ])
            con.executemany("INSERT INTO rooms(room_no,hostel_id,capacity) VALUES(?,?,?)", [
                ("101","H01",2),("102","H01",2),("103","H01",3),
                ("201","H02",2),("202","H02",2),("203","H02",3)
            ])
            room_ids = [r[0] for r in con.execute("SELECT id FROM rooms ORDER BY id").fetchall()]
            con.executemany("INSERT INTO allotments(student_roll,room_id,payment_amount,payment_date) VALUES(?,?,?,?)", [
                ("24CS001",room_ids[0],42000,date.today().isoformat()),
                ("24CH014",room_ids[0],42000,date.today().isoformat()),
                ("25EE022",room_ids[3],40000,date.today().isoformat()),
                ("23ME031",room_ids[4],40000,date.today().isoformat()),
            ])
            con.executemany("INSERT INTO complaints(student_roll,room_id,category,description,priority,status) VALUES(?,?,?,?,?,?)", [
                ("24CS001",room_ids[0],"Electrical","Study light is flickering","Medium","Open"),
                ("24CH014",room_ids[0],"Plumbing","Washbasin tap is leaking","High","In progress"),
                ("25EE022",room_ids[3],"Cleaning","Common area needs cleaning","Low","Resolved"),
            ])

def fetch_all(sql, args=()):
    with db() as con:
        return [dict(row) for row in con.execute(sql, args).fetchall()]

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/api/dashboard")
def dashboard():
    with db() as con:
        students = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        rooms = con.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        capacity = con.execute("SELECT COALESCE(SUM(capacity),0) FROM rooms").fetchone()[0]
        occupied = con.execute("SELECT COUNT(*) FROM allotments").fetchone()[0]
        open_complaints = con.execute("SELECT COUNT(*) FROM complaints WHERE status != 'Resolved'").fetchone()[0]
        resolved = con.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'").fetchone()[0]
        by_category = [dict(r) for r in con.execute(
            "SELECT category, COUNT(*) AS total FROM complaints GROUP BY category ORDER BY total DESC").fetchall()]
        recent = [dict(r) for r in con.execute("""
            SELECT c.id,c.category,c.description,c.priority,c.status,c.created_at,
                   COALESCE(s.name,'Unassigned') AS student, COALESCE(r.room_no,'—') AS room_no
            FROM complaints c LEFT JOIN students s ON s.roll_no=c.student_roll
            LEFT JOIN rooms r ON r.id=c.room_id ORDER BY c.id DESC LIMIT 5""").fetchall()]
    occupancy = round((occupied / capacity) * 100) if capacity else 0
    return jsonify({"students":students,"rooms":rooms,"capacity":capacity,"occupied":occupied,
                    "vacant":max(capacity-occupied,0),"occupancy":occupancy,
                    "open_complaints":open_complaints,"resolved_complaints":resolved,
                    "by_category":by_category,"recent":recent})

@app.get("/api/students")
def students():
    return jsonify(fetch_all("""
        SELECT s.roll_no,s.name,s.department,s.year,s.email,s.phone,
        h.name AS hostel,r.room_no
        FROM students s LEFT JOIN allotments a ON a.student_roll=s.roll_no
        LEFT JOIN rooms r ON r.id=a.room_id LEFT JOIN hostels h ON h.id=r.hostel_id
        ORDER BY s.name"""))

@app.post("/api/students")
def create_student():
    data = request.get_json(silent=True) or {}
    required = ["roll_no", "name", "department", "year"]
    if any(not str(data.get(key, "")).strip() for key in required):
        return jsonify({"error": "Roll number, name, department, and academic year are required."}), 400
    try:
        year = int(data["year"])
    except (TypeError, ValueError):
        return jsonify({"error": "Academic year must be a number from 1 to 5."}), 400
    if year < 1 or year > 5:
        return jsonify({"error": "Academic year must be between 1 and 5."}), 400
    roll_no = str(data["roll_no"]).strip().upper()
    name = str(data["name"]).strip()
    department = str(data["department"]).strip()
    email = str(data.get("email") or "").strip() or None
    phone = str(data.get("phone") or "").strip() or None
    try:
        with db() as con:
            con.execute("INSERT INTO students(roll_no,name,department,year,email,phone) VALUES(?,?,?,?,?,?)",
                        (roll_no, name, department, year, email, phone))
            con.commit()
    except sqlite3.IntegrityError as exc:
        message = "That roll number is already registered."
        if "email" in str(exc).lower():
            message = "That email address is already registered."
        return jsonify({"error": message}), 409
    return jsonify({"message": "Resident registered successfully.", "roll_no": roll_no}), 201

@app.get("/api/rooms")
def rooms():
    return jsonify(fetch_all("""
        SELECT r.id,r.room_no,h.name AS hostel,r.capacity,
        COUNT(a.id) AS occupied, r.capacity-COUNT(a.id) AS vacant
        FROM rooms r JOIN hostels h ON h.id=r.hostel_id
        LEFT JOIN allotments a ON a.room_id=r.id
        GROUP BY r.id ORDER BY h.name,r.room_no"""))

@app.get("/api/rooms/available")
def available_rooms():
    return jsonify(fetch_all("""
        SELECT r.id, r.room_no, h.name AS hostel, r.capacity,
               COUNT(a.id) AS occupied, r.capacity-COUNT(a.id) AS vacant
        FROM rooms r JOIN hostels h ON h.id=r.hostel_id
        LEFT JOIN allotments a ON a.room_id=r.id
        GROUP BY r.id HAVING COUNT(a.id) < r.capacity
        ORDER BY h.name, r.room_no
    """))

@app.post("/api/allotments")
def create_allotment():
    data = request.get_json(silent=True) or {}
    student_roll = str(data.get("student_roll") or "").strip().upper()
    try:
        room_id = int(data.get("room_id"))
    except (TypeError, ValueError):
        room_id = 0
    if not student_roll or not room_id:
        return jsonify({"error": "Choose both a resident and a room."}), 400
    with db() as con:
        student = con.execute("SELECT roll_no FROM students WHERE roll_no=?", (student_roll,)).fetchone()
        if not student:
            return jsonify({"error": "Resident was not found. Refresh and try again."}), 404
        existing = con.execute("SELECT id FROM allotments WHERE student_roll=?", (student_roll,)).fetchone()
        if existing:
            return jsonify({"error": "This resident already has a room allocated."}), 409
        room = con.execute("""
            SELECT r.id, r.capacity, r.room_no, h.name AS hostel, COUNT(a.id) AS occupied
            FROM rooms r JOIN hostels h ON h.id=r.hostel_id
            LEFT JOIN allotments a ON a.room_id=r.id WHERE r.id=? GROUP BY r.id
        """, (room_id,)).fetchone()
        if not room:
            return jsonify({"error": "Room was not found. Refresh and try again."}), 404
        if room["occupied"] >= room["capacity"]:
            return jsonify({"error": "That room is full. Choose another available room."}), 409
        try:
            con.execute("INSERT INTO allotments(student_roll,room_id,payment_amount,payment_date) VALUES(?,?,0,?)",
                        (student_roll, room_id, date.today().isoformat()))
            con.commit()
        except sqlite3.IntegrityError:
            return jsonify({"error": "This resident already has a room allocated."}), 409
    return jsonify({"message": f"Room {room['room_no']} at {room['hostel']} allocated successfully."}), 201

@app.get("/api/complaints")
def complaints():
    return jsonify(fetch_all("""
        SELECT c.id,c.category,c.description,c.priority,c.status,c.created_at,
        c.student_roll,COALESCE(s.name,'Unknown') AS student,COALESCE(r.room_no,'—') AS room_no
        FROM complaints c LEFT JOIN students s ON s.roll_no=c.student_roll
        LEFT JOIN rooms r ON r.id=c.room_id ORDER BY c.id DESC"""))

@app.post("/api/complaints")
def create_complaint():
    data = request.get_json(silent=True) or {}
    required = ["category","description"]
    if any(not str(data.get(k,"")).strip() for k in required):
        return jsonify({"error":"Category and description are required."}), 400
    with db() as con:
        con.execute("""INSERT INTO complaints(student_roll,room_id,category,description,priority,status)
        VALUES(?,?,?,?,?,'Open')""", (
            data.get("student_roll") or None, data.get("room_id") or None,
            data["category"].strip(), data["description"].strip(),
            data.get("priority","Medium")
        ))
        con.commit()
    return jsonify({"message":"Complaint created successfully."}), 201

@app.patch("/api/complaints/<int:complaint_id>")
def update_complaint(complaint_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in ["Open","In progress","Resolved"]:
        return jsonify({"error":"Invalid complaint status."}), 400
    with db() as con:
        cur = con.execute("UPDATE complaints SET status=? WHERE id=?", (status, complaint_id))
        con.commit()
        if cur.rowcount == 0:
            return jsonify({"error":"Complaint not found."}), 404
    return jsonify({"message":"Complaint status updated."})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
