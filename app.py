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

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'

# Московское время (UTC+3)
MSK = timezone(timedelta(hours=3))

os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)

if not os.path.exists(NEWS_FILE):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# ============================================================
# РАЗДАЧА СТАТИКИ
# ============================================================
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
    """Переводит заголовки новостей на русский"""
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
    """
    Преобразует текст новости в HTML с правильными списками.
    - Строки с точками в начале → <ul><li>...</li></ul>
    - Обычные строки → <p>...</p>
    - Пустые строки → <br>
    """
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
        
        if line.startswith('• '):
            is_list_item = True
            clean_text = line[2:]
        elif line.startswith('- '):
            is_list_item = True
            clean_text = line[2:]
        elif line.startswith('* '):
            is_list_item = True
            clean_text = line[2:]
        elif line.startswith('— '):
            is_list_item = True
            clean_text = line[2:]
        elif line.startswith('Fixed'):
            is_list_item = True
            clean_text = 'Исправлено: ' + line[6:]
        elif line.startswith('Fixed '):
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
    """Конвертирует дату из RSS в МСК"""
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
            print(f"RSS ответил с кодом {response.status_code}")
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
# ГЕРОИ (OpenDota API + FALLBACK)
# ============================================================
HERO_CACHE = {}
HEROES_LIST_CACHE = None

def get_heroes_list():
    """Получает список всех героев из OpenDota API"""
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
    """Получает данные о герое из OpenDota API"""
    global HERO_CACHE
    
    print(f"📡 Запрос данных для героя: {hero_name}")
    
    if hero_name in HERO_CACHE:
        print(f"✅ Данные из кэша для {hero_name}")
        return HERO_CACHE[hero_name]
    
    try:
        heroes = get_heroes_list()
        
        hero_id = None
        for h in heroes:
            if h['name'] == f'npc_dota_hero_{hero_name}':
                hero_id = h['id']
                break
        
        if not hero_id:
            print(f"❌ Герой {hero_name} не найден в списке")
            return None
        
        print(f"🆔 ID героя: {hero_id}")
        
        response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Данные героя получены")
            
            abilities_response = requests.get(f'https://api.opendota.com/api/heroes/{hero_id}/abilities', timeout=10)
            abilities = abilities_response.json() if abilities_response.status_code == 200 else []
            print(f"✅ Получено {len(abilities)} способностей")
            
            HERO_CACHE[hero_name] = {
                'data': data,
                'abilities': abilities
            }
            return HERO_CACHE[hero_name]
        else:
            print(f"❌ API героя вернул код: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка загрузки данных героя {hero_name}: {e}")
    
    return None

