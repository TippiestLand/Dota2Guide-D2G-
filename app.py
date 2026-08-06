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
from bs4 import BeautifulSoup

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'

MSK = timezone(timedelta(hours=3))

os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)

if not os.path.exists(NEWS_FILE):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ============================================================
# РАБОТА С НОВОСТЯМИ
# ============================================================
def load_news():
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки news.json: {e}")
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
        'Hero': 'Герой',
        'Balance': 'Баланс',
        'Fix': 'Исправление',
        'Hotfix': 'Срочное исправление',
        'Maintenance': 'Технические работы',
        'Server': 'Сервер',
        'Performance': 'Производительность',
        'Optimization': 'Оптимизация',
        'Security': 'Безопасность',
        'Feature': 'Нововведение',
        'Improvement': 'Улучшение',
        'Change': 'Изменение',
        'Adjustment': 'Корректировка',
        'Refinement': 'Доработка',
        'Enhancement': 'Усиление',
        'Nerf': 'Ослабление',
        'Buff': 'Усиление',
        'Rework': 'Переработка',
        'Redesign': 'Редизайн',
        'All Events': 'Все события',
        'Dota 2 Events': 'События Dota 2'
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

def convert_date_to_msk(date_string):
    try:
        date_obj = datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S %Z')
        date_obj_msk = date_obj.astimezone(MSK)
        return date_obj_msk.strftime('%d %B %Y, %H:%M МСК')
    except:
        return datetime.now(MSK).strftime('%d %B %Y, %H:%M МСК')

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
            date_formatted = convert_date_to_msk(pub_date_text)
            link_element = item.find('link')
            link_text = link_element.text if link_element is not None else ''
            description_element = item.find('description')
            if description_element is not None and description_element.text:
                desc_text = description_element.text
            else:
                desc_text = title_text
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            desc_clean = format_news_content(desc_clean)
            hash_id = int(hashlib.md5(title_text.encode('utf-8')).hexdigest()[:8], 16)
            news_items.append({
                'id': hash_id,
                'title': title_text,
                'date': date_formatted,
                'content': desc_clean,
                'link': link_text,
                'source': 'rss'
            })
        return news_items
    except Exception as e:
        print(f"Ошибка при получении RSS: {e}")
        return []

def update_news_from_rss():
    existing = load_news()
    rss_news = fetch_rss_news()
    if not rss_news:
        return 0
    existing_titles = {n.get('title') for n in existing if n.get('source') == 'rss'}
    new_items = [n for n in rss_news if n['title'] not in existing_titles]
    if new_items:
        updated_news = new_items + existing
        save_news(updated_news)
    return len(new_items)

# ============================================================
# ПАРСИНГ С ОФИЦИАЛЬНОГО САЙТА
# ============================================================
def parse_hero_from_official(hero_name):
    """
    Парсит данные героя с официального сайта dota2.com/hero/hero_name
    Возвращает словарь с данными или None
    """
    try:
        url = f'https://www.dota2.com/hero/{hero_name}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Не удалось загрузить страницу {hero_name}: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Ищем все скрипты с данными
        scripts = soup.find_all('script')
        hero_data = None
        
        for script in scripts:
            if script.string:
                # Ищем heroData в скрипте
                match = re.search(r'heroData\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        hero_data = json.loads(match.group(1))
                        break
                    except:
                        pass
                
                # Ищем window.__INITIAL_STATE__
                match2 = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                if match2:
                    try:
                        data = json.loads(match2.group(1))
                        if 'hero' in data:
                            hero_data = data['hero']
                            break
                    except:
                        pass
        
        if not hero_data:
            print(f"❌ Не найдены данные для {hero_name}")
            return None
        
        # Извлекаем нужные поля
        result = {
            'localized_name': hero_data.get('localized_name', hero_name.capitalize()),
            'bio': hero_data.get('bio', ''),
            'primary_attr': hero_data.get('primary_attr', 'universal'),
            'attack_type': hero_data.get('attack_type', 'melee'),
            'complexity': hero_data.get('complexity', 2),
            'roles': hero_data.get('roles', []),
            
            # Характеристики
            'base_str': hero_data.get('base_str', 0),
            'base_agi': hero_data.get('base_agi', 0),
            'base_int': hero_data.get('base_int', 0),
            'str_gain': hero_data.get('str_gain', 0),
            'agi_gain': hero_data.get('agi_gain', 0),
            'int_gain': hero_data.get('int_gain', 0),
            
            'base_health': hero_data.get('base_health', 0),
            'base_mana': hero_data.get('base_mana', 0),
            'base_armor': hero_data.get('base_armor', 0),
            'base_health_regen': hero_data.get('base_health_regen', 0),
            'base_mana_regen': hero_data.get('base_mana_regen', 0),
            
            'attack_min': hero_data.get('attack_min', 0),
            'attack_max': hero_data.get('attack_max', 0),
            'attack_rate': hero_data.get('attack_rate', 1.7),
            'attack_range': hero_data.get('attack_range', 150),
            
            'move_speed': hero_data.get('move_speed', 300),
            'day_vision': hero_data.get('day_vision', 1800),
            'night_vision': hero_data.get('night_vision', 800),
            
            # Способности
            'abilities': hero_data.get('abilities', []),
            
            # Таланты (дерево)
            'talents': hero_data.get('talents', []),
            
            # Аганим и Шард
            'aghanim': hero_data.get('aghanim', None),
            'shard': hero_data.get('shard', None),
            
            # Иконка героя
            'icon': hero_name
        }
        
        print(f"✅ Парсинг {hero_name} завершён")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка парсинга {hero_name}: {e}")
        return None

def get_hero_data_from_official(hero_name):
    """
    Пытается получить данные с официального сайта.
    Если есть кэш — использует его, иначе парсит.
    """
    cache_file = os.path.join(os.path.dirname(__file__), 'data', 'heroes_cache.json')
    
    # Загружаем кэш
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
        except:
            pass
    
    # Если герой есть в кэше — возвращаем
    if hero_name in cache:
        print(f"📦 Данные {hero_name} из кэша")
        return cache[hero_name]
    
    # Иначе парсим
    data = parse_hero_from_official(hero_name)
    if data:
        cache[hero_name] = data
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
        print(f"💾 Данные {hero_name} сохранены в кэш")
    
    return data

# ============================================================
# ГЕРОИ (OpenDota API + FALLBACK)
# ============================================================
HERO_CACHE = {}
HEROES_LIST_CACHE = None

def get_heroes_list():
    global HEROES_LIST_CACHE
    if HEROES_LIST_CACHE:
        return HEROES_LIST_CACHE
    try:
        print("📡 Запрос списка героев из OpenDota API...")
        response = requests.get('https://api.opendota.com/api/heroes', timeout=10)
        if response.status_code == 200:
            HEROES_LIST_CACHE = response.json()
            print(f"✅ Получено {len(HEROES_LIST_CACHE)} героев")
            return HEROES_LIST_CACHE
        else:
            print(f"❌ API вернул код: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка загрузки списка героев: {e}")
    return []

def get_hero_data(hero_name):
    global HERO_CACHE
    if hero_name in HERO_CACHE:
        return HERO_CACHE[hero_name]
    try:
        heroes = get_heroes_list()
        hero_id = None
        for h in heroes:
            if h['name'] == f'npc_dota_hero_{hero_name}':
                hero_id = h['id']
                break
        if not hero_id:
            return None
        response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}', timeout=10)
        if response.status_code == 200:
            data = response.json()
            abilities_response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}/abilities', timeout=10)
            abilities = abilities_response.json() if abilities_response.status_code == 200 else []
            HERO_CACHE[hero_name] = {
                'data': data,
                'abilities': abilities
            }
            return HERO_CACHE[hero_name]
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

