#!/usr/bin/env python
"""Add a test user to the database for development"""
import sqlite3
import sys
sys.path.insert(0, '.')

# Import the auth module to get the correct password hashing
try:
    from auth import get_password_hash
    print("✅ Using backend's password hashing")
except ImportError as e:
    print(f"⚠️  Could not import auth: {e}")
    # Fallback - use a simple hash
    def get_password_hash(password):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

# Connect to SQLite database
db_path = './local_dev.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
if not cursor.fetchone():
    print("Creating users table...")
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR UNIQUE NOT NULL,
            name VARCHAR NOT NULL,
            hashed_password VARCHAR NOT NULL,
            total_xp INTEGER DEFAULT 0,
            total_points INTEGER DEFAULT 0,
            current_level INTEGER DEFAULT 1,
            current_streak INTEGER DEFAULT 0,
            global_rank INTEGER DEFAULT 0,
            study_time_today FLOAT DEFAULT 0,
            quizzes_completed INTEGER DEFAULT 0,
            badges_earned INTEGER DEFAULT 0,
            materials_uploaded INTEGER DEFAULT 0,
            study_sessions INTEGER DEFAULT 0,
            quiz_accuracy FLOAT DEFAULT 0.0,
            last_active_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

# Check existing users
cursor.execute("SELECT COUNT(*) FROM users;")
user_count = cursor.fetchone()[0]
print(f'Users in DB: {user_count}')

if user_count == 0:
    hashed_pwd = get_password_hash('password123')
    cursor.execute("""
        INSERT INTO users (email, name, hashed_password)
        VALUES (?, ?, ?)
    """, ('test@example.com', 'Test User', hashed_pwd))
    conn.commit()
    print('\n✅ Added test user:')
    print('   Email: test@example.com')
    print('   Password: password123')
    print('\nYou can now log in with these credentials!')
else:
    cursor.execute("SELECT email FROM users;")
    users = cursor.fetchall()
    print('\n✅ Users already exist:')
    for user in users:
        print(f'   - {user[0]}')

conn.close()
