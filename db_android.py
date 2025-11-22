import sqlite3
import os
from pathlib import Path
import platform

# تحديد مسار قاعدة البيانات بناءً على النظام
def get_db_path():
    system = platform.system().lower()
    
    if system == "linux" and hasattr(os, 'getuid'):  # Android
        # على Android، استخدم المسار المخصص للتطبيقات
        app_dir = "/data/data/com.example.citymover/files"
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "city_app.db")
    elif system == "linux":  # Linux
        return os.path.join(os.path.expanduser("~"), ".city_app.db")
    else:  # Windows وغيرها
        return "city_app.db"

DB_FILE = get_db_path()

def get_connection():
    # التأكد من وجود المجلدات
    db_dir = os.path.dirname(DB_FILE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # لجعل النتائج كـ dictionaries
    return conn

def init_db():
    """إنشاء الجداول الأساسية إذا لم تكن موجودة."""
    print(f"جاري تهيئة قاعدة البيانات في: {DB_FILE}")
    
    with get_connection() as conn:
        cur = conn.cursor()

        # جدول المستخدمين
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'owner', 'admin')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # جدول المدن
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # جدول العقارات / المنازل
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                area TEXT,
                title TEXT NOT NULL,
                description TEXT,
                rent INTEGER,
                lat REAL,
                lon REAL,
                services TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE
            )
            """
        )

        # جدول للصور (اختياري للمستقبل)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS property_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(property_id) REFERENCES properties(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()

        # تعبئة المدن الافتراضية إذا كانت فارغة
        cur.execute("SELECT COUNT(*) FROM cities")
        count = cur.fetchone()[0]
        if count == 0:
            default_cities = [
                "دمشق", "حلب", "حمص", "حماة", "اللاذقية", "طرطوس",
                "دير الزور", "الرقة", "الحسكة", "ريف دمشق",
                "درعا", "القنيطرة", "سويدا", "إدلب"
            ]
            cur.executemany(
                "INSERT INTO cities (name) VALUES (?)",
                [(c,) for c in default_cities]
            )
            print(f"تم إضافة {len(default_cities)} مدينة افتراضية")

        # إنشاء مستخدمين تجريبيين إذا لم يوجدوا
        cur.execute("SELECT COUNT(*) FROM users")
        user_count = cur.fetchone()[0]
        if user_count == 0:
            demo_users = [
                ("user1", "123456", "user"),
                ("owner1", "123456", "owner"),
            ]
            cur.executemany(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                demo_users,
            )
            print("تم إنشاء المستخدمين التجريبيين: user1/123456 و owner1/123456")

        conn.commit()
    
    print("تم تهيئة قاعدة البيانات بنجاح!")

def create_user(username: str, password: str, role: str):
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            raise Exception("اسم المستخدم موجود مسبقاً")

def get_user_by_credentials(username: str, password: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password),
        )
        row = cur.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "role": row[2]}
        return None

def get_user_by_id(user_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, role FROM users WHERE id=?",
            (user_id,)
        )
        row = cur.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "role": row[2]}
        return None

def get_cities():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cities ORDER BY name")
        return [{"id": r[0], "name": r[1]} for r in cur.fetchall()]

def get_city_by_id(city_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM cities WHERE id=?", (city_id,))
        r = cur.fetchone()
        if r:
            return {"id": r[0], "name": r[1]}
        return None

def add_property(owner_id: int, city_id: int, area: str, title: str, description: str,
                 rent: int, lat: float, lon: float, services: str):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO properties (owner_id, city_id, area, title, description, rent, lat, lon, services)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (owner_id, city_id, area, title, description, rent, lat, lon, services),
        )
        conn.commit()
        return cur.lastrowid

def update_property(property_id: int, **kwargs):
    """تحديث بيانات عقار"""
    allowed_fields = ['title', 'area', 'description', 'rent', 'lat', 'lon', 'services']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
    
    if not updates:
        return False
        
    set_clause = ", ".join([f"{k}=?" for k in updates.keys()])
    values = list(updates.values())
    values.append(property_id)
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE properties SET {set_clause} WHERE id=?", values)
        conn.commit()
        return cur.rowcount > 0

def delete_property(property_id: int, owner_id: int):
    """حذف عقار (المالك يمكنه حذف عقاره فقط)"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM properties WHERE id=? AND owner_id=?", (property_id, owner_id))
        conn.commit()
        return cur.rowcount > 0

