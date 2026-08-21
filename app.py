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
# ДАННЫЕ ПАТЧА 7.41e (из твоего файла)
# ============================================================
def get_patch_741e():
    """Возвращает структурированные данные патча 7.41e"""
    return {
        'version': '7.41e',
        'date': '31 July 2026',
        'type': 'minor',
        'general_changes': [
            'Парные порталы: теперь подготовку телепортации можно прервать оцепенением',
            'Терзатель: теперь при смене разлома сбивает с цели летящие в него снаряды'
        ],
        'item_changes': [
            {'item': 'Abyssal Blade', 'old': '26', 'new': '30', 'detail': 'Бонус к силе увеличен с 26 до 30'},
            {'item': 'Butterfly', 'old': '35', 'new': '30', 'detail': 'Бонус к ловкости уменьшен с 35 до 30, бонус к урону увеличен с 25 до 30'},
            {'item': 'Chasm Stone', 'old': '800', 'new': '900', 'detail': 'Стоимость увеличена с 800 до 900 золота'},
            {'item': "Shiva's Guard", 'old': '1350', 'new': '1250', 'detail': 'Стоимость рецепта уменьшена с 1350 до 1250 золота'},
            {'item': 'Gleipnir', 'old': '400', 'new': '300', 'detail': 'Стоимость рецепта уменьшена с 400 до 300 золота'},
            {'item': "Crella's Crozier", 'detail': 'Rite of Rumusque: длительность кражи скорости увеличена с 1.5 до 2 секунд; Putrefaction Aura: кража скорости увеличена с 75% до 90%'},
            {'item': 'Divine Rapier', 'detail': 'Бонусы к урону от заклинаний от нескольких Divine Rapier больше не складываются'},
            {'item': 'Eye of Skadi', 'old': '20', 'new': '25', 'detail': 'Cold Attack: замедление атаки увеличено с 20% до 25%'},
            {'item': 'Hand of Midas', 'old': '35', 'new': '40', 'detail': 'Бонус к скорости атаки увеличен с 35 до 40'},
            {'item': "Heaven's Halberd", 'old': '16', 'new': '15', 'detail': 'Disarm: перезарядка уменьшена с 16 до 15 секунд'},
            {'item': 'Hurricane Pike', 'old': '6', 'new': '5', 'detail': 'Hurricane Thrust: длительность положительного эффекта уменьшена с 6 до 5 секунд'},
            {'item': 'Kaya', 'old': '30', 'new': '20', 'detail': 'Бонус к усилению восстановления маны уменьшен с 30% до 20%'},
            {'item': 'Meteor Hammer', 'old': '35', 'new': '25', 'detail': 'Бонус к усилению восстановления маны уменьшен с 35% до 25%'},
            {'item': 'Kaya and Sange', 'old': '40', 'new': '30', 'detail': 'Бонус к усилению восстановления маны уменьшен с 40% до 30%'},
            {'item': 'Yasha and Kaya', 'old': '40', 'new': '30', 'detail': 'Бонус к усилению восстановления маны уменьшен с 40% до 30%'},
            {'item': 'Mask of Madness', 'detail': 'Berserk: бонус к скорости передвижения для героев дальнего боя уменьшен с 8% до 6%, бонус к сопротивлению замедлениям у героев дальнего боя уменьшен с 30% до 15%'},
            {'item': 'Orb of Frost', 'detail': 'Frost: больше не срабатывает при атаке по союзным существам, снижение пополнения здоровья усилено с 13% до 15%'},
            {'item': 'Orb of Corrosion', 'old': '16', 'new': '18', 'detail': 'Corrosion: снижение пополнения здоровья усилено с 16% до 18%'},
            {'item': 'Orb of Venom', 'old': '10', 'new': '12', 'detail': 'Poison Attack: урон в секунду увеличен с 10 до 12'},
            {'item': 'Refresher Shard', 'detail': 'Больше не даёт +12 к восстановлению здоровья, +6 к восстановлению маны и +20 к урону'},
            {'item': 'Satanic', 'old': '30', 'new': '40', 'detail': 'Unholy Rage: перезарядка увеличена с 30 до 40 секунд'},
            {'item': 'Smoke of Deceit', 'detail': 'Disguise: бонусы к длительности эффектов больше не влияют на время действия'},
            {'item': 'Urn of Shadows', 'old': '1.25', 'new': '1', 'detail': 'Бонус к восстановлению маны уменьшен с 1.25 до 1; больше не получает заряды за погибших поблизости героев, если находится в тайнике'},
            {'item': 'Essence Distiller', 'detail': 'Больше не получает заряды за погибших поблизости героев, если находится в тайнике'},
            {'item': 'Spirit Vessel', 'detail': 'Больше не получает заряды за погибших поблизости героев, если находится в тайнике'},
            {'item': 'Veil of Discord', 'old': '50', 'new': '25', 'detail': 'Spell Weakness: расход маны уменьшен с 50 до 25'}
        ],
        'neutral_item_changes': [
            {'item': "Forager's Kit", 'old': '1', 'new': '0.75', 'detail': 'Forage: время сбора урожая уменьшено с 1 до 0.75 секунды'},
            {'item': "Conjurer's Catalyst", 'old': '30', 'new': '20', 'detail': 'Spellover: урон по области от существ, не являющихся героями, уменьшен с 30 до 20; теперь расчёт урона для срабатывания на иллюзиях не учитывает увеличение урона по иллюзиям'},
            {'item': "Enchanter's Bauble", 'old': '40', 'new': '35', 'detail': 'Enchant: увеличение бонусов чар при повторном создании артефакта ослаблено с 40% до 35%'},
            {'item': 'Witchbane', 'old': '40', 'new': '30', 'detail': 'Cleanse: перезарядка уменьшена с 40 до 30 секунд'},
            {'item': 'Greedy', 'old': '75/100', 'new': '65/90', 'detail': 'Бонус к золоту в минуту уменьшен с 75/100 до 65/90'},
            {'item': 'Feverish', 'detail': 'Больше не увеличивает расход и потерю маны на 7%; теперь уменьшает максимальную ману на 20%'}
        ],
        'hero_changes': [
            {'hero': 'Ancient Apparition', 'changes': ['Ice Blast: перезарядка уменьшена с 60/50/40 до 50/45/40 секунд']},
            {'hero': 'Axe', 'changes': ['Базовая ловкость уменьшена с 20 до 18', 'Battle Hunger: урон в секунду уменьшен с 12/18/24/30 до 12/16/20/24']},
            {'hero': 'Bane', 'changes': [
                'Ichor of Nyctasha: максимум кошмаров у врага увеличен с 5 до 6, снижение сопротивления эффектам за кошмар уменьшено с 5% до 4%',
                'Nightmare: длительность уменьшена с 3.5/4.5/5.5/6.5 до 3/4/5/6 секунд, теперь полностью отключает жертве обзор',
                "Fiend's Grip: уменьшение перезарядки от Aghanim's Scepter ослаблено с 45 до 40 секунд"
            ]},
            {'hero': 'Batrider', 'changes': ['Smoldering Resin: больше не срабатывает при атаке по союзным существам']},
            {'hero': 'Beastmaster', 'changes': ['Талант 20 уровня: бонус к урону от атак героя и его существ уменьшен с 30 до 25', 'Талант 25 уровня: уменьшение перезарядки Primal Roar ослаблено с 25 до 20 секунд']},
            {'hero': 'Centaur Warrunner', 'changes': ['Double Edge: длительность эффекта от применения с Aghanims Shard уменьшена с 15 до 12 секунд', 'Retaliate: множитель урона за силу уменьшен с 16/24/32/40% до 14/21/28/35%']},
            {'hero': 'Chaos Knight', 'changes': ['Chaos Bolt: скорость снаряда увеличена с 700 до 900']},
            {'hero': 'Clockwerk', 'changes': [
                'Power Cogs: сжигаемая мана уменьшена с 40/80/120/160 до 40/75/110/145',
                'дальность толчка шестерни её владельцем уменьшена с 1000 до 850/900/950/1000',
                'обзор шестерней днём и ночью уменьшен с 1600/600 до 800/400 соответственно',
                'шестерни больше не запрещают появляться нейтральным крипам'
            ]},
            {'hero': 'Death Prophet', 'changes': ['Прирост ловкости увеличен с 2 до 2.3, прирост урона за уровень увеличился с 3.6 до 3.7']},
            {'hero': 'Doom', 'changes': ['Дальность атаки уменьшена с 200 до 175', 'Infernal Blade: базовый урон увеличен с 15/30/45/60 до 18/34/50/66, урон от максимального здоровья изменён с 1/2/3/4% на 0.5/1.75/3/4.25%']},
            {'hero': 'Dragon Knight', 'changes': ["Wyrm's Wrath: дополнительный радиус заклинаний увеличен с 25/50/75/100 до 30/60/90/120"]},
            {'hero': 'Drow Ranger', 'changes': ['Multishot: расход маны увеличен с 50/70/90/110 до 70/85/100/115, дальность применения изменена, доля от базового урона уменьшена со 100/120/140/160% до 80/100/120/140%']},
            {'hero': 'Earth Spirit', 'changes': ['Базовый интеллект уменьшен с 18 до 17', 'Талант 20 уровня: бонус к урону и длительности Magnetize уменьшен с 30% до 25%']},
            {'hero': 'Elder Titan', 'changes': ['Momentum: броня от дополнительной скорости увеличена с 5% + 0.5% за уровень до 7% + 0.5% за уровень', 'Astral Spirit: применение подспособностей, возвращающих и перемещающих духа, больше не снимает невидимость с владельца']},
            {'hero': 'Ember Spirit', 'changes': ['Базовая скорость передвижения уменьшена с 300 до 295']},
            {'hero': 'Grimstroke', 'changes': ['Dark Portrait: чернильная иллюзия больше не имеет штрафа к радиусу обзора, свойственного другим иллюзиям']},
            {'hero': 'Gyrocopter', 'changes': ['Rocket Barrage: расход маны уменьшен с 85 до 75', 'Homing Missile: расход маны уменьшен со 120/130/140/150 до 120, перезарядка уменьшена с 30/24/18/12 до 26/21/16/11 секунд']},
            {'hero': 'Hoodwink', 'changes': ["Mistwoods Wayfarer: шанс срабатывания уменьшен с 14% + 1% за уровень на 14.25% + 0.75% за уровень", 'Sharpshooter: расход маны увеличен со 100/150/200 до 150/200/250', "Hunter's Boomerang: перезарядка увеличена с 18 до 20 секунд"]},
            {'hero': 'Invoker', 'changes': ['Ghost Walk: длительность уменьшена с 60 до 50 секунд, Aghanims Shard больше не увеличивает радиус замедления']},
            {'hero': 'Jakiro', 'changes': ['Прирост интеллекта увеличен с 3 до 3.3']},
            {'hero': 'Keeper of the Light', 'changes': ['Chakra Magic: перезарядка увеличена с 19/16/13/10 до 20/17/14/11 секунд', 'Solar Bind: дальность применения уменьшена с 850 до 750']},
            {'hero': 'Legion Commander', 'changes': ['Базовая сила увеличена с 24 до 25, урон на первом уровне увеличился с 57–61 до 58–62, прирост силы уменьшен с 3.1 до 3, базовая скорость атаки увеличена со 100 до 105', 'Талант 25 уровня: «Победа в дуэли сбрасывает перезарядку Duel» заменено на «Перезарядка Duel короче на 30 сек. при победе в дуэли»']},
            {'hero': 'Lina', 'changes': ['Базовая ловкость уменьшена с 23 до 21']},
            {'hero': 'Lone Druid', 'changes': ['Талант 15 уровня: уменьшение перезарядки Savage Roar ослаблено с 5 до 4 секунд', 'Талант 20 уровня: бонус к радиусу Savage Roar уменьшен со 150 до 125', 'Spirit Bear: базовая броня уменьшена на 1', 'Demolish: дополнительный урон постройкам уменьшен с 30% до 20%']},
            {'hero': 'Magnus', 'changes': ['Horn Toss: урон увеличен с 300 до 325']},
            {'hero': 'Mars', 'changes': ['Прирост интеллекта увеличен с 2.2 до 2.4']},
            {'hero': 'Medusa', 'changes': ['Split Shot: теперь переключение этой способности не снимает невидимость с владельца и доступно во время безмолвия']},
            {'hero': 'Morphling', 'changes': ['Morph: перезарядка уменьшена со 140/100/60 до 125/90/55 секунд, иллюзия от Aghanims Scepter больше не имеет штрафа к радиусу обзора']},
            {'hero': 'Muerta', 'changes': ['Gunslinger: переключение этой способности больше не снимает невидимость с владельца']},
            {'hero': 'Necrophos', 'changes': ['Sadist: восстановление здоровья/маны за эффект уменьшено с 3.7 + 0.3 за уровень до 3.8 + 0.2 за уровень', 'Death Seeker: дальность применения уменьшена с 750 до 600']},
            {'hero': 'Night Stalker', 'changes': ['Crippling Fear: радиус уменьшен с 375 до 350']},
            {'hero': 'Omniknight', 'changes': ['Hammer of Purity: лечение после атаки увеличено с 35% в течение 5 секунд до 40% в течение 4 секунд']},
            {'hero': 'Oracle', 'changes': ["Fate's Edict: теперь эффект этой способности на владельце или его союзниках могут развеять враги", 'False Promise: дальность применения увеличена с 700/800/900 до 800/850/900']},
            {'hero': 'Outworld Destroyer', 'changes': ['Objurgation: теперь применяется мгновенно и не прерывает передвижение, здоровье барьера увеличено с 120/180/240/300 до 150/200/250/300, перезарядка уменьшена с 36/34/32/30 до 36/33/30/27 секунд']},
            {'hero': 'Phantom Assassin', 'changes': ['Blur: теперь эффект этой способности нельзя развеять']},
            {'hero': 'Phantom Lancer', 'changes': ['Juxtapose: перезарядка с Aghanims Shard увеличена с 15 до 18 секунд']},
            {'hero': 'Puck', 'changes': ['Illusory Orb: перезарядка увеличена с 11/10/9/8 до 12/11/10/9 секунд']},
            {'hero': 'Pugna', 'changes': ['Базовый интеллект увеличен с 26 до 27, урон на первом уровне увеличился с 47–54 до 48–55']},
            {'hero': 'Queen of Pain', 'changes': ['Shadow Strike: расход маны уменьшен со 100/110/120/130 до 100/105/110/115', 'Sonic Wave: теперь урон от двух применений этой способности подряд складывается']},
            {'hero': 'Ringmaster', 'changes': ['Impalement Arts: периодический урон крипам изменён с 85/90/95/100 на 60/75/90/105']},
            {'hero': 'Shadow Fiend', 'changes': ['Базовый интеллект уменьшен с 18 до 16', 'Shadowraze: длительность действия эффекта уменьшена с 7 до 6 секунд', 'Талант 25 уровня «Shadowraze наносит урон от атак» больше не позволяет наложить на жертв модификаторы атаки']},
            {'hero': 'Snapfire', 'changes': [
                'Scatterblast: на начальную ширину выстрела больше не влияет увеличение радиуса заклинаний, дополнительный урон от выстрела в упор уменьшен с 30% до 25%',
                'Firesnap Cookie: урон от приземления уменьшен с 75/150/225/300 до 60/130/200/270',
                'Mortimer Kisses: урон от шара уменьшен со 180/270/360 до 170/250/330',
                'Талант 10 уровня: бонус к урону от лужи у Mortimer Kisses уменьшен с 35 до 30',
                'Талант 15 уровня: «–3 сек. перезарядки Firesnap Cookie» заменено на «+125 к дальности заклинаний»',
                'Талант 25 уровня: бонус к числу шаров от Mortimer Kisses уменьшен с 8 до 6'
            ]},
            {'hero': 'Sniper', 'changes': ['Concussive Grenade: теперь эту способность можно применять во время оцепенения, но она будет отталкивать владельца']},
            {'hero': 'Spectre', 'changes': ['Haunt: урон иллюзий изменён с 30/50/70% на 35/50/65%', 'Талант 25 уровня: бонус к урону всех иллюзий героя уменьшен с 15% до 12%']},
            {'hero': 'Templar Assassin', 'changes': ['Psionic Projection: теперь подготовку телепортации можно прервать оцепенением']},
            {'hero': 'Tiny', 'changes': ['Базовое восстановление здоровья уменьшено на 1']},
            {'hero': 'Treant Protector', 'changes': ['Базовая скорость атаки уменьшена со 100 до 90', 'Leech Seed: длительность оцепенения уменьшена с 0.9/1.1/1.3/1.5 до 0.75/1.0/1.25/1.5 сек.', 'Living Armor: расход маны увеличен с 65/70/75/80 до 80']},
            {'hero': 'Troll Warlord', 'changes': ['Базовая ловкость увеличена с 23 до 24, урон на первом уровне увеличился с 50–58 до 51–59', 'Battle Stance: переключение стоек больше не снимает невидимость с владельца', 'Battle Trance: теперь также даёт +35% к сопротивлению замедлениям']},
            {'hero': 'Underlord', 'changes': ["Fiend's Gate: теперь подготовку телепортации можно прервать оцепенением"]},
            {'hero': 'Undying', 'changes': ['Базовая скорость передвижения уменьшена с 300 до 295', 'Flesh Golem: дополнительная скорость передвижения увеличена с 20 до 25']},
            {'hero': 'Vengeful Spirit', 'changes': ['Vengeance Aura: иллюзия от Aghanims Scepter больше не имеет штрафа к радиусу обзора']},
            {'hero': 'Venomancer', 'changes': ['Snakebite: начальный урон увеличен с 40/60/80/100 до 40/70/100/130']},
            {'hero': 'Visage', 'changes': ['Stone Form: приказ гаргульям применить эту способность больше не снимает невидимость с владельца']},
            {'hero': 'Weaver', 'changes': ['Threads of Fate: расстояние разрыва нити увеличено с 900 до 890 + 10 за уровень героя']},
            {'hero': 'Witch Doctor', 'changes': ['Maledict: талант 20 уровня теперь считает иллюзии крипами, поэтому выпущенные ими снаряды не будут наносить урона']},
            {'hero': 'Zeus', 'changes': ["Thundergod's Wrath: урон уменьшен с 300/475/650 до 275/425/575", 'Lightning Hands: теперь переключение этой способности не снимает невидимость с владельца и доступно во время безмолвия, бонус к скорости атаки уменьшен со 30 до 20']}
        ]
    }

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
    patches = get_cache('patches')
    if not patches:
        patch_741e = get_patch_741e()
        patches = [patch_741e]
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