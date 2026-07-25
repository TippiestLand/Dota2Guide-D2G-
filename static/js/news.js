(function() {
    'use strict';

    const API_URL = '/api/news';

    async function fetchNews() {
        const newsFeed = document.getElementById('newsFeed');
        if (!newsFeed) return;

        newsFeed.innerHTML = `<div class="news-loading"><div class="loader"></div><p>Загрузка новостей...</p></div>`;

        try {
            const response = await fetch(API_URL + '?t=' + Date.now());
            if (!response.ok) throw new Error('Ошибка загрузки');
            const data = await response.json();

            if (data && data.length > 0) {
                renderNews(data);
            } else {
                newsFeed.innerHTML = `<div class="news-empty"><p>Новостей пока нет</p></div>`;
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
            <div class="news-card-vk">
                <div class="news-card-header">
                    <div class="news-avatar" style="background: ${getTypeColor(news.type)}20; color: ${getTypeColor(news.type)}">${getTypeIcon(news.type)}</div>
                    <div class="news-meta">
                        <div class="news-author">${escapeHtml(news.author || 'Valve')}</div>
                        <div class="news-date">${escapeHtml(news.date)}</div>
                    </div>
                    <div class="news-type-badge" style="background: ${getTypeColor(news.type)}20; color: ${getTypeColor(news.type)}">${getTypeLabel(news.type)}</div>
                </div>
                <div class="news-card-body">
                    <h3 class="news-title">${escapeHtml(news.title)}</h3>
                    <p class="news-preview">${escapeHtml(news.preview || news.content)}</p>
                </div>
                <div class="news-card-footer">
                    <a href="${escapeHtml(news.link || '#')}" target="_blank" class="news-read-more">Читать полностью →</a>
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