from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import hmac
import secrets
import time
from functools import wraps
import database as db
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# ===== КОНФИГ =====
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'tippi')

# ===== ИНИЦИАЛИЗАЦИЯ БД =====
db.init_db()

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
            user = db.get_user_by_username(username)
            if not user or user.get('role') != 'admin':
                return jsonify({'error': 'Недостаточно прав'}), 403
        except:
            return jsonify({'error': 'Неверный формат'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== СТАТИКА =====
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
    # Если файл существует в public — отдаём
    if os.path.exists(os.path.join('public', path)):
        return send_from_directory('public', path)
    return jsonify({'error': 'Not found'}), 404

# ===== РЕГИСТРАЦИЯ =====
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
    
    if db.get_user_by_username(username):
        return jsonify({'error': 'Пользователь с таким логином уже существует'}), 400
    
    if db.get_user_by_email(email):
        return jsonify({'error': 'Пользователь с таким email уже существует'}), 400
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    user = db.add_user(username, email, password_hash)
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

# ===== ВХОД =====
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email_or_username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not email_or_username or not password:
        return jsonify({'error': 'Все поля обязательны'}), 400
    
    user = db.get_user_by_email(email_or_username)
    if not user:
        user = db.get_user_by_username(email_or_username)
    
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

# ===== ПРОВЕРКА ТОКЕНА =====
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
        user = db.get_user_by_username(username)
        if not user:
            return jsonify({'valid': False}), 401
        return jsonify({
            'valid': True,
            'username': username,
            'role': user['role']
        })
    except:
        return jsonify({'valid': False}), 401

# ===== НОВОСТИ =====
@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(db.get_all_news())

@app.route('/api/news', methods=['POST'])
@admin_required
def add_news():
    data = request.json
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'error': 'Заголовок и текст обязательны'}), 400
    
    news = db.add_news(
        title=title,
        content=content,
        type=data.get('type', 'update'),
        link=data.get('link', ''),
        author='Admin'
    )
    return jsonify({'success': True, 'news': news})

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
@admin_required
def delete_news(news_id):
    deleted = db.delete_news(news_id)
    if deleted:
        return jsonify({'success': True})
    return jsonify({'error': 'Новость не найдена'}), 404

# ===== АДМИН: ОЧИСТКА =====
@app.route('/api/admin/clear_users', methods=['DELETE'])
@admin_required
def clear_users():
    deleted = db.delete_all_users()
    return jsonify({'success': True, 'deleted': deleted})

# ===== АДМИН: ПОВЫШЕНИЕ =====
@app.route('/api/admin/promote', methods=['POST'])
@admin_required
def promote_user():
    data = request.json
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'error': 'Укажите username'}), 400
    success = db.promote_to_admin(username)
    if success:
        return jsonify({'success': True, 'message': f'Пользователь {username} стал админом'})
    return jsonify({'error': 'Пользователь не найден'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)