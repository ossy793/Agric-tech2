from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
import sqlite3
import os
import uuid
import traceback
from typing import Optional

app = FastAPI(title="FarmRent Nigeria API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "frontend", "static", "images", "equipment")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "frontend", "static")), name="static")

DB_PATH = os.path.join(BASE_DIR, "farmrent.db")
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")


# ── Global error handler so crashes return JSON, never HTML ──────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"UNHANDLED ERROR on {request.url}:\n{tb}")
    return JSONResponse(status_code=500, content={"detail": str(exc), "traceback": tb})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables if not exist, add missing columns, seed demo data."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = OFF")
    c = conn.cursor()

    # Create tables
    c.executescript("""
        CREATE TABLE IF NOT EXISTS farmers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            farm_location TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            nin TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS rental_companies (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            business_location TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            tax_number TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS equipment (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price_per_day REAL NOT NULL,
            quantity_available INTEGER NOT NULL DEFAULT 1,
            delivery_available INTEGER DEFAULT 0,
            image_url TEXT,
            category TEXT DEFAULT 'general',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS rentals (
            id TEXT PRIMARY KEY,
            farmer_id TEXT NOT NULL,
            equipment_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            total_days INTEGER NOT NULL DEFAULT 1,
            total_price REAL NOT NULL DEFAULT 0,
            delivery_option TEXT DEFAULT 'pickup',
            delivery_address TEXT DEFAULT '',
            status TEXT DEFAULT 'confirmed',
            payment_status TEXT DEFAULT 'paid',
            payment_ref TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    # Add any missing columns (safe migrations)
    safe_add_column(c, "equipment", "image_url", "TEXT")
    safe_add_column(c, "equipment", "category", "TEXT DEFAULT 'general'")
    safe_add_column(c, "equipment", "delivery_available", "INTEGER DEFAULT 0")
    safe_add_column(c, "rentals", "delivery_address", "TEXT DEFAULT ''")
    safe_add_column(c, "rentals", "delivery_option", "TEXT DEFAULT 'pickup'")
    safe_add_column(c, "rentals", "payment_ref", "TEXT")
    safe_add_column(c, "rentals", "payment_status", "TEXT DEFAULT 'paid'")

    conn.commit()

    # Seed demo companies + equipment
    count = c.execute("SELECT COUNT(*) FROM rental_companies").fetchone()[0]
    if count == 0:
        cid1, cid2 = str(uuid.uuid4()), str(uuid.uuid4())
        c.executemany(
            "INSERT INTO rental_companies (id,business_name,business_location,email,phone,tax_number,password) VALUES (?,?,?,?,?,?,?)",
            [
                (cid1,"AgroMech Nigeria Ltd","Lagos, Nigeria","agromech@demo.com","08012345678","TAX001234","demo123"),
                (cid2,"FarmPower Solutions","Abuja, Nigeria","farmpower@demo.com","08098765432","TAX005678","demo123"),
            ]
        )
        seed_equipment = [
            (cid1,"Tractor (75HP)","Heavy-duty tractor for plowing, harrowing and cultivation. Diesel-powered with GPS.",15000,3,1,"tractors"),
            (cid1,"Combine Harvester","Multi-crop harvester for rice, maize and wheat. Reduces harvest time by 80%.",25000,1,1,"harvesters"),
            (cid1,"Irrigation Pump Set","High-capacity pump with 200m hose for dry-season irrigation.",3500,5,0,"irrigation"),
            (cid2,"Rice Transplanter","6-row self-propelled transplanter. Cuts labour cost by 70%.",8000,2,1,"planters"),
            (cid2,"Power Tiller","Walking tractor for small plots with plowing, ridging and weeding attachments.",4500,4,0,"tractors"),
            (cid2,"Maize Sheller","Electric sheller processing 2 tons/hour. Reduces post-harvest losses.",2500,6,1,"processing"),
            (cid1,"Boom Sprayer","30L boom sprayer for herbicides and pesticides covering 2ha/hour.",2000,8,0,"sprayers"),
            (cid2,"Cassava Harvester","Tractor-mounted harvester. Complete a harvest in hours not days.",6000,2,1,"harvesters"),
        ]
        c.executemany(
            "INSERT INTO equipment (id,company_id,name,description,price_per_day,quantity_available,delivery_available,category) VALUES (?,?,?,?,?,?,?,?)",
            [(str(uuid.uuid4()), *row) for row in seed_equipment]
        )
        conn.commit()

    conn.close()
    print("✅ DB initialised OK")


def safe_add_column(cursor, table, column, col_def):
    """Add a column to a table if it doesn't already exist."""
    try:
        existing = [row[1] for row in cursor.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
            print(f"  ➕ Added column {table}.{column}")
    except Exception as e:
        print(f"  ⚠️  safe_add_column({table}.{column}): {e}")


init_db()


# ── AUTH ─────────────────────────────────────────────────────────────────────

@app.post("/api/auth/farmer/signup")
def farmer_signup(data: dict, db: sqlite3.Connection = Depends(get_db)):
    fid = str(uuid.uuid4())
    try:
        db.execute(
            "INSERT INTO farmers (id,name,address,farm_location,email,phone,nin,password) VALUES (:id,:name,:address,:farm_location,:email,:phone,:nin,:password)",
            {**data, "id": fid}
        )
        db.commit()
        return {"success": True, "id": fid, "name": data["name"], "role": "farmer"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(400, f"Email or NIN already registered: {e}")


@app.post("/api/auth/farmer/login")
def farmer_login(data: dict, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM farmers WHERE email=? AND password=?",
        (data["email"], data["password"])
    ).fetchone()
    if not row:
        raise HTTPException(401, "Invalid credentials")
    return {"success": True, "id": row["id"], "name": row["name"], "role": "farmer"}


@app.post("/api/auth/company/signup")
def company_signup(data: dict, db: sqlite3.Connection = Depends(get_db)):
    cid = str(uuid.uuid4())
    try:
        db.execute(
            "INSERT INTO rental_companies (id,business_name,business_location,email,phone,tax_number,password) VALUES (:id,:business_name,:business_location,:email,:phone,:tax_number,:password)",
            {**data, "id": cid}
        )
        db.commit()
        return {"success": True, "id": cid, "name": data["business_name"], "role": "company"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(400, f"Email or Tax Number already registered: {e}")


@app.post("/api/auth/company/login")
def company_login(data: dict, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM rental_companies WHERE email=? AND password=?",
        (data["email"], data["password"])
    ).fetchone()
    if not row:
        raise HTTPException(401, "Invalid credentials")
    return {"success": True, "id": row["id"], "name": row["business_name"], "role": "company"}


# ── EQUIPMENT ────────────────────────────────────────────────────────────────

@app.get("/api/equipment")
def list_equipment(category: Optional[str] = None, db: sqlite3.Connection = Depends(get_db)):
    try:
        q = """
            SELECT e.id, e.name, e.description, e.price_per_day, e.quantity_available,
                   e.delivery_available, e.image_url, e.category, e.company_id, e.created_at,
                   rc.business_name, rc.business_location, rc.phone AS company_phone
            FROM equipment e
            JOIN rental_companies rc ON e.company_id = rc.id
            WHERE e.quantity_available > 0
        """
        params: list = []
        if category:
            q += " AND e.category = ?"
            params.append(category)
        q += " ORDER BY COALESCE(e.created_at, '') DESC"
        return [dict(r) for r in db.execute(q, params).fetchall()]
    except Exception as e:
        raise HTTPException(500, f"list_equipment error: {e}")


@app.post("/api/equipment")
async def add_equipment(
    company_id: str = Form(...),
    name: str = Form(...),
    description: str = Form(...),
    price_per_day: float = Form(...),
    quantity_available: int = Form(...),
    delivery_available: int = Form(0),
    category: str = Form("general"),
    image: Optional[UploadFile] = File(None),
    db: sqlite3.Connection = Depends(get_db)
):
    eid = str(uuid.uuid4())
    image_url = None

    # Handle optional image upload
    try:
        if image and getattr(image, "filename", None) and image.filename.strip():
            ext = os.path.splitext(image.filename)[1].lower()
            if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp"):
                ext = ".jpg"
            fname = f"{eid}{ext}"
            contents = await image.read()
            if contents:
                fpath = os.path.join(UPLOAD_DIR, fname)
                with open(fpath, "wb") as f:
                    f.write(contents)
                image_url = f"/static/images/equipment/{fname}"
    except Exception as img_err:
        print(f"Image upload skipped: {img_err}")

    try:
        db.execute(
            "INSERT INTO equipment (id,company_id,name,description,price_per_day,quantity_available,delivery_available,image_url,category) VALUES (?,?,?,?,?,?,?,?,?)",
            (eid, company_id, name, description, price_per_day, quantity_available, delivery_available, image_url, category)
        )
        db.commit()
    except Exception as e:
        raise HTTPException(500, f"DB insert error: {e}")

    return {"success": True, "id": eid}


@app.delete("/api/equipment/{equipment_id}")
def delete_equipment(equipment_id: str, db: sqlite3.Connection = Depends(get_db)):
    db.execute("DELETE FROM equipment WHERE id=?", (equipment_id,))
    db.commit()
    return {"success": True}


@app.get("/api/company/{company_id}/equipment")
def company_equipment(company_id: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute(
            "SELECT * FROM equipment WHERE company_id=? ORDER BY created_at DESC",
            (company_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(500, f"company_equipment error: {e}")


# ── RENTALS ──────────────────────────────────────────────────────────────────

@app.post("/api/rentals")
def create_rental(data: dict, db: sqlite3.Connection = Depends(get_db)):
    rid = str(uuid.uuid4())
    ref = f"PAY-{uuid.uuid4().hex[:10].upper()}"

    eq = db.execute("SELECT * FROM equipment WHERE id=?", (data["equipment_id"],)).fetchone()
    if not eq:
        raise HTTPException(404, "Equipment not found")
    if eq["quantity_available"] < data.get("quantity", 1):
        raise HTTPException(400, "Insufficient quantity available")

    try:
        db.execute(
            """INSERT INTO rentals
               (id,farmer_id,equipment_id,company_id,quantity,start_date,end_date,
                total_days,total_price,delivery_option,delivery_address,
                status,payment_status,payment_ref)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                rid, data["farmer_id"], data["equipment_id"], eq["company_id"],
                data.get("quantity", 1), data["start_date"], data["end_date"],
                data.get("total_days", 1), data.get("total_price", 0),
                data.get("delivery_option", "pickup"),
                data.get("delivery_address", ""),
                "confirmed", "paid", ref
            )
        )
        db.execute(
            "UPDATE equipment SET quantity_available = quantity_available - ? WHERE id=?",
            (data.get("quantity", 1), data["equipment_id"])
        )
        db.commit()
    except Exception as e:
        raise HTTPException(500, f"Rental creation error: {e}")

    return {"success": True, "rental_id": rid, "payment_ref": ref, "status": "confirmed"}


@app.get("/api/farmer/{farmer_id}/rentals")
def farmer_rentals(farmer_id: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute(
            """SELECT r.id, r.farmer_id, r.equipment_id, r.company_id,
                      r.quantity, r.start_date, r.end_date, r.total_days, r.total_price,
                      r.delivery_option, r.delivery_address, r.status, r.payment_status,
                      r.payment_ref, r.created_at,
                      e.name AS equipment_name, e.image_url, e.price_per_day,
                      rc.business_name, rc.phone AS company_phone
               FROM rentals r
               JOIN equipment e ON r.equipment_id = e.id
               JOIN rental_companies rc ON r.company_id = rc.id
               WHERE r.farmer_id = ?
               ORDER BY r.created_at DESC""",
            (farmer_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(500, f"farmer_rentals error: {e}")


@app.get("/api/company/{company_id}/rentals")
def company_rentals(company_id: str, db: sqlite3.Connection = Depends(get_db)):
    try:
        rows = db.execute(
            """SELECT r.id, r.farmer_id, r.equipment_id, r.company_id,
                      r.quantity, r.start_date, r.end_date, r.total_days, r.total_price,
                      r.delivery_option, r.delivery_address, r.status, r.payment_status,
                      r.payment_ref, r.created_at,
                      e.name AS equipment_name, e.image_url,
                      f.name AS farmer_name, f.phone AS farmer_phone, f.farm_location
               FROM rentals r
               JOIN equipment e ON r.equipment_id = e.id
               JOIN farmers f ON r.farmer_id = f.id
               WHERE r.company_id = ?
               ORDER BY r.created_at DESC""",
            (company_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(500, f"company_rentals error: {e}")


@app.put("/api/rentals/{rental_id}/status")
def update_rental_status(rental_id: str, data: dict, db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE rentals SET status=? WHERE id=?", (data["status"], rental_id))
    db.commit()
    return {"success": True}


# ── DEBUG endpoint (remove in production) ────────────────────────────────────
@app.get("/api/debug/tables")
def debug_tables(db: sqlite3.Connection = Depends(get_db)):
    out = {}
    for table in ["farmers", "rental_companies", "equipment", "rentals"]:
        try:
            cols = [r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()]
            count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            out[table] = {"columns": cols, "rows": count}
        except Exception as e:
            out[table] = {"error": str(e)}
    return out


# ── FRONTEND PAGES ────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return FileResponse(os.path.join(TEMPLATE_DIR, "index.html"))

@app.get("/auth")
def auth_page():
    return FileResponse(os.path.join(TEMPLATE_DIR, "auth.html"))

@app.get("/marketplace")
def marketplace_page():
    return FileResponse(os.path.join(TEMPLATE_DIR, "marketplace.html"))

@app.get("/farmer-dashboard")
def farmer_dashboard():
    return FileResponse(os.path.join(TEMPLATE_DIR, "farmer-dashboard.html"))

@app.get("/company-dashboard")
def company_dashboard():
    return FileResponse(os.path.join(TEMPLATE_DIR, "company-dashboard.html"))

@app.get("/{path:path}")
def catch_all(path: str):
    if path.startswith("api/"):
        raise HTTPException(404, f"API route not found: /{path}")
    f = os.path.join(TEMPLATE_DIR, f"{path}.html")
    if os.path.exists(f):
        return FileResponse(f)
    return FileResponse(os.path.join(TEMPLATE_DIR, "index.html"))