# ============================================================
# ЛОКАЛЬНЫЕ ДАННЫЕ ГЕРОЕВ (FALLBACK) — ВСЕ ГЕРОИ
# ============================================================
LOCAL_HEROES_DATA = {
    'abaddon': {
        'data': {
            'localized_name': 'Abaddon',
            'bio': 'Абаддон — универсальный герой, способный защищать союзников и наносить урон врагам.',
            'base_str': 22, 'base_agi': 15, 'base_int': 18,
            'base_health': 620, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.7, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'universal',
            'str_gain': 2.6, 'agi_gain': 1.5, 'int_gain': 2.0
        },
        'abilities': [
            {'dname': 'Мистический туман', 'desc': 'Лечит союзников или наносит урон врагам.', 'img': 'abaddon_mist_coil.png'},
            {'dname': 'Щит без света', 'desc': 'Создает щит, поглощающий урон.', 'img': 'abaddon_aphotic_shield.png'},
            {'dname': 'Ледяная скорбь', 'desc': 'Атаки замедляют врагов.', 'img': 'abaddon_frostmourne.png'},
            {'dname': 'Возврат времени', 'desc': 'Превращает урон в исцеление.', 'img': 'abaddon_borrowed_time.png'}
        ]
    },
    'axe': {
        'data': {
            'localized_name': 'Axe',
            'bio': 'Акс — герой силы, заставляющий врагов атаковать его.',
            'base_str': 25, 'base_agi': 20, 'base_int': 18,
            'base_health': 660, 'base_mana': 300, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 60, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 2.0, 'int_gain': 1.6
        },
        'abilities': [
            {'dname': 'Боевой клич', 'desc': 'Провоцирует врагов.', 'img': 'axe_berserkers_call.png'},
            {'dname': 'Голод битвы', 'desc': 'Наносит урон и замедляет.', 'img': 'axe_battle_hunger.png'},
            {'dname': 'Жажда битвы', 'desc': 'Увеличивает скорость атаки.', 'img': 'axe_counter_helix.png'},
            {'dname': 'Уничтожение', 'desc': 'Уничтожает врага с низким здоровьем.', 'img': 'axe_culling_blade.png'}
        ]
    },
    'pudge': {
        'data': {
            'localized_name': 'Pudge',
            'bio': 'Пудж — герой силы, известный своим мясным крюком.',
            'base_str': 25, 'base_agi': 14, 'base_int': 16,
            'base_health': 650, 'base_mana': 280, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 52, 'base_attack_max': 62, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 3.2, 'agi_gain': 1.5, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Мясной крюк', 'desc': 'Вытягивает врага.', 'img': 'pudge_meat_hook.png'},
            {'dname': 'Гниение', 'desc': 'Наносит урон врагам.', 'img': 'pudge_rot.png'},
            {'dname': 'Плоть', 'desc': 'Увеличивает урон и здоровье.', 'img': 'pudge_flesh_heap.png'},
            {'dname': 'Расчленение', 'desc': 'Наносит огромный урон.', 'img': 'pudge_dismember.png'}
        ]
    },
    'beastmaster': {
        'data': {
            'localized_name': 'Beastmaster',
            'bio': 'Beastmaster призывает зверей на помощь.',
            'base_str': 24, 'base_agi': 19, 'base_int': 16,
            'base_health': 640, 'base_mana': 310, 'base_armor': 2.0,
            'attack_rate': 2.2, 'move_speed': 310,
            'base_attack_min': 49, 'base_attack_max': 53, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.9, 'agi_gain': 2.0, 'int_gain': 1.9
        },
        'abilities': [
            {'dname': 'Призыв кабана', 'desc': 'Призывает кабана.', 'img': 'beastmaster_boar.png'},
            {'dname': 'Призыв ястреба', 'desc': 'Призывает ястреба.', 'img': 'beastmaster_hawk.png'},
            {'dname': 'Топоры дикой охоты', 'desc': 'Бросает два топора.', 'img': 'beastmaster_axes.png'},
            {'dname': 'Оглушительный рёв', 'desc': 'Оглушает врагов.', 'img': 'beastmaster_roar.png'}
        ]
    },
    'alchemist': {
        'data': {
            'localized_name': 'Alchemist',
            'bio': 'Алхимик — герой силы, который зарабатывает золото быстрее всех.',
            'base_str': 23, 'base_agi': 18, 'base_int': 19,
            'base_health': 630, 'base_mana': 300, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.7, 'agi_gain': 1.6, 'int_gain': 1.9
        },
        'abilities': [
            {'dname': 'Нестабильная смесь', 'desc': 'Бросает кислоту, наносящую урон.', 'img': 'alchemist_acid_spray.png'},
            {'dname': 'Нестабильная смесь', 'desc': 'Взрывает врагов.', 'img': 'alchemist_unstable_concoction.png'},
            {'dname': 'Огненный щит', 'desc': 'Сжигает врагов вокруг.', 'img': 'alchemist_fire_shield.png'},
            {'dname': 'Алхимия', 'desc': 'Пассивно увеличивает золото.', 'img': 'alchemist_greevils_greed.png'}
        ]
    },
    'antimage': {
        'data': {
            'localized_name': 'Anti-Mage',
            'bio': 'Anti-Mage — герой ловкости, который уничтожает ману врагов.',
            'base_str': 21, 'base_agi': 25, 'base_int': 12,
            'base_health': 580, 'base_mana': 280, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 315,
            'base_attack_min': 54, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.6, 'agi_gain': 2.8, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Удар маны', 'desc': 'Сжигает ману врага.', 'img': 'antimage_mana_break.png'},
            {'dname': 'Телепорт', 'desc': 'Телепортируется на короткое расстояние.', 'img': 'antimage_blink.png'},
            {'dname': 'Защита от магии', 'desc': 'Пассивная защита.', 'img': 'antimage_spell_shield.png'},
            {'dname': 'Уничтожение маны', 'desc': 'Наносит урон за сожжённую ману.', 'img': 'antimage_mana_void.png'}
        ]
    },
    'crystal_maiden': {
        'data': {
            'localized_name': 'Crystal Maiden',
            'bio': 'Crystal Maiden — герой интеллекта, который контролирует врагов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Ледяная глыба', 'desc': 'Замораживает врага.', 'img': 'crystal_maiden_crystal_nova.png'},
            {'dname': 'Ледяная глыба', 'desc': 'Наносит урон и замедляет.', 'img': 'crystal_maiden_frostbite.png'},
            {'dname': 'Ледяная аура', 'desc': 'Пассивное замедление.', 'img': 'crystal_maiden_crystal_aura.png'},
            {'dname': 'Ледяной шторм', 'desc': 'Наносит огромный урон по области.', 'img': 'crystal_maiden_freezing_field.png'}
        ]
    },
    'invoker': {
        'data': {
            'localized_name': 'Invoker',
            'bio': 'Invoker — герой интеллекта, который комбинирует стихии.',
            'base_str': 19, 'base_agi': 20, 'base_int': 24,
            'base_health': 580, 'base_mana': 340, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 3.5
        },
        'abilities': [
            {'dname': 'Экзорцизм', 'desc': 'Комбинация стихий.', 'img': 'invoker_invoke.png'},
            {'dname': 'Солнечный удар', 'desc': 'Наносит урон.', 'img': 'invoker_sun_strike.png'},
            {'dname': 'Ледяная стена', 'desc': 'Создаёт стену.', 'img': 'invoker_ice_wall.png'},
            {'dname': 'Метеорит', 'desc': 'Призывает метеорит.', 'img': 'invoker_meteor.png'}
        ]
    },
    'juggernaut': {
        'data': {
            'localized_name': 'Juggernaut',
            'bio': 'Juggernaut — герой ловкости, который убивает врагов ультимейтом.',
            'base_str': 20, 'base_agi': 22, 'base_int': 16,
            'base_health': 580, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 2.0, 'agi_gain': 2.6, 'int_gain': 1.6
        },
        'abilities': [
            {'dname': 'Вихрь клинков', 'desc': 'Наносит урон вокруг.', 'img': 'juggernaut_blade_fury.png'},
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'juggernaut_healing_ward.png'},
            {'dname': 'Удар по площади', 'desc': 'Наносит дополнительный урон.', 'img': 'juggernaut_blade_dance.png'},
            {'dname': 'Омнислэш', 'desc': 'Наносит удары по всем врагам.', 'img': 'juggernaut_omni_slash.png'}
        ]
    },
    'lion': {
        'data': {
            'localized_name': 'Lion',
            'bio': 'Lion — герой интеллекта, который уничтожает врагов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Землетрясение', 'desc': 'Оглушает врагов.', 'img': 'lion_impale.png'},
            {'dname': 'Вытягивание маны', 'desc': 'Крадёт ману.', 'img': 'lion_mana_drain.png'},
            {'dname': 'Трансформация', 'desc': 'Превращает врага.', 'img': 'lion_hex.png'},
            {'dname': 'Пронзающий взгляд', 'desc': 'Наносит огромный урон.', 'img': 'lion_finger_of_death.png'}
        ]
    },
    'phantom_assassin': {
        'data': {
            'localized_name': 'Phantom Assassin',
            'bio': 'Phantom Assassin — герой ловкости, которая убивает с критическим ударом.',
            'base_str': 19, 'base_agi': 23, 'base_int': 15,
            'base_health': 560, 'base_mana': 280, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.8, 'int_gain': 1.6
        },
        'abilities': [
            {'dname': 'Кинжал', 'desc': 'Бросает кинжал.', 'img': 'phantom_assassin_stifling_dagger.png'},
            {'dname': 'Уклонение', 'desc': 'Уклоняется от атак.', 'img': 'phantom_assassin_blur.png'},
            {'dname': 'Критический удар', 'desc': 'Наносит критический урон.', 'img': 'phantom_assassin_coup_de_grace.png'},
            {'dname': 'Смертельный удар', 'desc': 'Телепортируется и наносит урон.', 'img': 'phantom_assassin_phantom_strike.png'}
        ]
    },
    'puck': {
        'data': {
            'localized_name': 'Puck',
            'bio': 'Puck — герой интеллекта, который уклоняется от врагов.',
            'base_str': 17, 'base_agi': 18, 'base_int': 22,
            'base_health': 520, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Сфера', 'desc': 'Выпускает сферу.', 'img': 'puck_illusory_orb.png'},
            {'dname': 'Фаза', 'desc': 'Уклоняется от атак.', 'img': 'puck_phase_shift.png'},
            {'dname': 'Подавление', 'desc': 'Оглушает врагов.', 'img': 'puck_waning_rift.png'},
            {'dname': 'Сон', 'desc': 'Усыпляет врагов.', 'img': 'puck_dream_coil.png'}
        ]
    },
    'razor': {
        'data': {
            'localized_name': 'Razor',
            'bio': 'Razor — герой ловкости, который крадёт урон.',
            'base_str': 20, 'base_agi': 22, 'base_int': 18,
            'base_health': 580, 'base_mana': 300, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 295,
            'base_attack_min': 50, 'base_attack_max': 56, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 2.0, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Плазменная дуга', 'desc': 'Крадёт урон.', 'img': 'razor_plasma_field.png'},
            {'dname': 'Статическая связь', 'desc': 'Крадёт урон.', 'img': 'razor_static_link.png'},
            {'dname': 'Шторм', 'desc': 'Наносит урон вокруг.', 'img': 'razor_unstable_current.png'},
            {'dname': 'Глаз бури', 'desc': 'Наносит урон по области.', 'img': 'razor_eye_of_the_storm.png'}
        ]
    },
    'sniper': {
        'data': {
            'localized_name': 'Sniper',
            'bio': 'Sniper — герой ловкости, который стреляет издалека.',
            'base_str': 18, 'base_agi': 20, 'base_int': 18,
            'base_health': 560, 'base_mana': 300, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 290,
            'base_attack_min': 45, 'base_attack_max': 55, 'attack_range': 600,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Прицельный выстрел', 'desc': 'Наносит урон и замедляет.', 'img': 'sniper_shrapnel.png'},
            {'dname': 'Головной выстрел', 'desc': 'Наносит дополнительный урон.', 'img': 'sniper_headshot.png'},
            {'dname': 'Снайперская стойка', 'desc': 'Увеличивает дальность.', 'img': 'sniper_take_aim.png'},
            {'dname': 'Выстрел в голову', 'desc': 'Наносит огромный урон.', 'img': 'sniper_assassinate.png'}
        ]
    },
    'storm_spirit': {
        'data': {
            'localized_name': 'Storm Spirit',
            'bio': 'Storm Spirit — герой интеллекта, который перемещается молниеносно.',
            'base_str': 19, 'base_agi': 20, 'base_int': 22,
            'base_health': 560, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Молния', 'desc': 'Наносит урон.', 'img': 'storm_spirit_static_remnant.png'},
            {'dname': 'Электрический рывок', 'desc': 'Телепортируется.', 'img': 'storm_spirit_electric_vortex.png'},
            {'dname': 'Шаровая молния', 'desc': 'Перемещается через врагов.', 'img': 'storm_spirit_ball_lightning.png'},
            {'dname': 'Разряд', 'desc': 'Наносит урон по области.', 'img': 'storm_spirit_overload.png'}
        ]
    },
    'sven': {
        'data': {
            'localized_name': 'Sven',
            'bio': 'Sven — герой силы, который наносит огромный урон.',
            'base_str': 25, 'base_agi': 18, 'base_int': 16,
            'base_health': 650, 'base_mana': 280, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 310,
            'base_attack_min': 50, 'base_attack_max': 60, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 2.0, 'int_gain': 1.6
        },
        'abilities': [
            {'dname': 'Божественный молот', 'desc': 'Наносит урон по области.', 'img': 'sven_storm_hammer.png'},
            {'dname': 'Божественный меч', 'desc': 'Увеличивает урон.', 'img': 'sven_gods_strength.png'},
            {'dname': 'Божественная броня', 'desc': 'Увеличивает броню.', 'img': 'sven_warcry.png'},
            {'dname': 'Удар молнии', 'desc': 'Наносит урон.', 'img': 'sven_cleave.png'}
        ]
    },
    'tiny': {
        'data': {
            'localized_name': 'Tiny',
            'bio': 'Tiny — герой силы, который бросает врагов.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 62, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 3.0, 'agi_gain': 1.8, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Бросок', 'desc': 'Бросает врага.', 'img': 'tiny_toss.png'},
            {'dname': 'Камень', 'desc': 'Наносит урон.', 'img': 'tiny_avalanche.png'},
            {'dname': 'Удар', 'desc': 'Наносит урон.', 'img': 'tiny_tree_grab.png'},
            {'dname': 'Удар', 'desc': 'Наносит урон.', 'img': 'tiny_tree_throw.png'}
        ]
    },
    'zeus': {
        'data': {
            'localized_name': 'Zeus',
            'bio': 'Zeus — герой интеллекта, который убивает врагов молниями.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Молния', 'desc': 'Наносит урон.', 'img': 'zeus_arc_lightning.png'},
            {'dname': 'Священный удар', 'desc': 'Наносит урон.', 'img': 'zeus_lightning_bolt.png'},
            {'dname': 'Божественный удар', 'desc': 'Наносит урон по всем врагам.', 'img': 'zeus_thundergods_wrath.png'},
            {'dname': 'Статический разряд', 'desc': 'Наносит урон.', 'img': 'zeus_static_field.png'}
        ]
    }
}

