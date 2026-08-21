from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import hashlib
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import time
from bs4 import BeautifulSoup

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

MSK = timezone(timedelta(hours=3))

# ============================================================
# КЭШ
# ============================================================
CACHE = {}
CACHE_TIME = {}
CACHE_DURATION = 86400  # 24 часа

def get_cache(key):
    if key in CACHE and (time.time() - CACHE_TIME.get(key, 0)) < CACHE_DURATION:
        return CACHE[key]
    return None

def set_cache(key, value):
    CACHE[key] = value
    CACHE_TIME[key] = time.time()

# ============================================================
# ПРОКСИ К NODE.JS СЕРВЕРУ ДЛЯ ПАТЧЕЙ
# ============================================================
PATCHES_API_URL = os.environ.get('PATCHES_API_URL', 'http://localhost:5001')

def get_patches_from_node():
    """Получает данные о патчах через Node.js сервер"""
    try:
        print(f"📡 Запрос патчей к Node.js серверу: {PATCHES_API_URL}/api/patches/latest/10")
        response = requests.get(f'{PATCHES_API_URL}/api/patches/latest/10', timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Получено {len(data)} патчей из Node.js")
            return data
        else:
            print(f"❌ Node.js сервер вернул ошибку: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к Node.js серверу")
        return None
    except Exception as e:
        print(f"❌ Ошибка при запросе к Node.js: {e}")
        return None

# ============================================================
# РЕАЛЬНЫЕ ДАННЫЕ ПАТЧЕЙ (ФОЛБЭК, ЕСЛИ NODE.JS НЕ ДОСТУПЕН)
# ============================================================
def get_fallback_patches():
    """Возвращает тестовые данные, если Node.js сервер недоступен"""
    return [
        {
            'version': '7.41e',
            'date': '31 July 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+6.0', 'detail': 'Базовая атака увеличена на 6', 'ability': 'Base Attack'},
                {'hero': 'Juggernaut', 'change': '+4.4', 'detail': 'Базовая атака увеличена на 4.4', 'ability': 'Base Attack'},
                {'hero': 'Lina', 'change': '+3.3', 'detail': 'Dragon Slave урон увеличен с 120 до 135', 'ability': 'Dragon Slave'},
                {'hero': 'Shadow Fiend', 'change': '+2.7', 'detail': 'Shadowraze урон увеличен с 90 до 100', 'ability': 'Shadowraze'},
                {'hero': 'Treant Protector', 'change': '+2.7', 'detail': 'Living Armor блок урона увеличен', 'ability': 'Living Armor'},
                {'hero': 'Phantom Assassin', 'change': '+2.6', 'detail': 'Blur теперь нельзя развеять', 'ability': 'Blur'}
            ],
            'item_changes': [
                {'item': 'Mage Slayer', 'old': '20', 'new': '15', 'detail': 'Урон уменьшен с 20 до 15'},
                {'item': 'Shadow Blade', 'old': '30', 'new': '25', 'detail': 'Скорость атаки уменьшена с 30 до 25'},
                {'item': 'Harpoon', 'detail': 'Больше не перемещает закованных существ'}
            ],
            'neutral_item_changes': [
                {'item': 'Spellover', 'detail': 'Добавлена внутренняя перезарядка 0.1с'},
                {'item': 'False Flight', 'old': '5', 'new': '6.5', 'detail': 'Длительность увеличена с 5 до 6.5 секунд'},
                {'item': 'Reverberate', 'old': '110', 'new': '90', 'detail': 'Урон уменьшен с 110 до 90'}
            ]
        },
        {
            'version': '7.41d',
            'date': '5 June 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Meepo', 'change': '-3.2', 'detail': 'Poof урон уменьшен с 80 до 60', 'ability': 'Poof'},
                {'hero': 'Ember Spirit', 'change': '-2.1', 'detail': 'Flame Guard урон уменьшен с 50 до 40', 'ability': 'Flame Guard'},
                {'hero': 'Beastmaster', 'change': '-1.8', 'detail': 'Wild Axes урон уменьшен с 70 до 55', 'ability': 'Wild Axes'}
            ],
            'item_changes': [],
            'neutral_item_changes': []
        },
        {
            'version': '7.41',
            'date': '25 March 2026',
            'type': 'major',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+5.0', 'detail': 'Aghanims Scepter: сжигание маны улучшено', 'ability': 'Aghanims'},
                {'hero': 'Tinker', 'change': 'NEW', 'detail': 'Добавлена новая способность - турель', 'ability': 'New Ability'},
                {'hero': 'Omniknight', 'change': 'REWORK', 'detail': 'Guardian Angel переработан в персональную ауру', 'ability': 'Guardian Angel'}
            ],
            'item_changes': [
                {'item': 'Chasm Stone', 'detail': 'Новый предмет добавлен'},
                {'item': 'Shawl', 'detail': 'Новый предмет добавлен'},
                {'item': 'Splintmail', 'detail': 'Новый предмет добавлен'},
                {'item': 'Wizard Hat', 'detail': 'Новый предмет добавлен'}
            ],
            'neutral_item_changes': [
                {'item': 'Tier 1', 'old': '7:00', 'new': '0:00', 'detail': 'Доступность изменена с 7:00 на 0:00'}
            ]
        }
    ]

