import flet as ft
import sqlite3
import os
from pathlib import Path
from datetime import datetime

# استيراد مكتبة flet_map إذا كانت متوفرة
try:
    import flet_map as map
except ImportError:
    # إذا لم تكن متوفرة، استخدم بديل
    class MockMap:
        def __init__(self, *args, **kwargs):
            pass
            
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
            
    class MockMapLatitudeLongitude:
        def __init__(self, lat, lon):
            self.latitude = lat
            self.longitude = lon
            
    class MockMapTapEvent:
        def __init__(self):
            self.name = "tap"
            self.coordinates = MockMapLatitudeLongitude(0, 0)
            
    class MockTileLayer:
        def __init__(self, *args, **kwargs):
            pass
            
    class MockMarkerLayer:
        def __init__(self, *args, **kwargs):
            self.markers = []
            
    class MockMarker:
        def __init__(self, *args, **kwargs):
            pass
            
    class MapInteractiveFlag:
        ALL = "all"
        
    class MapInteractionConfiguration:
        def __init__(self, flags=None):
            self.flags = flags
            
    map = MockMap()
    map.Map = MockMap
    map.MapLatitudeLongitude = MockMapLatitudeLongitude
    map.MapTapEvent = MockMapTapEvent
    map.TileLayer = MockTileLayer
    map.MarkerLayer = MockMarkerLayer
    map.Marker = MockMarker
    map.MapInteractiveFlag = MapInteractiveFlag
    map.MapInteractionConfiguration = MapInteractionConfiguration

