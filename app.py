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
# ПАРСИНГ ПАТЧЕЙ С DOTA2PROTRACKER.COM
# ============================================================
def parse_patches():
    """Парсит страницу с патчами и извлекает полную информацию"""
    try:
        print("🌐 Парсинг патчей с dota2protracker.com...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get('https://dota2protracker.com/patches', headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем скрипты с данными
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Ищем __NEXT_DATA__
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
        
        # Если через скрипты не нашли, парсим HTML
        return parse_patches_html(soup)
    except Exception as e:
        print(f"❌ Ошибка парсинга патчей: {e}")
        return get_test_patches()

def parse_patches_html(soup):
    """Парсит патчи из HTML-структуры страницы"""
    patches = []
    
    # Ищем карточки патчей
    patch_cards = soup.find_all('div', class_=re.compile(r'patch-card|PatchCard|patchCard'))
    
    for card in patch_cards:
        patch = extract_patch_from_card(card)
        if patch:
            patches.append(patch)
    
    if patches:
        print(f"✅ Найдено {len(patches)} патчей через HTML")
        return patches
    
    return get_test_patches()

def extract_patch_from_card(card):
    """Извлекает данные патча из HTML-карточки"""
    try:
        patch = {
            'version': '',
            'date': '',
            'type': 'minor',
            'title': '',
            'description': '',
            'days_since_prev': 0,
            'days_active': 0,
            'stats': {'heroes': 0, 'items': 0, 'neutral_items': 0, 'general': 0},
            'hero_changes': [],
            'item_changes': [],
            'neutral_item_changes': [],
            'general_changes': []
        }
        
        text = card.text
        
        # Версия патча
        version_match = re.search(r'7\.\d+[a-z]?', text)
        if version_match:
            patch['version'] = version_match.group(0)
        
        # Дата
        date_match = re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', text)
        if date_match:
            patch['date'] = date_match.group(0)
        
        # Статистика изменений
        hero_count_match = re.search(r'(\d+)\s*[Hh]ero', text)
        if hero_count_match:
            patch['stats']['heroes'] = int(hero_count_match.group(1))
        
        item_count_match = re.search(r'(\d+)\s*[Ii]tem', text)
        if item_count_match:
            patch['stats']['items'] = int(item_count_match.group(1))
        
        neutral_count_match = re.search(r'(\d+)\s*[Nn]eutral', text)
        if neutral_count_match:
            patch['stats']['neutral_items'] = int(neutral_count_match.group(1))
        
        # Изменения героев - ищем блоки с иконками героев
        hero_blocks = card.find_all('div', class_=re.compile(r'hero-item|HeroItem|heroChange'))
        for block in hero_blocks:
            change = extract_hero_change_from_block(block)
            if change:
                patch['hero_changes'].append(change)
        
        # Изменения предметов
        item_blocks = card.find_all('div', class_=re.compile(r'item-item|ItemItem|itemChange'))
        for block in item_blocks:
            change = extract_item_change_from_block(block)
            if change:
                patch['item_changes'].append(change)
        
        # Определяем тип патча
        if patch['stats']['heroes'] > 100 or patch['stats']['items'] > 50:
            patch['type'] = 'major'
        
        return patch
    except Exception as e:
        print(f"⚠️ Ошибка извлечения патча: {e}")
        return None

def extract_hero_change_from_block(block):
    """Извлекает изменения героя из блока"""
    try:
        change = {
            'hero': '',
            'hero_icon': '',
            'old_value': '',
            'new_value': '',
            'change_value': '',
            'description': ''
        }
        
        text = block.text.strip()
        
        # Имя героя
        name_elem = block.find('a') or block.find('div', class_=re.compile(r'name|hero-name'))
        if name_elem:
            change['hero'] = name_elem.text.strip()
        
        # Иконка героя
        img_elem = block.find('img')
        if img_elem and img_elem.get('src'):
            change['hero_icon'] = img_elem['src']
        
        # Числовые изменения
        value_match = re.search(r'([+-]?\d+\.?\d*)', text)
        if value_match:
            change['change_value'] = value_match.group(1)
        
        # Старое -> новое
        arrow_match = re.search(r'(\d+)\s*->\s*(\d+)', text)
        if arrow_match:
            change['old_value'] = arrow_match.group(1)
            change['new_value'] = arrow_match.group(2)
        
        # Описание изменения
        if text and len(text) > 2:
            change['description'] = text
        
        return change
    except:
        return None

def extract_item_change_from_block(block):
    """Извлекает изменения предмета из блока"""
    try:
        change = {
            'item': '',
            'item_icon': '',
            'old_value': '',
            'new_value': '',
            'description': ''
        }
        
        text = block.text.strip()
        
        # Название предмета
        name_elem = block.find('div', class_=re.compile(r'name|item-name'))
        if name_elem:
            change['item'] = name_elem.text.strip()
        else:
            words = text.split()
            if words:
                change['item'] = words[0]
        
        # Иконка
        img_elem = block.find('img')
        if img_elem and img_elem.get('src'):
            change['item_icon'] = img_elem['src']
        
        # Старое -> новое
        arrow_match = re.search(r'(\d+)\s*->\s*(\d+)', text)
        if arrow_match:
            change['old_value'] = arrow_match.group(1)
            change['new_value'] = arrow_match.group(2)
        
        # Описание
        if text and len(text) > 2:
            change['description'] = text
        
        return change
    except:
        return None

def get_test_patches():
    """Возвращает тестовые данные с полной информацией"""
    return [
        {
            'version': '7.41e',
            'date': '31 July 2026',
            'type': 'minor',
            'title': 'Баланс предметов, талантов и механик',
            'description': 'Patch 7.41e Adjusts Item Balance, Hero Talents, and Utility Mechanics Across the Map.',
            'days_since_prev': 18,
            'days_active': 18,
            'stats': {'heroes': 57, 'items': 26, 'neutral_items': 6, 'general': 0},
            'hero_changes': [
                {'hero': 'Phantom Assassin', 'hero_icon': '/heroes/phantom_assassin.png', 'change_value': '+1.2', 'description': 'Blur - Now cannot be dispelled'},
                {'hero': 'Treant Protector', 'hero_icon': '/heroes/treant_protector.png', 'change_value': '+1.0', 'description': 'Living Armor damage block increased'},
                {'hero': 'Lina', 'hero_icon': '/heroes/lina.png', 'change_value': '+3.3', 'description': 'Dragon Slave damage increased'},
                {'hero': 'Shadow Fiend', 'hero_icon': '/heroes/shadow_fiend.png', 'change_value': '+2.7', 'description': 'Shadowraze damage increased'}
            ],
            'item_changes': [
                {'item': 'Mage Slayer', 'item_icon': '/items/mage_slayer.png', 'old_value': '20', 'new_value': '15', 'description': 'Damage reduced'},
                {'item': 'Shadow Blade', 'item_icon': '/items/shadow_blade.png', 'old_value': '30', 'new_value': '25', 'description': 'Attack speed reduced'},
                {'item': 'Harpoon', 'item_icon': '/items/harpoon.png', 'description': 'Can no longer move rooted casters'}
            ],
            'neutral_item_changes': [
                {'item': 'Spellover', 'item_icon': '/items/spellover.png', 'description': 'Added internal cooldown'},
                {'item': 'False Flight', 'item_icon': '/items/false_flight.png', 'old_value': '5', 'new_value': '6.5', 'description': 'Duration increased'},
                {'item': 'Reverberate', 'item_icon': '/items/reverberate.png', 'old_value': '110', 'new_value': '90', 'description': 'Damage decreased'}
            ]
        },
        {
            'version': '7.41d',
            'date': '5 June 2026',
            'type': 'minor',
            'stats': {'heroes': 82, 'items': 3, 'neutral_items': 5, 'general': 0},
            'hero_changes': [
                {'hero': 'Meepo', 'hero_icon': '/heroes/meepo.png', 'change_value': '-3.2', 'description': 'Poof damage reduced'},
                {'hero': 'Ember Spirit', 'hero_icon': '/heroes/ember_spirit.png', 'change_value': '-2.1', 'description': 'Flame Guard damage reduced'}
            ],
            'item_changes': [],
            'neutral_item_changes': [
                {'item': 'Spellover', 'item_icon': '/items/spellover.png', 'description': 'Added 0.1s internal cooldown'}
            ]
        },
        {
            'version': '7.41',
            'date': '25 March 2026',
            'type': 'major',
            'stats': {'heroes': 126, 'items': 71, 'neutral_items': 20, 'general': 4},
            'hero_changes': [
                {'hero': 'Tinker', 'hero_icon': '/heroes/tinker.png', 'description': 'New turret-based ability added'},
                {'hero': 'Omniknight', 'hero_icon': '/heroes/omniknight.png', 'description': 'Guardian Angel reworked into personal aura'},
                {'hero': 'Anti-Mage', 'hero_icon': '/heroes/anti_mage.png', 'description': 'Aghanims Scepter mana burn upgraded'}
            ],
            'item_changes': [
                {'item': 'Chasm Stone', 'item_icon': '/items/chasm_stone.png', 'description': 'New item added'},
                {'item': 'Shawl', 'item_icon': '/items/shawl.png', 'description': 'New item added'}
            ],
            'neutral_item_changes': [
                {'item': 'Tier 1 Items', 'item_icon': '/items/tier1.png', 'old_value': '7:00', 'new_value': '0:00', 'description': 'Availability moved to 0:00'}
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
    patches = get_cache('patches')
    if not patches:
        patches = parse_patches()
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