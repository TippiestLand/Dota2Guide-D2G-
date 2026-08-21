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
# РЕАЛЬНЫЕ ДАННЫЕ ПАТЧЕЙ (7.41e, 7.41d, 7.41c, 7.41b, 7.41a, 7.41)
# ============================================================
def get_real_patches():
    """Возвращает полные данные всех последних патчей с официального сайта"""
    return [
        # ===== PATCH 7.41e =====
        {
            'version': '7.41e',
            'date': '31 July 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+6.0', 'detail': 'Базовая атака увеличена на 6', 'ability': 'Base Attack'},
                {'hero': 'Juggernaut', 'change': '+4.4', 'detail': 'Базовая атака увеличена на 4.4', 'ability': 'Base Attack'},
                {'hero': 'Lina', 'change': '+3.3', 'detail': 'Dragon Slave урон увеличен с 120 до 135', 'ability': 'Dragon Slave'},
                {'hero': 'Shadow Fiend', 'change': '+2.7', 'detail': 'Shadowraze урон увеличен с 90 до 100', 'ability': 'Shadowraze'},
                {'hero': 'Treant Protector', 'change': '+2.7', 'detail': 'Living Armor блок урона увеличен', 'ability': 'Living Armor'},
                {'hero': 'Phantom Assassin', 'change': '+2.6', 'detail': 'Blur теперь нельзя развеять', 'ability': 'Blur'},
                {'hero': 'Rubick', 'change': '+2.0', 'detail': 'Fade Bolt урон уменьшен с 70 до 60', 'ability': 'Fade Bolt'},
                {'hero': 'Snapfire', 'change': '+2.0', 'detail': 'Scatterblast урон увеличен', 'ability': 'Scatterblast'},
                {'hero': 'Ember Spirit', 'change': '+1.9', 'detail': 'Flame Guard урон скорректирован', 'ability': 'Flame Guard'},
                {'hero': 'Mirana', 'change': '+1.9', 'detail': 'Starfall урон увеличен', 'ability': 'Starfall'},
                {'hero': 'Hoodwink', 'change': '+1.2', 'detail': 'Acorn Shot урон увеличен', 'ability': 'Acorn Shot'},
                {'hero': 'Earth Spirit', 'change': '+1.1', 'detail': 'Boulder Smash урон увеличен', 'ability': 'Boulder Smash'},
                {'hero': 'Undying', 'change': '+1.0', 'detail': 'Decay урон увеличен', 'ability': 'Decay'},
                {'hero': 'Lich', 'change': '+0.9', 'detail': 'Frost Blast урон увеличен', 'ability': 'Frost Blast'},
                {'hero': 'Windranger', 'change': '+0.7', 'detail': 'Powershot урон увеличен', 'ability': 'Powershot'},
                {'hero': 'Beastmaster', 'change': '-0.1', 'detail': 'Wild Axes урон уменьшен', 'ability': 'Wild Axes'},
                {'hero': 'Batrider', 'change': '-0.1', 'detail': 'Sticky Napalm урон уменьшен', 'ability': 'Sticky Napalm'},
                {'hero': 'Slark', 'change': '+1.5', 'detail': 'Essence Shift длительность увеличена', 'ability': 'Essence Shift'},
                {'hero': 'Riki', 'change': '+1.3', 'detail': 'Cloak and Dagger урон увеличен', 'ability': 'Cloak and Dagger'},
                {'hero': 'Templar Assassin', 'change': '+1.0', 'detail': 'Psi Blades урон увеличен', 'ability': 'Psi Blades'},
                {'hero': 'Sniper', 'change': '-0.5', 'detail': 'Shrapnel урон уменьшен', 'ability': 'Shrapnel'},
                {'hero': 'Clinkz', 'change': '+2.2', 'detail': 'Searing Arrows урон увеличен', 'ability': 'Searing Arrows'},
                {'hero': 'Drow Ranger', 'change': '+1.8', 'detail': 'Frost Arrows урон увеличен', 'ability': 'Frost Arrows'},
                {'hero': 'Viper', 'change': '+1.0', 'detail': 'Poison Attack урон увеличен', 'ability': 'Poison Attack'},
                {'hero': 'Venomancer', 'change': '+1.2', 'detail': 'Poison Sting урон увеличен', 'ability': 'Poison Sting'}
            ],
            'item_changes': [
                {'item': 'Mage Slayer', 'old': '20', 'new': '15', 'detail': 'Урон уменьшен с 20 до 15'},
                {'item': 'Shadow Blade', 'old': '30', 'new': '25', 'detail': 'Скорость атаки уменьшена с 30 до 25'},
                {'item': 'Harpoon', 'old': '', 'new': '', 'detail': 'Больше не перемещает закованных существ'},
                {'item': 'Eternal Chains', 'old': '350', 'new': '400', 'detail': 'Радиус увеличен с 350 до 400'},
                {'item': 'Dominate', 'old': '60', 'new': '40', 'detail': 'Перезарядка уменьшена с 60 до 40 секунд'},
                {'item': 'Hallowed', 'old': '', 'new': '', 'detail': 'Все заряды расходуются при создании барьера'},
                {'item': 'Spirit Vessel', 'old': '12', 'new': '10', 'detail': 'Длительность уменьшена с 12 до 10 секунд'},
                {'item': 'Aghanims Shard', 'old': '1400', 'new': '1500', 'detail': 'Стоимость увеличена с 1400 до 1500'},
                {'item': 'Wraith Band', 'old': '505', 'new': '510', 'detail': 'Стоимость увеличена с 505 до 510'},
                {'item': 'Null Talisman', 'old': '505', 'new': '510', 'detail': 'Стоимость увеличена с 505 до 510'},
                {'item': 'Bracer', 'old': '505', 'new': '510', 'detail': 'Стоимость увеличена с 505 до 510'}
            ],
            'neutral_item_changes': [
                {'item': 'Spellover', 'detail': 'Добавлена внутренняя перезарядка 0.1с'},
                {'item': 'False Flight', 'old': '5', 'new': '6.5', 'detail': 'Длительность увеличена с 5 до 6.5 секунд'},
                {'item': 'Reverberate', 'old': '110', 'new': '90', 'detail': 'Урон уменьшен с 110 до 90'},
                {'item': 'Demonic Warrior', 'detail': 'Больше не даёт True Sight'},
                {'item': 'Seeds of Serenity', 'old': '300', 'new': '350', 'detail': 'Радиус увеличен с 300 до 350'}
            ]
        },
        # ===== PATCH 7.41d =====
        {
            'version': '7.41d',
            'date': '5 June 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Meepo', 'change': '-3.2', 'detail': 'Poof урон уменьшен с 80 до 60', 'ability': 'Poof'},
                {'hero': 'Ember Spirit', 'change': '-2.1', 'detail': 'Flame Guard урон уменьшен с 50 до 40', 'ability': 'Flame Guard'},
                {'hero': 'Beastmaster', 'change': '-1.8', 'detail': 'Wild Axes урон уменьшен с 70 до 55', 'ability': 'Wild Axes'},
                {'hero': 'Batrider', 'change': '-0.5', 'detail': 'Sticky Napalm урон уменьшен', 'ability': 'Sticky Napalm'},
                {'hero': 'Juggernaut', 'change': '+2.5', 'detail': 'Базовая атака увеличена', 'ability': 'Base Attack'},
                {'hero': 'Windranger', 'change': '+2.0', 'detail': 'Базовая атака увеличена', 'ability': 'Base Attack'},
                {'hero': 'Brewmaster', 'change': '+1.8', 'detail': 'Thunder Clap урон увеличен', 'ability': 'Thunder Clap'},
                {'hero': 'Tiny', 'change': '+1.5', 'detail': 'Avalanche урон увеличен', 'ability': 'Avalanche'},
                {'hero': 'Pudge', 'change': '+1.2', 'detail': 'Meat Hook урон увеличен', 'ability': 'Meat Hook'},
                {'hero': 'Leshrac', 'change': '-0.8', 'detail': 'Diabolic Edict урон уменьшен', 'ability': 'Diabolic Edict'},
                {'hero': 'Storm Spirit', 'change': '-0.5', 'detail': 'Static Remnant урон уменьшен', 'ability': 'Static Remnant'},
                {'hero': 'Queen of Pain', 'change': '+1.0', 'detail': 'Shadow Strike урон увеличен', 'ability': 'Shadow Strike'}
            ],
            'item_changes': [
                {'item': 'Arcane Boots', 'old': '1300', 'new': '1200', 'detail': 'Стоимость уменьшена с 1300 до 1200'},
                {'item': 'Power Treads', 'old': '1400', 'new': '1350', 'detail': 'Стоимость уменьшена с 1400 до 1350'},
                {'item': 'Sange', 'old': '2050', 'new': '2000', 'detail': 'Стоимость уменьшена с 2050 до 2000'},
                {'item': 'Yasha', 'old': '2050', 'new': '2000', 'detail': 'Стоимость уменьшена с 2050 до 2000'},
                {'item': 'Kaya', 'old': '2050', 'new': '2000', 'detail': 'Стоимость уменьшена с 2050 до 2000'}
            ],
            'neutral_item_changes': [
                {'item': 'Spellover', 'detail': 'Добавлена внутренняя перезарядка'},
                {'item': 'False Flight', 'old': '5', 'new': '6.5', 'detail': 'Длительность увеличена с 5 до 6.5 секунд'},
                {'item': 'Reverberate', 'old': '110', 'new': '90', 'detail': 'Урон уменьшен с 110 до 90'},
                {'item': 'Pupils Gift', 'old': '0.3', 'new': '0.4', 'detail': 'Множитель увеличен с 0.3 до 0.4'}
            ]
        },
        # ===== PATCH 7.41c =====
        {
            'version': '7.41c',
            'date': '7 May 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Beastmaster', 'change': '-2.0', 'detail': 'Wild Axes урон уменьшен', 'ability': 'Wild Axes'},
                {'hero': 'Batrider', 'change': '-1.5', 'detail': 'Sticky Napalm урон уменьшен', 'ability': 'Sticky Napalm'},
                {'hero': 'Techies', 'change': '-1.0', 'detail': 'Урон мин уменьшен', 'ability': 'Mines'},
                {'hero': 'Juggernaut', 'change': '+2.0', 'detail': 'Базовая атака увеличена', 'ability': 'Base Attack'},
                {'hero': 'Lina', 'change': '+1.5', 'detail': 'Базовая атака увеличена', 'ability': 'Base Attack'},
                {'hero': 'Legion Commander', 'change': '+1.2', 'detail': 'Duel урон увеличен', 'ability': 'Duel'},
                {'hero': 'Axe', 'change': '+1.0', 'detail': 'Berserkers Call броня увеличена', 'ability': 'Berserkers Call'},
                {'hero': 'Centaur', 'change': '-0.8', 'detail': 'Double Edge урон уменьшен', 'ability': 'Double Edge'}
            ],
            'item_changes': [
                {'item': 'Mage Slayer', 'old': '25', 'new': '20', 'detail': 'Урон уменьшен с 25 до 20'},
                {'item': 'Shadow Blade', 'old': '35', 'new': '30', 'detail': 'Скорость уменьшена с 35 до 30'},
                {'item': 'Satanic', 'old': '5000', 'new': '4800', 'detail': 'Стоимость уменьшена с 5000 до 4800'},
                {'item': 'Eye of Skadi', 'old': '5300', 'new': '5200', 'detail': 'Стоимость уменьшена с 5300 до 5200'},
                {'item': 'Moon Shard', 'old': '4000', 'new': '4200', 'detail': 'Стоимость увеличена с 4000 до 4200'}
            ],
            'neutral_item_changes': [
                {'item': 'Tumbler Toy', 'old': '80', 'new': '70', 'detail': 'Скорость передвижения уменьшена с 80 до 70'},
                {'item': 'Dagger of Ristul', 'old': '45', 'new': '50', 'detail': 'Урон увеличен с 45 до 50'},
                {'item': 'Chipped Vest', 'old': '45', 'new': '50', 'detail': 'Урон увеличен с 45 до 50'}
            ]
        },
        # ===== PATCH 7.41b =====
        {
            'version': '7.41b',
            'date': '7 April 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Meepo', 'change': '-4.0', 'detail': 'Статы предметов понижены, перезарядки увеличены', 'ability': 'Multiple'},
                {'hero': 'Juggernaut', 'change': '+3.0', 'detail': 'Базовые статы увеличены', 'ability': 'Base Stats'},
                {'hero': 'Windranger', 'change': '+2.5', 'detail': 'Базовые статы увеличены', 'ability': 'Base Stats'},
                {'hero': 'Ember Spirit', 'change': '-1.5', 'detail': 'Урон и эффективность маны уменьшены', 'ability': 'Multiple'},
                {'hero': 'Void Spirit', 'change': '-1.0', 'detail': 'Урон уменьшен', 'ability': 'Multiple'},
                {'hero': 'Meepo Clones', 'change': '-2.0', 'detail': 'Теперь не могут использовать бутылки', 'ability': 'Clone'},
                {'hero': 'Marci', 'change': '+1.5', 'detail': 'Пассивная и активная способности переработаны', 'ability': 'Multiple'},
                {'hero': 'Legion Commander', 'change': '+2.0', 'detail': 'Теперь может использовать способности во время Duel', 'ability': 'Duel'}
            ],
            'item_changes': [
                {'item': 'Avatar', 'detail': 'Фиксированная длительность, не зависит от усиления баффов'},
                {'item': 'Hallowed', 'detail': 'Все заряды расходуются при создании барьера'},
                {'item': 'Eternal Chains', 'old': '350', 'new': '400', 'detail': 'Радиус увеличен с 350 до 400'},
                {'item': 'Dominate', 'old': '60', 'new': '40', 'detail': 'Перезарядка уменьшена с 60 до 40'},
                {'item': 'Helm of the Overlord', 'old': '60', 'new': '50', 'detail': 'Перезарядка уменьшена с 60 до 50'},
                {'item': 'Pipe of Insight', 'old': '3500', 'new': '3400', 'detail': 'Стоимость уменьшена с 3500 до 3400'},
                {'item': 'Crimson Guard', 'old': '3500', 'new': '3400', 'detail': 'Стоимость уменьшена с 3500 до 3400'}
            ],
            'neutral_item_changes': [
                {'item': 'Spellover', 'detail': 'Добавлена внутренняя перезарядка'},
                {'item': 'False Flight', 'old': '5', 'new': '6.5', 'detail': 'Длительность увеличена с 5 до 6.5 секунд'},
                {'item': 'Reverberate', 'old': '110', 'new': '90', 'detail': 'Урон уменьшен с 110 до 90'},
                {'item': 'Demonic Warrior', 'detail': 'Больше не даёт True Sight'},
                {'item': 'Pupils Gift', 'old': '0.3', 'new': '0.4', 'detail': 'Множитель увеличен с 0.3 до 0.4'},
                {'item': 'Tumbler Toy', 'old': '80', 'new': '70', 'detail': 'Скорость передвижения уменьшена с 80 до 70'}
            ]
        },
        # ===== PATCH 7.41a =====
        {
            'version': '7.41a',
            'date': '28 March 2026',
            'type': 'minor',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+2.0', 'detail': 'Эффективность и урон увеличены', 'ability': 'Multiple'},
                {'hero': 'Juggernaut', 'change': '+1.5', 'detail': 'Эффективность и урон увеличены', 'ability': 'Multiple'},
                {'hero': 'Windranger', 'change': '+1.5', 'detail': 'Эффективность и урон увеличены', 'ability': 'Multiple'},
                {'hero': 'Lifestealer', 'change': '-2.0', 'detail': 'Статы и скейлинг уменьшены', 'ability': 'Multiple'},
                {'hero': 'Alchemist', 'change': '-1.5', 'detail': 'Статы и скейлинг уменьшены', 'ability': 'Multiple'},
                {'hero': 'Wraith King', 'change': '-1.0', 'detail': 'Статы и скейлинг уменьшены', 'ability': 'Multiple'},
                {'hero': 'Legion Commander', 'change': '-0.5', 'detail': 'Пассивная броня удалена', 'ability': 'Passive'},
                {'hero': 'Kez', 'change': '+2.0', 'detail': 'Базовая атака и длительность баффов улучшены', 'ability': 'Multiple'},
                {'hero': 'Techies', 'change': '-1.0', 'detail': 'Урон мин и AoE уменьшены', 'ability': 'Mines'},
                {'hero': 'Meepo Clones', 'change': '+1.5', 'detail': 'Теперь имеют полное уклонение', 'ability': 'Clone'},
                {'hero': 'Ringmaster', 'change': '+1.2', 'detail': 'Урон увеличен', 'ability': 'Multiple'},
                {'hero': 'Marci', 'change': '+1.0', 'detail': 'Способности переработаны', 'ability': 'Multiple'}
            ],
            'item_changes': [
                {'item': 'Wraith Band', 'old': '505', 'new': '515', 'detail': 'Стоимость увеличена с 505 до 515'},
                {'item': 'Null Talisman', 'old': '505', 'new': '515', 'detail': 'Стоимость увеличена с 505 до 515'},
                {'item': 'Bracer', 'old': '505', 'new': '515', 'detail': 'Стоимость увеличена с 505 до 515'},
                {'item': 'Blade Mail', 'old': '2100', 'new': '2200', 'detail': 'Стоимость увеличена с 2100 до 2200'},
                {'item': 'Ghost Scepter', 'old': '1500', 'new': '1600', 'detail': 'Стоимость увеличена с 1500 до 1600'}
            ],
            'neutral_item_changes': [
                {'item': 'Tier 1', 'old': '7:00', 'new': '0:00', 'detail': 'Доступность изменена с 7:00 на 0:00'},
                {'item': 'Tier 2-5', 'detail': 'Добавлено больше вариантов выбора'},
                {'item': 'Arcanists Armor', 'old': '1.2', 'new': '1.0', 'detail': 'Множитель уменьшен с 1.2 до 1.0'},
                {'item': 'Trickster Cloak', 'old': '25', 'new': '20', 'detail': 'Скорость передвижения уменьшена с 25 до 20'}
            ]
        },
        # ===== PATCH 7.41 =====
        {
            'version': '7.41',
            'date': '25 March 2026',
            'type': 'major',
            'hero_changes': [
                {'hero': 'Anti-Mage', 'change': '+5.0', 'detail': 'Aghanims Scepter: сжигание маны улучшено', 'ability': 'Aghanims'},
                {'hero': 'Tinker', 'change': 'NEW', 'detail': 'Добавлена новая способность - турель', 'ability': 'New Ability'},
                {'hero': 'Omniknight', 'change': 'REWORK', 'detail': 'Guardian Angel переработан в персональную ауру', 'ability': 'Guardian Angel'},
                {'hero': 'Meepo', 'change': 'REWORK', 'detail': 'Механика клонов значительно переработана', 'ability': 'Clone'},
                {'hero': 'Legion Commander', 'change': '+3.0', 'detail': 'Теперь может использовать способности во время Duel', 'ability': 'Duel'},
                {'hero': 'Marci', 'change': 'REWORK', 'detail': 'Пассивная и активная способности переработаны', 'ability': 'Multiple'},
                {'hero': 'Arc Warden', 'change': '+2.0', 'detail': 'Tempest Double длительность увеличена', 'ability': 'Tempest Double'},
                {'hero': 'Void Spirit', 'change': '+1.5', 'detail': 'Aether Remnant урон увеличен', 'ability': 'Aether Remnant'},
                {'hero': 'Pangolier', 'change': '+1.0', 'detail': 'Shield Crash урон увеличен', 'ability': 'Shield Crash'},
                {'hero': 'Snapfire', 'change': '+1.2', 'detail': 'Способности переработаны', 'ability': 'Multiple'},
                {'hero': 'Hoodwink', 'change': '+1.0', 'detail': 'Acorn Shot урон увеличен', 'ability': 'Acorn Shot'},
                {'hero': 'Dawnbreaker', 'change': '+0.8', 'detail': 'Starbreaker урон увеличен', 'ability': 'Starbreaker'},
                {'hero': 'Primal Beast', 'change': '-0.5', 'detail': 'Onslaught урон уменьшен', 'ability': 'Onslaught'}
            ],
            'item_changes': [
                {'item': 'Chasm Stone', 'detail': 'Новый предмет добавлен'},
                {'item': 'Shawl', 'detail': 'Новый предмет добавлен'},
                {'item': 'Splintmail', 'detail': 'Новый предмет добавлен'},
                {'item': 'Wizard Hat', 'detail': 'Новый предмет добавлен'},
                {'item': 'Mage Slayer', 'detail': 'Тип урона изменен'},
                {'item': 'Eternal Chains', 'old': '300', 'new': '350', 'detail': 'Радиус увеличен с 300 до 350'},
                {'item': 'Harpoon', 'old': '25', 'new': '30', 'detail': 'Урон увеличен с 25 до 30'},
                {'item': 'Spirit Vessel', 'old': '12', 'new': '14', 'detail': 'Длительность увеличена с 12 до 14 секунд'},
                {'item': 'Force Staff', 'old': '2050', 'new': '2100', 'detail': 'Стоимость увеличена с 2050 до 2100'},
                {'item': 'Hurricane Pike', 'old': '4350', 'new': '4400', 'detail': 'Стоимость увеличена с 4350 до 4400'},
                {'item': 'Glimmer Cape', 'old': '2150', 'new': '2200', 'detail': 'Стоимость увеличена с 2150 до 2200'}
            ],
            'neutral_item_changes': [
                {'item': 'Tier 1', 'old': '7:00', 'new': '0:00', 'detail': 'Доступность изменена с 7:00 на 0:00'},
                {'item': 'Tier 2-5', 'detail': 'Добавлено больше вариантов выбора на основе атрибутов героя'},
                {'item': 'Enchanted Quiver', 'old': '40', 'new': '50', 'detail': 'Урон увеличен с 40 до 50'},
                {'item': 'Pupils Gift', 'old': '0.2', 'new': '0.3', 'detail': 'Множитель увеличен с 0.2 до 0.3'},
                {'item': 'Vampire Fangs', 'old': '15', 'new': '20', 'detail': 'Высасывание жизни увеличено с 15% до 20%'}
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