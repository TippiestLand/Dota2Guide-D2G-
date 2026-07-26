(function() {
    'use strict';

    const API_URL = '/api/news';

    async function fetchNews() {
        const newsFeed = document.getElementById('newsFeed');
        if (!newsFeed) return;

        newsFeed.innerHTML = `
            <div class="news-loading">
                <div class="loader"></div>
                <p>Загрузка новостей...</p>
            </div>
        `;

        try {
            const response = await fetch(API_URL + '?t=' + Date.now());
            if (!response.ok) throw new Error('Ошибка загрузки');
            const data = await response.json();

            if (data && data.length > 0) {
                renderNews(data);
            } else {
                newsFeed.innerHTML = `
                    <div class="news-empty">
                        <p>Новостей пока нет</p>
                        <p style="font-size:0.8rem; color:#666; margin-top:8px;">Новости появятся здесь автоматически</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Ошибка загрузки новостей:', error);
            newsFeed.innerHTML = `
                <div class="news-empty">
                    <p>Не удалось загрузить новости</p>
                    <button onclick="location.reload()" class="btn btn-secondary" style="margin-top:15px; padding:8px 24px; font-size:0.8rem;">Обновить</button>
                </div>
            `;
        }
    }

    function renderNews(newsItems) {
        const newsFeed = document.getElementById('newsFeed');
        if (!newsFeed) return;

        const sorted = [...newsItems].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));

        newsFeed.innerHTML = sorted.map(news => `
            <div class="news-card-vk ${news.source === 'rss' ? 'news-rss' : 'news-manual'}">
                <div class="news-card-header">
                    <div class="news-avatar" style="background: ${getTypeColor(news.type)}20; color: ${getTypeColor(news.type)}">
                        ${getTypeIcon(news.type)}
                    </div>
                    <div class="news-meta">
                        <div class="news-author">
                            ${escapeHtml(news.author || 'Valve')}
                            ${news.source === 'rss' 
                                ? '<span style="font-size:0.6rem; background:rgba(78,205,196,0.15); color:#4ecdc4; padding:2px 10px; border-radius:12px; margin-left:8px;">📡</span>' 
                                : '<span style="font-size:0.6rem; background:rgba(240,185,11,0.15); color:#f0b90b; padding:2px 10px; border-radius:12px; margin-left:8px;">✏️</span>'
                            }
                        </div>
                        <div class="news-date">${escapeHtml(news.date)}</div>
                    </div>
                    <div class="news-type-badge" style="background: ${getTypeColor(news.type)}20; color: ${getTypeColor(news.type)}">
                        ${getTypeLabel(news.type)}
                    </div>
                </div>
                <div class="news-card-body">
                    <h3 class="news-title">${escapeHtml(news.title)}</h3>
                    <div class="news-content">
                        <p class="news-preview">${escapeHtml(news.preview || news.content)}</p>
                    </div>
                </div>
                <div class="news-card-footer">
                    ${news.link ? `<a href="${escapeHtml(news.link)}" target="_blank" class="news-read-more">Читать на Steam →</a>` : ''}
                </div>
            </div>
        `).join('');
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getTypeIcon(type) {
        const icons = { 'update': '⚙️', 'event': '🎪', 'tournament': '🏆', 'hero': '🦸', 'feature': '✨' };
        return icons[type] || '📰';
    }

    function getTypeColor(type) {
        const colors = { 'update': '#f0b90b', 'event': '#ff6b6b', 'tournament': '#4ecdc4', 'hero': '#a29bfe', 'feature': '#fd79a8' };
        return colors[type] || '#888';
    }

    function getTypeLabel(type) {
        const labels = { 'update': 'Обновление', 'event': 'Событие', 'tournament': 'Турнир', 'hero': 'Новый герой', 'feature': 'Новинка' };
        return labels[type] || 'Новость';
    }

    window.fetchNews = fetchNews;

    document.addEventListener('DOMContentLoaded', function() {
        const checkInterval = setInterval(() => {
            const newsFeed = document.getElementById('newsFeed');
            if (newsFeed) {
                clearInterval(checkInterval);
                fetchNews();
            }
        }, 100);
        if (document.getElementById('newsFeed')) fetchNews();
    });
})();