@app.route('/test-hero/<hero_name>')
def test_hero(hero_name):
    return f"""
    <h1>Тест маршрута героя</h1>
    <p>Герой: <strong>{hero_name}</strong></p>
    <p>Если вы видите это сообщение — маршрут работает!</p>
    <p><a href="/">На главную</a></p>
    """

@app.route('/hero/<hero_name>')
def hero_page(hero_name):
    print(f"🔍 Запрос героя: {hero_name}")
    
    # Пытаемся получить с официального сайта
    hero_data = get_hero_data_from_official(hero_name)
    
    if hero_data:
        print(f"✅ Рендерим hero.html для {hero_name}")
        return render_template('hero.html', 
                              hero=hero_data)
    
    # Fallback — OpenDota API
    hero_data_api = get_hero_data(hero_name)
    if hero_data_api:
        print(f"✅ Рендерим hero.html из OpenDota для {hero_name}")
        return render_template('hero.html', 
                              hero=hero_data_api['data'],
                              abilities=hero_data_api['abilities'])
    
    print("❌ Герой не найден, редирект на главную")
    return redirect(url_for('index'))

@app.route('/api/hero/<hero_name>')
def api_hero(hero_name):
    """API для получения данных героя (с официального сайта)"""
    print(f"🔍 API запрос героя: {hero_name}")
    
    # Пытаемся получить с официального сайта
    hero_data = get_hero_data_from_official(hero_name)
    
    if hero_data:
        return jsonify(hero_data)
    
    # Fallback — OpenDota API
    hero_data_api = get_hero_data(hero_name)
    if hero_data_api:
        return jsonify({
            'data': hero_data_api['data'],
            'abilities': hero_data_api['abilities']
        })
    
    # Общий fallback
    print(f"❌ Герой {hero_name} не найден")
    return jsonify({'error': 'Hero not found'}), 404

# ============================================================
# ИНИЦИАЛИЗАЦИЯ НОВОСТЕЙ
# ============================================================
def initialize_news():
    print("=" * 60)
    print("🚀 ИНИЦИАЛИЗАЦИЯ НОВОСТЕЙ")
    print("=" * 60)
    existing = load_news()
    print(f"📰 Существующих новостей: {len(existing)}")
    if len(existing) > 0:
        print("✅ Новости уже есть, пропускаем загрузку")
        return
    print("📝 Новостей нет. Загружаем свежие из RSS...")
    rss_news = fetch_rss_news()
    if rss_news and len(rss_news) > 0:
        save_news(rss_news)
        print(f"✅ Добавлено {len(rss_news)} свежих новостей из RSS")
        for item in rss_news[:3]:
            print(f"   📌 {item['title']}")
        return
    print("⚠️ RSS не загрузился. Добавляем тестовую новость...")
    test_news = [
        {
            'id': 1,
            'title': 'Добро пожаловать в Dota 2 Guide!',
            'date': datetime.now(MSK).strftime('%d %B %Y, %H:%M МСК'),
            'content': '<p>Новости Dota 2 будут загружаться автоматически из официального RSS-канала Steam.</p><ul><li>Все новости будут переведены на русский язык</li><li>Дата и время — по Московскому времени</li><li>Форматирование — как в официальных новостях Steam</li></ul>',
            'link': 'https://store.steampowered.com/news/app/570',
            'source': 'manual'
        }
    ]
    save_news(test_news)
    print("✅ Добавлена тестовая новость")
    print("=" * 60)

initialize_news()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)