def get_properties_by_city(city_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
                   u.username, u.id as owner_id
            FROM properties p
            JOIN users u ON p.owner_id = u.id
            WHERE p.city_id=?
            ORDER BY p.created_at DESC
            """,
            (city_id,),
        )
        res = []
        for r in cur.fetchall():
            res.append(
                {
                    "id": r[0],
                    "title": r[1],
                    "area": r[2],
                    "description": r[3],
                    "rent": r[4],
                    "lat": r[5],
                    "lon": r[6],
                    "services": r[7],
                    "owner_username": r[8],
                    "owner_id": r[9],
                }
            )
        return res

def get_properties_by_owner(owner_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services, p.city_id
            FROM properties p
            WHERE p.owner_id=?
            ORDER BY p.created_at DESC
            """,
            (owner_id,),
        )
        res = []
        for r in cur.fetchall():
            res.append(
                {
                    "id": r[0],
                    "title": r[1],
                    "area": r[2],
                    "description": r[3],
                    "rent": r[4],
                    "lat": r[5],
                    "lon": r[6],
                    "services": r[7],
                    "city_id": r[8],
                }
            )
        return res

def get_property_by_id(property_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
                   p.owner_id, p.city_id, u.username as owner_username
            FROM properties p
            JOIN users u ON p.owner_id = u.id
            WHERE p.id=?
            """,
            (property_id,),
        )
        r = cur.fetchone()
        if r:
            return {
                "id": r[0],
                "title": r[1],
                "area": r[2],
                "description": r[3],
                "rent": r[4],
                "lat": r[5],
                "lon": r[6],
                "services": r[7],
                "owner_id": r[8],
                "city_id": r[9],
                "owner_username": r[10],
            }
        return None

def search_properties(city_id: int = None, area: str = None, max_rent: int = None):
    """بحث في العقارات"""
    query = """
        SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
               u.username, c.name as city_name
        FROM properties p
        JOIN users u ON p.owner_id = u.id
        JOIN cities c ON p.city_id = c.id
        WHERE 1=1
    """
    params = []
    
    if city_id:
        query += " AND p.city_id = ?"
        params.append(city_id)
    
    if area:
        query += " AND p.area LIKE ?"
        params.append(f"%{area}%")
    
    if max_rent:
        query += " AND p.rent <= ?"
        params.append(max_rent)
    
    query += " ORDER BY p.created_at DESC"
    
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        res = []
        for r in cur.fetchall():
            res.append(
                {
                    "id": r[0],
                    "title": r[1],
                    "area": r[2],
                    "description": r[3],
                    "rent": r[4],
                    "lat": r[5],
                    "lon": r[6],
                    "services": r[7],
                    "owner_username": r[8],
                    "city_name": r[9],
                }
            )
        return res

def get_all_areas_by_city(city_id: int):
    """جلب جميع المناطق المتاحة لمدينة معينة"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT area FROM properties 
            WHERE city_id = ? AND area IS NOT NULL AND area != ''
            ORDER BY area
        """, (city_id,))
        return [row[0] for row in cur.fetchall()]

def get_properties_by_city_and_area(city_id: int, area: str):
    """جلب العقارات بناءً على المدينة والمنطقة"""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
                   u.username as owner_username, u.id as owner_id
            FROM properties p
            JOIN users u ON p.owner_id = u.id
            WHERE p.city_id = ? AND p.area = ?
            ORDER BY p.created_at DESC
        """, (city_id, area))
        properties = []
        for row in cur.fetchall():
            properties.append({
                "id": row[0],
                "title": row[1],
                "area": row[2],
                "description": row[3],
                "rent": row[4],
                "lat": row[5],
                "lon": row[6],
                "services": row[7],
                "owner_username": row[8],
                "owner_id": row[9]
            })
        return properties

# دالة مساعدة لفحص حالة قاعدة البيانات
def check_db_status():
    """فحص حالة قاعدة البيانات"""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            
            # فحص الجداول
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            
            # فحص عدد المستخدمين
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            
            # فحص عدد العقارات
            cur.execute("SELECT COUNT(*) FROM properties")
            property_count = cur.fetchone()[0]
            
            return {
                "db_file": DB_FILE,
                "tables": tables,
                "user_count": user_count,
                "property_count": property_count,
                "status": "healthy"
            }
    except Exception as e:
        return {
            "db_file": DB_FILE,
            "error": str(e),
            "status": "error"
        }

# تهيئة قاعدة البيانات تلقائياً عند الاستيراد
if __name__ != "__main__":
    init_db()