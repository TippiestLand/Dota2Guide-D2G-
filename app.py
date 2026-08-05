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
# ЛОКАЛЬНЫЕ ДАННЫЕ ГЕРОЕВ (СО ВСЕМИ СПОСОБНОСТЯМИ)
# ============================================================
LOCAL_HEROES_DATA = {
    'abaddon': {
        'data': {
            'localized_name': 'Abaddon',
            'bio': 'Абаддон — универсальный герой, защищающий союзников. Его способности позволяют лечить, создавать щиты и возвращать урон.',
            'base_str': 22, 'base_agi': 15, 'base_int': 18,
            'base_health': 620, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.7, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'universal',
            'str_gain': 2.6, 'agi_gain': 1.5, 'int_gain': 2.0
        },
        'abilities': [
            {'dname': 'Мистический туман', 'desc': 'Лечит союзников или наносит урон врагам.', 'img': 'abaddon_mist_coil.png'},
            {'dname': 'Щит без света', 'desc': 'Создаёт щит, поглощающий урон. При разрушении взрывается.', 'img': 'abaddon_aphotic_shield.png'},
            {'dname': 'Ледяная скорбь', 'desc': 'Атаки замедляют врагов и наносят дополнительный урон.', 'img': 'abaddon_frostmourne.png'},
            {'dname': 'Возврат времени', 'desc': 'Превращает получаемый урон в исцеление.', 'img': 'abaddon_borrowed_time.png'},
            {'dname': 'Врождённая: Дыхание тьмы', 'desc': 'Пассивно накладывает ослабление на врагов.', 'img': 'abaddon_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Возврат времени активируется автоматически при низком здоровье.', 'img': 'abaddon_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Мистический туман наносит дополнительный урон.', 'img': 'abaddon_shard.png'}
        ]
    },
    'axe': {
        'data': {
            'localized_name': 'Axe',
            'bio': 'Акс — герой силы, заставляющий врагов атаковать его. Наносит чистый урон и уничтожает слабых врагов.',
            'base_str': 25, 'base_agi': 20, 'base_int': 18,
            'base_health': 660, 'base_mana': 300, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 60, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 2.0, 'int_gain': 1.6
        },
        'abilities': [
            {'dname': 'Боевой клич', 'desc': 'Провоцирует врагов атаковать Акса.', 'img': 'axe_berserkers_call.png'},
            {'dname': 'Голод битвы', 'desc': 'Наносит урон и замедляет врага.', 'img': 'axe_battle_hunger.png'},
            {'dname': 'Контр-удар', 'desc': 'Пассивная способность, наносящая урон при атаке.', 'img': 'axe_counter_helix.png'},
            {'dname': 'Уничтожение', 'desc': 'Мгновенно уничтожает врага с низким здоровьем.', 'img': 'axe_culling_blade.png'},
            {'dname': 'Врождённая: Ярость', 'desc': 'Акс получает дополнительную броню с каждым убийством.', 'img': 'axe_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Уничтожение сбрасывает перезарядку при убийстве.', 'img': 'axe_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Голод битвы наносит дополнительный урон.', 'img': 'axe_shard.png'}
        ]
    },
    'pudge': {
        'data': {
            'localized_name': 'Pudge',
            'bio': 'Пудж — герой силы, известный своим мясным крюком. Вытягивает врагов и восстанавливает здоровье.',
            'base_str': 25, 'base_agi': 14, 'base_int': 16,
            'base_health': 650, 'base_mana': 280, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 52, 'base_attack_max': 62, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 3.2, 'agi_gain': 1.5, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Мясной крюк', 'desc': 'Бросает крюк, вытягивая врага к Пуджу.', 'img': 'pudge_meat_hook.png'},
            {'dname': 'Гниение', 'desc': 'Выпускает ядовитый газ, наносящий урон врагам.', 'img': 'pudge_rot.png'},
            {'dname': 'Плоть', 'desc': 'Пассивно увеличивает урон и здоровье.', 'img': 'pudge_flesh_heap.png'},
            {'dname': 'Расчленение', 'desc': 'Наносит огромный урон и восстанавливает здоровье.', 'img': 'pudge_dismember.png'},
            {'dname': 'Врождённая: Крюк', 'desc': 'Мясной крюк наносит дополнительный урон.', 'img': 'pudge_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Расчленение лечит союзников.', 'img': 'pudge_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Гниение наносит дополнительный урон.', 'img': 'pudge_shard.png'}
        ]
    },
    'beastmaster': {
        'data': {
            'localized_name': 'Beastmaster',
            'bio': 'Beastmaster призывает зверей на помощь. Его оглушительный рёв позволяет напасть на врагов.',
            'base_str': 24, 'base_agi': 19, 'base_int': 16,
            'base_health': 640, 'base_mana': 310, 'base_armor': 2.0,
            'attack_rate': 2.2, 'move_speed': 310,
            'base_attack_min': 49, 'base_attack_max': 53, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.9, 'agi_gain': 2.0, 'int_gain': 1.9
        },
        'abilities': [
            {'dname': 'Призыв кабана', 'desc': 'Призывает кабана, который замедляет врагов.', 'img': 'beastmaster_boar.png'},
            {'dname': 'Призыв ястреба', 'desc': 'Призывает ястреба, дающего обзор.', 'img': 'beastmaster_hawk.png'},
            {'dname': 'Топоры дикой охоты', 'desc': 'Бросает два топора, проходящих сквозь врагов.', 'img': 'beastmaster_axes.png'},
            {'dname': 'Оглушительный рёв', 'desc': 'Оглушает врагов и ускоряет союзников.', 'img': 'beastmaster_roar.png'},
            {'dname': 'Врождённая: Звериная мощь', 'desc': 'Увеличивает урон призванных существ.', 'img': 'beastmaster_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Рёв наносит дополнительный урон.', 'img': 'beastmaster_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Топоры наносят дополнительный урон.', 'img': 'beastmaster_shard.png'}
        ]
    },
    'bristleback': {
        'data': {
            'localized_name': 'Bristleback',
            'bio': 'Bristleback — герой силы, который получает меньше урона со спины.',
            'base_str': 23, 'base_agi': 17, 'base_int': 15,
            'base_health': 630, 'base_mana': 280, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.8, 'int_gain': 1.6
        },
        'abilities': [
            {'dname': 'Иглы', 'desc': 'Наносит урон врагам вокруг.', 'img': 'bristleback_quill_spray.png'},
            {'dname': 'Бронированная спина', 'desc': 'Уменьшает урон со спины.', 'img': 'bristleback_bristleback.png'},
            {'dname': 'Сопли', 'desc': 'Замедляет врага и снижает его броню.', 'img': 'bristleback_viscous_nasal_goo.png'},
            {'dname': 'Варварство', 'desc': 'Увеличивает урон и скорость атаки.', 'img': 'bristleback_warpath.png'},
            {'dname': 'Врождённая: Колючки', 'desc': 'Иглы наносят дополнительный урон.', 'img': 'bristleback_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Варварство увеличивает броню.', 'img': 'bristleback_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Сопли наносят дополнительный урон.', 'img': 'bristleback_shard.png'}
        ]
    },
    'centaur': {
        'data': {
            'localized_name': 'Centaur Warrunner',
            'bio': 'Centaur Warrunner — герой силы, который наносит урон при получении атак.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Топот', 'desc': 'Оглушает врагов вокруг.', 'img': 'centaur_hoof_stomp.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'centaur_double_edge.png'},
            {'dname': 'Возврат урона', 'desc': 'Возвращает урон врагам.', 'img': 'centaur_return.png'},
            {'dname': 'Стойкость', 'desc': 'Увеличивает здоровье и урон.', 'img': 'centaur_stampede.png'},
            {'dname': 'Врождённая: Копыта', 'desc': 'Удар наносит дополнительный урон.', 'img': 'centaur_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Стойкость увеличивает броню.', 'img': 'centaur_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Топот наносит дополнительный урон.', 'img': 'centaur_shard.png'}
        ]
    },
    'chaos_knight': {
        'data': {
            'localized_name': 'Chaos Knight',
            'bio': 'Chaos Knight — герой силы, который создаёт иллюзии и наносит огромный урон.',
            'base_str': 24, 'base_agi': 18, 'base_int': 16,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 310,
            'base_attack_min': 52, 'base_attack_max': 62, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.9, 'agi_gain': 1.8, 'int_gain': 1.6
        },
        'abilities': [
            {'dname': 'Хаотичный удар', 'desc': 'Оглушает врага и наносит случайный урон.', 'img': 'chaos_knight_chaos_bolt.png'},
            {'dname': 'Реальность', 'desc': 'Телепортирует к врагу и притягивает его.', 'img': 'chaos_knight_reality_rift.png'},
            {'dname': 'Критический удар', 'desc': 'Пассивная способность, наносящая критический урон.', 'img': 'chaos_knight_chaos_strike.png'},
            {'dname': 'Фантазм', 'desc': 'Создаёт иллюзии героя.', 'img': 'chaos_knight_phantasm.png'},
            {'dname': 'Врождённая: Хаос', 'desc': 'Хаотичный удар наносит дополнительный урон.', 'img': 'chaos_knight_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Фантазм создаёт дополнительные иллюзии.', 'img': 'chaos_knight_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Реальность наносит дополнительный урон.', 'img': 'chaos_knight_shard.png'}
        ]
    },
    'clockwerk': {
        'data': {
            'localized_name': 'Clockwerk',
            'bio': 'Clockwerk — герой силы, который управляет механизмами.',
            'base_str': 22, 'base_agi': 16, 'base_int': 18,
            'base_health': 620, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.7, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Батарейка', 'desc': 'Наносит урон врагам вокруг.', 'img': 'rattletrap_battery_assault.png'},
            {'dname': 'Коготь', 'desc': 'Цепляется за врага.', 'img': 'rattletrap_power_cogs.png'},
            {'dname': 'Ракета', 'desc': 'Запускает ракету.', 'img': 'rattletrap_rocket_flare.png'},
            {'dname': 'Крюк', 'desc': 'Цепляется за врага.', 'img': 'rattletrap_hookshot.png'},
            {'dname': 'Врождённая: Механика', 'desc': 'Батарейка наносит дополнительный урон.', 'img': 'rattletrap_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Крюк наносит дополнительный урон.', 'img': 'rattletrap_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Коготь наносит дополнительный урон.', 'img': 'rattletrap_shard.png'}
        ]
    },
    'dawnbreaker': {
        'data': {
            'localized_name': 'Dawnbreaker',
            'bio': 'Dawnbreaker — герой силы, которая призывает молнию.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Молот', 'desc': 'Бросает молот, наносящий урон.', 'img': 'dawnbreaker_starbreaker.png'},
            {'dname': 'Исцеление', 'desc': 'Лечит союзников.', 'img': 'dawnbreaker_celestial_hammer.png'},
            {'dname': 'Свет', 'desc': 'Наносит урон врагам.', 'img': 'dawnbreaker_luminosity.png'},
            {'dname': 'Ультимейт', 'desc': 'Призывает молнию.', 'img': 'dawnbreaker_solar_guardian.png'},
            {'dname': 'Врождённая: Свет', 'desc': 'Молот наносит дополнительный урон.', 'img': 'dawnbreaker_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'dawnbreaker_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Исцеление наносит дополнительный урон.', 'img': 'dawnbreaker_shard.png'}
        ]
    },
    'doom_bringer': {
        'data': {
            'localized_name': 'Doom',
            'bio': 'Doom — герой силы, который накладывает проклятие на врагов.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Пожирание', 'desc': 'Пожирает врага, получая его способности.', 'img': 'doom_bringer_devour.png'},
            {'dname': 'Выжженная земля', 'desc': 'Наносит урон врагам вокруг.', 'img': 'doom_bringer_scorched_earth.png'},
            {'dname': 'Смертельный удар', 'desc': 'Наносит дополнительный урон.', 'img': 'doom_bringer_lvl_death.png'},
            {'dname': 'Судьба', 'desc': 'Останавливает врага.', 'img': 'doom_bringer_doom.png'},
            {'dname': 'Врождённая: Ад', 'desc': 'Пожирание наносит дополнительный урон.', 'img': 'doom_bringer_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Судьба наносит дополнительный урон.', 'img': 'doom_bringer_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Выжженная земля наносит дополнительный урон.', 'img': 'doom_bringer_shard.png'}
        ]
    },
    'dragon_knight': {
        'data': {
            'localized_name': 'Dragon Knight',
            'bio': 'Dragon Knight — герой силы, который превращается в дракона.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Дыхание дракона', 'desc': 'Наносит урон врагам.', 'img': 'dragon_knight_breathe_fire.png'},
            {'dname': 'Кровь дракона', 'desc': 'Увеличивает броню.', 'img': 'dragon_knight_dragon_blood.png'},
            {'dname': 'Удар дракона', 'desc': 'Наносит дополнительный урон.', 'img': 'dragon_knight_dragon_tail.png'},
            {'dname': 'Форма дракона', 'desc': 'Превращается в дракона.', 'img': 'dragon_knight_elder_dragon_form.png'},
            {'dname': 'Врождённая: Дракон', 'desc': 'Дыхание дракона наносит дополнительный урон.', 'img': 'dragon_knight_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Форма дракона увеличивает урон.', 'img': 'dragon_knight_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар дракона наносит дополнительный урон.', 'img': 'dragon_knight_shard.png'}
        ]
    },
    'earth_spirit': {
        'data': {
            'localized_name': 'Earth Spirit',
            'bio': 'Earth Spirit — герой силы, который управляет камнями.',
            'base_str': 22, 'base_agi': 16, 'base_int': 18,
            'base_health': 620, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.7, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Камень', 'desc': 'Бросает камень.', 'img': 'earth_spirit_boulder_smash.png'},
            {'dname': 'Толчок', 'desc': 'Толкает врага.', 'img': 'earth_spirit_rolling_boulder.png'},
            {'dname': 'Земля', 'desc': 'Наносит урон врагам.', 'img': 'earth_spirit_geomagnetic_grip.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'earth_spirit_magnetize.png'},
            {'dname': 'Врождённая: Земля', 'desc': 'Камень наносит дополнительный урон.', 'img': 'earth_spirit_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'earth_spirit_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Толчок наносит дополнительный урон.', 'img': 'earth_spirit_shard.png'}
        ]
    },
    'earthshaker': {
        'data': {
            'localized_name': 'Earthshaker',
            'bio': 'Earthshaker — герой силы, который создаёт трещины в земле.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Трещина', 'desc': 'Создаёт трещину в земле.', 'img': 'earthshaker_fissure.png'},
            {'dname': 'Тотем', 'desc': 'Увеличивает урон следующей атаки.', 'img': 'earthshaker_enchant_totem.png'},
            {'dname': 'Отдача', 'desc': 'Наносит урон после каждой способности.', 'img': 'earthshaker_aftershock.png'},
            {'dname': 'Эхо-удар', 'desc': 'Наносит урон по площади.', 'img': 'earthshaker_echo_slam.png'},
            {'dname': 'Врождённая: Земля', 'desc': 'Трещина наносит дополнительный урон.', 'img': 'earthshaker_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Эхо-удар наносит дополнительный урон.', 'img': 'earthshaker_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Тотем наносит дополнительный урон.', 'img': 'earthshaker_shard.png'}
        ]
    },
    'elder_titan': {
        'data': {
            'localized_name': 'Elder Titan',
            'bio': 'Elder Titan — герой силы, который управляет землёй.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Стук', 'desc': 'Наносит урон врагам.', 'img': 'elder_titan_echo_stomp.png'},
            {'dname': 'Дух', 'desc': 'Призывает духа.', 'img': 'elder_titan_astral_spirit.png'},
            {'dname': 'Аура', 'desc': 'Увеличивает броню.', 'img': 'elder_titan_natural_order.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'elder_titan_earth_splitter.png'},
            {'dname': 'Врождённая: Титан', 'desc': 'Стук наносит дополнительный урон.', 'img': 'elder_titan_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'elder_titan_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Дух наносит дополнительный урон.', 'img': 'elder_titan_shard.png'}
        ]
    },
    'huskar': {
        'data': {
            'localized_name': 'Huskar',
            'bio': 'Huskar — герой силы, который жертвует здоровьем для урона.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Внутренняя сила', 'desc': 'Лечит союзников.', 'img': 'huskar_inner_vitality.png'},
            {'dname': 'Горящее копьё', 'desc': 'Наносит урон врагам.', 'img': 'huskar_burning_spear.png'},
            {'dname': 'Жертва', 'desc': 'Жертвует здоровьем.', 'img': 'huskar_life_break.png'},
            {'dname': 'Божественный удар', 'desc': 'Наносит урон врагам.', 'img': 'huskar_life_break.png'},
            {'dname': 'Врождённая: Жертва', 'desc': 'Внутренняя сила наносит дополнительный урон.', 'img': 'huskar_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Жертва наносит дополнительный урон.', 'img': 'huskar_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Горящее копьё наносит дополнительный урон.', 'img': 'huskar_shard.png'}
        ]
    },
    'kunkka': {
        'data': {
            'localized_name': 'Kunkka',
            'bio': 'Kunkka — герой силы, который управляет водой.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Поток', 'desc': 'Создаёт волну.', 'img': 'kunkka_torrent.png'},
            {'dname': 'Прилив', 'desc': 'Наносит урон врагам.', 'img': 'kunkka_tidebringer.png'},
            {'dname': 'Корабль-призрак', 'desc': 'Призывает корабль.', 'img': 'kunkka_ghost_ship.png'},
            {'dname': 'Метка', 'desc': 'Помечает врага.', 'img': 'kunkka_x_marks_the_spot.png'},
            {'dname': 'Врождённая: Море', 'desc': 'Поток наносит дополнительный урон.', 'img': 'kunkka_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Корабль-призрак наносит дополнительный урон.', 'img': 'kunkka_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Прилив наносит дополнительный урон.', 'img': 'kunkka_shard.png'}
        ]
    },
    'legion_commander': {
        'data': {
            'localized_name': 'Legion Commander',
            'bio': 'Legion Commander — герой силы, которая вызывает врагов на дуэль.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Подавляющие шансы', 'desc': 'Наносит урон врагам.', 'img': 'legion_commander_overwhelming_odds.png'},
            {'dname': 'Атака', 'desc': 'Лечит союзников.', 'img': 'legion_commander_press_the_attack.png'},
            {'dname': 'Мгновение храбрости', 'desc': 'Пассивный урон.', 'img': 'legion_commander_moment_of_courage.png'},
            {'dname': 'Дуэль', 'desc': 'Вызывает врага на дуэль.', 'img': 'legion_commander_duel.png'},
            {'dname': 'Врождённая: Легион', 'desc': 'Подавляющие шансы наносят дополнительный урон.', 'img': 'legion_commander_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Дуэль наносит дополнительный урон.', 'img': 'legion_commander_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Атака наносит дополнительный урон.', 'img': 'legion_commander_shard.png'}
        ]
    },
    'life_stealer': {
        'data': {
            'localized_name': 'Lifestealer',
            'bio': 'Lifestealer — герой силы, который восстанавливает здоровье от атак.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Ярость', 'desc': 'Увеличивает скорость атаки.', 'img': 'life_stealer_rage.png'},
            {'dname': 'Пир', 'desc': 'Восстанавливает здоровье от атак.', 'img': 'life_stealer_feast.png'},
            {'dname': 'Открытые раны', 'desc': 'Заражает врага.', 'img': 'life_stealer_open_wounds.png'},
            {'dname': 'Заражение', 'desc': 'Вселяется в врага.', 'img': 'life_stealer_infest.png'},
            {'dname': 'Врождённая: Жизнь', 'desc': 'Пир наносит дополнительный урон.', 'img': 'life_stealer_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Заражение наносит дополнительный урон.', 'img': 'life_stealer_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Открытые раны наносят дополнительный урон.', 'img': 'life_stealer_shard.png'}
        ]
    },
    'lycan': {
        'data': {
            'localized_name': 'Lycan',
            'bio': 'Lycan — герой силы, который превращается в волка.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Призыв волков', 'desc': 'Призывает волков.', 'img': 'lycan_summon_wolves.png'},
            {'dname': 'Вой', 'desc': 'Увеличивает скорость.', 'img': 'lycan_howl.png'},
            {'dname': 'Яростный импульс', 'desc': 'Увеличивает урон.', 'img': 'lycan_feral_impulse.png'},
            {'dname': 'Оборотень', 'desc': 'Превращается в волка.', 'img': 'lycan_shapeshift.png'},
            {'dname': 'Врождённая: Волк', 'desc': 'Призыв волков наносит дополнительный урон.', 'img': 'lycan_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Оборотень наносит дополнительный урон.', 'img': 'lycan_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Вой наносит дополнительный урон.', 'img': 'lycan_shard.png'}
        ]
    },
    'mars': {
        'data': {
            'localized_name': 'Mars',
            'bio': 'Mars — герой силы, который создаёт барьер из щитов.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Копьё', 'desc': 'Бросает копьё, наносящее урон.', 'img': 'mars_spear.png'},
            {'dname': 'Удар бога', 'desc': 'Наносит урон врагам.', 'img': 'mars_gods_rebuke.png'},
            {'dname': 'Бастион', 'desc': 'Увеличивает броню.', 'img': 'mars_bulwark.png'},
            {'dname': 'Арена крови', 'desc': 'Создаёт стену копий.', 'img': 'mars_arena_of_blood.png'},
            {'dname': 'Врождённая: Бог', 'desc': 'Копьё наносит дополнительный урон.', 'img': 'mars_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Арена крови наносит дополнительный урон.', 'img': 'mars_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар бога наносит дополнительный урон.', 'img': 'mars_shard.png'}
        ]
    },
    'night_stalker': {
        'data': {
            'localized_name': 'Night Stalker',
            'bio': 'Night Stalker — герой силы, который сильнее ночью.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Безмолвие', 'desc': 'Заставляет врага замолчать.', 'img': 'night_stalker_void.png'},
            {'dname': 'Парализующий страх', 'desc': 'Наносит дополнительный урон.', 'img': 'night_stalker_crippling_fear.png'},
            {'dname': 'Ночной охотник', 'desc': 'Увеличивает скорость ночью.', 'img': 'night_stalker_hunter_in_the_night.png'},
            {'dname': 'Тьма', 'desc': 'Погружает в темноту.', 'img': 'night_stalker_darkness.png'},
            {'dname': 'Врождённая: Ночь', 'desc': 'Безмолвие наносит дополнительный урон.', 'img': 'night_stalker_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Тьма наносит дополнительный урон.', 'img': 'night_stalker_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Парализующий страх наносит дополнительный урон.', 'img': 'night_stalker_shard.png'}
        ]
    },
    'ogre_magi': {
        'data': {
            'localized_name': 'Ogre Magi',
            'bio': 'Ogre Magi — герой силы, который бросает огненные шары.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Огненный шар', 'desc': 'Бросает огненный шар.', 'img': 'ogre_magi_fireblast.png'},
            {'dname': 'Замедление', 'desc': 'Замедляет врага.', 'img': 'ogre_magi_ignite.png'},
            {'dname': 'Кровожадность', 'desc': 'Увеличивает скорость атаки.', 'img': 'ogre_magi_bloodlust.png'},
            {'dname': 'Мультикаст', 'desc': 'Повторяет способности.', 'img': 'ogre_magi_multicast.png'},
            {'dname': 'Врождённая: Магия', 'desc': 'Огненный шар наносит дополнительный урон.', 'img': 'ogre_magi_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Мультикаст наносит дополнительный урон.', 'img': 'ogre_magi_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Замедление наносит дополнительный урон.', 'img': 'ogre_magi_shard.png'}
        ]
    },
    'omniknight': {
        'data': {
            'localized_name': 'Omniknight',
            'bio': 'Omniknight — герой силы, который лечит и защищает союзников.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Очищение', 'desc': 'Лечит союзников.', 'img': 'omniknight_purification.png'},
            {'dname': 'Отталкивание', 'desc': 'Защищает от магии.', 'img': 'omniknight_repel.png'},
            {'dname': 'Ангел-хранитель', 'desc': 'Защищает от физического урона.', 'img': 'omniknight_guardian_angel.png'},
            {'dname': 'Аура', 'desc': 'Замедляет врагов.', 'img': 'omniknight_degen_aura.png'},
            {'dname': 'Врождённая: Свет', 'desc': 'Очищение наносит дополнительный урон.', 'img': 'omniknight_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ангел-хранитель наносит дополнительный урон.', 'img': 'omniknight_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Отталкивание наносит дополнительный урон.', 'img': 'omniknight_shard.png'}
        ]
    },
    'phoenix': {
        'data': {
            'localized_name': 'Phoenix',
            'bio': 'Phoenix — герой силы, который возрождается из пепла.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Огненные духи', 'desc': 'Наносит урон врагам.', 'img': 'phoenix_fire_spirits.png'},
            {'dname': 'Луч', 'desc': 'Наносит урон по площади.', 'img': 'phoenix_sun_ray.png'},
            {'dname': 'Супернова', 'desc': 'Возрождается из яйца.', 'img': 'phoenix_supernova.png'},
            {'dname': 'Пикирование', 'desc': 'Пикирует на врагов.', 'img': 'phoenix_icarus_dive.png'},
            {'dname': 'Врождённая: Птица', 'desc': 'Огненные духи наносят дополнительный урон.', 'img': 'phoenix_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Супернова наносит дополнительный урон.', 'img': 'phoenix_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Луч наносит дополнительный урон.', 'img': 'phoenix_shard.png'}
        ]
    },
    'primal_beast': {
        'data': {
            'localized_name': 'Primal Beast',
            'bio': 'Primal Beast — герой силы, который наносит урон своими ударами.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Натиск', 'desc': 'Наносит урон врагам.', 'img': 'primal_beast_onslaught.png'},
            {'dname': 'Топот', 'desc': 'Увеличивает урон.', 'img': 'primal_beast_trample.png'},
            {'dname': 'Шум', 'desc': 'Увеличивает броню.', 'img': 'primal_beast_uproar.png'},
            {'dname': 'Разрушение', 'desc': 'Наносит огромный урон.', 'img': 'primal_beast_pulverize.png'},
            {'dname': 'Врождённая: Зверь', 'desc': 'Натиск наносит дополнительный урон.', 'img': 'primal_beast_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Разрушение наносит дополнительный урон.', 'img': 'primal_beast_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Топот наносит дополнительный урон.', 'img': 'primal_beast_shard.png'}
        ]
    },
    'slardar': {
        'data': {
            'localized_name': 'Slardar',
            'bio': 'Slardar — герой силы, который оглушает врагов.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Дробление', 'desc': 'Оглушает врага.', 'img': 'slardar_slithereen_crush.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'slardar_bash.png'},
            {'dname': 'Усиление урона', 'desc': 'Снижает броню врага.', 'img': 'slardar_amplify_damage.png'},
            {'dname': 'Спринт', 'desc': 'Увеличивает броню.', 'img': 'slardar_guardian_sprint.png'},
            {'dname': 'Врождённая: Море', 'desc': 'Дробление наносит дополнительный урон.', 'img': 'slardar_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Усиление урона наносит дополнительный урон.', 'img': 'slardar_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'slardar_shard.png'}
        ]
    },
    'spirit_breaker': {
        'data': {
            'localized_name': 'Spirit Breaker',
            'bio': 'Spirit Breaker — герой силы, который таранит врагов.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Заряд тьмы', 'desc': 'Таранит врага.', 'img': 'spirit_breaker_charge_of_darkness.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'spirit_breaker_greater_bash.png'},
            {'dname': 'Ускорение', 'desc': 'Увеличивает скорость.', 'img': 'spirit_breaker_empowering_haste.png'},
            {'dname': 'Удар по площади', 'desc': 'Наносит урон по площади.', 'img': 'spirit_breaker_nether_strike.png'},
            {'dname': 'Врождённая: Тьма', 'desc': 'Заряд тьмы наносит дополнительный урон.', 'img': 'spirit_breaker_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Удар по площади наносит дополнительный урон.', 'img': 'spirit_breaker_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'spirit_breaker_shard.png'}
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
            {'dname': 'Молот', 'desc': 'Бросает молот, оглушающий врагов.', 'img': 'sven_storm_hammer.png'},
            {'dname': 'Сила бога', 'desc': 'Увеличивает урон на время.', 'img': 'sven_gods_strength.png'},
            {'dname': 'Боевой клич', 'desc': 'Увеличивает броню союзников.', 'img': 'sven_warcry.png'},
            {'dname': 'Рассечение', 'desc': 'Наносит урон по площади.', 'img': 'sven_great_cleave.png'},
            {'dname': 'Врождённая: Бог', 'desc': 'Молот наносит дополнительный урон.', 'img': 'sven_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Сила бога наносит дополнительный урон.', 'img': 'sven_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Рассечение наносит дополнительный урон.', 'img': 'sven_shard.png'}
        ]
    },
    'tidehunter': {
        'data': {
            'localized_name': 'Tidehunter',
            'bio': 'Tidehunter — герой силы, который наносит урон по площади.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Поток', 'desc': 'Создаёт волну, наносящую урон.', 'img': 'tidehunter_gush.png'},
            {'dname': 'Панцирь', 'desc': 'Уменьшает получаемый урон.', 'img': 'tidehunter_kraken_shell.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'tidehunter_anchor_smash.png'},
            {'dname': 'Опустошение', 'desc': 'Наносит урон по площади.', 'img': 'tidehunter_ravage.png'},
            {'dname': 'Врождённая: Море', 'desc': 'Поток наносит дополнительный урон.', 'img': 'tidehunter_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Опустошение наносит дополнительный урон.', 'img': 'tidehunter_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'tidehunter_shard.png'}
        ]
    },
    'timbersaw': {
        'data': {
            'localized_name': 'Timbersaw',
            'bio': 'Timbersaw — герой силы, который рубит деревья.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Смертельный вихрь', 'desc': 'Рубит деревья.', 'img': 'shredder_whirling_death.png'},
            {'dname': 'Цепь', 'desc': 'Цепляется за дерево.', 'img': 'shredder_timber_chain.png'},
            {'dname': 'Реактивная броня', 'desc': 'Увеличивает броню.', 'img': 'shredder_reactive_armor.png'},
            {'dname': 'Чакрам', 'desc': 'Наносит дополнительный урон.', 'img': 'shredder_chakram.png'},
            {'dname': 'Врождённая: Дерево', 'desc': 'Смертельный вихрь наносит дополнительный урон.', 'img': 'shredder_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Чакрам наносит дополнительный урон.', 'img': 'shredder_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Цепь наносит дополнительный урон.', 'img': 'shredder_shard.png'}
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
            {'dname': 'Лавина', 'desc': 'Наносит урон по площади.', 'img': 'tiny_avalanche.png'},
            {'dname': 'Хватка', 'desc': 'Увеличивает урон.', 'img': 'tiny_tree_grab.png'},
            {'dname': 'Бросок дерева', 'desc': 'Бросает дерево.', 'img': 'tiny_tree_throw.png'},
            {'dname': 'Врождённая: Камень', 'desc': 'Бросок наносит дополнительный урон.', 'img': 'tiny_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Лавина наносит дополнительный урон.', 'img': 'tiny_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Хватка наносит дополнительный урон.', 'img': 'tiny_shard.png'}
        ]
    },
    'treant': {
        'data': {
            'localized_name': 'Treant Protector',
            'bio': 'Treant Protector — герой силы, который защищает деревья.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Семя', 'desc': 'Укореняет врага.', 'img': 'treant_leech_seed.png'},
            {'dname': 'Живая броня', 'desc': 'Увеличивает броню союзника.', 'img': 'treant_living_armor.png'},
            {'dname': 'Маскировка', 'desc': 'Лечит союзников.', 'img': 'treant_natures_guise.png'},
            {'dname': 'Разрастание', 'desc': 'Наносит урон по площади.', 'img': 'treant_overgrowth.png'},
            {'dname': 'Врождённая: Природа', 'desc': 'Семя наносит дополнительный урон.', 'img': 'treant_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Разрастание наносит дополнительный урон.', 'img': 'treant_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Живая броня наносит дополнительный урон.', 'img': 'treant_shard.png'}
        ]
    },
    'tusk': {
        'data': {
            'localized_name': 'Tusk',
            'bio': 'Tusk — герой силы, который использует лёд.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Ледяные осколки', 'desc': 'Создаёт ледяной шар.', 'img': 'tusk_ice_shards.png'},
            {'dname': 'Снежок', 'desc': 'Наносит урон врагам.', 'img': 'tusk_snowball.png'},
            {'dname': 'Сигил', 'desc': 'Увеличивает броню.', 'img': 'tusk_frozen_sigil.png'},
            {'dname': 'Удар', 'desc': 'Наносит урон по площади.', 'img': 'tusk_walrus_punch.png'},
            {'dname': 'Врождённая: Лёд', 'desc': 'Ледяные осколки наносят дополнительный урон.', 'img': 'tusk_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Удар наносит дополнительный урон.', 'img': 'tusk_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Снежок наносит дополнительный урон.', 'img': 'tusk_shard.png'}
        ]
    },
    'underlord': {
        'data': {
            'localized_name': 'Underlord',
            'bio': 'Underlord — герой силы, который создаёт порталы.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Огненный шторм', 'desc': 'Наносит урон врагам.', 'img': 'abyssal_underlord_firestorm.png'},
            {'dname': 'Тёмный разрыв', 'desc': 'Создаёт портал.', 'img': 'abyssal_underlord_dark_rift.png'},
            {'dname': 'Аура истощения', 'desc': 'Увеличивает броню.', 'img': 'abyssal_underlord_atrophy_aura.png'},
            {'dname': 'Яма', 'desc': 'Наносит дополнительный урон.', 'img': 'abyssal_underlord_pit_of_malice.png'},
            {'dname': 'Врождённая: Тьма', 'desc': 'Огненный шторм наносит дополнительный урон.', 'img': 'abyssal_underlord_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Тёмный разрыв наносит дополнительный урон.', 'img': 'abyssal_underlord_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Яма наносит дополнительный урон.', 'img': 'abyssal_underlord_shard.png'}
        ]
    },
    'undying': {
        'data': {
            'localized_name': 'Undying',
            'bio': 'Undying — герой силы, который создаёт зомби.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Надгробие', 'desc': 'Призывает зомби.', 'img': 'undying_tombstone.png'},
            {'dname': 'Разложение', 'desc': 'Наносит урон врагам.', 'img': 'undying_decay.png'},
            {'dname': 'Разрыв души', 'desc': 'Лечит союзников.', 'img': 'undying_soul_rip.png'},
            {'dname': 'Голем', 'desc': 'Жертвует здоровьем.', 'img': 'undying_flesh_golem.png'},
            {'dname': 'Врождённая: Смерть', 'desc': 'Надгробие наносит дополнительный урон.', 'img': 'undying_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Голем наносит дополнительный урон.', 'img': 'undying_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Разложение наносит дополнительный урон.', 'img': 'undying_shard.png'}
        ]
    },
    'wraith_king': {
        'data': {
            'localized_name': 'Wraith King',
            'bio': 'Wraith King — герой силы, который возрождается после смерти.',
            'base_str': 24, 'base_agi': 16, 'base_int': 18,
            'base_health': 640, 'base_mana': 290, 'base_armor': 2.5,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 50, 'base_attack_max': 58, 'attack_range': 150,
            'primary_attr': 'str',
            'str_gain': 2.8, 'agi_gain': 1.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Адский взрыв', 'desc': 'Наносит урон врагам.', 'img': 'skeleton_king_hellfire_blast.png'},
            {'dname': 'Вампиризм', 'desc': 'Восстанавливает здоровье.', 'img': 'skeleton_king_vampiric_aura.png'},
            {'dname': 'Возрождение', 'desc': 'Возрождается после смерти.', 'img': 'skeleton_king_reincarnation.png'},
            {'dname': 'Смертельный удар', 'desc': 'Наносит урон по площади.', 'img': 'skeleton_king_mortal_strike.png'},
            {'dname': 'Врождённая: Король', 'desc': 'Адский взрыв наносит дополнительный урон.', 'img': 'skeleton_king_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Возрождение наносит дополнительный урон.', 'img': 'skeleton_king_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Смертельный удар наносит дополнительный урон.', 'img': 'skeleton_king_shard.png'}
        ]
    },
    # ===== ЛОВКОСТЬ =====
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
            {'dname': 'Щит', 'desc': 'Защита от магии.', 'img': 'antimage_spell_shield.png'},
            {'dname': 'Уничтожение маны', 'desc': 'Наносит урон за сожжённую ману.', 'img': 'antimage_mana_void.png'},
            {'dname': 'Врождённая: Магия', 'desc': 'Удар маны наносит дополнительный урон.', 'img': 'antimage_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Уничтожение маны наносит дополнительный урон.', 'img': 'antimage_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Телепорт наносит дополнительный урон.', 'img': 'antimage_shard.png'}
        ]
    },
    'bloodseeker': {
        'data': {
            'localized_name': 'Bloodseeker',
            'bio': 'Bloodseeker — герой ловкости, который преследует раненых врагов.',
            'base_str': 22, 'base_agi': 24, 'base_int': 16,
            'base_health': 600, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 50, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Жажда крови', 'desc': 'Увеличивает скорость при низком здоровье врага.', 'img': 'bloodseeker_strygwyr_thirst.png'},
            {'dname': 'Кровавая ярость', 'desc': 'Увеличивает урон.', 'img': 'bloodseeker_blood_rage.png'},
            {'dname': 'Кровавое исцеление', 'desc': 'Лечит от убийств.', 'img': 'bloodseeker_blood_bath.png'},
            {'dname': 'Разрыв', 'desc': 'Наносит урон при движении.', 'img': 'bloodseeker_rupture.png'},
            {'dname': 'Врождённая: Кровь', 'desc': 'Жажда крови наносит дополнительный урон.', 'img': 'bloodseeker_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Разрыв наносит дополнительный урон.', 'img': 'bloodseeker_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Кровавая ярость наносит дополнительный урон.', 'img': 'bloodseeker_shard.png'}
        ]
    },
    'bounty_hunter': {
        'data': {
            'localized_name': 'Bounty Hunter',
            'bio': 'Bounty Hunter — герой ловкости, который охотится на врагов.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 300, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 315,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Кинжал', 'desc': 'Бросает кинжал.', 'img': 'bounty_hunter_shuriken_toss.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'bounty_hunter_jinada.png'},
            {'dname': 'Отслеживание', 'desc': 'Помечает врага.', 'img': 'bounty_hunter_track.png'},
            {'dname': 'Невидимость', 'desc': 'Становится невидимым.', 'img': 'bounty_hunter_wind_walk.png'},
            {'dname': 'Врождённая: Охота', 'desc': 'Кинжал наносит дополнительный урон.', 'img': 'bounty_hunter_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Отслеживание наносит дополнительный урон.', 'img': 'bounty_hunter_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'bounty_hunter_shard.png'}
        ]
    },
    'broodmother': {
        'data': {
            'localized_name': 'Broodmother',
            'bio': 'Broodmother — герой ловкости, которая создаёт паутину.',
            'base_str': 20, 'base_agi': 22, 'base_int': 18,
            'base_health': 580, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 300,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Паутина', 'desc': 'Создаёт паутину.', 'img': 'broodmother_spin_web.png'},
            {'dname': 'Укус', 'desc': 'Наносит дополнительный урон.', 'img': 'broodmother_incapacitating_bite.png'},
            {'dname': 'Яйца', 'desc': 'Призывает пауков.', 'img': 'broodmother_spawn_spiderlings.png'},
            {'dname': 'Голод', 'desc': 'Наносит урон по площади.', 'img': 'broodmother_insatiable_hunger.png'},
            {'dname': 'Врождённая: Паутина', 'desc': 'Паутина наносит дополнительный урон.', 'img': 'broodmother_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Голод наносит дополнительный урон.', 'img': 'broodmother_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Укус наносит дополнительный урон.', 'img': 'broodmother_shard.png'}
        ]
    },
    'clinkz': {
        'data': {
            'localized_name': 'Clinkz',
            'bio': 'Clinkz — герой ловкости, который стреляет огненными стрелами.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 600,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Огненная стрела', 'desc': 'Наносит дополнительный урон.', 'img': 'clinkz_searing_arrows.png'},
            {'dname': 'Невидимость', 'desc': 'Становится невидимым.', 'img': 'clinkz_skeleton_walk.png'},
            {'dname': 'Армия', 'desc': 'Призывает скелетов.', 'img': 'clinkz_burning_army.png'},
            {'dname': 'Пожирание', 'desc': 'Увеличивает урон и здоровье.', 'img': 'clinkz_death_pact.png'},
            {'dname': 'Врождённая: Огонь', 'desc': 'Огненная стрела наносит дополнительный урон.', 'img': 'clinkz_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Пожирание наносит дополнительный урон.', 'img': 'clinkz_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Армия наносит дополнительный урон.', 'img': 'clinkz_shard.png'}
        ]
    },
    'drow_ranger': {
        'data': {
            'localized_name': 'Drow Ranger',
            'bio': 'Drow Ranger — герой ловкости, которая стреляет с большой дальности.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 600,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Ледяная стрела', 'desc': 'Замедляет врага.', 'img': 'drow_ranger_frost_arrows.png'},
            {'dname': 'Безмолвие', 'desc': 'Заставляет врага замолчать.', 'img': 'drow_ranger_silence.png'},
            {'dname': 'Аура', 'desc': 'Увеличивает урон.', 'img': 'drow_ranger_trueshot_aura.png'},
            {'dname': 'Меткость', 'desc': 'Наносит дополнительный урон.', 'img': 'drow_ranger_marksmanship.png'},
            {'dname': 'Врождённая: Лёд', 'desc': 'Ледяная стрела наносит дополнительный урон.', 'img': 'drow_ranger_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Меткость наносит дополнительный урон.', 'img': 'drow_ranger_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Безмолвие наносит дополнительный урон.', 'img': 'drow_ranger_shard.png'}
        ]
    },
    'ember_spirit': {
        'data': {
            'localized_name': 'Ember Spirit',
            'bio': 'Ember Spirit — герой ловкости, который управляет огнём.',
            'base_str': 20, 'base_agi': 22, 'base_int': 18,
            'base_health': 580, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Огненный остаток', 'desc': 'Телепортируется.', 'img': 'ember_spirit_fire_remnant.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'ember_spirit_sleight_of_fist.png'},
            {'dname': 'Щит', 'desc': 'Защищает от магии.', 'img': 'ember_spirit_flame_guard.png'},
            {'dname': 'Активация', 'desc': 'Активирует остатки.', 'img': 'ember_spirit_activate_fire_remnant.png'},
            {'dname': 'Врождённая: Огонь', 'desc': 'Огненный остаток наносит дополнительный урон.', 'img': 'ember_spirit_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Удар наносит дополнительный урон.', 'img': 'ember_spirit_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Щит наносит дополнительный урон.', 'img': 'ember_spirit_shard.png'}
        ]
    },
    'faceless_void': {
        'data': {
            'localized_name': 'Faceless Void',
            'bio': 'Faceless Void — герой ловкости, который управляет временем.',
            'base_str': 22, 'base_agi': 24, 'base_int': 16,
            'base_health': 600, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 50, 'base_attack_max': 56, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Удар времени', 'desc': 'Наносит дополнительный урон.', 'img': 'faceless_void_time_lock.png'},
            {'dname': 'Прогулка во времени', 'desc': 'Телепортируется.', 'img': 'faceless_void_time_walk.png'},
            {'dname': 'Диссонанс', 'desc': 'Замедляет врагов.', 'img': 'faceless_void_time_dilation.png'},
            {'dname': 'Хроносфера', 'desc': 'Останавливает время.', 'img': 'faceless_void_chronosphere.png'},
            {'dname': 'Врождённая: Время', 'desc': 'Удар времени наносит дополнительный урон.', 'img': 'faceless_void_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Хроносфера наносит дополнительный урон.', 'img': 'faceless_void_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Прогулка во времени наносит дополнительный урон.', 'img': 'faceless_void_shard.png'}
        ]
    },
    'gyrocopter': {
        'data': {
            'localized_name': 'Gyrocopter',
            'bio': 'Gyrocopter — герой ловкости, который стреляет ракетами.',
            'base_str': 20, 'base_agi': 22, 'base_int': 18,
            'base_health': 580, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Ракетный залп', 'desc': 'Запускает ракеты.', 'img': 'gyrocopter_rocket_barrage.png'},
            {'dname': 'Самонаводящаяся ракета', 'desc': 'Запускает ракету.', 'img': 'gyrocopter_homing_missile.png'},
            {'dname': 'Зенитный огонь', 'desc': 'Наносит урон по площади.', 'img': 'gyrocopter_flak_cannon.png'},
            {'dname': 'Вызов', 'desc': 'Наносит урон по площади.', 'img': 'gyrocopter_call_down.png'},
            {'dname': 'Врождённая: Ракеты', 'desc': 'Ракетный залп наносит дополнительный урон.', 'img': 'gyrocopter_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Вызов наносит дополнительный урон.', 'img': 'gyrocopter_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Зенитный огонь наносит дополнительный урон.', 'img': 'gyrocopter_shard.png'}
        ]
    },
    'hoodwink': {
        'data': {
            'localized_name': 'Hoodwink',
            'bio': 'Hoodwink — герой ловкости, который стреляет из арбалета.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 600,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Арбалет', 'desc': 'Стреляет из арбалета.', 'img': 'hoodwink_acorn_shot.png'},
            {'dname': 'Ловушка', 'desc': 'Создаёт ловушку.', 'img': 'hoodwink_bushwhack.png'},
            {'dname': 'Скрытность', 'desc': 'Становится невидимым.', 'img': 'hoodwink_scurry.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'hoodwink_sharpshooter.png'},
            {'dname': 'Врождённая: Лес', 'desc': 'Арбалет наносит дополнительный урон.', 'img': 'hoodwink_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'hoodwink_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Ловушка наносит дополнительный урон.', 'img': 'hoodwink_shard.png'}
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
            {'dname': 'Тотем', 'desc': 'Лечит союзников.', 'img': 'juggernaut_healing_ward.png'},
            {'dname': 'Танец клинков', 'desc': 'Наносит дополнительный урон.', 'img': 'juggernaut_blade_dance.png'},
            {'dname': 'Омнислэш', 'desc': 'Наносит удары по всем врагам.', 'img': 'juggernaut_omni_slash.png'},
            {'dname': 'Врождённая: Клинки', 'desc': 'Вихрь клинков наносит дополнительный урон.', 'img': 'juggernaut_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Омнислэш наносит дополнительный урон.', 'img': 'juggernaut_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Танец клинков наносит дополнительный урон.', 'img': 'juggernaut_shard.png'}
        ]
    },
    'lone_druid': {
        'data': {
            'localized_name': 'Lone Druid',
            'bio': 'Lone Druid — герой ловкости, который призывает медведя.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Дух-медведь', 'desc': 'Призывает медведя.', 'img': 'lone_druid_spirit_bear.png'},
            {'dname': 'Ярость', 'desc': 'Увеличивает урон.', 'img': 'lone_druid_rabid.png'},
            {'dname': 'Истинная форма', 'desc': 'Превращается в медведя.', 'img': 'lone_druid_true_form.png'},
            {'dname': 'Рёв', 'desc': 'Лечит союзников.', 'img': 'lone_druid_savage_roar.png'},
            {'dname': 'Врождённая: Природа', 'desc': 'Дух-медведь наносит дополнительный урон.', 'img': 'lone_druid_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Рёв наносит дополнительный урон.', 'img': 'lone_druid_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Ярость наносит дополнительный урон.', 'img': 'lone_druid_shard.png'}
        ]
    },
    'luna': {
        'data': {
            'localized_name': 'Luna',
            'bio': 'Luna — герой ловкости, которая стреляет лунными лучами.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Лунный луч', 'desc': 'Наносит урон.', 'img': 'luna_lucent_beam.png'},
            {'dname': 'Лунная аура', 'desc': 'Увеличивает урон союзников.', 'img': 'luna_moon_glaive.png'},
            {'dname': 'Благословение', 'desc': 'Увеличивает здоровье.', 'img': 'luna_lunar_blessing.png'},
            {'dname': 'Затмение', 'desc': 'Наносит урон по площади.', 'img': 'luna_eclipse.png'},
            {'dname': 'Врождённая: Луна', 'desc': 'Лунный луч наносит дополнительный урон.', 'img': 'luna_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Затмение наносит дополнительный урон.', 'img': 'luna_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Лунная аура наносит дополнительный урон.', 'img': 'luna_shard.png'}
        ]
    },
    'medusa': {
        'data': {
            'localized_name': 'Medusa',
            'bio': 'Medusa — герой ловкости, которая превращает врагов в камень.',
            'base_str': 20, 'base_agi': 22, 'base_int': 18,
            'base_health': 580, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 290,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 600,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Каменный взгляд', 'desc': 'Замедляет врагов.', 'img': 'medusa_stone_gaze.png'},
            {'dname': 'Мистическая змея', 'desc': 'Наносит урон врагам.', 'img': 'medusa_mystic_snake.png'},
            {'dname': 'Магический щит', 'desc': 'Защищает от урона.', 'img': 'medusa_mana_shield.png'},
            {'dname': 'Разделение', 'desc': 'Наносит урон по площади.', 'img': 'medusa_split_shot.png'},
            {'dname': 'Врождённая: Камень', 'desc': 'Каменный взгляд наносит дополнительный урон.', 'img': 'medusa_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Разделение наносит дополнительный урон.', 'img': 'medusa_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Мистическая змея наносит дополнительный урон.', 'img': 'medusa_shard.png'}
        ]
    },
    'meepo': {
        'data': {
            'localized_name': 'Meepo',
            'bio': 'Meepo — герой ловкости, который создаёт клонов.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Клон', 'desc': 'Создаёт клона.', 'img': 'meepo_poof.png'},
            {'dname': 'Сеть', 'desc': 'Ловит врага.', 'img': 'meepo_net.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'meepo_geostrike.png'},
            {'dname': 'Телепорт', 'desc': 'Телепортирует клонов.', 'img': 'meepo_earthbind.png'},
            {'dname': 'Врождённая: Клоны', 'desc': 'Клон наносит дополнительный урон.', 'img': 'meepo_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Телепорт наносит дополнительный урон.', 'img': 'meepo_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Сеть наносит дополнительный урон.', 'img': 'meepo_shard.png'}
        ]
    },
    'mirana': {
        'data': {
            'localized_name': 'Mirana',
            'bio': 'Mirana — герой ловкости, которая стреляет стрелами.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 600,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Стрела', 'desc': 'Оглушает врага.', 'img': 'mirana_arrow.png'},
            {'dname': 'Звёздный удар', 'desc': 'Наносит урон.', 'img': 'mirana_starfall.png'},
            {'dname': 'Прыжок', 'desc': 'Прыгает на врага.', 'img': 'mirana_leap.png'},
            {'dname': 'Тень', 'desc': 'Наносит урон по площади.', 'img': 'mirana_moonlight_shadow.png'},
            {'dname': 'Врождённая: Звезда', 'desc': 'Стрела наносит дополнительный урон.', 'img': 'mirana_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Тень наносит дополнительный урон.', 'img': 'mirana_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Звёздный удар наносит дополнительный урон.', 'img': 'mirana_shard.png'}
        ]
    },
    'monkey_king': {
        'data': {
            'localized_name': 'Monkey King',
            'bio': 'Monkey King — герой ловкости, который использует посох.',
            'base_str': 20, 'base_agi': 22, 'base_int': 18,
            'base_health': 580, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 300,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'monkey_king_boundless_strike.png'},
            {'dname': 'Древесный танец', 'desc': 'Забирается на дерево.', 'img': 'monkey_king_tree_dance.png'},
            {'dname': 'Озорство', 'desc': 'Создаёт иллюзии.', 'img': 'monkey_king_mischief.png'},
            {'dname': 'Команда', 'desc': 'Наносит урон по площади.', 'img': 'monkey_king_wukongs_command.png'},
            {'dname': 'Врождённая: Обезьяна', 'desc': 'Удар наносит дополнительный урон.', 'img': 'monkey_king_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Команда наносит дополнительный урон.', 'img': 'monkey_king_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Древесный танец наносит дополнительный урон.', 'img': 'monkey_king_shard.png'}
        ]
    },
    'morphling': {
        'data': {
            'localized_name': 'Morphling',
            'bio': 'Morphling — герой ловкости, который меняет форму.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 300,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Волна', 'desc': 'Наносит урон врагам.', 'img': 'morphling_waveform.png'},
            {'dname': 'Морфинг', 'desc': 'Меняет атрибуты.', 'img': 'morphling_morph.png'},
            {'dname': 'Адаптивный удар', 'desc': 'Наносит дополнительный урон.', 'img': 'morphling_adaptive_strike.png'},
            {'dname': 'Копия', 'desc': 'Превращается в другого героя.', 'img': 'morphling_replicate.png'},
            {'dname': 'Врождённая: Вода', 'desc': 'Волна наносит дополнительный урон.', 'img': 'morphling_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Копия наносит дополнительный урон.', 'img': 'morphling_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Адаптивный удар наносит дополнительный урон.', 'img': 'morphling_shard.png'}
        ]
    },
    'naga_siren': {
        'data': {
            'localized_name': 'Naga Siren',
            'bio': 'Naga Siren — герой ловкости, которая усыпляет врагов.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Песня сирены', 'desc': 'Усыпляет врагов.', 'img': 'naga_siren_song_of_the_siren.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'naga_siren_rip_tide.png'},
            {'dname': 'Сеть', 'desc': 'Ловит врага.', 'img': 'naga_siren_ensnare.png'},
            {'dname': 'Иллюзии', 'desc': 'Создаёт иллюзии.', 'img': 'naga_siren_mirror_image.png'},
            {'dname': 'Врождённая: Песня', 'desc': 'Песня сирены наносит дополнительный урон.', 'img': 'naga_siren_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Иллюзии наносят дополнительный урон.', 'img': 'naga_siren_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'naga_siren_shard.png'}
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
            {'dname': 'Размытость', 'desc': 'Уклоняется от атак.', 'img': 'phantom_assassin_blur.png'},
            {'dname': 'Удар', 'desc': 'Наносит критический урон.', 'img': 'phantom_assassin_coup_de_grace.png'},
            {'dname': 'Удар призрака', 'desc': 'Телепортируется и наносит урон.', 'img': 'phantom_assassin_phantom_strike.png'},
            {'dname': 'Врождённая: Призрак', 'desc': 'Кинжал наносит дополнительный урон.', 'img': 'phantom_assassin_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Удар призрака наносит дополнительный урон.', 'img': 'phantom_assassin_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Размытость наносит дополнительный урон.', 'img': 'phantom_assassin_shard.png'}
        ]
    },
    'phantom_lancer': {
        'data': {
            'localized_name': 'Phantom Lancer',
            'bio': 'Phantom Lancer — герой ловкости, который создаёт множество иллюзий.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Копьё', 'desc': 'Бросает копьё.', 'img': 'phantom_lancer_spirit_lance.png'},
            {'dname': 'Двойник', 'desc': 'Создаёт иллюзии.', 'img': 'phantom_lancer_doppelwalk.png'},
            {'dname': 'Рывок', 'desc': 'Наносит дополнительный урон.', 'img': 'phantom_lancer_phantom_rush.png'},
            {'dname': 'Наслоение', 'desc': 'Наносит урон по площади.', 'img': 'phantom_lancer_juxtapose.png'},
            {'dname': 'Врождённая: Иллюзии', 'desc': 'Копьё наносит дополнительный урон.', 'img': 'phantom_lancer_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Наслоение наносит дополнительный урон.', 'img': 'phantom_lancer_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Рывок наносит дополнительный урон.', 'img': 'phantom_lancer_shard.png'}
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
            {'dname': 'Плазменное поле', 'desc': 'Наносит урон врагам.', 'img': 'razor_plasma_field.png'},
            {'dname': 'Статическая связь', 'desc': 'Крадёт урон.', 'img': 'razor_static_link.png'},
            {'dname': 'Нестабильный ток', 'desc': 'Наносит урон вокруг.', 'img': 'razor_unstable_current.png'},
            {'dname': 'Глаз бури', 'desc': 'Наносит урон по области.', 'img': 'razor_eye_of_the_storm.png'},
            {'dname': 'Врождённая: Электричество', 'desc': 'Плазменное поле наносит дополнительный урон.', 'img': 'razor_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Глаз бури наносит дополнительный урон.', 'img': 'razor_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Статическая связь наносит дополнительный урон.', 'img': 'razor_shard.png'}
        ]
    },
    'riki': {
        'data': {
            'localized_name': 'Riki',
            'bio': 'Riki — герой ловкости, который остаётся невидимым.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Удар в спину', 'desc': 'Наносит дополнительный урон.', 'img': 'riki_backstab.png'},
            {'dname': 'Дымовая завеса', 'desc': 'Создаёт дымовую завесу.', 'img': 'riki_smoke_screen.png'},
            {'dname': 'Невидимость', 'desc': 'Становится невидимым.', 'img': 'riki_permanent_invisibility.png'},
            {'dname': 'Удары', 'desc': 'Наносит урон по площади.', 'img': 'riki_tricks_of_the_trade.png'},
            {'dname': 'Врождённая: Тень', 'desc': 'Удар в спину наносит дополнительный урон.', 'img': 'riki_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Удары наносят дополнительный урон.', 'img': 'riki_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Дымовая завеса наносит дополнительный урон.', 'img': 'riki_shard.png'}
        ]
    },
    'shadow_fiend': {
        'data': {
            'localized_name': 'Shadow Fiend',
            'bio': 'Shadow Fiend — герой ловкости, который собирает души.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Тень', 'desc': 'Наносит урон врагам.', 'img': 'nevermore_shadowraze.png'},
            {'dname': 'Мастерство', 'desc': 'Собирает души.', 'img': 'nevermore_necromastery.png'},
            {'dname': 'Присутствие', 'desc': 'Снижает броню врагов.', 'img': 'nevermore_presence_of_the_dark_lord.png'},
            {'dname': 'Требование', 'desc': 'Наносит урон по площади.', 'img': 'nevermore_requiem.png'},
            {'dname': 'Врождённая: Души', 'desc': 'Тень наносит дополнительный урон.', 'img': 'nevermore_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Требование наносит дополнительный урон.', 'img': 'nevermore_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Мастерство наносит дополнительный урон.', 'img': 'nevermore_shard.png'}
        ]
    },
    'slark': {
        'data': {
            'localized_name': 'Slark',
            'bio': 'Slark — герой ловкости, который восстанавливает здоровье.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Тёмный договор', 'desc': 'Наносит урон врагам.', 'img': 'slark_dark_pact.png'},
            {'dname': 'Прыжок', 'desc': 'Прыгает на врага.', 'img': 'slark_pounce.png'},
            {'dname': 'Эссенция', 'desc': 'Восстанавливает здоровье.', 'img': 'slark_essence_shift.png'},
            {'dname': 'Танец', 'desc': 'Становится невидимым.', 'img': 'slark_shadow_dance.png'},
            {'dname': 'Врождённая: Тень', 'desc': 'Тёмный договор наносит дополнительный урон.', 'img': 'slark_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Танец наносит дополнительный урон.', 'img': 'slark_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Эссенция наносит дополнительный урон.', 'img': 'slark_shard.png'}
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
            {'dname': 'Осколки', 'desc': 'Наносит урон по площади.', 'img': 'sniper_shrapnel.png'},
            {'dname': 'Выстрел в голову', 'desc': 'Наносит дополнительный урон.', 'img': 'sniper_headshot.png'},
            {'dname': 'Прицеливание', 'desc': 'Увеличивает дальность.', 'img': 'sniper_take_aim.png'},
            {'dname': 'Выстрел', 'desc': 'Наносит огромный урон.', 'img': 'sniper_assassinate.png'},
            {'dname': 'Врождённая: Снайпер', 'desc': 'Осколки наносят дополнительный урон.', 'img': 'sniper_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Выстрел наносит дополнительный урон.', 'img': 'sniper_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Выстрел в голову наносит дополнительный урон.', 'img': 'sniper_shard.png'}
        ]
    },
    'spectre': {
        'data': {
            'localized_name': 'Spectre',
            'bio': 'Spectre — герой ловкости, которая создаёт иллюзии.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Кинжал', 'desc': 'Бросает кинжал.', 'img': 'spectre_spectral_dagger.png'},
            {'dname': 'Разрушение', 'desc': 'Создаёт иллюзии.', 'img': 'spectre_desolate.png'},
            {'dname': 'Отражение', 'desc': 'Наносит урон врагам.', 'img': 'spectre_dispersion.png'},
            {'dname': 'Призрак', 'desc': 'Телепортируется к врагу.', 'img': 'spectre_haunt.png'},
            {'dname': 'Врождённая: Призрак', 'desc': 'Кинжал наносит дополнительный урон.', 'img': 'spectre_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Призрак наносит дополнительный урон.', 'img': 'spectre_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Отражение наносит дополнительный урон.', 'img': 'spectre_shard.png'}
        ]
    },
    'templar_assassin': {
        'data': {
            'localized_name': 'Templar Assassin',
            'bio': 'Templar Assassin — герой ловкости, которая скрывается от врагов.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Скрытность', 'desc': 'Становится невидимой.', 'img': 'templar_assassin_meld.png'},
            {'dname': 'Пси-клинки', 'desc': 'Наносит дополнительный урон.', 'img': 'templar_assassin_psi_blades.png'},
            {'dname': 'Рефракция', 'desc': 'Защищает от урона.', 'img': 'templar_assassin_refraction.png'},
            {'dname': 'Ловушка', 'desc': 'Создаёт ловушку.', 'img': 'templar_assassin_trap.png'},
            {'dname': 'Врождённая: Пси', 'desc': 'Скрытность наносит дополнительный урон.', 'img': 'templar_assassin_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ловушка наносит дополнительный урон.', 'img': 'templar_assassin_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Рефракция наносит дополнительный урон.', 'img': 'templar_assassin_shard.png'}
        ]
    },
    'terrorblade': {
        'data': {
            'localized_name': 'Terrorblade',
            'bio': 'Terrorblade — герой ловкости, который создаёт иллюзии.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Иллюзии', 'desc': 'Создаёт иллюзии.', 'img': 'terrorblade_conjure_image.png'},
            {'dname': 'Метаморфоза', 'desc': 'Наносит дополнительный урон.', 'img': 'terrorblade_metamorphosis.png'},
            {'dname': 'Отражение', 'desc': 'Создаёт копию врага.', 'img': 'terrorblade_reflection.png'},
            {'dname': 'Разделение', 'desc': 'Меняется местами с врагом.', 'img': 'terrorblade_sunder.png'},
            {'dname': 'Врождённая: Иллюзии', 'desc': 'Иллюзии наносят дополнительный урон.', 'img': 'terrorblade_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Разделение наносит дополнительный урон.', 'img': 'terrorblade_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Отражение наносит дополнительный урон.', 'img': 'terrorblade_shard.png'}
        ]
    },
    'troll_warlord': {
        'data': {
            'localized_name': 'Troll Warlord',
            'bio': 'Troll Warlord — герой ловкости, который быстро атакует.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Топоры', 'desc': 'Оглушает врага.', 'img': 'troll_warlord_whirling_axes.png'},
            {'dname': 'Транс', 'desc': 'Увеличивает скорость.', 'img': 'troll_warlord_battle_trance.png'},
            {'dname': 'Рвение', 'desc': 'Наносит дополнительный урон.', 'img': 'troll_warlord_fervor.png'},
            {'dname': 'Ярость', 'desc': 'Увеличивает скорость атаки.', 'img': 'troll_warlord_berserkers_rage.png'},
            {'dname': 'Врождённая: Тролль', 'desc': 'Топоры наносят дополнительный урон.', 'img': 'troll_warlord_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ярость наносит дополнительный урон.', 'img': 'troll_warlord_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Транс наносит дополнительный урон.', 'img': 'troll_warlord_shard.png'}
        ]
    },
    'ursa': {
        'data': {
            'localized_name': 'Ursa',
            'bio': 'Ursa — герой ловкости, который наносит огромный урон.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 310,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 150,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'ursa_earthshock.png'},
            {'dname': 'Свирепость', 'desc': 'Увеличивает урон.', 'img': 'ursa_overpower.png'},
            {'dname': 'Ярость', 'desc': 'Наносит дополнительный урон.', 'img': 'ursa_fury_swipes.png'},
            {'dname': 'Ярость', 'desc': 'Наносит урон врагам.', 'img': 'ursa_enrage.png'},
            {'dname': 'Врождённая: Медведь', 'desc': 'Удар наносит дополнительный урон.', 'img': 'ursa_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ярость наносит дополнительный урон.', 'img': 'ursa_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Свирепость наносит дополнительный урон.', 'img': 'ursa_shard.png'}
        ]
    },
    'venomancer': {
        'data': {
            'localized_name': 'Venomancer',
            'bio': 'Venomancer — герой ловкости, который отравляет врагов.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'venomancer_venomous_gale.png'},
            {'dname': 'Тотем', 'desc': 'Создаёт тотем.', 'img': 'venomancer_plague_ward.png'},
            {'dname': 'Кожа', 'desc': 'Наносит урон врагам.', 'img': 'venomancer_poison_sting.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'venomancer_poison_nova.png'},
            {'dname': 'Врождённая: Яд', 'desc': 'Яд наносит дополнительный урон.', 'img': 'venomancer_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'venomancer_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Тотем наносит дополнительный урон.', 'img': 'venomancer_shard.png'}
        ]
    },
    'viper': {
        'data': {
            'localized_name': 'Viper',
            'bio': 'Viper — герой ловкости, который отравляет врагов.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 295,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'viper_poison_attack.png'},
            {'dname': 'Токсин', 'desc': 'Наносит урон по площади.', 'img': 'viper_nethertoxin.png'},
            {'dname': 'Кожа', 'desc': 'Увеличивает броню.', 'img': 'viper_corrosive_skin.png'},
            {'dname': 'Удар', 'desc': 'Наносит урон врагам.', 'img': 'viper_viper_strike.png'},
            {'dname': 'Врождённая: Яд', 'desc': 'Яд наносит дополнительный урон.', 'img': 'viper_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Удар наносит дополнительный урон.', 'img': 'viper_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Токсин наносит дополнительный урон.', 'img': 'viper_shard.png'}
        ]
    },
    'weaver': {
        'data': {
            'localized_name': 'Weaver',
            'bio': 'Weaver — герой ловкости, который управляет временем.',
            'base_str': 18, 'base_agi': 22, 'base_int': 18,
            'base_health': 560, 'base_mana': 290, 'base_armor': 2.0,
            'attack_rate': 1.6, 'move_speed': 305,
            'base_attack_min': 48, 'base_attack_max': 54, 'attack_range': 500,
            'primary_attr': 'agi',
            'str_gain': 1.8, 'agi_gain': 2.6, 'int_gain': 1.8
        },
        'abilities': [
            {'dname': 'Рой', 'desc': 'Наносит урон врагам.', 'img': 'weaver_the_swarm.png'},
            {'dname': 'Скучи', 'desc': 'Прыгает на врага.', 'img': 'weaver_shukuchi.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'weaver_geminate_attack.png'},
            {'dname': 'Время', 'desc': 'Откатывает время.', 'img': 'weaver_time_lapse.png'},
            {'dname': 'Врождённая: Время', 'desc': 'Рой наносит дополнительный урон.', 'img': 'weaver_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Время наносит дополнительный урон.', 'img': 'weaver_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'weaver_shard.png'}
        ]
    },
    # ===== ИНТЕЛЛЕКТ =====
    'ancient_apparition': {
        'data': {
            'localized_name': 'Ancient Apparition',
            'bio': 'Ancient Apparition — герой интеллекта, который замораживает врагов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Ледяной взрыв', 'desc': 'Наносит урон по площади.', 'img': 'ancient_apparition_ice_blast.png'},
            {'dname': 'Холод', 'desc': 'Замедляет врагов.', 'img': 'ancient_apparition_cold_feet.png'},
            {'dname': 'Прикосновение', 'desc': 'Создаёт призрака.', 'img': 'ancient_apparition_chilling_touch.png'},
            {'dname': 'Вихрь', 'desc': 'Наносит урон врагам.', 'img': 'ancient_apparition_ice_vortex.png'},
            {'dname': 'Врождённая: Лёд', 'desc': 'Ледяной взрыв наносит дополнительный урон.', 'img': 'ancient_apparition_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Вихрь наносит дополнительный урон.', 'img': 'ancient_apparition_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Холод наносит дополнительный урон.', 'img': 'ancient_apparition_shard.png'}
        ]
    },
    'chen': {
        'data': {
            'localized_name': 'Chen',
            'bio': 'Chen — герой интеллекта, который подчиняет нейтралов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Подчинение', 'desc': 'Подчиняет нейтрального врага.', 'img': 'chen_holy_persuasion.png'},
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'chen_hand_of_god.png'},
            {'dname': 'Божественная защита', 'desc': 'Защищает союзников.', 'img': 'chen_test_of_faith.png'},
            {'dname': 'Ультимейт', 'desc': 'Призывает союзников.', 'img': 'chen_divine_favor.png'},
            {'dname': 'Врождённая: Божественность', 'desc': 'Подчинение наносит дополнительный урон.', 'img': 'chen_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'chen_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Лечение наносит дополнительный урон.', 'img': 'chen_shard.png'}
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
            {'dname': 'Кристальная вспышка', 'desc': 'Замораживает врага.', 'img': 'crystal_maiden_crystal_nova.png'},
            {'dname': 'Укус холода', 'desc': 'Наносит урон и замедляет.', 'img': 'crystal_maiden_frostbite.png'},
            {'dname': 'Аура', 'desc': 'Пассивное замедление.', 'img': 'crystal_maiden_crystal_aura.png'},
            {'dname': 'Поле', 'desc': 'Наносит огромный урон по области.', 'img': 'crystal_maiden_freezing_field.png'},
            {'dname': 'Врождённая: Лёд', 'desc': 'Кристальная вспышка наносит дополнительный урон.', 'img': 'crystal_maiden_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Поле наносит дополнительный урон.', 'img': 'crystal_maiden_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Укус холода наносит дополнительный урон.', 'img': 'crystal_maiden_shard.png'}
        ]
    },
    'dark_seer': {
        'data': {
            'localized_name': 'Dark Seer',
            'bio': 'Dark Seer — герой интеллекта, который создаёт иллюзии.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Стена', 'desc': 'Создаёт стену иллюзий.', 'img': 'dark_seer_wall_of_replica.png'},
            {'dname': 'Ускорение', 'desc': 'Увеличивает скорость.', 'img': 'dark_seer_surge.png'},
            {'dname': 'Ионы', 'desc': 'Наносит урон врагам.', 'img': 'dark_seer_ion_shell.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'dark_seer_vacuum.png'},
            {'dname': 'Врождённая: Тьма', 'desc': 'Стена наносит дополнительный урон.', 'img': 'dark_seer_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'dark_seer_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Ионы наносят дополнительный урон.', 'img': 'dark_seer_shard.png'}
        ]
    },
    'dark_willow': {
        'data': {
            'localized_name': 'Dark Willow',
            'bio': 'Dark Willow — герой интеллекта, который управляет тенями.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Тень', 'desc': 'Наносит урон врагам.', 'img': 'dark_willow_shadow_realm.png'},
            {'dname': 'Страх', 'desc': 'Оглушает врага.', 'img': 'dark_willow_terrorize.png'},
            {'dname': 'Корни', 'desc': 'Ловит врага.', 'img': 'dark_willow_cursed_crown.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'dark_willow_bramble_maze.png'},
            {'dname': 'Врождённая: Тень', 'desc': 'Тень наносит дополнительный урон.', 'img': 'dark_willow_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'dark_willow_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Страх наносит дополнительный урон.', 'img': 'dark_willow_shard.png'}
        ]
    },
    'disruptor': {
        'data': {
            'localized_name': 'Disruptor',
            'bio': 'Disruptor — герой интеллекта, который управляет электричеством.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Молния', 'desc': 'Наносит урон врагам.', 'img': 'disruptor_thunder_strike.png'},
            {'dname': 'Замедление', 'desc': 'Замедляет врага.', 'img': 'disruptor_glimpse.png'},
            {'dname': 'Барьер', 'desc': 'Создаёт барьер.', 'img': 'disruptor_kinetic_field.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'disruptor_static_storm.png'},
            {'dname': 'Врождённая: Электричество', 'desc': 'Молния наносит дополнительный урон.', 'img': 'disruptor_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'disruptor_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Барьер наносит дополнительный урон.', 'img': 'disruptor_shard.png'}
        ]
    },
    'enchantress': {
        'data': {
            'localized_name': 'Enchantress',
            'bio': 'Enchantress — герой интеллекта, который призывает существ.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Подчинение', 'desc': 'Подчиняет существо.', 'img': 'enchantress_enchant.png'},
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'enchantress_natures_attendants.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'enchantress_impetus.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'enchantress_untruth.png'},
            {'dname': 'Врождённая: Природа', 'desc': 'Подчинение наносит дополнительный урон.', 'img': 'enchantress_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'enchantress_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Лечение наносит дополнительный урон.', 'img': 'enchantress_shard.png'}
        ]
    },
    'grimstroke': {
        'data': {
            'localized_name': 'Grimstroke',
            'bio': 'Grimstroke — герой интеллекта, который рисует врагов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Кисть', 'desc': 'Наносит урон врагам.', 'img': 'grimstroke_brush_fire.png'},
            {'dname': 'Связь', 'desc': 'Связывает врагов.', 'img': 'grimstroke_soul_bind.png'},
            {'dname': 'Краска', 'desc': 'Наносит урон врагам.', 'img': 'grimstroke_dark_portrait.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'grimstroke_ink_swell.png'},
            {'dname': 'Врождённая: Краска', 'desc': 'Кисть наносит дополнительный урон.', 'img': 'grimstroke_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'grimstroke_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Связь наносит дополнительный урон.', 'img': 'grimstroke_shard.png'}
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
            {'dname': 'Призыв', 'desc': 'Комбинация стихий.', 'img': 'invoker_invoke.png'},
            {'dname': 'Солнечный удар', 'desc': 'Наносит урон.', 'img': 'invoker_sun_strike.png'},
            {'dname': 'Ледяная стена', 'desc': 'Создаёт стену.', 'img': 'invoker_ice_wall.png'},
            {'dname': 'Метеор', 'desc': 'Призывает метеорит.', 'img': 'invoker_meteor.png'},
            {'dname': 'Врождённая: Стихии', 'desc': 'Призыв наносит дополнительный урон.', 'img': 'invoker_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Метеор наносит дополнительный урон.', 'img': 'invoker_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Ледяная стена наносит дополнительный урон.', 'img': 'invoker_shard.png'}
        ]
    },
    'jakiro': {
        'data': {
            'localized_name': 'Jakiro',
            'bio': 'Jakiro — герой интеллекта, который управляет огнём и льдом.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Двойное дыхание', 'desc': 'Наносит урон врагам.', 'img': 'jakiro_dual_breath.png'},
            {'dname': 'Ледяная стена', 'desc': 'Создаёт ледяную стену.', 'img': 'jakiro_ice_path.png'},
            {'dname': 'Огненный шар', 'desc': 'Наносит урон врагам.', 'img': 'jakiro_liquid_fire.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'jakiro_macropyre.png'},
            {'dname': 'Врождённая: Огонь и лёд', 'desc': 'Двойное дыхание наносит дополнительный урон.', 'img': 'jakiro_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'jakiro_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Огненный шар наносит дополнительный урон.', 'img': 'jakiro_shard.png'}
        ]
    },
    'keeper_of_the_light': {
        'data': {
            'localized_name': 'Keeper of the Light',
            'bio': 'Keeper of the Light — герой интеллекта, который управляет светом.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Свет', 'desc': 'Наносит урон врагам.', 'img': 'keeper_of_the_light_illuminate.png'},
            {'dname': 'Мана', 'desc': 'Восстанавливает ману.', 'img': 'keeper_of_the_light_chakra_magic.png'},
            {'dname': 'Слепящий свет', 'desc': 'Ослепляет врага.', 'img': 'keeper_of_the_light_blinding_light.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'keeper_of_the_light_spirit_form.png'},
            {'dname': 'Врождённая: Свет', 'desc': 'Свет наносит дополнительный урон.', 'img': 'keeper_of_the_light_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'keeper_of_the_light_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Слепящий свет наносит дополнительный урон.', 'img': 'keeper_of_the_light_shard.png'}
        ]
    },
    'leshrac': {
        'data': {
            'localized_name': 'Leshrac',
            'bio': 'Leshrac — герой интеллекта, который управляет молниями.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Молния', 'desc': 'Наносит урон врагам.', 'img': 'leshrac_split_earth.png'},
            {'dname': 'Молния', 'desc': 'Наносит урон врагам.', 'img': 'leshrac_lightning_storm.png'},
            {'dname': 'Аура', 'desc': 'Наносит урон вокруг.', 'img': 'leshrac_diabolic_edict.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'leshrac_pulse_nova.png'},
            {'dname': 'Врождённая: Молния', 'desc': 'Молния наносит дополнительный урон.', 'img': 'leshrac_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'leshrac_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Аура наносит дополнительный урон.', 'img': 'leshrac_shard.png'}
        ]
    },
    'lich': {
        'data': {
            'localized_name': 'Lich',
            'bio': 'Lich — герой интеллекта, который жертвует союзниками.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Ледяной взрыв', 'desc': 'Наносит урон врагам.', 'img': 'lich_frost_blast.png'},
            {'dname': 'Жертва', 'desc': 'Жертвует союзником.', 'img': 'lich_sacrifice.png'},
            {'dname': 'Ледяная броня', 'desc': 'Увеличивает броню.', 'img': 'lich_ice_armor.png'},
            {'dname': 'Цепь', 'desc': 'Наносит урон по площади.', 'img': 'lich_chain_frost.png'},
            {'dname': 'Врождённая: Смерть', 'desc': 'Ледяной взрыв наносит дополнительный урон.', 'img': 'lich_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Цепь наносит дополнительный урон.', 'img': 'lich_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Жертва наносит дополнительный урон.', 'img': 'lich_shard.png'}
        ]
    },
    'lina': {
        'data': {
            'localized_name': 'Lina',
            'bio': 'Lina — герой интеллекта, которая сжигает врагов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Огненный шар', 'desc': 'Наносит урон врагам.', 'img': 'lina_dragon_slave.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'lina_fiery_soul.png'},
            {'dname': 'Замедление', 'desc': 'Замедляет врага.', 'img': 'lina_light_strike_array.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит огромный урон.', 'img': 'lina_laguna_blade.png'},
            {'dname': 'Врождённая: Огонь', 'desc': 'Огненный шар наносит дополнительный урон.', 'img': 'lina_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'lina_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'lina_shard.png'}
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
            {'dname': 'Палец смерти', 'desc': 'Наносит огромный урон.', 'img': 'lion_finger_of_death.png'},
            {'dname': 'Врождённая: Лев', 'desc': 'Землетрясение наносит дополнительный урон.', 'img': 'lion_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Палец смерти наносит дополнительный урон.', 'img': 'lion_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Трансформация наносит дополнительный урон.', 'img': 'lion_shard.png'}
        ]
    },
    'muerta': {
        'data': {
            'localized_name': 'Muerta',
            'bio': 'Muerta — герой интеллекта, который управляет духами.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Дух', 'desc': 'Наносит урон врагам.', 'img': 'muerta_dead_shot.png'},
            {'dname': 'Тень', 'desc': 'Наносит урон врагам.', 'img': 'muerta_the_reaping.png'},
            {'dname': 'Жертва', 'desc': 'Жертвует здоровьем.', 'img': 'muerta_pierce_the_veil.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'muerta_ghost_lance.png'},
            {'dname': 'Врождённая: Смерть', 'desc': 'Дух наносит дополнительный урон.', 'img': 'muerta_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'muerta_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Тень наносит дополнительный урон.', 'img': 'muerta_shard.png'}
        ]
    },
    'necrolyte': {
        'data': {
            'localized_name': 'Necrophos',
            'bio': 'Necrophos — герой интеллекта, который уничтожает врагов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Смертельный удар', 'desc': 'Наносит урон врагам.', 'img': 'necrolyte_death_pulse.png'},
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'necrolyte_sadist.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'necrolyte_heartstopper_aura.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит огромный урон.', 'img': 'necrolyte_reapers_scythe.png'},
            {'dname': 'Врождённая: Смерть', 'desc': 'Смертельный удар наносит дополнительный урон.', 'img': 'necrolyte_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'necrolyte_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Яд наносит дополнительный урон.', 'img': 'necrolyte_shard.png'}
        ]
    },
    'oracle': {
        'data': {
            'localized_name': 'Oracle',
            'bio': 'Oracle — герой интеллекта, который предсказывает будущее.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Предсказание', 'desc': 'Наносит урон врагам.', 'img': 'oracle_fortunes_end.png'},
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'oracle_purifying_flames.png'},
            {'dname': 'Защита', 'desc': 'Защищает союзников.', 'img': 'oracle_fates_edict.png'},
            {'dname': 'Ультимейт', 'desc': 'Предсказывает судьбу.', 'img': 'oracle_false_promise.png'},
            {'dname': 'Врождённая: Судьба', 'desc': 'Предсказание наносит дополнительный урон.', 'img': 'oracle_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'oracle_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Лечение наносит дополнительный урон.', 'img': 'oracle_shard.png'}
        ]
    },
    'obsidian_destroyer': {
        'data': {
            'localized_name': 'Outworld Destroyer',
            'bio': 'Outworld Destroyer — герой интеллекта, который уничтожает ману.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Сфера', 'desc': 'Наносит урон врагам.', 'img': 'obsidian_destroyer_arcane_orb.png'},
            {'dname': 'Воронка', 'desc': 'Крадёт ману.', 'img': 'obsidian_destroyer_essence_flux.png'},
            {'dname': 'Тюрьма', 'desc': 'Заточает врага.', 'img': 'obsidian_destroyer_astral_imprisonment.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'obsidian_destroyer_sanity_eclipse.png'},
            {'dname': 'Врождённая: Магия', 'desc': 'Сфера наносит дополнительный урон.', 'img': 'obsidian_destroyer_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'obsidian_destroyer_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Тюрьма наносит дополнительный урон.', 'img': 'obsidian_destroyer_shard.png'}
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
            {'dname': 'Кокон', 'desc': 'Усыпляет врагов.', 'img': 'puck_dream_coil.png'},
            {'dname': 'Врождённая: Фаза', 'desc': 'Сфера наносит дополнительный урон.', 'img': 'puck_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Кокон наносит дополнительный урон.', 'img': 'puck_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Фаза наносит дополнительный урон.', 'img': 'puck_shard.png'}
        ]
    },
    'pugna': {
        'data': {
            'localized_name': 'Pugna',
            'bio': 'Pugna — герой интеллекта, который разрушает здания.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Разрушение', 'desc': 'Наносит урон зданиям.', 'img': 'pugna_nether_blast.png'},
            {'dname': 'Снижение урона', 'desc': 'Снижает урон врага.', 'img': 'pugna_decrepify.png'},
            {'dname': 'Восстановление', 'desc': 'Восстанавливает здоровье.', 'img': 'pugna_life_drain.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'pugna_nether_ward.png'},
            {'dname': 'Врождённая: Разрушение', 'desc': 'Разрушение наносит дополнительный урон.', 'img': 'pugna_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'pugna_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Снижение урона наносит дополнительный урон.', 'img': 'pugna_shard.png'}
        ]
    },
    'queen_of_pain': {
        'data': {
            'localized_name': 'Queen of Pain',
            'bio': 'Queen of Pain — герой интеллекта, который наносит боль.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Крик боли', 'desc': 'Наносит урон врагам.', 'img': 'queenofpain_scream_of_pain.png'},
            {'dname': 'Телепорт', 'desc': 'Телепортируется.', 'img': 'queenofpain_blink.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'queenofpain_shadow_strike.png'},
            {'dname': 'Волна', 'desc': 'Наносит урон по площади.', 'img': 'queenofpain_sonic_wave.png'},
            {'dname': 'Врождённая: Боль', 'desc': 'Крик боли наносит дополнительный урон.', 'img': 'queenofpain_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Волна наносит дополнительный урон.', 'img': 'queenofpain_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Яд наносит дополнительный урон.', 'img': 'queenofpain_shard.png'}
        ]
    },
    'ringmaster': {
        'data': {
            'localized_name': 'Ringmaster',
            'bio': 'Ringmaster — герой интеллекта, который управляет цирком.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Цирк', 'desc': 'Создаёт цирк.', 'img': 'ringmaster_escape_artist.png'},
            {'dname': 'Шоу', 'desc': 'Наносит урон врагам.', 'img': 'ringmaster_wheel_of_fortune.png'},
            {'dname': 'Фокус', 'desc': 'Оглушает врага.', 'img': 'ringmaster_spotlight.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'ringmaster_grand_finale.png'},
            {'dname': 'Врождённая: Цирк', 'desc': 'Цирк наносит дополнительный урон.', 'img': 'ringmaster_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'ringmaster_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Фокус наносит дополнительный урон.', 'img': 'ringmaster_shard.png'}
        ]
    },
    'rubick': {
        'data': {
            'localized_name': 'Rubick',
            'bio': 'Rubick — герой интеллекта, который крадёт способности.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Кража', 'desc': 'Крадёт способность.', 'img': 'rubick_spell_steal.png'},
            {'dname': 'Телекинез', 'desc': 'Поднимает врага.', 'img': 'rubick_telekinesis.png'},
            {'dname': 'Фада', 'desc': 'Наносит урон врагам.', 'img': 'rubick_fade_bolt.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'rubick_null_field.png'},
            {'dname': 'Врождённая: Магия', 'desc': 'Кража наносит дополнительный урон.', 'img': 'rubick_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'rubick_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Телекинез наносит дополнительный урон.', 'img': 'rubick_shard.png'}
        ]
    },
    'shadow_demon': {
        'data': {
            'localized_name': 'Shadow Demon',
            'bio': 'Shadow Demon — герой интеллекта, который создаёт иллюзии.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Разрушение', 'desc': 'Наносит урон врагам.', 'img': 'shadow_demon_shadow_poison.png'},
            {'dname': 'Захват', 'desc': 'Захватывает врага.', 'img': 'shadow_demon_disruption.png'},
            {'dname': 'Дух', 'desc': 'Создаёт духа.', 'img': 'shadow_demon_soul_catcher.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'shadow_demon_demonic_purge.png'},
            {'dname': 'Врождённая: Тень', 'desc': 'Разрушение наносит дополнительный урон.', 'img': 'shadow_demon_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'shadow_demon_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Захват наносит дополнительный урон.', 'img': 'shadow_demon_shard.png'}
        ]
    },
    'shadow_shaman': {
        'data': {
            'localized_name': 'Shadow Shaman',
            'bio': 'Shadow Shaman — герой интеллекта, который создаёт тотемы.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Тотем', 'desc': 'Создаёт тотем.', 'img': 'shadow_shaman_mass_serpent_ward.png'},
            {'dname': 'Оглушение', 'desc': 'Оглушает врага.', 'img': 'shadow_shaman_shackles.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'shadow_shaman_ether_shock.png'},
            {'dname': 'Превращение', 'desc': 'Превращает врага.', 'img': 'shadow_shaman_hex.png'},
            {'dname': 'Врождённая: Шаман', 'desc': 'Тотем наносит дополнительный урон.', 'img': 'shadow_shaman_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Превращение наносит дополнительный урон.', 'img': 'shadow_shaman_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Оглушение наносит дополнительный урон.', 'img': 'shadow_shaman_shard.png'}
        ]
    },
    'silencer': {
        'data': {
            'localized_name': 'Silencer',
            'bio': 'Silencer — герой интеллекта, который заставляет молчать.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Проклятие', 'desc': 'Заставляет врага молчать.', 'img': 'silencer_curse_of_the_silent.png'},
            {'dname': 'Клинки', 'desc': 'Наносит дополнительный урон.', 'img': 'silencer_glaives_of_wisdom.png'},
            {'dname': 'Проклятие', 'desc': 'Крадёт интеллект.', 'img': 'silencer_arcane_curse.png'},
            {'dname': 'Глобальное молчание', 'desc': 'Заставляет всех молчать.', 'img': 'silencer_global_silence.png'},
            {'dname': 'Врождённая: Молчание', 'desc': 'Проклятие наносит дополнительный урон.', 'img': 'silencer_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Глобальное молчание наносит дополнительный урон.', 'img': 'silencer_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Клинки наносят дополнительный урон.', 'img': 'silencer_shard.png'}
        ]
    },
    'skywrath_mage': {
        'data': {
            'localized_name': 'Skywrath Mage',
            'bio': 'Skywrath Mage — герой интеллекта, который стреляет магией.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Стрела', 'desc': 'Наносит урон врагам.', 'img': 'skywrath_mage_arcane_bolt.png'},
            {'dname': 'Замедление', 'desc': 'Замедляет врага.', 'img': 'skywrath_mage_concussive_shot.png'},
            {'dname': 'Печать', 'desc': 'Защищает от магии.', 'img': 'skywrath_mage_ancient_seal.png'},
            {'dname': 'Вспышка', 'desc': 'Наносит огромный урон.', 'img': 'skywrath_mage_mystic_flare.png'},
            {'dname': 'Врождённая: Магия', 'desc': 'Стрела наносит дополнительный урон.', 'img': 'skywrath_mage_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Вспышка наносит дополнительный урон.', 'img': 'skywrath_mage_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Замедление наносит дополнительный урон.', 'img': 'skywrath_mage_shard.png'}
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
            {'dname': 'Остаток', 'desc': 'Наносит урон.', 'img': 'storm_spirit_static_remnant.png'},
            {'dname': 'Вихрь', 'desc': 'Захватывает врага.', 'img': 'storm_spirit_electric_vortex.png'},
            {'dname': 'Шар', 'desc': 'Перемещается через врагов.', 'img': 'storm_spirit_ball_lightning.png'},
            {'dname': 'Перегрузка', 'desc': 'Наносит дополнительный урон.', 'img': 'storm_spirit_overload.png'},
            {'dname': 'Врождённая: Шар', 'desc': 'Остаток наносит дополнительный урон.', 'img': 'storm_spirit_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Перегрузка наносит дополнительный урон.', 'img': 'storm_spirit_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Вихрь наносит дополнительный урон.', 'img': 'storm_spirit_shard.png'}
        ]
    },
    'tinker': {
        'data': {
            'localized_name': 'Tinker',
            'bio': 'Tinker — герой интеллекта, который создаёт машины.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Ракета', 'desc': 'Запускает ракету.', 'img': 'tinker_rocket_flare.png'},
            {'dname': 'Лазер', 'desc': 'Наносит урон врагам.', 'img': 'tinker_laser.png'},
            {'dname': 'Телепорт', 'desc': 'Телепортируется.', 'img': 'tinker_rearm.png'},
            {'dname': 'Марш', 'desc': 'Перезаряжает способности.', 'img': 'tinker_march_of_the_machines.png'},
            {'dname': 'Врождённая: Машины', 'desc': 'Ракета наносит дополнительный урон.', 'img': 'tinker_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Марш наносит дополнительный урон.', 'img': 'tinker_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Лазер наносит дополнительный урон.', 'img': 'tinker_shard.png'}
        ]
    },
    'warlock': {
        'data': {
            'localized_name': 'Warlock',
            'bio': 'Warlock — герой интеллекта, который призывает голема.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Связь', 'desc': 'Связывает союзников.', 'img': 'warlock_fatal_bonds.png'},
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'warlock_shadow_word.png'},
            {'dname': 'Голем', 'desc': 'Призывает голема.', 'img': 'warlock_chaotic_offering.png'},
            {'dname': 'Турбулентность', 'desc': 'Наносит урон по площади.', 'img': 'warlock_upheaval.png'},
            {'dname': 'Врождённая: Голем', 'desc': 'Связь наносит дополнительный урон.', 'img': 'warlock_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Голем наносит дополнительный урон.', 'img': 'warlock_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Лечение наносит дополнительный урон.', 'img': 'warlock_shard.png'}
        ]
    },
    'winter_wyvern': {
        'data': {
            'localized_name': 'Winter Wyvern',
            'bio': 'Winter Wyvern — герой интеллекта, который замораживает врагов.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Дыхание', 'desc': 'Замораживает врагов.', 'img': 'winter_wyvern_arctic_burn.png'},
            {'dname': 'Кокон', 'desc': 'Заключает врага в кокон.', 'img': 'winter_wyvern_cold_embrace.png'},
            {'dname': 'Осколки', 'desc': 'Наносит урон врагам.', 'img': 'winter_wyvern_splinter_blast.png'},
            {'dname': 'Проклятие', 'desc': 'Замораживает врагов.', 'img': 'winter_wyvern_winters_curse.png'},
            {'dname': 'Врождённая: Лёд', 'desc': 'Дыхание наносит дополнительный урон.', 'img': 'winter_wyvern_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Проклятие наносит дополнительный урон.', 'img': 'winter_wyvern_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Кокон наносит дополнительный урон.', 'img': 'winter_wyvern_shard.png'}
        ]
    },
    'witch_doctor': {
        'data': {
            'localized_name': 'Witch Doctor',
            'bio': 'Witch Doctor — герой интеллекта, который лечит и наносит урон.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'int',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Тотем смерти', 'desc': 'Создаёт тотем смерти.', 'img': 'witch_doctor_death_ward.png'},
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'witch_doctor_heal.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'witch_doctor_paralyzing_cask.png'},
            {'dname': 'Проклятие', 'desc': 'Наносит урон по площади.', 'img': 'witch_doctor_maledict.png'},
            {'dname': 'Врождённая: Доктор', 'desc': 'Тотем смерти наносит дополнительный урон.', 'img': 'witch_doctor_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Проклятие наносит дополнительный урон.', 'img': 'witch_doctor_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Лечение наносит дополнительный урон.', 'img': 'witch_doctor_shard.png'}
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
            {'dname': 'Удар', 'desc': 'Наносит урон.', 'img': 'zeus_lightning_bolt.png'},
            {'dname': 'Гнев', 'desc': 'Наносит урон по всем врагам.', 'img': 'zeus_thundergods_wrath.png'},
            {'dname': 'Поле', 'desc': 'Наносит урон.', 'img': 'zeus_static_field.png'},
            {'dname': 'Врождённая: Бог', 'desc': 'Молния наносит дополнительный урон.', 'img': 'zeus_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Гнев наносит дополнительный урон.', 'img': 'zeus_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'zeus_shard.png'}
        ]
    },
    # ===== УНИВЕРСАЛЬНЫЕ =====
    'abaddon': {
        'data': {
            'localized_name': 'Abaddon',
            'bio': 'Абаддон — универсальный герой, который защищает союзников.',
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
            {'dname': 'Возврат времени', 'desc': 'Превращает получаемый урон в исцеление.', 'img': 'abaddon_borrowed_time.png'},
            {'dname': 'Врождённая: Тьма', 'desc': 'Мистический туман наносит дополнительный урон.', 'img': 'abaddon_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Возврат времени наносит дополнительный урон.', 'img': 'abaddon_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Щит без света наносит дополнительный урон.', 'img': 'abaddon_shard.png'}
        ]
    },
    'arc_warden': {
        'data': {
            'localized_name': 'Arc Warden',
            'bio': 'Arc Warden — универсальный герой, который создаёт клонов.',
            'base_str': 22, 'base_agi': 18, 'base_int': 20,
            'base_health': 600, 'base_mana': 300, 'base_armor': 2.0,
            'attack_rate': 1.7, 'move_speed': 300,
            'base_attack_min': 45, 'base_attack_max': 55, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.0
        },
        'abilities': [
            {'dname': 'Клон', 'desc': 'Создаёт клона.', 'img': 'arc_warden_tempest_double.png'},
            {'dname': 'Молния', 'desc': 'Наносит урон врагам.', 'img': 'arc_warden_flux.png'},
            {'dname': 'Пузырь', 'desc': 'Создаёт магнитное поле.', 'img': 'arc_warden_magnetic_field.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'arc_warden_spark_wraith.png'},
            {'dname': 'Врождённая: Клоны', 'desc': 'Клон наносит дополнительный урон.', 'img': 'arc_warden_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'arc_warden_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Молния наносит дополнительный урон.', 'img': 'arc_warden_shard.png'}
        ]
    },
    'bane': {
        'data': {
            'localized_name': 'Bane',
            'bio': 'Bane — универсальный герой, который усыпляет врагов.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Кошмар', 'desc': 'Усыпляет врага.', 'img': 'bane_nightmare.png'},
            {'dname': 'Вампиризм', 'desc': 'Крадёт здоровье.', 'img': 'bane_brain_sap.png'},
            {'dname': 'Ослабление', 'desc': 'Снижает урон врага.', 'img': 'bane_enfeeble.png'},
            {'dname': 'Власть', 'desc': 'Захватывает врага.', 'img': 'bane_fiends_grip.png'},
            {'dname': 'Врождённая: Кошмар', 'desc': 'Кошмар наносит дополнительный урон.', 'img': 'bane_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Власть наносит дополнительный урон.', 'img': 'bane_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Вампиризм наносит дополнительный урон.', 'img': 'bane_shard.png'}
        ]
    },
    'batrider': {
        'data': {
            'localized_name': 'Batrider',
            'bio': 'Batrider — универсальный герой, который управляет огнём.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Огненная ловушка', 'desc': 'Создаёт огненную ловушку.', 'img': 'batrider_flaming_lasso.png'},
            {'dname': 'Клей', 'desc': 'Замедляет врага.', 'img': 'batrider_sticky_napalm.png'},
            {'dname': 'Огненный шар', 'desc': 'Наносит урон врагам.', 'img': 'batrider_firefly.png'},
            {'dname': 'Ультимейт', 'desc': 'Удерживает врага.', 'img': 'batrider_flaming_lasso.png'},
            {'dname': 'Врождённая: Огонь', 'desc': 'Огненная ловушка наносит дополнительный урон.', 'img': 'batrider_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'batrider_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Клей наносит дополнительный урон.', 'img': 'batrider_shard.png'}
        ]
    },
    'brewmaster': {
        'data': {
            'localized_name': 'Brewmaster',
            'bio': 'Brewmaster — универсальный герой, который призывает духов.',
            'base_str': 22, 'base_agi': 18, 'base_int': 20,
            'base_health': 600, 'base_mana': 300, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 45, 'base_attack_max': 55, 'attack_range': 150,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.0
        },
        'abilities': [
            {'dname': 'Туман', 'desc': 'Наносит урон врагам.', 'img': 'brewmaster_thunder_clap.png'},
            {'dname': 'Пиво', 'desc': 'Замедляет врага.', 'img': 'brewmaster_drunken_haze.png'},
            {'dname': 'Уклонение', 'desc': 'Уклоняется от атак.', 'img': 'brewmaster_drunken_brawler.png'},
            {'dname': 'Духи', 'desc': 'Призывает духов.', 'img': 'brewmaster_primal_split.png'},
            {'dname': 'Врождённая: Пиво', 'desc': 'Туман наносит дополнительный урон.', 'img': 'brewmaster_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Духи наносят дополнительный урон.', 'img': 'brewmaster_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Пиво наносит дополнительный урон.', 'img': 'brewmaster_shard.png'}
        ]
    },
    'dazzle': {
        'data': {
            'localized_name': 'Dazzle',
            'bio': 'Dazzle — универсальный герой, который лечит союзников.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Лечение', 'desc': 'Лечит союзников.', 'img': 'dazzle_shadow_wave.png'},
            {'dname': 'Броня', 'desc': 'Увеличивает броню.', 'img': 'dazzle_weave.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'dazzle_poison_touch.png'},
            {'dname': 'Ультимейт', 'desc': 'Защищает от смерти.', 'img': 'dazzle_shallow_grave.png'},
            {'dname': 'Врождённая: Лечение', 'desc': 'Лечение наносит дополнительный урон.', 'img': 'dazzle_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'dazzle_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Броня наносит дополнительный урон.', 'img': 'dazzle_shard.png'}
        ]
    },
    'death_prophet': {
        'data': {
            'localized_name': 'Death Prophet',
            'bio': 'Death Prophet — универсальный герой, который призывает духов.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Духи', 'desc': 'Призывает духов.', 'img': 'death_prophet_exorcism.png'},
            {'dname': 'Волна', 'desc': 'Наносит урон врагам.', 'img': 'death_prophet_crypt_swarm.png'},
            {'dname': 'Безмолвие', 'desc': 'Заставляет врага замолчать.', 'img': 'death_prophet_silence.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'death_prophet_exorcism.png'},
            {'dname': 'Врождённая: Духи', 'desc': 'Волна наносит дополнительный урон.', 'img': 'death_prophet_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'death_prophet_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Безмолвие наносит дополнительный урон.', 'img': 'death_prophet_shard.png'}
        ]
    },
    'enigma': {
        'data': {
            'localized_name': 'Enigma',
            'bio': 'Enigma — универсальный герой, который создаёт чёрную дыру.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Чёрная дыра', 'desc': 'Создаёт чёрную дыру.', 'img': 'enigma_black_hole.png'},
            {'dname': 'Малифис', 'desc': 'Наносит урон врагам.', 'img': 'enigma_malefice.png'},
            {'dname': 'Обработка', 'desc': 'Создаёт прислужников.', 'img': 'enigma_demonic_conversion.png'},
            {'dname': 'Вихрь', 'desc': 'Наносит урон по площади.', 'img': 'enigma_midnight_pulse.png'},
            {'dname': 'Врождённая: Тьма', 'desc': 'Чёрная дыра наносит дополнительный урон.', 'img': 'enigma_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Вихрь наносит дополнительный урон.', 'img': 'enigma_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Малифис наносит дополнительный урон.', 'img': 'enigma_shard.png'}
        ]
    },
    'furion': {
        'data': {
            'localized_name': "Nature's Prophet",
            'bio': "Nature's Prophet — универсальный герой, который управляет природой.",
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Телепорт', 'desc': 'Телепортируется.', 'img': 'furion_teleportation.png'},
            {'dname': 'Деревья', 'desc': 'Призывает деревья.', 'img': 'furion_natures_call.png'},
            {'dname': 'Урон', 'desc': 'Наносит урон врагам.', 'img': 'furion_wrath_of_nature.png'},
            {'dname': 'Рост', 'desc': 'Создаёт деревья.', 'img': 'furion_sprout.png'},
            {'dname': 'Врождённая: Природа', 'desc': 'Телепорт наносит дополнительный урон.', 'img': 'furion_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Урон наносит дополнительный урон.', 'img': 'furion_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Деревья наносят дополнительный урон.', 'img': 'furion_shard.png'}
        ]
    },
    'magnus': {
        'data': {
            'localized_name': 'Magnus',
            'bio': 'Magnus — универсальный герой, который управляет силой.',
            'base_str': 22, 'base_agi': 18, 'base_int': 20,
            'base_health': 600, 'base_mana': 300, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 300,
            'base_attack_min': 45, 'base_attack_max': 55, 'attack_range': 150,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.0
        },
        'abilities': [
            {'dname': 'Удар', 'desc': 'Наносит урон врагам.', 'img': 'magnus_shockwave.png'},
            {'dname': 'Сила', 'desc': 'Увеличивает урон.', 'img': 'magnus_empower.png'},
            {'dname': 'Рог', 'desc': 'Отбрасывает врага.', 'img': 'magnus_skewer.png'},
            {'dname': 'Ультимейт', 'desc': 'Притягивает врагов.', 'img': 'magnus_reverse_polarity.png'},
            {'dname': 'Врождённая: Сила', 'desc': 'Удар наносит дополнительный урон.', 'img': 'magnus_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'magnus_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Рог наносит дополнительный урон.', 'img': 'magnus_shard.png'}
        ]
    },
    'marci': {
        'data': {
            'localized_name': 'Marci',
            'bio': 'Marci — универсальный герой, который наносит урон.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Удар', 'desc': 'Наносит урон врагам.', 'img': 'marci_throw.png'},
            {'dname': 'Восстановление', 'desc': 'Лечит союзников.', 'img': 'marci_rebound.png'},
            {'dname': 'Ярость', 'desc': 'Увеличивает урон.', 'img': 'marci_sidekick.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'marci_unleash.png'},
            {'dname': 'Врождённая: Ярость', 'desc': 'Удар наносит дополнительный урон.', 'img': 'marci_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'marci_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Восстановление наносит дополнительный урон.', 'img': 'marci_shard.png'}
        ]
    },
    'nyx_assassin': {
        'data': {
            'localized_name': 'Nyx Assassin',
            'bio': 'Nyx Assassin — универсальный герой, который скрывается от врагов.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Удар', 'desc': 'Наносит урон врагам.', 'img': 'nyx_assassin_impale.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'nyx_assassin_mana_burn.png'},
            {'dname': 'Скрытность', 'desc': 'Становится невидимым.', 'img': 'nyx_assassin_vendetta.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'nyx_assassin_spiked_carapace.png'},
            {'dname': 'Врождённая: Ночной', 'desc': 'Удар наносит дополнительный урон.', 'img': 'nyx_assassin_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'nyx_assassin_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Яд наносит дополнительный урон.', 'img': 'nyx_assassin_shard.png'}
        ]
    },
    'pangolier': {
        'data': {
            'localized_name': 'Pangolier',
            'bio': 'Pangolier — универсальный герой, который управляет щитом.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Удар', 'desc': 'Наносит урон врагам.', 'img': 'pangolier_swashbuckle.png'},
            {'dname': 'Броня', 'desc': 'Увеличивает броню.', 'img': 'pangolier_shield_crash.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'pangolier_lucky_shot.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'pangolier_rolling_thunder.png'},
            {'dname': 'Врождённая: Щит', 'desc': 'Удар наносит дополнительный урон.', 'img': 'pangolier_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'pangolier_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Броня наносит дополнительный урон.', 'img': 'pangolier_shard.png'}
        ]
    },
    'sand_king': {
        'data': {
            'localized_name': 'Sand King',
            'bio': 'Sand King — универсальный герой, который управляет песком.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Удар', 'desc': 'Наносит урон врагам.', 'img': 'sand_king_caustic_finale.png'},
            {'dname': 'Песок', 'desc': 'Наносит урон врагам.', 'img': 'sand_king_sand_storm.png'},
            {'dname': 'Скрытность', 'desc': 'Становится невидимым.', 'img': 'sand_king_sand_storm.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'sand_king_epicenter.png'},
            {'dname': 'Врождённая: Песок', 'desc': 'Удар наносит дополнительный урон.', 'img': 'sand_king_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'sand_king_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Песок наносит дополнительный урон.', 'img': 'sand_king_shard.png'}
        ]
    },
    'snapfire': {
        'data': {
            'localized_name': 'Snapfire',
            'bio': 'Snapfire — универсальный герой, который стреляет огнём.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Огонь', 'desc': 'Наносит урон врагам.', 'img': 'snapfire_scatterblast.png'},
            {'dname': 'Печенье', 'desc': 'Наносит урон врагам.', 'img': 'snapfire_firesnap_cookie.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'snapfire_mortimer_kisses.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'snapfire_lil_shredder.png'},
            {'dname': 'Врождённая: Огонь', 'desc': 'Огонь наносит дополнительный урон.', 'img': 'snapfire_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'snapfire_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Печенье наносит дополнительный урон.', 'img': 'snapfire_shard.png'}
        ]
    },
    'techies': {
        'data': {
            'localized_name': 'Techies',
            'bio': 'Techies — универсальный герой, который ставит мины.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Мина', 'desc': 'Ставит мину.', 'img': 'techies_land_mines.png'},
            {'dname': 'Бомба', 'desc': 'Ставит бомбу.', 'img': 'techies_suicide_squad.png'},
            {'dname': 'Замедление', 'desc': 'Замедляет врага.', 'img': 'techies_stasis_trap.png'},
            {'dname': 'Ультимейт', 'desc': 'Ставит бомбу.', 'img': 'techies_minefield_sign.png'},
            {'dname': 'Врождённая: Мины', 'desc': 'Мина наносит дополнительный урон.', 'img': 'techies_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'techies_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Бомба наносит дополнительный урон.', 'img': 'techies_shard.png'}
        ]
    },
    'visage': {
        'data': {
            'localized_name': 'Visage',
            'bio': 'Visage — универсальный герой, который призывает птиц.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Птицы', 'desc': 'Призывает птиц.', 'img': 'visage_summon_familiars.png'},
            {'dname': 'Яд', 'desc': 'Наносит урон врагам.', 'img': 'visage_soul_assumption.png'},
            {'dname': 'Броня', 'desc': 'Увеличивает броню.', 'img': 'visage_gravekeepers_cloak.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'visage_familiars.png'},
            {'dname': 'Врождённая: Птицы', 'desc': 'Птицы наносят дополнительный урон.', 'img': 'visage_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'visage_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Яд наносит дополнительный урон.', 'img': 'visage_shard.png'}
        ]
    },
    'void_spirit': {
        'data': {
            'localized_name': 'Void Spirit',
            'bio': 'Void Spirit — универсальный герой, который управляет пространством.',
            'base_str': 20, 'base_agi': 18, 'base_int': 22,
            'base_health': 580, 'base_mana': 320, 'base_armor': 2.0,
            'attack_rate': 1.8, 'move_speed': 290,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 2.0, 'agi_gain': 1.8, 'int_gain': 2.2
        },
        'abilities': [
            {'dname': 'Сфера', 'desc': 'Создаёт сферу.', 'img': 'void_spirit_astral_step.png'},
            {'dname': 'Щит', 'desc': 'Создаёт щит.', 'img': 'void_spirit_resonant_pulse.png'},
            {'dname': 'Удар', 'desc': 'Наносит урон врагам.', 'img': 'void_spirit_dissimilate.png'},
            {'dname': 'Ультимейт', 'desc': 'Наносит урон по площади.', 'img': 'void_spirit_echo_slam.png'},
            {'dname': 'Врождённая: Пространство', 'desc': 'Сфера наносит дополнительный урон.', 'img': 'void_spirit_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'void_spirit_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'void_spirit_shard.png'}
        ]
    },
    'windranger': {
        'data': {
            'localized_name': 'Windranger',
            'bio': 'Windranger — универсальный герой, который управляет ветром.',
            'base_str': 18, 'base_agi': 16, 'base_int': 22,
            'base_health': 540, 'base_mana': 320, 'base_armor': 1.5,
            'attack_rate': 1.8, 'move_speed': 285,
            'base_attack_min': 40, 'base_attack_max': 50, 'attack_range': 600,
            'primary_attr': 'universal',
            'str_gain': 1.8, 'agi_gain': 1.6, 'int_gain': 3.2
        },
        'abilities': [
            {'dname': 'Ветер', 'desc': 'Наносит урон врагам.', 'img': 'windrunner_shackleshot.png'},
            {'dname': 'Удар', 'desc': 'Наносит дополнительный урон.', 'img': 'windrunner_powershot.png'},
            {'dname': 'Скорость', 'desc': 'Увеличивает скорость.', 'img': 'windrunner_windrun.png'},
            {'dname': 'Ультимейт', 'desc': 'Увеличивает скорость атаки.', 'img': 'windrunner_focus_fire.png'},
            {'dname': 'Врождённая: Ветер', 'desc': 'Ветер наносит дополнительный урон.', 'img': 'windranger_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Ультимейт наносит дополнительный урон.', 'img': 'windranger_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Удар наносит дополнительный урон.', 'img': 'windranger_shard.png'}
        ]
    },
    'wisp': {
        'data': {
            'localized_name': 'Io',
            'bio': 'Io — универсальный герой, который связывает союзников.',
            'base_str': 19, 'base_agi': 14, 'base_int': 21,
            'base_health': 538, 'base_mana': 327, 'base_armor': 3.34,
            'attack_rate': 1.49, 'move_speed': 320,
            'base_attack_min': 52.5, 'base_attack_max': 56.7, 'attack_range': 500,
            'primary_attr': 'universal',
            'str_gain': 3.0, 'agi_gain': 1.6, 'int_gain': 1.7
        },
        'abilities': [
            {'dname': 'Связь', 'desc': 'Связывает союзника.', 'img': 'wisp_tether.png'},
            {'dname': 'Духи', 'desc': 'Призывает духов.', 'img': 'wisp_spirits.png'},
            {'dname': 'Перегрузка', 'desc': 'Увеличивает скорость.', 'img': 'wisp_overcharge.png'},
            {'dname': 'Телепорт', 'desc': 'Телепортируется.', 'img': 'wisp_relocate.png'},
            {'dname': 'Врождённая: Духи', 'desc': 'Связь наносит дополнительный урон.', 'img': 'wisp_innate.png'},
            {'dname': 'Улучшение от Аганима', 'desc': 'Телепорт наносит дополнительный урон.', 'img': 'wisp_scepter.png'},
            {'dname': 'Улучшение от Шарда', 'desc': 'Духи наносят дополнительный урон.', 'img': 'wisp_shard.png'}
        ]
    }
}

def get_local_hero_data(hero_name):
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
    return f"""
    <h1>Тест маршрута героя</h1>
    <p>Герой: <strong>{hero_name}</strong></p>
    <p>Если вы видите это сообщение — маршрут работает!</p>
    <p><a href="/">На главную</a></p>
    """

@app.route('/hero/<hero_name>')
def hero_page(hero_name):
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
    print(f"🔍 API запрос героя: {hero_name}")
    hero_data = get_hero_data(hero_name)
    if not hero_data:
        print(f"⚠️ OpenDota не ответил, ищем локальные данные для {hero_name}")
        local_data = get_local_hero_data(hero_name)
        if local_data:
            print(f"✅ Использованы локальные данные для {hero_name}")
            return jsonify(local_data)
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
    print("✅ Добавлена тестовая новость")
    print("=" * 60)

initialize_news()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)