# قاعدة البيانات
class DatabaseManager:
    def __init__(self):
        self.db_path = "city_mover.db"
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cur = conn.cursor()
        
        # جدول المستخدمين
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'owner')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المدن
        cur.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                lat REAL,
                lon REAL
            )
        ''')
        
        # جدول العقارات
        cur.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                city_id INTEGER NOT NULL,
                area TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                rent INTEGER,
                lat REAL,
                lon REAL,
                services TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users (id),
                FOREIGN KEY (city_id) REFERENCES cities (id)
            )
        ''')
        
        # إضافة المدن إذا لم تكن موجودة
        cities = [
            ("دمشق", 33.5138, 36.2765),
            ("حلب", 36.2021, 37.1343),
            ("حمص", 34.7324, 36.7137),
            ("اللاذقية", 35.5177, 35.7831),
            ("حماة", 35.1318, 36.7578)
        ]
        
        for city in cities:
            cur.execute("INSERT OR IGNORE INTO cities (name, lat, lon) VALUES (?, ?, ?)", city)
        
        # إضافة مستخدمين تجريبيين
        users = [
            ("user1", "123456", "user"),
            ("owner1", "123456", "owner")
        ]
        
        for user in users:
            cur.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", user)
        
        conn.commit()
        conn.close()

    def get_user_by_credentials(self, username: str, password: str):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role FROM users WHERE username = ? AND password = ?", 
                   (username, password))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "username": row[1], "role": row[2]}
        return None

    def create_user(self, username: str, password: str, role: str):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                   (username, password, role))
        user_id = cur.lastrowid
        conn.commit()
        conn.close()
        return user_id

    def get_cities(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, lat, lon FROM cities")
        cities = []
        for row in cur.fetchall():
            cities.append({"id": row[0], "name": row[1], "lat": row[2], "lon": row[3]})
        conn.close()
        return cities

    def get_city_by_id(self, city_id: int):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, lat, lon FROM cities WHERE id = ?", (city_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "name": row[1], "lat": row[2], "lon": row[3]}
        return None

    def add_property(self, owner_id: int, city_id: int, area: str, title: str, 
                    description: str = None, rent: int = None, lat: float = None, 
                    lon: float = None, services: str = None):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO properties 
            (owner_id, city_id, area, title, description, rent, lat, lon, services)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (owner_id, city_id, area, title, description, rent, lat, lon, services))
        conn.commit()
        conn.close()

    def get_properties_by_owner(self, owner_id: int):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT id, city_id, area, title, description, rent, lat, lon, services
            FROM properties WHERE owner_id = ?
        ''', (owner_id,))
        properties = []
        for row in cur.fetchall():
            properties.append({
                "id": row[0], "city_id": row[1], "area": row[2], "title": row[3],
                "description": row[4], "rent": row[5], "lat": row[6], "lon": row[7],
                "services": row[8]
            })
        conn.close()
        return properties

# تهيئة قاعدة البيانات
db = DatabaseManager()

def main(page: ft.Page):
    # إعدادات خاصة بالموبايل والأندرويد
    page.title = "City Mover - تطبيق الانتقال للمدن"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
def main(page: ft.Page):
    # إعدادات خاصة بالموبايل والأندرويد
    page.title = "City Mover - تطبيق الانتقال للمدن"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    #  إضافة الأيقونة 
    try:
        # محاولة تحميل الأيقونة من مجلد assets
        page.window.icon = "assets/icon.png"
    except Exception as e:
        print(f"لم يتم العثور على الأيقونة: {e}")
        # استخدام أيقونة افتراضية إذا لم توجد
        page.window.icon = ft.Icons.LOCATION_CITY
     
    # إعدادات للأندرويد
    page.platform = ft.PagePlatform.ANDROID
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.BLUE,
        use_material3=True
    )
    
    # تحسينات للموبايل
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.START
    
    # ألوان التطبيق
    PRIMARY_COLOR = "#1E40AF"
    SECONDARY_COLOR = "#0EA5E9"
    ACCENT_COLOR = "#F59E0B"
    SUCCESS_COLOR = "#10B981"
    WARNING_COLOR = "#F59E0B"
    ERROR_COLOR = "#EF4444"
    BACKGROUND_COLOR = "#F8FAFC"
    SURFACE_COLOR = "#FFFFFF"
    TEXT_COLOR = "#1E293B"

    # تخزين بيانات الجلسة
    if not page.session.contains_key("user"):
        page.session.set("user", None)

    # ---------- مناطق دمشق المفعلة ----------
    DAMASCUS_ACTIVE_AREAS = ["المزة", "كفرسوسة", "الميدان"]
    
    # ---------- جميع مناطق دمشق ----------
    DAMASCUS_ALL_AREAS = [
        "المزة", "كفرسوسة", "الميدان", "القدم", "القصاع", "المالكي", "أبو رمانة",
        "البرامكة", "ركن الدين", "الصالحية", "الشعلان", "المهاجرين", "العدوي",
        "القنوات", "باب توما", "باب شرقي", "ساروجة", "العفيف", "الجسر الأبيض",
        "الزاهرة", "الرحمانية", "دمر", "السبينة", "جوبر", "حرستا", "دوما",
        "داريا", "معضمية الشام", "صحنايا", "الكسوة", "التضامن", "الهامة",
        "قدسيا", "يملك", "القدم", "القابون", "برزة", "القطيفة", "الخضيري",
        "الزبداني", "بلد", "جرمانا", "سقبا", "معربا", "عربين", "حزة", "ببيلا"
    ]

    # ---------- عناصر مشتركة ----------

    def create_logo():
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.LOCATION_CITY, color="white", size=24),
                ft.Column([
                    ft.Text("City Mover", size=14, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text("تطبيق الانتقال", size=10, color="white"),
                ], spacing=0)
            ], spacing=8),
            padding=10,
        )

    def app_bar(title: str):
        user = page.session.get("user")
        right_controls = []
        if user:
            user_icon = ft.Icons.PERSON if user['role'] == 'user' else ft.Icons.BUSINESS_CENTER
            user_color = SECONDARY_COLOR if user['role'] == 'user' else ACCENT_COLOR
            
            right_controls = [
                ft.PopupMenuButton(
                    items=[
                        ft.PopupMenuItem(
                            content=ft.Row([
                                ft.Icon(user_icon, color=user_color, size=20),
                                ft.Column([
                                    ft.Text(f"{user['username']}", size=14),
                                    ft.Text(
                                        "مستخدم" if user['role'] == 'user' else "مالك", 
                                        size=12, 
                                        color=user_color
                                    ),
                                ], spacing=2)
                            ], spacing=8)
                        ),
                        ft.PopupMenuItem(),
                        ft.PopupMenuItem(
                            text="تسجيل الخروج",
                            icon=ft.Icons.LOGOUT,
                            on_click=logout,
                        ),
                    ]
                )
            ]

        return ft.AppBar(
            leading=create_logo(),
            title=ft.Text(title, weight=ft.FontWeight.BOLD, color="white", size=16),
            center_title=False,
            toolbar_height=60,
            bgcolor=PRIMARY_COLOR,
            actions=right_controls,
        )

    def logout(e=None):
        page.session.set("user", None)
        page.go("/login")

    def create_card(content, color=SURFACE_COLOR, elevation=1):
        return ft.Container(
            content=content,
            padding=15,
            margin=8,
            border_radius=12,
            bgcolor=color,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.BLACK12,
                offset=ft.Offset(0, 2),
            ),
        )

    def create_section_header(title: str, icon: str = None):
        content = [ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR)]
        if icon:
            content.insert(0, ft.Icon(icon, color=PRIMARY_COLOR, size=20))
        return ft.Container(
            content=ft.Row(content, spacing=8),
            padding=ft.padding.only(bottom=8, top=5),
        )

    def create_mobile_button(text: str, icon: str, on_click, color=PRIMARY_COLOR, expand=True):
        return ft.ElevatedButton(
            text=text,
            icon=icon,
            on_click=on_click,
            style=ft.ButtonStyle(
                color="white",
                bgcolor=color,
                padding=ft.padding.symmetric(horizontal=16, vertical=12),
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            expand=expand,
        )

    # ---------- شاشة تسجيل الدخول / إنشاء حساب ----------

    def login_view():
        username = ft.TextField(
            label="اسم المستخدم",
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            content_padding=12,
        )
        password = ft.TextField(
            label="كلمة المرور",
            expand=True,
            password=True,
            can_reveal_password=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            content_padding=12,
        )

        mode_tabs = ft.Tabs(
            tabs=[
                ft.Tab(
                    text="تسجيل الدخول",
                    icon=ft.Icons.LOGIN,
                ),
                ft.Tab(
                    text="إنشاء حساب",
                    icon=ft.Icons.PERSON_ADD,
                ),
            ],
            selected_index=0,
            expand=1,
            indicator_color=SECONDARY_COLOR,
            label_color=PRIMARY_COLOR,
            unselected_label_color=ft.Colors.GREY_600,
        )

        role_dropdown = ft.Dropdown(
            label="نوع الحساب",
            options=[
                ft.dropdown.Option("user", "مستخدم"),
                ft.dropdown.Option("owner", "مالك عقار"),
            ],
            value="user",
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            content_padding=12,
        )

        msg = ft.Text(color=ERROR_COLOR, size=14)

        def submit(e):
            nonlocal username, password
            if mode_tabs.selected_index == 0:
                # تسجيل الدخول
                user = db.get_user_by_credentials(username.value.strip(), password.value.strip())
                if not user:
                    msg.value = "بيانات الدخول غير صحيحة"
                    msg.color = ERROR_COLOR
                    page.update()
                    return
                page.session.set("user", user)
                if user["role"] == "owner":
                    page.go("/owner")
                else:
                    page.go("/user")
            else:
                # إنشاء حساب جديد
                uname = username.value.strip()
                pwd = password.value.strip()
                role = role_dropdown.value
                if not uname or not pwd:
                    msg.value = "الرجاء إدخال اسم مستخدم وكلمة مرور"
                    msg.color = ERROR_COLOR
                    page.update()
                    return
                try:
                    user_id = db.create_user(uname, pwd, role)
                    new_user = {"id": user_id, "username": uname, "role": role}
                    page.session.set("user", new_user)
                    msg.value = "تم إنشاء الحساب بنجاح!"
                    msg.color = SUCCESS_COLOR
                    page.update()
                    if role == "owner":
                        page.go("/owner")
                    else:
                        page.go("/user")
                except Exception as ex:
                    msg.value = f"خطأ في إنشاء الحساب: {ex}"
                    msg.color = ERROR_COLOR
                    page.update()

        submit_btn = create_mobile_button(
            "متابعة", 
            ft.Icons.ARROW_FORWARD, 
            submit,
            color=PRIMARY_COLOR
        )

        content_col = ft.Column(
            [
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.LOCATION_CITY, size=36, color=PRIMARY_COLOR),
                            ft.Column([
                                ft.Text("City Mover", size=24, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                                ft.Text("تطبيق الانتقال للمدن", size=14, color=TEXT_COLOR),
                            ], spacing=0)
                        ], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Text(
                            "يساعدك على الانتقال لمدينة جديدة والعثور على سكن وخدمات قريبة",
                            size=12,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=20,
                    margin=ft.margin.only(bottom=10),
                ),
                
                create_card(
                    ft.Column([
                        mode_tabs,
                        ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                        ft.Row([username], spacing=10),
                        ft.Row([password], spacing=10),
                        ft.Row([role_dropdown], spacing=10),
                        ft.Container(
                            content=submit_btn,
                            padding=10,
                        ),
                        msg,
                    ], spacing=10)
                ),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("حسابات تجريبية:", size=12, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        create_card(
                            ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.PERSON, size=14, color=SECONDARY_COLOR),
                                    ft.Text("مستخدم: user1 / 123456", size=11),
                                ]),
                                ft.Row([
                                    ft.Icon(ft.Icons.BUSINESS_CENTER, size=14, color=ACCENT_COLOR),
                                    ft.Text("مالك: owner1 / 123456", size=11),
                                ]),
                            ], spacing=5),
                            color=BACKGROUND_COLOR,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            scroll=ft.ScrollMode.ADAPTIVE,
        )

        return ft.View(
            route="/login",
            controls=[
                app_bar("تسجيل الدخول"),
                ft.Container(
                    content=content_col,
                    padding=10,
                    expand=True,
                    bgcolor=BACKGROUND_COLOR,
                ),
            ],
        )

    # ---------- شاشة المستخدم (User) ----------

    def user_view():
        user = page.session.get("user")
        if not user or user["role"] != "user":
            page.go("/login")
            return login_view()

        cities = db.get_cities()
        city_dropdown = ft.Dropdown(
            label="اختر المدينة",
            expand=True,
            options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in cities],
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            content_padding=12,
        )

        area_dropdown = ft.Dropdown(
            label="اختر المنطقة",
            expand=True,
            options=[],
            disabled=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            content_padding=12,
        )

        selected_city_name = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR)
        selected_area_name = ft.Text("", size=14, color=TEXT_COLOR)
        
        properties_container = ft.ListView(
            expand=True,
            spacing=10,
            padding=10,
        )
        
        tips_container = ft.Column(spacing=8)

        user_marker_layer_ref = ft.Ref[map.MarkerLayer]()

        user_map = map.Map(
            expand=True,
            height=250,
            initial_center=map.MapLatitudeLongitude(33.5138, 36.2765),
            initial_zoom=11,
            interaction_configuration=map.MapInteractionConfiguration(
                flags=map.MapInteractiveFlag.ALL
            ),
            layers=[
                map.TileLayer(
                    url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                ),
                map.MarkerLayer(ref=user_marker_layer_ref, markers=[]),
            ],
        )

        def get_all_areas_by_city(city_id: int):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT area FROM properties 
                WHERE city_id = ? AND area IS NOT NULL AND area != ''
            """, (city_id,))
            areas = [row[0] for row in cur.fetchall()]
            conn.close()
            return areas

        def get_properties_by_city_and_area(city_id: int, area: str):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT p.id, p.title, p.area, p.description, p.rent, p.lat, p.lon, p.services,
                       u.username as owner_username
                FROM properties p
                JOIN users u ON p.owner_id = u.id
                WHERE p.city_id = ? AND p.area = ?
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
                    "owner_username": row[8]
                })
            conn.close()
            return properties

        def load_areas_for_city(city_id: int):
            area_dropdown.options.clear()
            area_dropdown.disabled = True
            
            city = db.get_city_by_id(city_id)
            if not city:
                return
                
            city_name = city["name"]
            
            if city_name == "دمشق":
                for area in DAMASCUS_ALL_AREAS:
                    is_active = area in DAMASCUS_ACTIVE_AREAS
                    area_text = f"{area} {'✓' if is_active else ''}"
                    area_dropdown.options.append(ft.dropdown.Option(area, area_text))
                
                area_dropdown.disabled = False
                selected_area_name.value = f"المناطق المفعلة: {', '.join(DAMASCUS_ACTIVE_AREAS)}"
                selected_area_name.color = SUCCESS_COLOR
            else:
                all_areas = get_all_areas_by_city(city_id)
                for area in all_areas:
                    area_dropdown.options.append(ft.dropdown.Option(area, area))
                area_dropdown.disabled = False
                selected_area_name.value = f"المناطق المتاحة: {len(all_areas)} منطقة"
                selected_area_name.color = TEXT_COLOR
            
            area_dropdown.value = None
            properties_container.controls.clear()
            page.update()

        def load_tips_for_city(city_name: str):
            tips_container.controls.clear()
            tips_container.controls.append(
                create_section_header("نصائح سريعة", ft.Icons.LIGHTBULB)
            )
            base_tips = [
                "• احسب ميزانيتك الشهرية (السكن + المواصلات + الطعام)",
                "• تعرّف على المواصلات العامة في المدينة",
                "• ابحث عن الخدمات الأساسية القريبة",
                "• زر الحي في أوقات مختلفة لمعرفة الازدحام",
                "• تحقق من جودة الخدمات الأساسية",
                "• اسأل السكان المحليين عن تجاربهم",
            ]
            for t in base_tips:
                tips_container.controls.append(
                    ft.Container(
                        content=ft.Text(t, size=12, color=ft.Colors.GREY_700),
                        padding=ft.padding.symmetric(vertical=3),
                    )
                )

        def contact_owner(owner_username: str, property_title: str):
            def send_message(e):
                if message_field.value.strip():
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"تم إرسال رسالتك إلى {owner_username}"),
                        bgcolor=SUCCESS_COLOR,
                    )
                    page.snack_bar.open = True
                    page.update()
                    page.close(dlg)
                else:
                    message_field.error_text = "الرجاء كتابة رسالة"
                    page.update()

            message_field = ft.TextField(
                label="رسالتك إلى المالك",
                multiline=True,
                min_lines=3,
                max_lines=5,
                expand=True,
                border_color=PRIMARY_COLOR,
                filled=True,
            )
            
            dlg = ft.AlertDialog(
                title=ft.Text(f"التواصل مع {owner_username}", size=16),
                content=ft.Column([
                    ft.Text(f"بخصوص: {property_title}", size=14),
                    message_field
                ], tight=True, height=200),
                actions=[
                    ft.Row([
                        create_mobile_button("إرسال", ft.Icons.SEND, send_message, color=SUCCESS_COLOR, expand=True),
                        create_mobile_button("إلغاء", ft.Icons.CLOSE, lambda e: page.close(dlg), color=ERROR_COLOR, expand=True),
                    ], spacing=10)
                ],
            )
            
            page.open(dlg)

        def show_properties(e=None):
            properties_container.controls.clear()
            if user_marker_layer_ref.current:
                user_marker_layer_ref.current.markers.clear()

            if not city_dropdown.value:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("الرجاء اختيار مدينة أولاً", color=ERROR_COLOR),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
                page.update()
                return

            city_id = int(city_dropdown.value)
            city = db.get_city_by_id(city_id)
            city_name = city["name"] if city else ""
            selected_city_name.value = f"المدينة: {city_name}"

            if not area_dropdown.value:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("الرجاء اختيار منطقة", color=WARNING_COLOR),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
                page.update()
                return

            if city_name == "دمشق" and area_dropdown.value not in DAMASCUS_ACTIVE_AREAS:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("لا توجد منازل متاحة في هذه المنطقة", color=ERROR_COLOR),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
                page.update()
                return

            props = get_properties_by_city_and_area(city_id, area_dropdown.value)

            if not props:
                properties_container.controls.append(
                    ft.Container(
                        content=ft.Text("لا يوجد منازل متاحة حالياً"),
                        padding=10,
                        alignment=ft.alignment.center,
                    )
                )
            else:
                for p in props:
                    def make_show_on_map(lat=p["lat"], lon=p["lon"], title=p["title"]):
                        def _inner(ev):
                            if lat is None or lon is None:
                                page.snack_bar = ft.SnackBar(
                                    ft.Text("لا توجد إحداثيات لهذا المنزل"),
                                    bgcolor=WARNING_COLOR,
                                )
                                page.snack_bar.open = True
                                page.update()
                                return

                            if user_marker_layer_ref.current:
                                user_marker_layer_ref.current.markers.clear()
                                user_marker_layer_ref.current.markers.append(
                                    map.Marker(
                                        content=ft.Icon(ft.Icons.HOME, color=ft.Colors.RED),
                                        coordinates=map.MapLatitudeLongitude(lat, lon),
                                    )
                                )
                            page.update()
                        return _inner

                    def make_contact_owner(username=p["owner_username"], title=p["title"]):
                        return lambda e: contact_owner(username, title)

                    card = create_card(
                        ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.HOME, color=PRIMARY_COLOR, size=20),
                                ft.Text(p["title"], size=14, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR, expand=True),
                            ]),
                            ft.Divider(height=8),
                            ft.Column([
                                ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=14), ft.Text(f"المنطقة: {p['area']}", size=12)]),
                                ft.Row([ft.Icon(ft.Icons.ATTACH_MONEY, size=14), ft.Text(f"الإيجار: {p['rent']} ل.س", size=12)]),
                                ft.Row([ft.Icon(ft.Icons.PERSON, size=14), ft.Text(f"المالك: {p['owner_username']}", size=12)]),
                            ], spacing=5),
                            ft.Divider(height=8),
                            ft.Text(p["description"] or "", size=11, color=ft.Colors.GREY_700),
                            ft.Text(f"الخدمات: {p['services'] or 'غير مذكورة'}", size=10, color=ft.Colors.GREY_600),
                            ft.Divider(height=10),
                            ft.Row([
                                create_mobile_button("الموقع", ft.Icons.MAP, make_show_on_map(), color=SECONDARY_COLOR),
                                create_mobile_button("خرائط", ft.Icons.OPEN_IN_NEW, 
                                                   lambda ev, lat=p["lat"], lon=p["lon"]: page.launch_url(f"https://maps.google.com?q={lat},{lon}") 
                                                   if lat and lon else None, color=PRIMARY_COLOR),
                                create_mobile_button("تواصل", ft.Icons.CHAT, make_contact_owner(), color=SUCCESS_COLOR),
                            ], spacing=5),
                        ])
                    )
                    properties_container.controls.append(card)

            load_tips_for_city(city_name)
            page.update()

        def on_city_change(e):
            if city_dropdown.value:
                load_areas_for_city(int(city_dropdown.value))
                show_properties()

        def on_area_change(e):
            show_properties()

        city_dropdown.on_change = on_city_change
        area_dropdown.on_change = on_area_change

        # واجهة المستخدم للموبايل
        search_section = ft.Container(
            content=ft.Column([
                create_section_header("البحث عن سكن", ft.Icons.SEARCH),
                create_card(ft.Column([
                    ft.Text("اختر المدينة:", size=14),
                    ft.Row([city_dropdown]),
                    ft.Text("اختر المنطقة:", size=14),
                    ft.Row([area_dropdown]),
                    selected_city_name,
                    selected_area_name,
                ], spacing=8))
            ], spacing=5),
            padding=5,
        )

        properties_section = ft.Container(
            content=ft.Column([
                create_section_header("المنازل المتاحة", ft.Icons.HOME),
                properties_container
            ], spacing=5),
            expand=True,
        )

        map_section = ft.Container(
            content=ft.Column([
                create_section_header("خريطة الموقع", ft.Icons.MAP),
                create_card(ft.Container(content=user_map, height=250))
            ], spacing=5),
        )

        tips_section = ft.Container(
            content=ft.Column([
                create_section_header("نصائح الانتقال", ft.Icons.LIGHTBULB),
                create_card(ft.Container(content=tips_container, height=150))
            ], spacing=5),
        )

        # استخدام Tabs للتنقل بين الأقسام في الموبايل
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="البحث",
                    icon=ft.Icons.SEARCH,
                    content=ft.Column([search_section, properties_section], scroll=ft.ScrollMode.ADAPTIVE)
                ),
                ft.Tab(
                    text="الخريطة",
                    icon=ft.Icons.MAP,
                    content=ft.Column([map_section], scroll=ft.ScrollMode.ADAPTIVE)
                ),
                ft.Tab(
                    text="النصائح", 
                    icon=ft.Icons.LIGHTBULB,
                    content=ft.Column([tips_section], scroll=ft.ScrollMode.ADAPTIVE)
                ),
            ],
            expand=True,
        )

        return ft.View(
            route="/user",
            appbar=app_bar("لوحة المستخدم"),
            controls=[
                ft.Container(
                    content=tabs,
                    expand=True,
                    bgcolor=BACKGROUND_COLOR,
                )
            ],
        )

    # ---------- شاشة المالك (Owner) ----------

    def owner_view():
        user = page.session.get("user")
        if not user or user["role"] != "owner":
            page.go("/login")
            return login_view()

        cities = db.get_cities()
        city_dropdown = ft.Dropdown(
            label="المدينة",
            expand=True,
            options=[ft.dropdown.Option(str(c["id"]), c["name"]) for c in cities],
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            content_padding=12,
        )

        area_dropdown = ft.Dropdown(
            label="المنطقة",
            expand=True,
            options=[],
            disabled=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            bgcolor="white",
            content_padding=12,
        )

        area_field = ft.TextField(
            label="أو اكتب منطقة جديدة", 
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            content_padding=12,
        )
        title_field = ft.TextField(
            label="عنوان الإعلان",
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            content_padding=12,
        )
        rent_field = ft.TextField(
            label="الإيجار الشهري (ل.س)", 
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            content_padding=12,
        )
        desc_field = ft.TextField(
            label="وصف المنزل",
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            content_padding=12,
        )
        services_field = ft.TextField(
            label="الخدمات القريبة",
            multiline=True,
            min_lines=2,
            max_lines=3,
            expand=True,
            border_color=PRIMARY_COLOR,
            filled=True,
            content_padding=12,
        )
        lat_field = ft.TextField(
            label="خط العرض", 
            expand=1,
            border_color=PRIMARY_COLOR,
            filled=True,
            content_padding=12,
        )
        lon_field = ft.TextField(
            label="خط الطول", 
            expand=1,
            border_color=PRIMARY_COLOR,
            filled=True,
            content_padding=12,
        )

        msg = ft.Text(color=ERROR_COLOR, size=14)

        owner_marker_layer_ref = ft.Ref[map.MarkerLayer]()

        def handle_owner_map_tap(e: map.MapTapEvent):
            if e.name != "tap":
                return
            coords = e.coordinates
            lat = coords.latitude
            lon = coords.longitude
            lat_field.value = f"{lat:.6f}"
            lon_field.value = f"{lon:.6f}"

            if owner_marker_layer_ref.current:
                owner_marker_layer_ref.current.markers.clear()
                owner_marker_layer_ref.current.markers.append(
                    map.Marker(
                        content=ft.Icon(ft.Icons.LOCATION_ON, color=ERROR_COLOR),
                        coordinates=coords,
                    )
                )
            msg.value = "تم اختيار موقع العقار"
            msg.color = SUCCESS_COLOR
            page.update()

        owner_map = map.Map(
            expand=True,
            height=200,
            initial_center=map.MapLatitudeLongitude(33.5138, 36.2765),
            initial_zoom=11,
            interaction_configuration=map.MapInteractionConfiguration(
                flags=map.MapInteractiveFlag.ALL
            ),
            on_tap=handle_owner_map_tap,
            layers=[
                map.TileLayer(url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png"),
                map.MarkerLayer(ref=owner_marker_layer_ref, markers=[]),
            ],
        )

        def get_all_areas_by_city_owner(city_id: int):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT DISTINCT area FROM properties 
                WHERE city_id = ? AND area IS NOT NULL AND area != ''
            """, (city_id,))
            areas = [row[0] for row in cur.fetchall()]
            conn.close()
            return areas

        def load_areas_for_owner_city(city_id: int):
            area_dropdown.options.clear()
            area_dropdown.disabled = True
            
            city = db.get_city_by_id(city_id)
            if not city:
                return
                
            city_name = city["name"]
            
            if city_name == "دمشق":
                for area in DAMASCUS_ALL_AREAS:
                    is_active = area in DAMASCUS_ACTIVE_AREAS
                    area_text = f"{area} {'✓' if is_active else ''}"
                    area_dropdown.options.append(ft.dropdown.Option(area, area_text))
                
                area_dropdown.disabled = False
                msg.value = f"المناطق المفعلة: {', '.join(DAMASCUS_ACTIVE_AREAS)}"
                msg.color = SUCCESS_COLOR
            else:
                all_areas = get_all_areas_by_city_owner(city_id)
                for area in all_areas:
                    area_dropdown.options.append(ft.dropdown.Option(area, area))
                area_dropdown.disabled = False
                msg.value = f"تم تحميل {len(all_areas)} منطقة"
                msg.color = TEXT_COLOR
            
            area_dropdown.value = None
            page.update()

        def on_city_change_owner(e):
            if city_dropdown.value:
                load_areas_for_owner_city(int(city_dropdown.value))

        city_dropdown.on_change = on_city_change_owner

        def open_google_maps(e=None):
            try:
                lat = float(lat_field.value)
                lon = float(lon_field.value)
                page.launch_url(f"https://maps.google.com?q={lat},{lon}")
                return
            except Exception:
                pass

            if city_dropdown.value:
                city = db.get_city_by_id(int(city_dropdown.value))
                if city:
                    page.launch_url(f"https://maps.google.com/search/{city['name']}")
                    return

            page.launch_url("https://maps.google.com")

        def save_property(e):
            if not city_dropdown.value:
                msg.value = "الرجاء اختيار مدينة"
                msg.color = ERROR_COLOR
                page.update()
                return

            selected_area = None
            if area_dropdown.value:
                selected_area = area_dropdown.value
            elif area_field.value.strip():
                selected_area = area_field.value.strip()
            
            if not selected_area:
                msg.value = "الرجاء اختيار أو كتابة منطقة"
                msg.color = ERROR_COLOR
                page.update()
                return

            city_id = int(city_dropdown.value)
            city = db.get_city_by_id(city_id)
            city_name = city["name"] if city else ""

            if city_name == "دمشق" and selected_area not in DAMASCUS_ACTIVE_AREAS:
                msg.value = f"لدمشق: يمكنك فقط إضافة عقارات في المناطق التالية: {', '.join(DAMASCUS_ACTIVE_AREAS)}"
                msg.color = ERROR_COLOR
                page.update()
                return

            try:
                rent = int(rent_field.value) if rent_field.value else None
            except ValueError:
                msg.value = "الإيجار يجب أن يكون رقماً"
                msg.color = ERROR_COLOR
                page.update()
                return
            try:
                lat = float(lat_field.value) if lat_field.value else None
                lon = float(lon_field.value) if lon_field.value else None
            except ValueError:
                msg.value = "إحداثيات غير صحيحة"
                msg.color = ERROR_COLOR
                page.update()
                return

            try:
                db.add_property(
                    owner_id=user["id"],
                    city_id=city_id,
                    area=selected_area,
                    title=title_field.value.strip(),
                    description=desc_field.value.strip(),
                    rent=rent,
                    lat=lat,
                    lon=lon,
                    services=services_field.value.strip(),
                )
                msg.value = "تم حفظ العقار بنجاح ✅"
                msg.color = SUCCESS_COLOR

                area_field.value = ""
                title_field.value = ""
                rent_field.value = ""
                desc_field.value = ""
                services_field.value = ""
                lat_field.value = ""
                lon_field.value = ""
                if owner_marker_layer_ref.current:
                    owner_marker_layer_ref.current.markers.clear()
                page.update()
                load_owner_properties()
            except Exception as ex:
                msg.value = f"حدث خطأ: {ex}"
                msg.color = ERROR_COLOR
                page.update()

        def edit_property(property_id: int):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT title, area, description, rent, lat, lon, services
                FROM properties WHERE id = ?
            """, (property_id,))
            prop = cur.fetchone()
            conn.close()
            
            if not prop:
                return
            
            edit_title = ft.TextField(label="العنوان", value=prop[0], expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_area = ft.TextField(label="المنطقة", value=prop[1], expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_desc = ft.TextField(label="الوصف", value=prop[2], multiline=True, min_lines=2, expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_rent = ft.TextField(label="الإيجار", value=str(prop[3]) if prop[3] else "", expand=True, border_color=PRIMARY_COLOR, filled=True)
            edit_lat = ft.TextField(label="خط العرض", value=str(prop[4]) if prop[4] else "", expand=1, border_color=PRIMARY_COLOR, filled=True)
            edit_lon = ft.TextField(label="خط الطول", value=str(prop[5]) if prop[5] else "", expand=1, border_color=PRIMARY_COLOR, filled=True)
            edit_services = ft.TextField(label="الخدمات", value=prop[6] or "", multiline=True, min_lines=2, expand=True, border_color=PRIMARY_COLOR, filled=True)
            
            def update_property(e):
                try:
                    rent_val = int(edit_rent.value) if edit_rent.value.strip() else None
                    lat_val = float(edit_lat.value) if edit_lat.value.strip() else None
                    lon_val = float(edit_lon.value) if edit_lon.value.strip() else None
                    
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE properties 
                        SET title=?, area=?, description=?, rent=?, lat=?, lon=?, services=?
                        WHERE id=?
                    """, (
                        edit_title.value.strip(),
                        edit_area.value.strip(),
                        edit_desc.value.strip(),
                        rent_val,
                        lat_val,
                        lon_val,
                        edit_services.value.strip(),
                        property_id
                    ))
                    conn.commit()
                    conn.close()
                    
                    page.snack_bar = ft.SnackBar(ft.Text("تم التحديث بنجاح"), bgcolor=SUCCESS_COLOR)
                    page.snack_bar.open = True
                    page.update()
                    page.close(dlg)
                    load_owner_properties()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"خطأ: {ex}"), bgcolor=ERROR_COLOR)
                    page.snack_bar.open = True
                    page.update()
            
            dlg = ft.AlertDialog(
                title=ft.Text("تعديل العقار", size=16),
                content=ft.Container(
                    content=ft.Column([
                        edit_title,
                        edit_area,
                        edit_desc,
                        ft.Row([edit_rent, edit_lat, edit_lon], spacing=5),
                        edit_services
                    ], scroll=ft.ScrollMode.ADAPTIVE, height=300),
                    padding=10,
                ),
                actions=[
                    ft.Row([
                        create_mobile_button("حفظ", ft.Icons.SAVE, update_property, color=SUCCESS_COLOR),
                        create_mobile_button("إلغاء", ft.Icons.CLOSE, lambda e: page.close(dlg), color=ERROR_COLOR),
                    ], spacing=10)
                ],
            )
            
            page.open(dlg)

        add_btn = create_mobile_button("حفظ العقار", ft.Icons.SAVE, save_property, color=SUCCESS_COLOR)
        open_maps_btn = create_mobile_button("فتح خرائط جوجل", ft.Icons.OPEN_IN_NEW, open_google_maps, color=PRIMARY_COLOR)

        properties_list = ft.ListView(expand=True, spacing=10, padding=10)

        def load_owner_properties():
            properties_list.controls.clear()
            props = db.get_properties_by_owner(user["id"])
            if not props:
                properties_list.controls.append(
                    create_card(
                        ft.Column([
                            ft.Icon(ft.Icons.HOME, size=30, color=ft.Colors.GREY_400),
                            ft.Text("لم تقم بإضافة أي عقار", size=14, color=ft.Colors.GREY_600),
                            ft.Text("استخدم النموذج لإضافة عقارك الأول", size=12, color=ft.Colors.GREY_500),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        color=BACKGROUND_COLOR,
                    )
                )
            else:
                for p in props:
                    city = db.get_city_by_id(p.get("city_id", 0))
                    city_name = city["name"] if city else ""
                    is_active_area = city_name == "دمشق" and p["area"] in DAMASCUS_ACTIVE_AREAS
                    
                    def make_edit_function(prop_id=p["id"]):
                        return lambda e: edit_property(prop_id)
                    
                    properties_list.controls.append(
                        create_card(
                            ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.APARTMENT, color=PRIMARY_COLOR, size=20),
                                    ft.Text(p["title"], size=14, weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR, expand=True),
                                    ft.Container(
                                        content=ft.Row([ft.Icon(ft.Icons.CHECK, size=12, color="white"), ft.Text("مفعل", size=10)]),
                                        bgcolor=SUCCESS_COLOR,
                                        padding=5,
                                        border_radius=10,
                                        visible=is_active_area
                                    ) if is_active_area else ft.Container()
                                ]),
                                ft.Divider(height=8),
                                ft.Column([
                                    ft.Row([ft.Icon(ft.Icons.LOCATION_CITY, size=12), ft.Text(f"المدينة: {city_name}", size=11)]),
                                    ft.Row([ft.Icon(ft.Icons.MAP, size=12), ft.Text(f"المنطقة: {p['area']}", size=11)]),
                                    ft.Row([ft.Icon(ft.Icons.ATTACH_MONEY, size=12), ft.Text(f"الإيجار: {p['rent']} ل.س", size=11)]),
                                ], spacing=3),
                                ft.Divider(height=8),
                                ft.Text(p["description"] or "", size=11, color=ft.Colors.GREY_700),
                                ft.Text(f"الخدمات: {p['services'] or 'غير مذكورة'}", size=10, color=ft.Colors.GREY_600),
                                ft.Divider(height=10),
                                ft.Row([
                                    create_mobile_button("تعديل", ft.Icons.EDIT, make_edit_function(), color=PRIMARY_COLOR)
                                ]),
                            ])
                        )
                    )

        load_owner_properties()

        # واجهة المالك للموبايل باستخدام Tabs
        add_property_tab = ft.Column([
            create_section_header("إضافة عقار جديد", ft.Icons.ADD),
            create_card(ft.Column([
                ft.Text("المدينة:", size=14),
                ft.Row([city_dropdown]),
                ft.Text("المنطقة:", size=14),
                ft.Row([area_dropdown]),
                ft.Row([area_field]),
                ft.Container(
                    content=ft.Text("ملاحظة: لدمشق، يمكنك فقط إضافة عقارات في المناطق المفعلة", size=10, color=WARNING_COLOR),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=8,
                    border_radius=8,
                ),
            ], spacing=8)),
            create_card(ft.Column([
                ft.Row([title_field]),
                ft.Row([rent_field]),
                ft.Row([desc_field]),
                ft.Row([services_field]),
            ], spacing=8)),
            create_card(ft.Column([
                ft.Row([lat_field, lon_field], spacing=5),
                ft.Text("اضغط على الخريطة لتحديد الموقع", size=11, color=ft.Colors.GREY_600),
                ft.Container(content=owner_map, height=200),
                ft.Row([open_maps_btn]),
            ], spacing=8)),
            ft.Container(content=add_btn, padding=10),
            ft.Container(content=msg, alignment=ft.alignment.center),
        ], scroll=ft.ScrollMode.ADAPTIVE)

        my_properties_tab = ft.Column([
            create_section_header("عقاراتي", ft.Icons.HOME),
            properties_list
        ], scroll=ft.ScrollMode.ADAPTIVE)

        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="إضافة عقار", icon=ft.Icons.ADD, content=add_property_tab),
                ft.Tab(text="عقاراتي", icon=ft.Icons.LIST, content=my_properties_tab),
            ],
            expand=True,
        )

        return ft.View(
            route="/owner",
            appbar=app_bar("لوحة المالك"),
            controls=[
                ft.Container(
                    content=tabs,
                    expand=True,
                    bgcolor=BACKGROUND_COLOR,
                )
            ],
        )

    # ---------- إدارة الـ Routes ----------

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        if page.route == "/login":
            page.views.append(login_view())
        elif page.route == "/user":
            page.views.append(user_view())
        elif page.route == "/owner":
            page.views.append(owner_view())
        else:
            page.go("/login")
            page.views.append(login_view())
        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    page.go("/login")


if __name__ == "__main__":
    # تشغيل التطبيق كتطبيق أندرويد
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,
        assets_dir="assets"
    )