"""
database.py
-----------
This file handles everything related to the SQLite database:
  1. Opening a connection to the database file.
  2. Creating all the tables the app needs (if they don't already exist).

We use Python's built-in "sqlite3" module. There is no separate database
server to install - SQLite simply stores everything in one file called
"rin_smart_bite.db" sitting next to this script.
"""

import sqlite3
import os

# Path to the SQLite database file (stored in the same folder as this file)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rin_smart_bite.db")


def get_db():
    """
    Open and return a connection to the database.

    row_factory = sqlite3.Row lets us access columns by name, e.g. row["name"],
    instead of only by numeric index, e.g. row[0]. This makes the rest of the
    code MUCH easier to read and explain.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Turn on foreign key checks so that, for example, an OrderItem always
    # points to a real Order and a real FoodItem.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Create every table used by RIN'S SMART BITE.

    "CREATE TABLE IF NOT EXISTS" means this function is safe to run every
    time the app starts - it will not wipe out existing data.
    """
    conn = get_db()
    cur = conn.cursor()

    # ---------------------------------------------------------------
    # USERS - customers, admins, and delivery partners all live here.
    # The "role" column tells us which type of user this is.
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',   -- customer, admin, delivery
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------------------------------------------------------
    # RESTAURANTS
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS restaurant (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cover_image TEXT,
            logo_image TEXT,
            cuisine TEXT,
            rating REAL DEFAULT 4.0,
            review_count INTEGER DEFAULT 0,
            price_for_two INTEGER DEFAULT 300,
            delivery_time INTEGER DEFAULT 30,     -- minutes
            delivery_fee INTEGER DEFAULT 30,
            distance_km REAL DEFAULT 2.0,
            address TEXT,
            opening_hours TEXT DEFAULT '9:00 AM - 11:00 PM',
            offer_text TEXT,
            description TEXT,
            is_veg_only INTEGER DEFAULT 0,
            is_open INTEGER DEFAULT 1,
            latitude REAL DEFAULT 11.0168,
            longitude REAL DEFAULT 76.9558
        )
    """)

    # ---------------------------------------------------------------
    # FOOD CATEGORIES (e.g. Biryani, Pizza, Desserts...)
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS food_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            image TEXT
        )
    """)

    # ---------------------------------------------------------------
    # FOOD ITEMS - the menu items belonging to a restaurant
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS food_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL,
            category_id INTEGER,
            menu_section TEXT DEFAULT 'Recommended',   -- e.g. Starters, Biryani, Desserts
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            image TEXT,
            rating REAL DEFAULT 4.0,
            is_veg INTEGER DEFAULT 1,
            calories INTEGER DEFAULT 250,
            prep_time INTEGER DEFAULT 15,
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (restaurant_id) REFERENCES restaurant (id),
            FOREIGN KEY (category_id) REFERENCES food_category (id)
        )
    """)

    # ---------------------------------------------------------------
    # CART + CART ITEMS
    # Each user has (at most) one active cart tied to one restaurant.
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            restaurant_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (restaurant_id) REFERENCES restaurant (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id INTEGER NOT NULL,
            food_item_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            size TEXT DEFAULT 'Regular',
            extras TEXT DEFAULT '',            -- comma separated extra names
            extras_price INTEGER DEFAULT 0,
            special_instructions TEXT DEFAULT '',
            FOREIGN KEY (cart_id) REFERENCES cart (id),
            FOREIGN KEY (food_item_id) REFERENCES food_item (id)
        )
    """)

    # ---------------------------------------------------------------
    # ADDRESS
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS address (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            address_type TEXT DEFAULT 'HOME',   -- HOME, WORK, OTHER
            full_name TEXT,
            phone TEXT,
            house_no TEXT,
            street TEXT,
            area TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            landmark TEXT,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    """)

    # ---------------------------------------------------------------
    # FAVORITES (a user can favorite a restaurant or a food item)
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS favorite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            restaurant_id INTEGER,
            food_item_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    """)

    # ---------------------------------------------------------------
    # COUPONS
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS coupon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            description TEXT,
            discount_type TEXT DEFAULT 'PERCENT',   -- PERCENT or FLAT
            discount_value INTEGER DEFAULT 10,
            max_discount INTEGER DEFAULT 100,
            min_order_value INTEGER DEFAULT 0,
            expiry_date TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    # ---------------------------------------------------------------
    # OFFERS (marketing banners shown on the Offers page)
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS offer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            coupon_code TEXT,
            image TEXT
        )
    """)

    # ---------------------------------------------------------------
    # ORDERS + ORDER ITEMS
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS "order" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT UNIQUE,
            user_id INTEGER NOT NULL,
            restaurant_id INTEGER NOT NULL,
            address_id INTEGER,
            item_total INTEGER DEFAULT 0,
            delivery_fee INTEGER DEFAULT 0,
            platform_fee INTEGER DEFAULT 0,
            taxes INTEGER DEFAULT 0,
            discount INTEGER DEFAULT 0,
            coupon_code TEXT,
            grand_total INTEGER DEFAULT 0,
            status TEXT DEFAULT 'placed',
            delivery_partner_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (restaurant_id) REFERENCES restaurant (id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            food_item_id INTEGER NOT NULL,
            food_name TEXT,
            quantity INTEGER DEFAULT 1,
            unit_price INTEGER DEFAULT 0,
            size TEXT DEFAULT 'Regular',
            extras TEXT DEFAULT '',
            FOREIGN KEY (order_id) REFERENCES "order" (id)
        )
    """)

    # ---------------------------------------------------------------
    # PAYMENT
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            transaction_id TEXT,
            method TEXT,            -- UPI, CARD, COD
            amount INTEGER,
            status TEXT DEFAULT 'success',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES "order" (id)
        )
    """)

    # ---------------------------------------------------------------
    # DELIVERY PARTNERS
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS delivery_partner (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            rating REAL DEFAULT 4.7,
            vehicle_type TEXT DEFAULT 'Bike',
            vehicle_number TEXT,
            avatar TEXT
        )
    """)

    # ---------------------------------------------------------------
    # DELIVERY TRACKING - one row per order, holding the simulated
    # GPS position of the delivery partner as the order moves along.
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS delivery_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER UNIQUE NOT NULL,
            current_lat REAL,
            current_lng REAL,
            distance_remaining_km REAL,
            eta_minutes INTEGER,
            step_index INTEGER DEFAULT 0,     -- how far along the route we are
            FOREIGN KEY (order_id) REFERENCES "order" (id)
        )
    """)

    # ---------------------------------------------------------------
    # NOTIFICATIONS
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------------------------------------------------------------
    # REVIEWS
    # ---------------------------------------------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            restaurant_id INTEGER,
            restaurant_rating INTEGER,
            food_rating INTEGER,
            delivery_rating INTEGER,
            comment TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
