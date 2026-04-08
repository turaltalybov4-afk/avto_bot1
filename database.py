import sqlite3

import config

conn = sqlite3.connect(config.DATABASE_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS clients (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT,
    car_brand TEXT,
    car_model TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service TEXT,
    date TEXT,
    time TEXT,
    status TEXT,
    comment TEXT,
    service_price INTEGER DEFAULT 0,
    upsell_details TEXT DEFAULT '',
    upsell_total INTEGER DEFAULT 0,
    total_price INTEGER DEFAULT 0,
    reminder_24_sent INTEGER DEFAULT 0,
    reminder_2_sent INTEGER DEFAULT 0
)
""")

# Backward-compatible migration for existing databases.
cursor.execute("PRAGMA table_info(bookings)")
booking_columns = {row[1] for row in cursor.fetchall()}

if "reminder_24_sent" not in booking_columns:
    cursor.execute("ALTER TABLE bookings ADD COLUMN reminder_24_sent INTEGER DEFAULT 0")

if "reminder_2_sent" not in booking_columns:
    cursor.execute("ALTER TABLE bookings ADD COLUMN reminder_2_sent INTEGER DEFAULT 0")

if "service_price" not in booking_columns:
    cursor.execute("ALTER TABLE bookings ADD COLUMN service_price INTEGER DEFAULT 0")

if "upsell_details" not in booking_columns:
    cursor.execute("ALTER TABLE bookings ADD COLUMN upsell_details TEXT DEFAULT ''")

if "upsell_total" not in booking_columns:
    cursor.execute("ALTER TABLE bookings ADD COLUMN upsell_total INTEGER DEFAULT 0")

if "total_price" not in booking_columns:
    cursor.execute("ALTER TABLE bookings ADD COLUMN total_price INTEGER DEFAULT 0")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    service TEXT,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS app_meta (
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    client_name TEXT,
    username TEXT,
    request_text TEXT,
    quantity TEXT,
    preferred_date TEXT,
    contact TEXT,
    comment TEXT,
    status TEXT DEFAULT 'new',
    created_at TEXT
)
""")

conn.commit()