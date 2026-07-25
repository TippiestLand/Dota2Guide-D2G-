import psycopg2
import psycopg2.extras
from datetime import datetime
import os
import urllib.parse

# ===== ПОДКЛЮЧЕНИЕ К БД =====
def get_db_connection():
    """Подключение к PostgreSQL"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    if database_url:
        return psycopg2.connect(database_url)
    
    # Локальные настройки (если нет DATABASE_URL)
    return psycopg2.connect(
        dbname='dota2_guide',
        user='postgres',
        password='123456',
        host='localhost',
        port='5432'
    )

def init_db():
    """Создание таблиц"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                preview TEXT,
                type TEXT DEFAULT 'update',
                date TEXT NOT NULL,
                link TEXT,
                author TEXT DEFAULT 'Admin',
                timestamp BIGINT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news(timestamp DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_type ON news(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        
        conn.commit()
        conn.close()
        print('✅ Таблицы созданы в PostgreSQL')
        return True
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def get_all_news():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM news ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def add_news(title, content, type='update', link='', author='Admin'):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        preview = content[:300] + ('...' if len(content) > 300 else '')
        date = datetime.now().strftime('%d %B %Y')
        timestamp = int(datetime.now().timestamp() * 1000)
        
        cursor.execute('''
            INSERT INTO news (title, content, preview, type, date, link, author, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (title, content, preview, type, date, link, author, timestamp))
        
        news_id = cursor.fetchone()['id']
        conn.commit()
        conn.close()
        return get_news_by_id(news_id)
    except Exception as e:
        print(f"❌ Ошибка добавления: {e}")
        return None

def get_news_by_id(news_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM news WHERE id = %s', (news_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def delete_news(news_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM news WHERE id = %s', (news_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"❌ Ошибка удаления: {e}")
        return False

def add_user(username, email, password_hash):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, role
        ''', (username, email, password_hash))
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'role': row[3]
        }
    except Exception as e:
        print(f"❌ Ошибка добавления пользователя: {e}")
        return None

def get_user_by_username(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def get_user_by_email(email):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def delete_all_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users')
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 0

def promote_to_admin(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET role = %s WHERE username = %s', ('admin', username))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == '__main__':
    init_db()
    print('✅ База данных готова!')