from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
CORS(app)

NEWS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'news.json')
RSS_URL = 'https://store.steampowered.com/feeds/news/app/570/?l=russian'

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
    except:
        return []

def save_news(news):
    with open(NEWS_FILE, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=4)

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
                'source': 'rss'
            })
        
        return news_items
    except Exception as e:
        print(f"RSS error: {e}")
        return []

def update_news_from_rss():
    existing = load_news()
    rss_news = fetch_rss_news()
    if not rss_news:
        return 0
    
    existing_rss_titles = {n.get('title') for n in existing if n.get('source') == 'rss'}
    new_items = [n for n in rss_news if n['title'] not in existing_rss_titles]
    manual_news = [n for n in existing if n.get('source') != 'rss']
    updated_news = new_items + manual_news
    updated_news.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    save_news(updated_news)
    return len(new_items)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify(load_news())

if __name__ == '__main__':
    try:
        count = update_news_from_rss()
        print(f"📰 Загружено {count} новых RSS новостей")
    except:
        print("⚠️ RSS не загрузился")
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)