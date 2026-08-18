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
# ПАРСИНГ ОФИЦИАЛЬНОГО САЙТА DOTA 2
# ============================================================
def parse_dota2_official(hero_name):
    """Парсит данные героя с официального сайта Dota 2"""
    try:
        url = f'https://www.dota2.com/hero/{hero_name}'
        print(f"🌐 Парсинг официального сайта: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем скрипт с данными героя
        scripts = soup.find_all('script')
        hero_data = None
        
        for script in scripts:
            if script.string:
                # Ищем heroData в скриптах
                if 'heroData' in script.string:
                    try:
                        # Пытаемся найти JSON с данными
                        match = re.search(r'heroData\s*=\s*({.*?});', script.string, re.DOTALL)
                        if match:
                            hero_data = json.loads(match.group(1))
                            break
                    except:
                        pass
                
                # Альтернативный поиск
                if 'window.heroData' in script.string:
                    try:
                        match = re.search(r'window\.heroData\s*=\s*({.*?});', script.string, re.DOTALL)
                        if match:
                            hero_data = json.loads(match.group(1))
                            break
                    except:
                        pass
        
        if hero_data:
            print(f"✅ Найдены данные на официальном сайте для {hero_name}")
            return hero_data
        
        # Если не нашли через скрипты, пробуем парсить HTML
        return parse_dota2_html(soup, hero_name)
        
    except Exception as e:
        print(f"❌ Ошибка парсинга официального сайта: {e}")
        return None

def parse_dota2_html(soup, hero_name):
    """Парсит данные из HTML структуры официального сайта"""
    try:
        data = {}
        
        # Ищем имя героя
        name_elem = soup.find('h1', class_='hero-name')
        if name_elem:
            data['localized_name'] = name_elem.text.strip()
        
        # Ищем атрибут
        attr_elem = soup.find('div', class_='hero-attribute')
        if attr_elem:
            attr_text = attr_elem.text.strip().lower()
            if 'strength' in attr_text or 'сила' in attr_text:
                data['primary_attr'] = 'str'
            elif 'agility' in attr_text or 'ловкость' in attr_text:
                data['primary_attr'] = 'agi'
            elif 'intelligence' in attr_text or 'интеллект' in attr_text:
                data['primary_attr'] = 'int'
            else:
                data['primary_attr'] = 'universal'
        
        # Ищем тип атаки
        attack_elem = soup.find('div', class_='hero-attack-type')
        if attack_elem:
            attack_text = attack_elem.text.strip().lower()
            data['attack_type'] = 'Melee' if 'melee' in attack_text or 'ближний' in attack_text else 'Ranged'
        
        # Ищем статистику
        stats = {}
        stat_items = soup.find_all('div', class_='stat-item')
        for item in stat_items:
            label = item.find('span', class_='stat-label')
            value = item.find('span', class_='stat-value')
            if label and value:
                key = label.text.strip().upper()
                val = value.text.strip()
                if 'STR' in key or 'СИЛА' in key:
                    parts = val.split('+')
                    data['base_str'] = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                    data['str_gain'] = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                elif 'AGI' in key or 'ЛОВКОСТЬ' in key:
                    parts = val.split('+')
                    data['base_agi'] = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                    data['agi_gain'] = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                elif 'INT' in key or 'ИНТЕЛЛЕКТ' in key:
                    parts = val.split('+')
                    data['base_int'] = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                    data['int_gain'] = float(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
        
        # Ищем здоровье, ману, броню
        health_elem = soup.find('div', class_='hero-health')
        if health_elem:
            data['base_health'] = int(health_elem.text.strip()) if health_elem.text.strip().isdigit() else 0
        
        mana_elem = soup.find('div', class_='hero-mana')
        if mana_elem:
            data['base_mana'] = int(mana_elem.text.strip()) if mana_elem.text.strip().isdigit() else 0
        
        armor_elem = soup.find('div', class_='hero-armor')
        if armor_elem:
            data['base_armor'] = float(armor_elem.text.strip()) if armor_elem.text.strip() else 0
        
        # Ищем скорость
        speed_elem = soup.find('div', class_='hero-speed')
        if speed_elem:
            data['move_speed'] = int(speed_elem.text.strip()) if speed_elem.text.strip().isdigit() else 0
        
        # Ищем урон
        damage_elem = soup.find('div', class_='hero-damage')
        if damage_elem:
            damage_text = damage_elem.text.strip()
            if '-' in damage_text:
                parts = damage_text.split('-')
                data['base_attack_min'] = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                data['base_attack_max'] = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
        
        # Ищем описание
        bio_elem = soup.find('div', class_='hero-bio')
        if bio_elem:
            data['bio'] = bio_elem.text.strip()
        
        print(f"✅ Данные из HTML для {hero_name} загружены")
        return data
        
    except Exception as e:
        print(f"❌ Ошибка парсинга HTML: {e}")
        return None

def get_hero_data_official(hero_name):
    """Получает данные героя с официального сайта с кэшированием"""
    global HERO_CACHE
    
    cache_key = f"official_{hero_name}"
    if cache_key in HERO_CACHE:
        cache_time = HERO_CACHE[cache_key].get('cache_time', 0)
        if (time.time() - cache_time) < CACHE_DURATION:
            print(f"📦 Официальные данные {hero_name} из кэша")
            return HERO_CACHE[cache_key]
    
    data = parse_dota2_official(hero_name)
    if data:
        result = {
            'data': data,
            'abilities': [],
            'cache_time': time.time()
        }
        HERO_CACHE[cache_key] = result
        return result
    
    return None

# ============================================================
# OpenDota API (резервный источник)
# ============================================================
def get_heroes_list():
    """Получает список героев из OpenDota"""
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

def get_hero_data_opendota(hero_name):
    """Получает данные героя из OpenDota"""
    global HERO_CACHE
    
    if hero_name in HERO_CACHE:
        cache_time = HERO_CACHE[hero_name].get('cache_time', 0)
        if (time.time() - cache_time) < CACHE_DURATION:
            print(f"📦 Данные {hero_name} из кэша OpenDota")
            return HERO_CACHE[hero_name]
    
    heroes = get_heroes_list()
    stats = get_heroes_stats()
    
    hero_id = None
    for hero in heroes:
        if hero.get('name', '').lower() == f'npc_dota_hero_{hero_name}'.lower():
            hero_id = hero.get('id')
            break
        if hero.get('localized_name', '').lower() == hero_name.replace('_', ' ').lower():
            hero_id = hero.get('id')
            break
    
    if not hero_id:
        return None
    
    hero_stats = None
    for stat in stats:
        if stat.get('id') == hero_id:
            hero_stats = stat
            break
    
    if not hero_stats:
        return None
    
    abilities = []
    try:
        abilities_response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}/abilities', timeout=5)
        if abilities_response.status_code == 200:
            abilities = abilities_response.json()
            print(f"✅ Получено {len(abilities)} способностей для {hero_name}")
    except:
        pass
    
    result = {
        'data': hero_stats,
        'abilities': abilities,
        'cache_time': time.time()
    }
    
    HERO_CACHE[hero_name] = result
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
    
    # Сначала пробуем официальный сайт
    official_data = get_hero_data_official(hero_name)
    if official_data:
        print(f"✅ Отправляем официальные данные для {hero_name}")
        return jsonify(official_data)
    
    # Если официальные данные не получены - используем OpenDota
    print(f"⚠️ Официальные данные не найдены, используем OpenDota для {hero_name}")
    hero_data = get_hero_data_opendota(hero_name)
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