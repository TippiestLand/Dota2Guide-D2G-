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
HERO_CACHE = {}
HEROES_LIST_CACHE = None
HEROES_STATS_CACHE = None
HEROES_CACHE_TIME = 0
CACHE_DURATION = 86400  # 24 часа

# ============================================================
# ПАРСИНГ СПИСКА ГЕРОЕВ С DOTA2PROTRACKER.COM
# ============================================================
def parse_heroes_from_d2pt():
    """Парсит список героев с dota2protracker.com"""
    try:
        print("🌐 Парсинг списка героев с dota2protracker.com...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get('https://dota2protracker.com/heroes', headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем скрипт с данными
        scripts = soup.find_all('script')
        heroes_data = None
        
        for script in scripts:
            if script.string and 'heroes' in script.string and '[' in script.string:
                try:
                    # Ищем массив с героями
                    match = re.search(r'heroes\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                    if match:
                        heroes_data = json.loads(match.group(1))
                        break
                except:
                    pass
        
        if heroes_data:
            print(f"✅ Найдено {len(heroes_data)} героев на dota2protracker.com")
            return heroes_data
        
        # Если не нашли через скрипты, парсим HTML
        hero_elements = soup.find_all('a', class_='hero-link')
        heroes = []
        for elem in hero_elements:
            name = elem.text.strip()
            if name:
                heroes.append({'name': name})
        
        if heroes:
            print(f"✅ Найдено {len(heroes)} героев через HTML")
            return heroes
        
        return None
    except Exception as e:
        print(f"❌ Ошибка парсинга dota2protracker.com: {e}")
        return None

# ============================================================
# OpenDota API (основной источник статистики)
# ============================================================
def get_heroes_list():
    """Получает список героев из OpenDota (резерв)"""
    global HEROES_LIST_CACHE, HEROES_CACHE_TIME
    current_time = time.time()
    
    if HEROES_LIST_CACHE and (current_time - HEROES_CACHE_TIME) < CACHE_DURATION:
        print("📦 Список героев из кэша")
        return HEROES_LIST_CACHE
    
    # Сначала пробуем dota2protracker.com
    d2pt_heroes = parse_heroes_from_d2pt()
    if d2pt_heroes:
        HEROES_LIST_CACHE = d2pt_heroes
        HEROES_CACHE_TIME = current_time
        return HEROES_LIST_CACHE
    
    # Резерв - OpenDota
    try:
        print("📡 Запрос списка героев из OpenDota API...")
        response = requests.get('https://api.opendota.com/api/heroes', timeout=10)
        if response.status_code == 200:
            HEROES_LIST_CACHE = response.json()
            HEROES_CACHE_TIME = current_time
            print(f"✅ Получено {len(HEROES_LIST_CACHE)} героев из OpenDota")
            return HEROES_LIST_CACHE
    except Exception as e:
        print(f"❌ Ошибка загрузки списка героев: {e}")
    
    return HEROES_LIST_CACHE or []

def get_heroes_stats():
    """Получает статистику героев из OpenDota"""
    global HEROES_STATS_CACHE, HEROES_CACHE_TIME
    current_time = time.time()
    
    if HEROES_STATS_CACHE and (current_time - HEROES_CACHE_TIME) < CACHE_DURATION:
        print("📦 Статистика героев из кэша")
        return HEROES_STATS_CACHE
    
    try:
        print("📡 Запрос статистики героев из OpenDota API...")
        response = requests.get('https://api.opendota.com/api/heroStats', timeout=10)
        if response.status_code == 200:
            HEROES_STATS_CACHE = response.json()
            print(f"✅ Получена статистика для {len(HEROES_STATS_CACHE)} героев")
            return HEROES_STATS_CACHE
    except Exception as e:
        print(f"❌ Ошибка загрузки статистики: {e}")
    
    return HEROES_STATS_CACHE or []

def get_hero_data(hero_name):
    """Получает полные данные героя (статистика + способности)"""
    global HERO_CACHE
    
    if hero_name in HERO_CACHE:
        cache_time = HERO_CACHE[hero_name].get('cache_time', 0)
        if (time.time() - cache_time) < CACHE_DURATION:
            print(f"📦 Данные {hero_name} из кэша")
            return HERO_CACHE[hero_name]
    
    heroes = get_heroes_list()
    stats = get_heroes_stats()
    
    hero_id = None
    hero_info = None
    
    # Ищем героя в списке
    for hero in heroes:
        hero_api_name = hero.get('name', '').lower()
        hero_localized = hero.get('localized_name', '').lower()
        search_name = hero_name.replace('_', ' ').lower()
        
        if hero_api_name == f'npc_dota_hero_{hero_name}'.lower():
            hero_id = hero.get('id')
            hero_info = hero
            break
        if hero_localized == search_name:
            hero_id = hero.get('id')
            hero_info = hero
            break
        if hero_name.lower() in hero_api_name or hero_name.lower() in hero_localized:
            hero_id = hero.get('id')
            hero_info = hero
            break
    
    if not hero_id:
        print(f"❌ Герой {hero_name} не найден")
        return None
    
    # Ищем статистику героя
    hero_stats = None
    for stat in stats:
        if stat.get('id') == hero_id:
            hero_stats = stat
            break
    
    if not hero_stats:
        print(f"❌ Статистика для {hero_name} не найдена")
        return None
    
    # Добавляем недостающие поля
    hero_stats['localized_name'] = hero_info.get('localized_name', hero_name) if hero_info else hero_name
    hero_stats['icon'] = hero_name
    if hero_info:
        hero_stats['bio'] = hero_info.get('bio', 'Описание героя временно недоступно.')
        hero_stats['attack_type'] = hero_info.get('attack_type', 'Melee')
    
    # Получаем способности
    abilities = []
    try:
        abilities_response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}/abilities', timeout=5)
        if abilities_response.status_code == 200:
            abilities = abilities_response.json()
            print(f"✅ Получено {len(abilities)} способностей для {hero_name}")
    except Exception as e:
        print(f"⚠️ Не удалось получить способности: {e}")
    
    result = {
        'data': hero_stats,
        'abilities': abilities,
        'cache_time': time.time()
    }
    
    HERO_CACHE[hero_name] = result
    print(f"✅ Данные героя {hero_name} загружены")
    return result

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

@app.route('/api/heroes/list', methods=['GET'])
def get_heroes_list_api():
    heroes = get_heroes_list()
    result = []
    for hero in heroes:
        # Поддержка разных форматов данных
        if 'localized_name' in hero:
            name = hero.get('localized_name')
            icon = hero.get('name', '').replace('npc_dota_hero_', '') if hero.get('name') else name.lower().replace(' ', '_')
            primary_attr = hero.get('primary_attr', 'universal')
        else:
            name = hero.get('name', 'Unknown')
            icon = name.lower().replace(' ', '_')
            primary_attr = 'universal'
        
        result.append({
            'id': hero.get('id', 0),
            'name': name,
            'icon': icon,
            'primary_attr': primary_attr
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