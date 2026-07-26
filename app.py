from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import hashlib
import hmac
import secrets
import time
from datetime import datetime
import requests
import xml.etree.ElementTree as ET
from functools import wraps
import re

# ===== ПРАВИЛЬНАЯ НАСТРОЙКА FLASK =====
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

# ===== КОНФИГ =====
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'tippi')
ADMIN_PASSWORD_HASH = hashlib.sha256('admin123'.encode()).hexdigest()
NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'

# Создаём папку data если её нет
os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)

# Создаём news.json если его нет
if not os.path.exists(NEWS_FILE):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# ===== РАБОТА С JSON =====
def load_news():
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_news(news):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)

# ===== RSS =====
def fetch_rss_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        root = ET.fromstring(response.content)
        news_items = []
        
        for item in root.findall('.//item')[:15]:
            title = item.find('title')
            title_text = title.text if title is not None else 'Без названия'
            
            pub_date = item.find('pubDate')
            date_text = pub_date.text if pub_date is not None else datetime.now().strftime('%d %B %Y')
            
            link = item.find('link')
            link_text = link.text if link is not None else ''
            
            description = item.find('description')
            desc_text = description.text if description is not None else title_text
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            desc_clean = desc_clean[:500] + '...' if len(desc_clean) > 500 else desc_clean
            
            try:
                date_obj = datetime.strptime(pub_date.text, '%a, %d %b %Y %H:%M:%S %Z')
                date_formatted = date_obj.strftime('%d %B %Y')
            except:
                date_formatted = date_text
            
            news_items.append({
                'id': int(datetime.now().timestamp() * 1000) + len(news_items),
                'title': title_text,
                'date': date_formatted,
                'type': 'update',
                'preview': desc_clean,
                'content': desc_clean,
                'link': link_text,
                'author': 'Valve',
                'timestamp': int(datetime.now().timestamp() * 1000),
                'source': 'rss',
                'rss_title': title_text
            })
        
        return news_items
    except Exception as e:
        print(f"RSS error: {e}")
        return []

def update_news_from_rss():
    existing = load_news()
    manual_news = [n for n in existing if n.get('source') != 'rss']
    rss_news = fetch_rss_news()
    if not rss_news:
        return 0
    rss_titles = {n['rss_title'] for n in rss_news}
    existing_rss = [n for n in existing if n.get('source') == 'rss' and n.get('rss_title') in rss_titles]
    existing_rss_titles = {n.get('rss_title') for n in existing_rss}
    new_items = [n for n in rss_news if n['rss_title'] not in existing_rss_titles]
    updated_news = new_items + existing_rss + manual_news
    updated_news.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    save_news(updated_news)
    return len(new_items)

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
            if not hmac.compare_digest(signature, expected) or username != ADMIN_USERNAME:
                return jsonify({'error': 'Неверная подпись'}), 401
        except:
            return jsonify({'error': 'Неверный формат'}), 401
        return f(*args, **kwargs)
    return decorated

# ===== СТРАНИЦЫ =====
@app.route('/')
def index():
    return render_template('index.html')

# ===== API: ВХОД =====
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if username != ADMIN_USERNAME:
        return jsonify({'error': 'Неверный логин'}), 401
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != ADMIN_PASSWORD_HASH:
        return jsonify({'error': 'Неверный пароль'}), 401
    
    timestamp = str(int(time.time()))
    signature = hmac.new(SECRET_KEY.encode(), f"{username}|{timestamp}".encode(), hashlib.sha256).hexdigest()
    token = f"{username}|{timestamp}|{signature}"
    
    return jsonify({'token': token, 'username': username})

@app.route('/api/admin/verify', methods=['GET'])
@admin_required
def admin_verify():
    return jsonify({'valid': True})

# ===== API: НОВОСТИ =====
@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(load_news())

@app.route('/api/news', methods=['POST'])
@admin_required
def add_news():
    data = request.json
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not title or not content:
        return jsonify({'error': 'Заголовок и текст обязательны'}), 400
    
    news = load_news()
    new_item = {
        'id': int(time.time() * 1000),
        'title': title,
        'date': datetime.now().strftime('%d %B %Y'),
        'type': data.get('type', 'update'),
        'preview': content[:300] + ('...' if len(content) > 300 else ''),
        'content': content,
        'link': data.get('link', ''),
        'author': 'Admin',
        'timestamp': int(datetime.now().timestamp() * 1000),
        'source': 'manual'
    }
    news.insert(0, new_item)
    save_news(news)
    return jsonify({'success': True, 'news': new_item})

@app.route('/api/news/<int:news_id>', methods=['DELETE'])
@admin_required
def delete_news(news_id):
    news = load_news()
    news = [n for n in news if n.get('id') != news_id]
    save_news(news)
    return jsonify({'success': True})

@app.route('/api/admin/update_rss', methods=['POST'])
@admin_required
def update_rss():
    count = update_news_from_rss()
    return jsonify({'success': True, 'added': count})

if __name__ == '__main__':
    try:
        count = update_news_from_rss()
        print(f"📰 Загружено {count} новых RSS новостей")
    except:
        print("⚠️ RSS не загрузился")
    app.run(host='0.0.0.0', port=8000)