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
# ПАРСИНГ ПАТЧЕЙ С DOTA2PROTRACKER.COM
# ============================================================
def parse_patches():
    """Парсит страницу с патчами через HTML"""
    try:
        print("🌐 Парсинг патчей с dota2protracker.com...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get('https://dota2protracker.com/patches', headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все карточки патчей
        # Пробуем разные селекторы
        patch_cards = soup.find_all('div', class_=re.compile(r'patch|card|item'))
        
        patches = []
        
        # Если есть карточки с классом patch-card
        for card in patch_cards:
            # Проверяем, содержит ли карточка информацию о патче
            version_elem = card.find(string=re.compile(r'7\.\d+[a-z]?'))
            if version_elem:
                patch = extract_patch_info(card, version_elem)
                if patch and patch.get('version'):
                    patches.append(patch)
                    continue
            
            # Пробуем другие селекторы
            version_elem = card.find('div', class_=re.compile(r'version|patch|title'))
            if version_elem:
                patch = extract_patch_info(card, version_elem)
                if patch and patch.get('version'):
                    patches.append(patch)
        
        if patches:
            print(f"✅ Найдено {len(patches)} патчей")
            return patches
        
        # Если не нашли через селекторы - пробуем через скрипты
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Ищем JSON с данными
                match = re.search(r'patches\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                if match:
                    try:
                        patches_data = json.loads(match.group(1))
                        print(f"✅ Найдено {len(patches_data)} патчей через JSON")
                        return patches_data
                    except:
                        pass
                
                # Ищем __NEXT_DATA__ или __INITIAL_STATE__
                if '__NEXT_DATA__' in script.string:
                    try:
                        match = re.search(r'__NEXT_DATA__\s*=\s*({.*?});', script.string, re.DOTALL)
                        if match:
                            data = json.loads(match.group(1))
                            if 'props' in data and 'pageProps' in data['props']:
                                page_props = data['props']['pageProps']
                                if 'patches' in page_props:
                                    patches_data = page_props['patches']
                                    print(f"✅ Найдено {len(patches_data)} патчей через __NEXT_DATA__")
                                    return patches_data
                    except:
                        pass
        
        return None
    except Exception as e:
        print(f"❌ Ошибка парсинга патчей: {e}")
        return None

def extract_patch_info(card, version_elem):
    """Извлекает информацию о патче из HTML-элемента"""
    try:
        patch = {
            'version': version_elem.text.strip() if version_elem else 'Unknown',
            'date': 'Unknown',
            'type': 'minor',
            'title': '',
            'description': '',
            'stats': {'heroes': 0, 'items': 0, 'general': 0},
            'heroes': [],
            'days_since_prev': 0
        }
        
        # Ищем дату
        date_elem = card.find(string=re.compile(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}'))
        if date_elem:
            patch['date'] = date_elem.strip()
        
        # Ищем описание
        desc_elem = card.find('div', class_=re.compile(r'desc|description|content|summary'))
        if desc_elem:
            patch['description'] = desc_elem.text.strip()
        
        # Ищем заголовок
        title_elem = card.find('h3') or card.find('h2') or card.find('div', class_=re.compile(r'title|heading'))
        if title_elem:
            patch['title'] = title_elem.text.strip()
        
        # Определяем тип (мажорный/минорный)
        if 'major' in str(card).lower() or 'major' in patch.get('title', '').lower():
            patch['type'] = 'major'
        else:
            patch['type'] = 'minor'
        
        # Ищем статистику (герои, предметы)
        stats_text = card.text
        hero_match = re.search(r'(\d+)\s*[Hh]eroes?', stats_text)
        if hero_match:
            patch['stats']['heroes'] = int(hero_match.group(1))
        
        item_match = re.search(r'(\d+)\s*[Ii]tems?', stats_text)
        if item_match:
            patch['stats']['items'] = int(item_match.group(1))
        
        general_match = re.search(r'(\d+)\s*[Gg]eneral', stats_text)
        if general_match:
            patch['stats']['general'] = int(general_match.group(1))
        
        # Ищем героев
        hero_names = []
        hero_links = card.find_all('a', href=re.compile(r'/heroes/'))
        for link in hero_links:
            name = link.text.strip()
            if name and len(name) > 1 and name not in hero_names:
                hero_names.append(name)
        
        if hero_names:
            patch['heroes'] = hero_names[:20]  # Ограничиваем 20 героями
        
        # Ищем дни с прошлого патча
        days_match = re.search(r'(\d+)\s*[Dd]ays?', stats_text)
        if days_match:
            patch['days_since_prev'] = int(days_match.group(1))
        
        return patch
    except Exception as e:
        print(f"⚠️ Ошибка извлечения патча: {e}")
        return None

def get_patches_data():
    """Получает данные о патчах с кэшированием"""
    cache_key = 'patches_cache'
    if cache_key in HERO_CACHE:
        cache_time = HERO_CACHE[cache_key].get('cache_time', 0)
        if (time.time() - cache_time) < CACHE_DURATION:
            print("📦 Патчи из кэша")
            return HERO_CACHE[cache_key]['data']
    
    patches = parse_patches()
    if patches:
        HERO_CACHE[cache_key] = {
            'data': patches,
            'cache_time': time.time()
        }
        return patches
    
    # Если парсинг не удался, возвращаем тестовые данные
    print("⚠️ Используем тестовые данные патчей")
    return get_test_patches()

def get_test_patches():
    """Возвращает тестовые данные патчей"""
    return [
        {
            'version': '7.41e',
            'date': '31 July 2026',
            'type': 'minor',
            'title': 'Баланс предметов и талантов',
            'description': 'Patch 7.41e Adjusts Item Balance, Hero Talents, and Utility Mechanics Across the Map. This patch focuses on fine-tuning the current meta with careful adjustments to popular items and hero talents.',
            'stats': {'heroes': 57, 'items': 26, 'general': 2},
            'heroes': ['Anti-Mage', 'Juggernaut', 'Windranger', 'Lina', 'Techies', 'Meepo', 'Ember Spirit'],
            'days_since_prev': 18
        },
        {
            'version': '7.41d',
            'date': '5 June 2026',
            'type': 'minor',
            'title': 'Баланс героев и нейтральных предметов',
            'description': 'Patch 7.41d balances hero power levels and fine-tunes neutral item utility across the map. Several heroes received adjustments to their core abilities.',
            'stats': {'heroes': 82, 'items': 3, 'general': 1},
            'heroes': ['Meepo', 'Ember Spirit', 'Beastmaster', 'Batrider', 'Juggernaut'],
            'days_since_prev': 55
        },
        {
            'version': '7.41c',
            'date': '7 May 2026',
            'type': 'minor',
            'title': 'Изменения предметов и героев',
            'description': 'This patch adjusts various items, reducing Mage Slayer\'s damage and Shadow Blade\'s speed while preventing Harpoon from moving rooted casters. Several unspecified neutral items also received nerfs.',
            'stats': {'heroes': 82, 'items': 12, 'general': 2},
            'heroes': ['Beastmaster', 'Batrider', 'Techies', 'Juggernaut', 'Lina'],
            'days_since_prev': 29
        },
        {
            'version': '7.41b',
            'date': '7 April 2026',
            'type': 'minor',
            'title': 'Баланс ключевых предметов и героев',
            'description': 'Dota 2 Patch 7.41b Balances Key Items and Adjusts Hero Scaling and Talents. This update focuses on tuning item interactions, nerfing overperforming heroes like Meepo, and adjusting talent trees.',
            'stats': {'heroes': 61, 'items': 11, 'general': 1},
            'heroes': ['Meepo', 'Juggernaut', 'Windranger', 'Ember Spirit', 'Void Spirit'],
            'days_since_prev': 29
        },
        {
            'version': '7.41a',
            'date': '28 March 2026',
            'type': 'minor',
            'title': 'Ребаланс героев и эффективность предметов',
            'description': 'Significant hero rebalancing and item effectiveness adjustments. This patch rebalances the meta by nerfing top-tier heroes and neutral items while providing targeted buffs to underperforming carries.',
            'stats': {'heroes': 37, 'items': 1, 'general': 0},
            'heroes': ['Anti-Mage', 'Juggernaut', 'Windranger', 'Lifestealer', 'Alchemist', 'Wraith King'],
            'days_since_prev': 10
        },
        {
            'version': '7.41',
            'date': '25 March 2026',
            'type': 'major',
            'title': 'ГЛОБАЛЬНОЕ ОБНОВЛЕНИЕ',
            'description': 'Major Gameplay Overhaul with New Items, Innate Abilities, and Hero Reworks. This patch introduces significant system-wide changes, including new innate hero abilities, a massive item overhaul, and major mechanical reworks.',
            'stats': {'heroes': 126, 'items': 71, 'general': 4},
            'heroes': ['Tinker', 'Omniknight', 'Meepo', 'Anti-Mage', 'Legion Commander', 'Marci'],
            'days_since_prev': 62
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
    """Возвращает список патчей"""
    patches = get_patches_data()
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
# OpenDota API (для героев)
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

def get_hero_data(hero_name):
    """Получает данные героя"""
    global HERO_CACHE
    
    if hero_name in HERO_CACHE:
        cache_time = HERO_CACHE[hero_name].get('cache_time', 0)
        if (time.time() - cache_time) < CACHE_DURATION:
            print(f"📦 Данные {hero_name} из кэша")
            return HERO_CACHE[hero_name]
    
    stats = get_heroes_stats()
    
    hero_stats = None
    for stat in stats:
        if stat.get('name', '').lower() == f'npc_dota_hero_{hero_name}'.lower():
            hero_stats = stat
            break
        if stat.get('localized_name', '').lower() == hero_name.replace('_', ' ').lower():
            hero_stats = stat
            break
        if hero_name.lower() in stat.get('name', '').lower():
            hero_stats = stat
            break
    
    if not hero_stats:
        print(f"❌ Герой {hero_name} не найден")
        return None
    
    hero_stats['icon'] = hero_name
    hero_stats['bio'] = 'Описание героя временно недоступно.'
    
    abilities = []
    hero_id = hero_stats.get('id')
    if hero_id:
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