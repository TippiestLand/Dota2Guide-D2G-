from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import hashlib
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ============================================================
# 1. НАСТРОЙКА ПРИЛОЖЕНИЯ
# ============================================================
app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

# ============================================================
# 2. КОНФИГУРАЦИЯ
# ============================================================
NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'

# Создаём папку data, если её нет
os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)

# Создаём файл news.json, если его нет
if not os.path.exists(NEWS_FILE):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

# ============================================================
# 3. РАЗДАЧА СТАТИЧЕСКИХ ФАЙЛОВ
# ============================================================
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# ============================================================
# 4. РАБОТА С ФАЙЛОМ NEWS.JSON
# ============================================================
def load_news():
    """
    Загружает все новости из файла news.json.
    Если файл повреждён или его нет, возвращает пустой список.
    """
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки news.json: {e}")
        return []

def save_news(news):
    """
    Сохраняет список новостей в файл news.json.
    """
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)

# ============================================================
# 5. ПОЛУЧЕНИЕ НОВОСТЕЙ ИЗ RSS
# ============================================================
def fetch_rss_news():
    """
    Парсит RSS-ленту Steam и возвращает список новостей.
    Если что-то идёт не так, возвращает пустой список.
    """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"RSS ответил с кодом {response.status_code}")
            return []
        
        root = ET.fromstring(response.content)
        news_items = []
        
        # Проходим по всем элементам <item> в RSS
        for item in root.findall('.//item')[:15]:
            # Название
            title_element = item.find('title')
            title_text = title_element.text if title_element is not None else 'Без названия'
            
            # Дата публикации
            pub_date_element = item.find('pubDate')
            date_text = pub_date_element.text if pub_date_element is not None else datetime.now().strftime('%d %B %Y')
            
            # Ссылка
            link_element = item.find('link')
            link_text = link_element.text if link_element is not None else ''
            
            # Описание
            description_element = item.find('description')
            if description_element is not None and description_element.text:
                desc_text = description_element.text
            else:
                desc_text = title_text
            
            # Очищаем описание от HTML-тегов
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            desc_clean = desc_clean[:500] + '...' if len(desc_clean) > 500 else desc_clean
            
            # Пробуем преобразовать дату
            try:
                date_obj = datetime.strptime(pub_date_element.text, '%a, %d %b %Y %H:%M:%S %Z')
                date_formatted = date_obj.strftime('%d %B %Y')
            except:
                date_formatted = date_text
            
            # Генерируем уникальный ID на основе заголовка
            hash_id = int(hashlib.md5(title_text.encode('utf-8')).hexdigest()[:8], 16)
            
            # Создаём объект новости
            news_item = {
                'id': hash_id,
                'title': title_text,
                'date': date_formatted,
                'type': 'update',
                'preview': desc_clean,
                'content': desc_clean,
                'link': link_text,
                'author': 'Valve',
                'timestamp': int(datetime.now().timestamp() * 1000),
                'source': 'rss',
                'rss_title': title_text
            }
            news_items.append(news_item)
        
        return news_items
    except Exception as e:
        print(f"Ошибка при получении RSS: {e}")
        return []

# ============================================================
# 6. ОБНОВЛЕНИЕ НОВОСТЕЙ ИЗ RSS
# ============================================================
def update_news_from_rss():
    """
    Загружает свежие новости из RSS и добавляет только те,
    которых ещё нет в базе (сравниваем по заголовку).
    Возвращает количество добавленных новостей.
    """
    existing_news = load_news()
    rss_news = fetch_rss_news()
    
    if not rss_news:
        print("⚠️ RSS не загрузился, новости не добавлены")
        return 0
    
    # Собираем заголовки существующих RSS-новостей
    existing_titles = set()
    for news in existing_news:
        if news.get('source') == 'rss':
            existing_titles.add(news.get('title'))
    
    # Отбираем только новые новости
    new_items = []
    for item in rss_news:
        if item['title'] not in existing_titles:
            new_items.append(item)
    
    if not new_items:
        print(f"📰 Новых новостей нет (все {len(rss_news)} уже есть в базе)")
        return 0
    
    # Добавляем новые новости сверху (перед старыми)
    updated_news = new_items + existing_news
    save_news(updated_news)
    
    print(f"✅ Добавлено {len(new_items)} новых новостей:")
    for item in new_items:
        print(f"   📌 {item['title']}")
    
    return len(new_items)

# ============================================================
# 7. ГЛАВНАЯ СТРАНИЦА
# ============================================================
@app.route('/')
def index():
    """Отдаёт главную HTML-страницу."""
    return render_template('index.html')

# ============================================================
# 8. API: ПОЛУЧЕНИЕ НОВОСТЕЙ
# ============================================================
@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Возвращает все новости в формате JSON.
    Используется на фронтенде для отображения новостей.
    """
    news = load_news()
    return jsonify(news)

# ============================================================
# 9. ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 ЗАПУСК DOTA 2 GUIDE")
    print("=" * 60)
    
    # Пытаемся загрузить новости из RSS при старте
    added_count = 0
    try:
        added_count = update_news_from_rss()
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке RSS: {e}")
    
    # Если RSS не сработал и новостей нет — добавляем тестовую новость
    if added_count == 0:
        existing_news = load_news()
        if len(existing_news) == 0:
            print("📝 RSS не загрузился. Добавляем тестовую новость...")
            test_news = {
                'id': int(datetime.now().timestamp() * 1000),
                'title': 'Добро пожаловать в Dota 2 Guide!',
                'date': datetime.now().strftime('%d %B %Y'),
                'type': 'update',
                'preview': 'Новости Dota 2 будут загружаться автоматически из официального RSS-канала Steam. Если вы видите это сообщение, значит сайт работает корректно.',
                'content': 'Новости Dota 2 будут загружаться автоматически из официального RSS-канала Steam. Если вы видите это сообщение, значит сайт работает корректно. Новости появятся здесь в ближайшее время после того, как RSS-лента станет доступна.',
                'link': 'https://store.steampowered.com/news/app/570',
                'author': 'Dota 2 Guide',
                'timestamp': int(datetime.now().timestamp() * 1000),
                'source': 'manual'
            }
            save_news([test_news])
            print("✅ Тестовая новость добавлена!")
        else:
            print(f"📰 В базе уже есть {len(existing_news)} новостей")
    
    print("=" * 60)
    print("🌐 Сервер запускается...")
    print("=" * 60)
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)