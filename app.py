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
def parse_patches_full():
    """Парсит полную информацию о патчах с dota2protracker.com"""
    try:
        print("🌐 Парсинг полных данных патчей с dota2protracker.com...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get('https://dota2protracker.com/patches', headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем все карточки патчей
        patch_cards = soup.find_all('div', class_=re.compile(r'patch-card|PatchCard|card'))
        patches = []
        
        if patch_cards:
            for card in patch_cards:
                patch = extract_full_patch_data(card)
                if patch and patch.get('version'):
                    patches.append(patch)
            print(f"✅ Найдено {len(patches)} патчей через HTML")
            return patches
        
        # Ищем в скриптах
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
                
                # Ищем patches = [...]
                match = re.search(r'patches\s*=\s*(\[.*?\]);', script.string, re.DOTALL)
                if match:
                    try:
                        patches_data = json.loads(match.group(1))
                        print(f"✅ Найдено {len(patches_data)} патчей через JSON")
                        return patches_data
                    except:
                        pass
        
        return get_full_test_patches()
    except Exception as e:
        print(f"❌ Ошибка парсинга патчей: {e}")
        return get_full_test_patches()

def extract_full_patch_data(card):
    """Извлекает полные данные патча из HTML-карточки"""
    try:
        patch = {
            'version': '',
            'date': '',
            'type': 'minor',
            'title': '',
            'description': '',
            'days_ago': 0,
            'days_after_prev': 0,
            'stats': {'heroes': 0, 'items': 0, 'neutral_items': 0, 'general': 0},
            'heroes_stats': [],
            'hero_changes': [],
            'item_changes': [],
            'neutral_item_changes': [],
            'general_changes': []
        }
        
        text = card.text
        
        # Версия патча
        version_match = re.search(r'(7\.\d+[a-z]?)', text)
        if version_match:
            patch['version'] = version_match.group(1)
        
        # Дата
        date_match = re.search(r'([A-Z][a-z]+)\s+(\d{1,2}),?\s+(\d{4})', text)
        if date_match:
            patch['date'] = f"{date_match.group(1)} {date_match.group(2)} {date_match.group(3)}"
        
        # Дни
        days_match = re.search(r'(\d+)\s+days?\s+ago', text, re.IGNORECASE)
        if days_match:
            patch['days_ago'] = int(days_match.group(1))
        
        after_match = re.search(r'(\d+)\s+days?\s+after\s+prev', text, re.IGNORECASE)
        if after_match:
            patch['days_after_prev'] = int(after_match.group(1))
        
        # Статистика
        heroes_match = re.search(r'(\d+)\s*[Hh]eroes?', text)
        if heroes_match:
            patch['stats']['heroes'] = int(heroes_match.group(1))
        
        items_match = re.search(r'(\d+)\s*[Ii]tems?', text)
        if items_match:
            patch['stats']['items'] = int(items_match.group(1))
        
        neutral_match = re.search(r'(\d+)\s*[Nn]eutral', text)
        if neutral_match:
            patch['stats']['neutral_items'] = int(neutral_match.group(1))
        
        general_match = re.search(r'(\d+)\s*[Gg]eneral', text)
        if general_match:
            patch['stats']['general'] = int(general_match.group(1))
        
        # Описание
        desc_match = re.search(r'Patch\s+\d+\.\d+[a-z]?\s+(.*?)(?=Most Picked|$)', text, re.IGNORECASE)
        if desc_match:
            patch['description'] = desc_match.group(1).strip()
        
        # Заголовок
        title_match = re.search(r'Patch\s+\d+\.\d+[a-z]?\s+([A-Z][^.]*\.)', text)
        if title_match:
            patch['title'] = title_match.group(1).strip()
        
        # Определяем тип
        if patch['stats']['heroes'] > 100 or patch['stats']['items'] > 50:
            patch['type'] = 'major'
        else:
            patch['type'] = 'minor'
        
        # Парсим героев с их статистикой
        hero_blocks = card.find_all('div', class_=re.compile(r'hero-stats|HeroStats|hero-item|HeroItem'))
        for block in hero_blocks:
            hero_stat = extract_hero_stats(block)
            if hero_stat:
                patch['heroes_stats'].append(hero_stat)
        
        # Если не нашли через блоки - парсим через строки
        if not patch['heroes_stats']:
            hero_lines = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+([\d.]+%)\s+([\d.]+%)\s+([+-][\d.]+%)', text)
            for line in hero_lines:
                patch['heroes_stats'].append({
                    'name': line[0],
                    'pick_rate': line[1],
                    'win_rate': line[2],
                    'wr_delta': line[3]
                })
        
        # Парсим изменения героев
        hero_change_blocks = card.find_all('div', class_=re.compile(r'hero-change|HeroChange|change-item'))
        for block in hero_change_blocks:
            change = extract_hero_change_full(block)
            if change:
                patch['hero_changes'].append(change)
        
        # Парсим изменения предметов
        item_change_blocks = card.find_all('div', class_=re.compile(r'item-change|ItemChange|change-item'))
        for block in item_change_blocks:
            change = extract_item_change_full(block)
            if change:
                patch['item_changes'].append(change)
        
        return patch
    except Exception as e:
        print(f"⚠️ Ошибка извлечения патча: {e}")
        return None

def extract_hero_stats(block):
    """Извлекает статистику героя (пикрейт, винрейт, дельта)"""
    try:
        stats = {}
        text = block.text
        
        # Имя героя
        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
        if name_match:
            stats['name'] = name_match.group(1)
        
        # Пикрейт
        pick_match = re.search(r'([\d.]+%)\s*(?:pick|Пикрейт)', text, re.IGNORECASE)
        if pick_match:
            stats['pick_rate'] = pick_match.group(1)
        
        # Винрейт
        win_match = re.search(r'([\d.]+%)\s*(?:win|Винрейт)', text, re.IGNORECASE)
        if win_match:
            stats['win_rate'] = win_match.group(1)
        
        # WR дельта
        delta_match = re.search(r'([+-][\d.]+%)', text)
        if delta_match:
            stats['wr_delta'] = delta_match.group(1)
        
        return stats
    except:
        return None

def extract_hero_change_full(block):
    """Извлекает полные изменения героя"""
    try:
        change = {
            'hero': '',
            'ability': '',
            'changes': []
        }
        
        text = block.text.strip()
        if not text:
            return None
        
        # Имя героя
        hero_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
        if hero_match:
            change['hero'] = hero_match.group(1)
        
        # Название способности (в кавычках или с большой буквы)
        ability_match = re.search(r'"([^"]+)"|([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:now|duration|damage|mana|cooldown|radius|speed|armor|strength|agility|intelligence|attack|health)', text)
        if ability_match:
            change['ability'] = ability_match.group(1) or ability_match.group(2)
        
        # Разбиваем изменения по строкам
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and '•' in line:
                change['changes'].append(line.replace('•', '').strip())
            elif line and '-' in line and not line.startswith('--'):
                change['changes'].append(line)
        
        # Если нет структурированных изменений, добавляем весь текст
        if not change['changes'] and text:
            # Ищем изменения в формате "Base Attack Speed decreased from 100 to 90"
            change_match = re.findall(r'([A-Za-z\s]+)\s+(increased|decreased|reworked|added|removed|changed)\s+from\s+([\d.]+)\s+to\s+([\d.]+)', text)
            if change_match:
                for cm in change_match:
                    change['changes'].append(f"{cm[0]} {cm[1]} с {cm[2]} до {cm[3]}")
            else:
                change['changes'].append(text)
        
        return change
    except:
        return None

def extract_item_change_full(block):
    """Извлекает полные изменения предмета"""
    try:
        change = {
            'item': '',
            'changes': []
        }
        
        text = block.text.strip()
        if not text:
            return None
        
        # Название предмета
        item_match = re.search(r'"([^"]+)"', text)
        if item_match:
            change['item'] = item_match.group(1)
        else:
            words = text.split()
            if words:
                change['item'] = words[0]
        
        # Изменения
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and '•' in line:
                change['changes'].append(line.replace('•', '').strip())
            elif line and '-' in line and not line.startswith('--'):
                change['changes'].append(line)
        
        if not change['changes']:
            change['changes'].append(text)
        
        return change
    except:
        return None

def get_full_test_patches():
    """Возвращает полные тестовые данные патчей с изменениями"""
    return [
        {
            'version': '7.41e',
            'date': 'Jul 31, 2026',
            'type': 'minor',
            'title': 'Баланс предметов, талантов и механик',
            'description': 'Patch 7.41e Adjusts Item Balance, Hero Talents, and Utility Mechanics Across the Map',
            'days_ago': 19,
            'days_after_prev': 55,
            'stats': {'heroes': 57, 'items': 26, 'neutral_items': 0, 'general': 2},
            'heroes_stats': [
                {'name': 'Treant Protector', 'pick_rate': '24.9%', 'win_rate': '54.9%', 'wr_delta': '+15.9%'},
                {'name': 'Lina', 'pick_rate': '24.0%', 'win_rate': '49.0%', 'wr_delta': '+10.6%'},
                {'name': 'Shadow Fiend', 'pick_rate': '23.2%', 'win_rate': '50.6%', 'wr_delta': '+3.2%'},
                {'name': 'Undying', 'pick_rate': '23.1%', 'win_rate': '48.2%', 'wr_delta': '+2.0%'},
                {'name': 'Rubick', 'pick_rate': '20.5%', 'win_rate': '48.5%', 'wr_delta': '+10.7%'},
                {'name': 'Ember Spirit', 'pick_rate': '20.5%', 'win_rate': '51.6%', 'wr_delta': '+0.8%'},
                {'name': 'Mirana', 'pick_rate': '20.4%', 'win_rate': '48.9%', 'wr_delta': '+12.5%'},
                {'name': 'Snapfire', 'pick_rate': '20.2%', 'win_rate': '45.8%', 'wr_delta': '+7.8%'},
                {'name': 'Hoodwink', 'pick_rate': '19.4%', 'win_rate': '48.5%', 'wr_delta': '+7.8%'},
                {'name': 'Earth Spirit', 'pick_rate': '18.7%', 'win_rate': '51.1%', 'wr_delta': '+9.2%'}
            ],
            'hero_changes': [
                {
                    'hero': 'Treant Protector',
                    'ability': 'Base Attack Speed',
                    'changes': ['Base Attack Speed decreased from 100 to 90']
                },
                {
                    'hero': 'Treant Protector',
                    'ability': 'Leech Seed',
                    'changes': ['Root duration decreased from 0.9/1.1/1.3/1.5s to 0.75/1.0/1.25/1.5s']
                },
                {
                    'hero': 'Treant Protector',
                    'ability': 'Living Armor',
                    'changes': ['Mana Cost increased from 65/70/75/80 to 80']
                },
                {
                    'hero': 'Troll Warlord',
                    'ability': 'Base Stats',
                    'changes': ['Base Agility increased from 23 to 24', 'Damage on level 1 increased from 50-58 to 51-59']
                },
                {
                    'hero': 'Troll Warlord',
                    'ability': 'Switch Stance',
                    'changes': ['Toggling between stances no longer breaks invisibility']
                },
                {
                    'hero': 'Troll Warlord',
                    'ability': 'Battle Trance',
                    'changes': ['Now also grants 35% Slow Resistance']
                }
            ],
            'item_changes': [
                {'item': 'Mage Slayer', 'changes': ['Damage reduced from 20 to 15']},
                {'item': 'Shadow Blade', 'changes': ['Attack speed reduced from 30 to 25']},
                {'item': 'Harpoon', 'changes': ['Can no longer move rooted casters']}
            ],
            'neutral_item_changes': [],
            'general_changes': []
        },
        {
            'version': '7.41d',
            'date': 'Jun 5, 2026',
            'type': 'minor',
            'title': 'Баланс героев и нейтральных предметов',
            'description': 'Patch 7.41d balances hero power levels and fine-tunes neutral item utility across the map',
            'days_ago': 55,
            'days_after_prev': 29,
            'stats': {'heroes': 82, 'items': 3, 'neutral_items': 5, 'general': 1},
            'heroes_stats': [
                {'name': 'Meepo', 'pick_rate': '18.5%', 'win_rate': '52.3%', 'wr_delta': '-12.4%'},
                {'name': 'Ember Spirit', 'pick_rate': '17.8%', 'win_rate': '50.1%', 'wr_delta': '+6.2%'},
                {'name': 'Beastmaster', 'pick_rate': '16.9%', 'win_rate': '47.8%', 'wr_delta': '+3.1%'}
            ],
            'hero_changes': [
                {'hero': 'Meepo', 'ability': 'Poof', 'changes': ['Damage reduced from 80 to 60']},
                {'hero': 'Ember Spirit', 'ability': 'Flame Guard', 'changes': ['Damage reduced from 50 to 40']},
                {'hero': 'Beastmaster', 'ability': 'Wild Axes', 'changes': ['Damage reduced from 70 to 55']}
            ],
            'item_changes': [],
            'neutral_item_changes': [
                {'item': 'Spellover', 'changes': ['Added 0.1s internal cooldown', 'Increased damage thresholds']},
                {'item': 'False Flight', 'changes': ['Duration increased from 5s to 6.5s']},
                {'item': 'Reverberate', 'changes': ['Projectile physical damage decreased from 110 to 90']}
            ],
            'general_changes': []
        },
        {
            'version': '7.41',
            'date': 'Mar 25, 2026',
            'type': 'major',
            'title': 'Глобальное обновление: новые предметы и способности',
            'description': 'Major Gameplay Overhaul with New Items, Innate Abilities, and Hero Reworks',
            'days_ago': 62,
            'days_after_prev': 0,
            'stats': {'heroes': 126, 'items': 71, 'neutral_items': 20, 'general': 4},
            'heroes_stats': [
                {'name': 'Tinker', 'pick_rate': '22.1%', 'win_rate': '53.4%', 'wr_delta': '+8.7%'},
                {'name': 'Omniknight', 'pick_rate': '20.3%', 'win_rate': '51.2%', 'wr_delta': '+5.9%'}
            ],
            'hero_changes': [
                {'hero': 'Tinker', 'ability': 'New Ability', 'changes': ['Added new turret-based ability']},
                {'hero': 'Omniknight', 'ability': 'Guardian Angel', 'changes': ['Reworked into a personal aura']},
                {'hero': 'Anti-Mage', 'ability': 'Mana Burn', 'changes': ['Upgraded with Aghanims Scepter']},
                {'hero': 'Legion Commander', 'ability': 'Duel', 'changes': ['Can now use abilities during Duel']}
            ],
            'item_changes': [
                {'item': 'Chasm Stone', 'changes': ['New item added']},
                {'item': 'Shawl', 'changes': ['New item added']},
                {'item': 'Splintmail', 'changes': ['New item added']},
                {'item': 'Wizard Hat', 'changes': ['New item added']}
            ],
            'neutral_item_changes': [
                {'item': 'Tier 1 Items', 'changes': ['Availability moved from 7:00 to 0:00']}
            ],
            'general_changes': ['Shop categories rearranged', 'Many heroes updated with new Innate abilities']
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
    """Возвращает список патчей с полной информацией"""
    patches = get_cache('patches_full')
    if not patches:
        patches = parse_patches_full()
        set_cache('patches_full', patches)
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