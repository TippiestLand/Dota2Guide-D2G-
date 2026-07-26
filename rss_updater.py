import requests
import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime
import re

RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'
NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')

def fetch_rss_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(RSS_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return []
        
        root = ET.fromstring(response.content)
        news_items = []
        
        for item in root.findall('.//item')[:15]:
            title = item.find('title')
            title_text = title.text if title is not None else 'Без названия'
            
            pub_date = item.find('pubDate')
            date_text = pub_date.text if pub_date is not None else datetime.now().strftime('%d %B %Y')
            
            link = item.find('link')
            link_text = link.text if link is not None else ''
            
            description = item.find('description')
            desc_text = description.text if description is not None else title_text
            desc_clean = re.sub(r'<[^>]+>', '', desc_text)
            desc_clean = desc_clean[:500] + '...' if len(desc_clean) > 500 else desc_clean
            
            try:
                date_obj = datetime.strptime(pub_date.text, '%a, %d %b %Y %H:%M:%S %Z')
                date_formatted = date_obj.strftime('%d %B %Y')
            except:
                date_formatted = date_text
            
            news_items.append({
                'id': int(datetime.now().timestamp() * 1000) + len(news_items),
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
            })
        
        return news_items
    except Exception as e:
        print(f"RSS error: {e}")
        return []

def update_news():
    os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)
    
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    except:
        existing = []
    
    rss_news = fetch_rss_news()
    
    if not rss_news:
        print(f"⚠️ [{datetime.now()}] RSS не загрузился")
        return 0
    
    manual_news = [n for n in existing if n.get('source') != 'rss']
    
    rss_titles = {n['rss_title'] for n in rss_news}
    
    existing_rss = [n for n in existing if n.get('source') == 'rss' and n.get('rss_title') in rss_titles]
    
    existing_rss_titles = {n.get('rss_title') for n in existing_rss}
    new_items = [n for n in rss_news if n['rss_title'] not in existing_rss_titles]
    
    updated_news = new_items + existing_rss + manual_news
    
    updated_news.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(updated_news, f, ensure_ascii=False, indent=4)
    
    if new_items:
        print(f"✅ [{datetime.now()}] Добавлено {len(new_items)} новостей")
    else:
        print(f"ℹ️ [{datetime.now()}] Новых новостей нет")
    
    removed = len(existing) - len(updated_news) + len(new_items)
    if removed > 0:
        print(f"🗑️ Удалено {removed} устаревших RSS новостей")
    
    return len(new_items)

if __name__ == '__main__':
    update_news()