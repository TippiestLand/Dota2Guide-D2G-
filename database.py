import sqlite3
from datetime import datetime
import os

# ===== ПУТЬ К БД =====
# На Render используем папку data
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dota2.db')

# Создаём папку data если её нет
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                preview TEXT,
                type TEXT DEFAULT 'update',
                date TEXT NOT NULL,
                link TEXT,
                author TEXT DEFAULT 'Admin',
                timestamp INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        conn.commit()
        conn.close()
        print('✅ Таблицы созданы в SQLite')
        return True
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def get_all_news():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM news ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def add_news(title, content, type='update', link='', author='Admin'):
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        preview = content[:300] + ('...' if len(content) > 300 else '')
        date = datetime.now().strftime('%d %B %Y')
        timestamp = int(datetime.now().timestamp() * 1000)
        
        cursor.execute('''
            INSERT INTO news (title, content, preview, type, date, link, author, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, preview, type, date, link, author, timestamp))
        
        news_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return get_news_by_id(news_id)
    except Exception as e:
        print(f"❌ Ошибка добавления: {e}")
        return None

def get_news_by_id(news_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM news WHERE id = ?', (news_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def delete_news(news_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM news WHERE id = ?', (news_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        return False

def add_user(username, email, password_hash):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'id': user_id,
            'username': username,
            'email': email,
            'role': 'user'
        }
    except sqlite3.IntegrityError:
        return None
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")
        return None

def get_user_by_username(username):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        return None

def get_user_by_email(email):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        return None

def delete_all_users():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        return 0

def promote_to_admin(username):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = ? WHERE username = ?', ('admin', username))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except Exception as e:
        return False

if __name__ == '__main__':
    init_db()
    print('✅ База данных SQLite готова!')