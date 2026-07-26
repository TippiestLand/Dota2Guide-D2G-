from flask import Flask, render_template, jsonify, send_from_directory
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

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

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
    """Форматирует текст новости как в Steam — с точками в начале строк"""
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            if line.startswith('- '):
                formatted_lines.append('• ' + line[2:])
            elif line.startswith('* '):
                formatted_lines.append('• ' + line[2:])
            elif line.startswith('— '):
                formatted_lines.append('• ' + line[2:])
            elif line.startswith('• '):
                formatted_lines.append(line)
            elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.'):
                formatted_lines.append(line)
            elif line.startswith('Fixed'):
                formatted_lines.append('• Исправлено: ' + line[6:])
            elif line.startswith('Fixed '):
                formatted_lines.append('• Исправлено: ' + line[6:])
            else:
                formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

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
            
            # Переводим заголовок
            title_text = translate_title(title_text)

            pub_date_element = item.find('pubDate')
            
            # Конвертируем дату в МСК
            try:
                date_obj = datetime.strptime(pub_date_element.text, '%a, %d %b %Y %H:%M:%S %Z')
                date_obj_msk = date_obj.astimezone(MSK)
                date_formatted = date_obj_msk.strftime('%d %B %Y, %H:%M МСК')
            except:
                date_formatted = datetime.now(MSK).strftime('%d %B %Y, %H:%M МСК')

            link_element = item.find('link')
            link_text = link_element.text if link_element is not None else ''

            description_element = item.find('description')
            if description_element is not None and description_element.text:
                desc_text = description_element.text
            else:
                desc_text = title_text

            # Очищаем HTML
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            # Форматируем как в Steam (с точками)
            desc_clean = format_news_content(desc_clean)

            hash_id = int(hashlib.md5(title_text.encode('utf-8')).hexdigest()[:8], 16)

            news_items.append({
                'id': hash_id,
                'title': title_text,
                'date': date_formatted,
                'content': desc_clean,
                'link': link_text,
                'timestamp': int(datetime.now().timestamp() * 1000),
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(load_news())

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
            'content': 'Новости Dota 2 будут загружаться автоматически из официального RSS-канала Steam.\n• Все новости будут переведены на русский язык\n• Дата и время — по Московскому времени\n• Форматирование — как в официальных новостях Steam',
            'link': 'https://store.steampowered.com/news/app/570',
            'timestamp': int(datetime.now().timestamp() * 1000),
            'source': 'manual'
        }
    ]

    save_news(test_news)
    print(f"✅ Добавлена тестовая новость")
    print("=" * 60)

initialize_news()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)