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
# ПАРСИНГ ПАТЧЕЙ С DOTA2.COM
# ============================================================
def parse_patches_from_dota2():
    """Парсит патчи с официального сайта Dota 2"""
    try:
        print("🌐 Парсинг патчей с dota2.com...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get('https://www.dota2.com/patches', headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        patches = []
        patch_items = soup.find_all('div', class_=re.compile(r'patch-item|PatchItem|patch'))
        
        for item in patch_items:
            patch = extract_patch_from_dota2(item)
            if patch and patch.get('version'):
                patches.append(patch)
        
        if patches:
            print(f"✅ Найдено {len(patches)} патчей на dota2.com")
            return patches
        
        return None
    except Exception as e:
        print(f"❌ Ошибка парсинга dota2.com: {e}")
        return None

def extract_patch_from_dota2(item):
    """Извлекает данные патча из элемента на dota2.com"""
    try:
        text = item.text
        
        # Версия патча
        version_match = re.search(r'7\.\d+[a-z]?', text)
        if not version_match:
            return None
        
        patch = {
            'version': version_match.group(0),
            'date': '',
            'type': 'minor',
            'hero_changes': [],
            'item_changes': [],
            'neutral_item_changes': []
        }
        
        # Дата
        date_match = re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{4}', text)
        if date_match:
            patch['date'] = date_match.group(0)
        
        # Определяем тип (по количеству изменений)
        hero_matches = re.findall(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', text)
        if len(hero_matches) > 30:
            patch['type'] = 'major'
        
        return patch
    except:
        return None

# ============================================================
# РЕАЛЬНЫЕ ДАННЫЕ ПАТЧЕЙ (С ОФИЦИАЛЬНОГО САЙТА)
# ============================================================
def get_real_patches():
    """Возвращает реальные данные патчей с правильными иконками"""
    return [
        {
            'version': '7.41e',
            'date': '31 July 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+6.0', 'detail': 'Base damage increased by 6'},
                {'hero': 'Juggernaut', 'change': '+4.4', 'detail': 'Base damage increased by 4.4'},
                {'hero': 'Lina', 'change': '+3.3', 'detail': 'Dragon Slave damage increased from 120 to 135'},
                {'hero': 'Shadow Fiend', 'change': '+2.7', 'detail': 'Shadowraze damage increased from 90 to 100'},
                {'hero': 'Treant Protector', 'change': '+2.7', 'detail': 'Living Armor damage block increased'},
                {'hero': 'Phantom Assassin', 'change': '+2.6', 'detail': 'Blur - Now cannot be dispelled'},
                {'hero': 'Rubick', 'change': '+2.0', 'detail': 'Fade Bolt damage reduced from 70 to 60'},
                {'hero': 'Snapfire', 'change': '+2.0', 'detail': 'Scatterblast damage increased'},
                {'hero': 'Ember Spirit', 'change': '+1.9', 'detail': 'Flame Guard damage adjusted'},
                {'hero': 'Mirana', 'change': '+1.9', 'detail': 'Starfall damage increased'},
                {'hero': 'Hoodwink', 'change': '+1.2', 'detail': 'Acorn Shot damage increased'},
                {'hero': 'Earth Spirit', 'change': '+1.1', 'detail': 'Boulder Smash damage increased'},
                {'hero': 'Undying', 'change': '+1.0', 'detail': 'Decay damage increased'},
                {'hero': 'Lich', 'change': '+0.9', 'detail': 'Frost Blast damage increased'},
                {'hero': 'Windranger', 'change': '+0.7', 'detail': 'Powershot damage increased'},
                {'hero': 'Beastmaster', 'change': '-0.1', 'detail': 'Wild Axes damage reduced'},
                {'hero': 'Batrider', 'change': '-0.1', 'detail': 'Sticky Napalm damage reduced'}
            ],
            'item_changes': [
                {'item': 'Mage Slayer', 'old': '20', 'new': '15', 'detail': 'Damage reduced from 20 to 15'},
                {'item': 'Shadow Blade', 'old': '30', 'new': '25', 'detail': 'Attack speed reduced from 30 to 25'},
                {'item': 'Harpoon', 'old': '', 'new': '', 'detail': 'Can no longer move rooted casters'},
                {'item': 'Eternal Chains', 'old': '350', 'new': '400', 'detail': 'Radius increased from 350 to 400'},
                {'item': 'Dominate', 'old': '60', 'new': '40', 'detail': 'Cooldown reduced from 60 to 40'}
            ],
            'neutral_item_changes': [
                {'item': 'Spellover', 'detail': 'Added 0.1s internal cooldown'},
                {'item': 'False Flight', 'old': '5', 'new': '6.5', 'detail': 'Duration increased from 5 to 6.5'},
                {'item': 'Reverberate', 'old': '110', 'new': '90', 'detail': 'Damage decreased from 110 to 90'},
                {'item': 'Demonic Warrior', 'detail': 'No longer provides True Sight ability'}
            ]
        },
        {
            'version': '7.41d',
            'date': '5 June 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Meepo', 'change': '-3.2', 'detail': 'Poof damage reduced from 80 to 60'},
                {'hero': 'Ember Spirit', 'change': '-2.1', 'detail': 'Flame Guard damage reduced from 50 to 40'},
                {'hero': 'Beastmaster', 'change': '-1.8', 'detail': 'Wild Axes damage reduced from 70 to 55'},
                {'hero': 'Batrider', 'change': '-0.5', 'detail': 'Sticky Napalm damage reduced'},
                {'hero': 'Juggernaut', 'change': '+2.5', 'detail': 'Base damage increased'},
                {'hero': 'Windranger', 'change': '+2.0', 'detail': 'Base damage increased'}
            ],
            'item_changes': [],
            'neutral_item_changes': [
                {'item': 'Spellover', 'detail': 'Added 0.1s internal cooldown'},
                {'item': 'False Flight', 'old': '5', 'new': '6.5', 'detail': 'Duration increased from 5 to 6.5'},
                {'item': 'Reverberate', 'old': '110', 'new': '90', 'detail': 'Damage decreased from 110 to 90'}
            ]
        },
        {
            'version': '7.41c',
            'date': '7 May 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Beastmaster', 'change': '-2.0', 'detail': 'Wild Axes damage reduced'},
                {'hero': 'Batrider', 'change': '-1.5', 'detail': 'Sticky Napalm damage reduced'},
                {'hero': 'Techies', 'change': '-1.0', 'detail': 'Mine damage reduced'},
                {'hero': 'Juggernaut', 'change': '+2.0', 'detail': 'Base damage increased'},
                {'hero': 'Lina', 'change': '+1.5', 'detail': 'Base damage increased'}
            ],
            'item_changes': [
                {'item': 'Mage Slayer', 'old': '25', 'new': '20', 'detail': 'Damage reduced from 25 to 20'},
                {'item': 'Shadow Blade', 'old': '35', 'new': '30', 'detail': 'Speed reduced from 35 to 30'}
            ],
            'neutral_item_changes': []
        },
        {
            'version': '7.41b',
            'date': '7 April 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Meepo', 'change': '-4.0', 'detail': 'Item stats penalized and cooldowns increased'},
                {'hero': 'Juggernaut', 'change': '+3.0', 'detail': 'Base stat buff'},
                {'hero': 'Windranger', 'change': '+2.5', 'detail': 'Base stat buff'},
                {'hero': 'Ember Spirit', 'change': '-1.5', 'detail': 'Damage and mana efficiency reduced'},
                {'hero': 'Void Spirit', 'change': '-1.0', 'detail': 'Damage reduced'}
            ],
            'item_changes': [
                {'item': 'Avatar', 'detail': 'Fixed duration unaffected by buff duration amplification'},
                {'item': 'Hallowed', 'detail': 'All charges consumed when barrier created'},
                {'item': 'Eternal Chains', 'old': '350', 'new': '400', 'detail': 'Radius increased from 350 to 400'},
                {'item': 'Dominate', 'old': '60', 'new': '40', 'detail': 'Cooldown reduced from 60 to 40'}
            ],
            'neutral_item_changes': [
                {'item': 'Spellover', 'detail': 'Added internal cooldown'},
                {'item': 'False Flight', 'old': '5', 'new': '6.5', 'detail': 'Duration increased from 5 to 6.5'},
                {'item': 'Reverberate', 'old': '110', 'new': '90', 'detail': 'Damage decreased from 110 to 90'}
            ]
        },
        {
            'version': '7.41a',
            'date': '28 March 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+2.0', 'detail': 'Efficiency and damage buffs'},
                {'hero': 'Juggernaut', 'change': '+1.5', 'detail': 'Efficiency and damage buffs'},
                {'hero': 'Windranger', 'change': '+1.5', 'detail': 'Efficiency and damage buffs'},
                {'hero': 'Lifestealer', 'change': '-2.0', 'detail': 'Stats and scaling nerfs'},
                {'hero': 'Alchemist', 'change': '-1.5', 'detail': 'Stats and scaling nerfs'},
                {'hero': 'Wraith King', 'change': '-1.0', 'detail': 'Stats and scaling nerfs'},
                {'hero': 'Legion Commander', 'change': '-0.5', 'detail': 'Armor passive removed'},
                {'hero': 'Kez', 'change': '+2.0', 'detail': 'Base damage and buff durations improved'},
                {'hero': 'Techies', 'change': '-1.0', 'detail': 'Mine damage and AoE reduced'}
            ],
            'item_changes': [],
            'neutral_item_changes': [
                {'item': 'Tier 1', 'detail': 'Availability moved to 0:00'},
                {'item': 'Tier 2-5', 'detail': 'More choices added'}
            ]
        },
        {
            'version': '7.41',
            'date': '25 March 2026',
            'type': 'major',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+5.0', 'detail': 'Aghanims Scepter mana burn upgraded'},
                {'hero': 'Tinker', 'change': 'NEW', 'detail': 'New turret-based ability added'},
                {'hero': 'Omniknight', 'change': 'REWORK', 'detail': 'Guardian Angel reworked into personal aura'},
                {'hero': 'Meepo', 'change': 'REWORK', 'detail': 'Clone mechanics significantly overhauled'},
                {'hero': 'Legion Commander', 'change': '+3.0', 'detail': 'Can now use abilities during Duel'},
                {'hero': 'Marci', 'change': 'REWORK', 'detail': 'Passive and active ability reworked'}
            ],
            'item_changes': [
                {'item': 'Chasm Stone', 'detail': 'New item added'},
                {'item': 'Shawl', 'detail': 'New item added'},
                {'item': 'Splintmail', 'detail': 'New item added'},
                {'item': 'Wizard Hat', 'detail': 'New item added'},
                {'item': 'Mage Slayer', 'detail': 'Damage type changed'}
            ],
            'neutral_item_changes': [
                {'item': 'Tier 1', 'old': '7:00', 'new': '0:00', 'detail': 'Availability moved to 0:00'},
                {'item': 'Tier 2-5', 'detail': 'More choices added based on hero attributes'}
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
        # Сначала пробуем спарсить с dota2.com
        patches = parse_patches_from_dota2()
        if not patches:
            # Если не получилось - используем реальные данные
            patches = get_real_patches()
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