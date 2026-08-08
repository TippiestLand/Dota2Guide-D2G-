from flask import Flask, render_template, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
import os
import json
import hashlib
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import html
import time

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

MSK = timezone(timedelta(hours=3))

# ============================================================
# КЭШ ГЕРОЕВ (обновляется раз в сутки)
# ============================================================
HERO_CACHE = {}
HEROES_LIST_CACHE = None
HEROES_CACHE_TIME = 0
CACHE_DURATION = 86400  # 24 часа

def get_heroes_list():
    """Получает список героев с кэшированием"""
    global HEROES_LIST_CACHE, HEROES_CACHE_TIME
    current_time = time.time()
    
    if HEROES_LIST_CACHE and (current_time - HEROES_CACHE_TIME) < CACHE_DURATION:
        print("📦 Список героев из кэша")
        return HEROES_LIST_CACHE
    
    try:
        print("📡 Запрос списка героев из OpenDota API...")
        response = requests.get('https://api.opendota.com/api/heroes', timeout=10)
        if response.status_code == 200:
            HEROES_LIST_CACHE = response.json()
            HEROES_CACHE_TIME = current_time
            print(f"✅ Получено {len(HEROES_LIST_CACHE)} героев")
            return HEROES_LIST_CACHE
    except Exception as e:
        print(f"❌ Ошибка загрузки списка героев: {e}")
    
    return HEROES_LIST_CACHE or []

def get_hero_data(hero_name):
    """Получает полные данные героя с кэшированием"""
    global HERO_CACHE
    
    if hero_name in HERO_CACHE:
        cache_time = HERO_CACHE[hero_name].get('cache_time', 0)
        if (time.time() - cache_time) < CACHE_DURATION:
            print(f"📦 Данные {hero_name} из кэша")
            return HERO_CACHE[hero_name]
    
    heroes = get_heroes_list()
    hero_id = None
    
    # Ищем героя по имени
    for hero in heroes:
        if hero.get('name', '').lower() == f'npc_dota_hero_{hero_name}'.lower():
            hero_id = hero.get('id')
            break
        if hero.get('localized_name', '').lower() == hero_name.replace('_', ' ').lower():
            hero_id = hero.get('id')
            break
    
    if not hero_id:
        print(f"❌ Герой {hero_name} не найден")
        return None
    
    try:
        print(f"🆔 ID героя {hero_name}: {hero_id}")
        
        # Получаем данные героя
        response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}', timeout=10)
        if response.status_code != 200:
            return None
        
        hero_data = response.json()
        
        # Получаем способности
        abilities_response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}/abilities', timeout=10)
        abilities = abilities_response.json() if abilities_response.status_code == 200 else []
        
        # Добавляем локальное имя для иконки
        hero_data['icon'] = hero_name
        
        result = {
            'data': hero_data,
            'abilities': abilities,
            'cache_time': time.time()
        }
        
        HERO_CACHE[hero_name] = result
        print(f"✅ Данные героя {hero_name} загружены")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка загрузки данных героя {hero_name}: {e}")
        return None

# ============================================================
# МАРШРУТЫ
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(load_news())

@app.route('/api/heroes/list', methods=['GET'])
def get_heroes_list_api():
    """Возвращает список всех героев для фронтенда"""
    heroes = get_heroes_list()
    # Форматируем для фронтенда
    result = []
    for hero in heroes:
        result.append({
            'id': hero.get('id'),
            'name': hero.get('localized_name'),
            'icon': hero.get('name', '').replace('npc_dota_hero_', ''),
            'primary_attr': hero.get('primary_attr', 'universal')
        })
    return jsonify(result)

@app.route('/api/hero/<hero_name>')
def api_hero(hero_name):
    print(f"🔍 API запрос героя: {hero_name}")
    
    hero_data = get_hero_data(hero_name)
    if not hero_data:
        return jsonify({'error': 'Hero not found'}), 404
    
    return jsonify(hero_data)

# ============================================================
# НОВОСТИ (как было)
# ============================================================
NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'

os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)

if not os.path.exists(NEWS_FILE):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

def load_news():
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_news(news):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)

def translate_title(title):
    translations = {
        'Gameplay Update': 'Игровое обновление',
        'Gameplay Patch': 'Игровой патч',
        'Patch': 'Патч',
        'Update': 'Обновление',
        'Release': 'Релиз',
        'Announcement': 'Объявление',
        'Event': 'Событие',
        'Tournament': 'Турнир',
        'New Hero': 'Новый герой',
        'Balance': 'Баланс',
        'Fix': 'Исправление',
        'Hotfix': 'Срочное исправление',
    }
    for eng, rus in translations.items():
        if eng in title:
            return title.replace(eng, rus)
    return title

def fetch_rss_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        news_items = []
        for item in root.findall('.//item')[:15]:
            title_element = item.find('title')
            title_text = title_element.text if title_element is not None else 'Без названия'
            title_text = translate_title(title_text)
            pub_date_element = item.find('pubDate')
            pub_date_text = pub_date_element.text if pub_date_element is not None else ''
            link_element = item.find('link')
            link_text = link_element.text if link_element is not None else ''
            description_element = item.find('description')
            desc_text = description_element.text if description_element is not None else title_text
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            desc_clean = desc_clean[:500] + '...' if len(desc_clean) > 500 else desc_clean
            
            hash_id = int(hashlib.md5(title_text.encode('utf-8')).hexdigest()[:8], 16)
            news_items.append({
                'id': hash_id,
                'title': title_text,
                'date': datetime.now(MSK).strftime('%d %B %Y, %H:%M МСК'),
                'content': desc_clean,
                'link': link_text,
                'source': 'rss'
            })
        return news_items
    except Exception as e:
        print(f"Ошибка при получении RSS: {e}")
        return []

def initialize_news():
    print("=" * 60)
    print("🚀 ИНИЦИАЛИЗАЦИЯ НОВОСТЕЙ")
    print("=" * 60)
    existing = load_news()
    print(f"📰 Существующих новостей: {len(existing)}")
    if len(existing) > 0:
        print("✅ Новости уже есть")
        return
    print("📝 Загружаем свежие из RSS...")
    rss_news = fetch_rss_news()
    if rss_news:
        save_news(rss_news)
        print(f"✅ Добавлено {len(rss_news)} новостей")
    print("=" * 60)

initialize_news()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)