def get_local_hero_data(hero_name):
    """Возвращает локальные данные героя если они есть"""
    if hero_name in LOCAL_HEROES_DATA:
        return LOCAL_HEROES_DATA[hero_name]
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
    """Тестовый маршрут для проверки работы роутинга"""
    return f"""
    <h1>Тест маршрута героя</h1>
    <p>Герой: <strong>{hero_name}</strong></p>
    <p>Если вы видите это сообщение — маршрут работает!</p>
    <p><a href="/">На главную</a></p>
    """

@app.route('/hero/<hero_name>')
def hero_page(hero_name):
    """Страница героя"""
    print(f"🔍 Запрос героя: {hero_name}")
    
    hero_data = get_hero_data(hero_name)
    print(f"📦 Данные героя: {hero_data is not None}")
    
    if not hero_data:
        print("❌ Герой не найден, редирект на главную")
        return redirect(url_for('index'))
    
    print("✅ Рендерим hero.html")
    return render_template('hero.html', 
                          hero=hero_data['data'],
                          abilities=hero_data['abilities'])

@app.route('/api/hero/<hero_name>')
def api_hero(hero_name):
    """API для получения данных героя (с fallback)"""
    print(f"🔍 API запрос героя: {hero_name}")
    
    # Пытаемся получить данные из OpenDota
    hero_data = get_hero_data(hero_name)
    
    # Если OpenDota не ответил — используем локальные данные
    if not hero_data:
        print(f"⚠️ OpenDota не ответил, ищем локальные данные для {hero_name}")
        
        # Проверяем локальные данные
        local_data = get_local_hero_data(hero_name)
        if local_data:
            print(f"✅ Использованы локальные данные для {hero_name}")
            return jsonify(local_data)
        
        # Если героя нет в локальных данных — возвращаем общий fallback
        print(f"❌ Герой {hero_name} не найден в локальных данных, используем общий fallback")
        return jsonify({
            'data': {
                'localized_name': hero_name.capitalize(),
                'bio': 'Это тестовое описание героя ' + hero_name.capitalize() + '. Здесь будет полная информация о герое, его способностях и статистике.',
                'base_str': 22,
                'base_agi': 18,
                'base_int': 20,
                'base_health': 600,
                'base_mana': 300,
                'base_armor': 2,
                'attack_rate': 1.7,
                'move_speed': 300,
                'base_attack_min': 45,
                'base_attack_max': 55,
                'attack_range': 150,
                'primary_attr': 'universal',
                'str_gain': 2.6,
                'agi_gain': 1.8,
                'int_gain': 2.0
            },
            'abilities': [
                {'dname': 'Способность 1', 'desc': 'Описание способности 1', 'img': 'default_ability.png'},
                {'dname': 'Способность 2', 'desc': 'Описание способности 2', 'img': 'default_ability.png'},
                {'dname': 'Способность 3', 'desc': 'Описание способности 3', 'img': 'default_ability.png'},
                {'dname': 'Способность 4', 'desc': 'Описание способности 4', 'img': 'default_ability.png'}
            ]
        })
    
    return jsonify(hero_data)

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
    print(f"✅ Добавлена тестовая новость")
    print("=" * 60)

initialize_news()

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)