# ============================================================
# МАРШРУТЫ
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(load_news())

@app.route('/api/patches', methods=['GET'])
def get_patches():
    """Возвращает список патчей через Node.js сервер"""
    patches = get_cache('patches')
    if not patches:
        patches = get_patches_from_node()
        if patches:
            set_cache('patches', patches)
            print(f"✅ Патчи получены из Node.js и закэшированы")
        else:
            print("⚠️ Node.js недоступен, используем фолбэк данные")
            patches = get_fallback_patches()
            set_cache('patches', patches)
    return jsonify(patches)

@app.route('/api/heroes/list', methods=['GET'])
def get_heroes_list_api():
    heroes = get_heroes_list()
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
# OpenDota API
# ============================================================
def get_heroes_list():
    try:
        response = requests.get('https://api.opendota.com/api/heroes', timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def get_heroes_stats():
    try:
        response = requests.get('https://api.opendota.com/api/heroStats', timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def get_hero_data(hero_name):
    stats = get_heroes_stats()
    for stat in stats:
        if stat.get('name', '').lower() == f'npc_dota_hero_{hero_name}'.lower():
            stat['icon'] = hero_name
            stat['bio'] = 'Описание героя временно недоступно.'
            abilities = []
            hero_id = stat.get('id')
            if hero_id:
                try:
                    abilities_response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}/abilities', timeout=5)
                    if abilities_response.status_code == 200:
                        abilities = abilities_response.json()
                except:
                    pass
            return {'data': stat, 'abilities': abilities}
    return None

# ============================================================
# НОВОСТИ
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

def format_news_content(text):
    lines = text.split('\n')
    html_parts = []
    in_list = False
    list_items = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_parts.append('<ul>\n' + '\n'.join(list_items) + '\n</ul>')
                list_items = []
                in_list = False
            html_parts.append('<br>')
            continue
        
        is_list_item = False
        clean_text = line
        if line.startswith('• ') or line.startswith('- ') or line.startswith('* ') or line.startswith('— '):
            is_list_item = True
            clean_text = line[2:]
        elif line.startswith('Fixed'):
            is_list_item = True
            clean_text = 'Исправлено: ' + line[6:]
        
        if is_list_item:
            if not in_list:
                in_list = True
                list_items = []
            list_items.append('  <li>' + clean_text + '</li>')
        else:
            if in_list:
                html_parts.append('<ul>\n' + '\n'.join(list_items) + '\n</ul>')
                list_items = []
                in_list = False
            html_parts.append('<p>' + clean_text + '</p>')
    
    if in_list:
        html_parts.append('<ul>\n' + '\n'.join(list_items) + '\n</ul>')
    
    return '\n'.join(html_parts)

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
            if pub_date_element is not None and pub_date_element.text:
                try:
                    date_obj = datetime.strptime(pub_date_element.text, '%a, %d %b %Y %H:%M:%S %Z')
                    date_formatted = date_obj.strftime('%d %B %Y, %H:%M МСК')
                except:
                    date_formatted = datetime.now(MSK).strftime('%d %B %Y, %H:%M МСК')
            else:
                date_formatted = datetime.now(MSK).strftime('%d %B %Y, %H:%M МСК')
            
            link_element = item.find('link')
            link_text = link_element.text if link_element is not None else ''
            
            description_element = item.find('description')
            desc_text = description_element.text if description_element is not None else title_text
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            content_html = format_news_content(desc_clean)
            
            hash_id = int(hashlib.md5(title_text.encode('utf-8')).hexdigest()[:8], 16)
            
            news_items.append({
                'id': hash_id,
                'title': title_text,
                'date': date_formatted,
                'content': content_html,
                'link': link_text,
                'source': 'rss',
                'timestamp': int(datetime.now().timestamp() * 1000)
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
        print("✅ Новости уже есть, пропускаем загрузку")
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