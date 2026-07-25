from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import hmac
import secrets
import time
from functools import wraps
import os
import re
import sqlite3
from datetime import datetime

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# ===== КОНФИГ =====
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'tippi')

# ===== БАЗА ДАННЫХ =====
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dota2.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
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
        c.execute('''
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
        c.execute('CREATE INDEX IF NOT EXISTS idx_news_timestamp ON news(timestamp DESC)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        conn.commit()
        conn.close()
        print('✅ DB initialized')
        return True
    except Exception as e:
        print(f"DB init error: {e}")
        return False

init_db()

# ===== ФУНКЦИИ БД =====
def get_all_news():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM news ORDER BY timestamp DESC')
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except:
        return []

def add_news(title, content, type='update', link='', author='Admin'):
    try:
        conn = get_db()
        c = conn.cursor()
        preview = content[:300] + ('...' if len(content) > 300 else '')
        date = datetime.now().strftime('%d %B %Y')
        timestamp = int(datetime.now().timestamp() * 1000)
        c.execute('''
            INSERT INTO news (title, content, preview, type, date, link, author, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, content, preview, type, date, link, author, timestamp))
        news_id = c.lastrowid
        conn.commit()
        conn.close()
        return {'id': news_id, 'title': title, 'content': content}
    except:
        return None

def delete_news(news_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM news WHERE id = ?', (news_id,))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    except:
        return False

def add_user(username, email, password_hash):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
        ''', (username, email, password_hash))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return {'id': user_id, 'username': username, 'email': email, 'role': 'user'}
    except:
        return None

def get_user_by_username(username):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except:
        return None

def get_user_by_email(email):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except:
        return None

def delete_all_users():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM users')
        deleted = c.rowcount
        conn.commit()
        conn.close()
        return deleted
    except:
        return 0

def promote_to_admin(username):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE users SET role = ? WHERE username = ?', ('admin', username))
        updated = c.rowcount > 0
        conn.commit()
        conn.close()
        return updated
    except:
        return False

# ===== ПРОВЕРКА АДМИНА =====
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('X-Admin-Auth')
        if not auth:
            return jsonify({'error': 'Не авторизован'}), 401
        try:
            username, timestamp, signature = auth.split('|')
            if int(timestamp) < time.time() - 3600:
                return jsonify({'error': 'Сессия истекла'}), 401
            expected = hmac.new(SECRET_KEY.encode(), f"{username}|{timestamp}".encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                return jsonify({'error': 'Неверная подпись'}), 401
            user = get_user_by_username(username)
            if not user or user.get('role') != 'admin':
                return jsonify({'error': 'Недостаточно прав'}), 403
        except:
            return jsonify({'error': 'Неверный формат'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== СТРАНИЦЫ =====
@app.route('/')
def index():
    return send_from_directory('public', 'index.html')

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory('public/css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory('public/js', path)

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('public/assets', path)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('public', path)

# ===== API =====
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not email or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return jsonify({'error': 'Некорректный email'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Пароль должен быть минимум 6 символов'}), 400
    
    if get_user_by_username(username):
        return jsonify({'error': 'Пользователь с таким логином уже существует'}), 400
    
    if get_user_by_email(email):
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = add_user(username, email, password_hash)
    if not user:
        return jsonify({'error': 'Ошибка регистрации'}), 500
    
    timestamp = str(int(time.time()))
    signature = hmac.new(SECRET_KEY.encode(), f"{username}|{timestamp}".encode(), hashlib.sha256).hexdigest()
    token = f"{username}|{timestamp}|{signature}"
    
    return jsonify({
        'success': True,
        'token': token,
        'user': user,
        'message': 'Регистрация успешна!'
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email_or_username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not email_or_username or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    user = get_user_by_email(email_or_username)
    if not user:
        user = get_user_by_username(email_or_username)
    
    if not user:
        return jsonify({'error': 'Неверный логин/email или пароль'}), 401
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user['password_hash']:
        return jsonify({'error': 'Неверный логин/email или пароль'}), 401
    
    username = user['username']
    timestamp = str(int(time.time()))
    signature = hmac.new(SECRET_KEY.encode(), f"{username}|{timestamp}".encode(), hashlib.sha256).hexdigest()
    token = f"{username}|{timestamp}|{signature}"
    
    return jsonify({
        'success': True,
        'token': token,
        'user': user,
        'message': 'Вход выполнен!'
    })

@app.route('/api/verify', methods=['GET'])
def verify():
    auth = request.headers.get('X-Admin-Auth')
    if not auth:
        return jsonify({'valid': False}), 401
    try:
        username, timestamp, signature = auth.split('|')
        if int(timestamp) < time.time() - 3600:
            return jsonify({'valid': False}), 401
        expected = hmac.new(SECRET_KEY.encode(), f"{username}|{timestamp}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return jsonify({'valid': False}), 401
        user = get_user_by_username(username)
        if not user:
            return jsonify({'valid': False}), 401
        return jsonify({
            'valid': True,
            'username': username,
            'role': user['role']
        })
    except:
        return jsonify({'valid': False}), 401

@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(get_all_news())

@app.route('/api/news', methods=['POST'])
@admin_required
def add_news_route():
    data = request.json
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'error': 'Заголовок и текст обязательны'}), 400
    
    news = add_news(
        title=title,
        content=content,
        type=data.get('type', 'update'),
        link=data.get('link', ''),
        author='Admin'
    )
    return jsonify({'success': True, 'news': news})

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
@admin_required
def delete_news_route(news_id):
    deleted = delete_news(news_id)
    if deleted:
        return jsonify({'success': True})
    return jsonify({'error': 'Новость не найдена'}), 404

@app.route('/api/admin/clear_users', methods=['DELETE'])
@admin_required
def clear_users():
    deleted = delete_all_users()
    return jsonify({'success': True, 'deleted': deleted})

@app.route('/api/admin/promote', methods=['POST'])
@admin_required
def promote_user():
    data = request.json
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'error': 'Укажите username'}), 400
    success = promote_to_admin(username)
    if success:
        return jsonify({'success': True, 'message': f'Пользователь {username} стал админом'})
    return jsonify({'error': 'Пользователь не найден'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)