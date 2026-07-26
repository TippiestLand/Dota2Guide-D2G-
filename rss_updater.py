#!/usr/bin/env python3
"""
Скрипт для автоматического обновления новостей из RSS.
Запускается через cron на Render каждые 5 минут.
"""

import os
import json
import re
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ============================================================
# 1. КОНФИГУРАЦИЯ
# ============================================================
NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'

# ============================================================
# 2. РАБОТА С ФАЙЛОМ
# ============================================================
def load_news():
    """Загружает новости из файла."""
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        return []

def save_news(news):
    """Сохраняет новости в файл."""
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)

# ============================================================
# 3. ПОЛУЧЕНИЕ RSS
# ============================================================
def fetch_rss_news():
    """Парсит RSS и возвращает список новостей."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"RSS ответил с кодом {response.status_code}")
            return []
        
        root = ET.fromstring(response.content)
        news_items = []
        
        for item in root.findall('.//item')[:15]:
            # Название
            title_element = item.find('title')
            title_text = title_element.text if title_element is not None else 'Без названия'
            
            # Дата
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
            
            # Очистка от HTML
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            desc_clean = desc_clean[:500] + '...' if len(desc_clean) > 500 else desc_clean
            
            # Преобразование даты
            try:
                date_obj = datetime.strptime(pub_date_element.text, '%a, %d %b %Y %H:%M:%S %Z')
                date_formatted = date_obj.strftime('%d %B %Y')
            except:
                date_formatted = date_text
            
            # Уникальный ID на основе заголовка
            hash_id = int(hashlib.md5(title_text.encode('utf-8')).hexdigest()[:8], 16)
            
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
        print(f"Ошибка получения RSS: {e}")
        return []

# ============================================================
# 4. ОБНОВЛЕНИЕ
# ============================================================
def update_news_from_rss():
    """Добавляет новые RSS-новости в базу."""
    existing_news = load_news()
    rss_news = fetch_rss_news()
    
    if not rss_news:
        print("⚠️ RSS не загрузился")
        return 0
    
    # Собираем заголовки существующих RSS-новостей
    existing_titles = set()
    for news in existing_news:
        if news.get('source') == 'rss':
            existing_titles.add(news.get('title'))
    
    # Отбираем новые
    new_items = []
    for item in rss_news:
        if item['title'] not in existing_titles:
            new_items.append(item)
    
    if not new_items:
        print(f"📰 Новых новостей нет (все {len(rss_news)} уже есть)")
        return 0
    
    # Добавляем новые сверху
    updated_news = new_items + existing_news
    save_news(updated_news)
    
    print(f"✅ Добавлено {len(new_items)} новостей:")
    for item in new_items:
        print(f"   📌 {item['title']}")
    
    return len(new_items)

# ============================================================
# 5. ЗАПУСК
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("📡 RSS UPDATER ЗАПУЩЕН")
    print("=" * 60)
    
    count = update_news_from_rss()
    
    print("=" * 60)
    print(f"✅ Готово! Добавлено {count} новостей")
    print("=" * 60)