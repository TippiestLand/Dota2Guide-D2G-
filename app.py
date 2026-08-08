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

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

MSK = timezone(timedelta(hours=3))

# ============================================================
# КЭШ ГЕРОЕВ
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

def get_hero_stats(hero_id):
    """Получает детальную статистику героя из другого источника"""
    try:
        # Пробуем получить данные через /api/heroStats
        response = requests.get(f'https://api.opendota.com/api/heroStats', timeout=10)
        if response.status_code == 200:
            stats = response.json()
            for hero in stats:
                if hero.get('id') == hero_id:
                    return hero
    except Exception as e:
        print(f"⚠️ Ошибка получения heroStats: {e}")
    return None

def get_hero_data(hero_name):
    """Получает полные данные героя с кэшированием"""
    global HERO_CACHE
    
    # Проверяем кэш
    if hero_name in HERO_CACHE:
        cache_time = HERO_CACHE[hero_name].get('cache_time', 0)
        if (time.time() - cache_time) < CACHE_DURATION:
            print(f"📦 Данные {hero_name} из кэша")
            return HERO_CACHE[hero_name]
    
    heroes = get_heroes_list()
    hero_info = None
    hero_id = None
    
    # Ищем героя по имени
    for hero in heroes:
        hero_api_name = hero.get('name', '').lower()
        hero_localized = hero.get('localized_name', '').lower()
        search_name = hero_name.replace('_', ' ').lower()
        
        if hero_api_name == f'npc_dota_hero_{hero_name}'.lower():
            hero_info = hero
            hero_id = hero.get('id')
            break
        if hero_localized == search_name:
            hero_info = hero
            hero_id = hero.get('id')
            break
        if hero_name.lower() in hero_api_name or hero_name.lower() in hero_localized:
            hero_info = hero
            hero_id = hero.get('id')
            break
    
    if not hero_info:
        print(f"❌ Герой {hero_name} не найден в списке")
        return None
    
    print(f"🆔 ID героя {hero_name}: {hero_id}")
    
    try:
        # Пытаемся получить детальную статистику
        hero_stats = get_hero_stats(hero_id)
        
        # Используем данные из списка героев как основу
        detailed_data = hero_info.copy()
        
        # Если есть статистика - обновляем данные
        if hero_stats:
            print(f"✅ Получена статистика для {hero_name}")
            detailed_data.update(hero_stats)
        
        # Добавляем все необходимые поля (если их нет)
        detailed_data['base_str'] = detailed_data.get('base_str', detailed_data.get('base_str', 0))
        detailed_data['base_agi'] = detailed_data.get('base_agi', detailed_data.get('base_agi', 0))
        detailed_data['base_int'] = detailed_data.get('base_int', detailed_data.get('base_int', 0))
        detailed_data['str_gain'] = detailed_data.get('str_gain', detailed_data.get('str_gain', 0))
        detailed_data['agi_gain'] = detailed_data.get('agi_gain', detailed_data.get('agi_gain', 0))
        detailed_data['int_gain'] = detailed_data.get('int_gain', detailed_data.get('int_gain', 0))
        detailed_data['base_health'] = detailed_data.get('base_health', detailed_data.get('base_health', 200))
        detailed_data['base_mana'] = detailed_data.get('base_mana', detailed_data.get('base_mana', 75))
        detailed_data['base_armor'] = detailed_data.get('base_armor', detailed_data.get('base_armor', 0))
        detailed_data['move_speed'] = detailed_data.get('move_speed', detailed_data.get('move_speed', 300))
        detailed_data['attack_range'] = detailed_data.get('attack_range', detailed_data.get('attack_range', 150))
        detailed_data['attack_rate'] = detailed_data.get('attack_rate', detailed_data.get('attack_rate', 1.7))
        detailed_data['base_attack_min'] = detailed_data.get('base_attack_min', detailed_data.get('base_attack_min', 20))
        detailed_data['base_attack_max'] = detailed_data.get('base_attack_max', detailed_data.get('base_attack_max', 30))
        detailed_data['attack_type'] = detailed_data.get('attack_type', 'Melee')
        detailed_data['primary_attr'] = detailed_data.get('primary_attr', 'universal')
        detailed_data['localized_name'] = detailed_data.get('localized_name', hero_name)
        detailed_data['bio'] = detailed_data.get('bio', 'Описание героя временно недоступно.')
        detailed_data['icon'] = hero_name
        detailed_data['roles'] = detailed_data.get('roles', [])
        
        # Пытаемся получить способности
        abilities = []
        try:
            abilities_response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}/abilities', timeout=10)
            if abilities_response.status_code == 200:
                abilities = abilities_response.json()
                print(f"✅ Получено {len(abilities)} способностей для {hero_name}")
        except Exception as e:
            print(f"⚠️ Не удалось получить способности: {e}")
        
        # Если способностей нет, пробуем через другой эндпоинт
        if not abilities:
            try:
                # Пробуем через /api/constants/hero_abilities
                response = requests.get('https://api.opendota.com/api/constants/hero_abilities', timeout=10)
                if response.status_code == 200:
                    all_abilities = response.json()
                    hero_abilities = []
                    for key, ability in all_abilities.items():
                        if ability.get('hero_id') == hero_id:
                            hero_abilities.append(ability)
                    if hero_abilities:
                        abilities = hero_abilities
                        print(f"✅ Получено {len(abilities)} способностей через constants для {hero_name}")
            except Exception as e:
                print(f"⚠️ Не удалось получить способности через constants: {e}")
        
        result = {
            'data': detailed_data,
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

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(load_news())

@app.route('/api/heroes/list', methods=['GET'])
def get_heroes_list_api():
    """Возвращает список всех героев для фронтенда"""
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
        print(f"❌ Герой {hero_name} не найден")
        return jsonify({'error': 'Hero not found'}), 404
    
    print(f"✅ Данные героя {hero_name} отправлены")
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
    """Форматирует текст новости в HTML"""
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
    """Парсит RSS и возвращает новости с фиксированной датой"""
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
    """Инициализация новостей при старте"""
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
        for item in rss_news[:3]:
            print(f"   📌 {item['title']}")
    else:
        test_news = [{
            'id': 1,
            'title': 'Добро пожаловать в Dota 2 Guide!',
            'date': datetime.now(MSK).strftime('%d %B %Y, %H:%M МСК'),
            'content': '<p>Новости Dota 2 будут загружаться автоматически из официального RSS-канала Steam.</p><ul><li>Все новости будут переведены на русский язык</li><li>Дата и время — по Московскому времени</li><li>Форматирование — как в официальных новостях Steam</li></ul>',
            'link': 'https://store.steampowered.com/news/app/570',
            'source': 'manual',
            'timestamp': int(datetime.now().timestamp() * 1000)
        }]
        save_news(test_news)
        print("✅ Добавлена тестовая новость")
    
    print("=" * 60)

# Запускаем инициализацию
initialize_news()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)