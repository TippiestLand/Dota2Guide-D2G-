(function() {
    'use strict';

    var API_URL = '/api/news';
    var newsFeed = document.getElementById('newsFeed');

    function fetchNews() {
        if (!newsFeed) {
            console.warn('Элемент #newsFeed не найден на странице');
            return;
        }

        newsFeed.innerHTML = '' +
            '<div class="news-loading">' +
            '    <div class="loader"></div>' +
            '    <p>Загрузка новостей...</p>' +
            '</div>';

        fetch(API_URL + '?t=' + Date.now())
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Ошибка загрузки: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                if (data && data.length > 0) {
                    renderNews(data);
                } else {
                    newsFeed.innerHTML = '' +
                        '<div class="news-empty">' +
                        '    <p>Новостей пока нет</p>' +
                        '    <p style="font-size:0.8rem; color:#666; margin-top:8px;">' +
                        '        Новости появятся здесь автоматически' +
                        '    </p>' +
                        '</div>';
                }
            })
            .catch(function(error) {
                console.error('Ошибка загрузки новостей:', error);
                newsFeed.innerHTML = '' +
                    '<div class="news-empty">' +
                    '    <p>Не удалось загрузить новости</p>' +
                    '    <button onclick="location.reload()" ' +
                    '            class="btn btn-secondary" ' +
                    '            style="margin-top:15px; padding:8px 24px; font-size:0.8rem;">' +
                    '        Обновить' +
                    '    </button>' +
                    '</div>';
            });
    }

    function renderNews(newsItems) {
        if (!newsFeed) return;

        var sorted = newsItems.slice().sort(function(a, b) {
            return (b.timestamp || 0) - (a.timestamp || 0);
        });

        var html = '';
        for (var i = 0; i < sorted.length; i++) {
            var news = sorted[i];
            var typeColor = getTypeColor(news.type);
            var typeIcon = getTypeIcon(news.type);
            var typeLabel = getTypeLabel(news.type);
            var authorName = escapeHtml(news.author || 'Valve');
            var newsDate = escapeHtml(news.date);
            var newsTitle = escapeHtml(news.title);
            var newsContent = escapeHtml(news.content || news.preview || '');
            var newsLink = news.link ? escapeHtml(news.link) : '';
            var newsId = news.id || i;

            var linkHtml = '';
            if (newsLink) {
                linkHtml = '<a href="' + newsLink + '" target="_blank" class="news-read-more">Читать на Steam →</a>';
            }

            // Определяем, нужно ли показывать кнопку "Развернуть"
            var isLong = newsContent.length > 400;
            var shortContent = isLong ? newsContent.substring(0, 400) + '...' : newsContent;

            html += '<div class="news-card-vk" data-id="' + newsId + '">';
            html += '    <div class="news-card-header">';
            html += '        <div class="news-avatar" style="background: ' + typeColor + '20; color: ' + typeColor + '">';
            html += '            ' + typeIcon;
            html += '        </div>';
            html += '        <div class="news-meta">';
            html += '            <div class="news-author">' + authorName + '</div>';
            html += '            <div class="news-date">' + newsDate + '</div>';
            html += '        </div>';
            html += '        <div class="news-type-badge" style="background: ' + typeColor + '20; color: ' + typeColor + '">';
            html += '            ' + typeLabel;
            html += '        </div>';
            html += '    </div>';
            html += '    <div class="news-card-body">';
            html += '        <h3 class="news-title">' + newsTitle + '</h3>';
            html += '        <div class="news-content">';

            if (isLong) {
                html += '            <p class="news-preview" id="news-text-' + newsId + '">' + shortContent + '</p>';
                html += '            <button class="news-toggle-btn" data-id="' + newsId + '" data-full="' + escapeHtml(newsContent) + '" data-short="' + shortContent + '">';
                html += '                <span class="toggle-icon">▼</span> Развернуть';
                html += '            </button>';
            } else {
                html += '            <p class="news-preview">' + newsContent + '</p>';
            }

            html += '        </div>';
            html += '    </div>';
            html += '    <div class="news-card-footer">';
            html += '        ' + linkHtml;
            html += '    </div>';
            html += '</div>';
        }

        newsFeed.innerHTML = html;

        // ============================================================
        // ОБРАБОТЧИКИ ДЛЯ КНОПОК "РАЗВЕРНУТЬ/СВЕРНУТЬ"
        // ============================================================
        var toggleBtns = document.querySelectorAll('.news-toggle-btn');
        for (var j = 0; j < toggleBtns.length; j++) {
            toggleBtns[j].addEventListener('click', function() {
                var btn = this;
                var id = btn.dataset.id;
                var textEl = document.getElementById('news-text-' + id);
                var icon = btn.querySelector('.toggle-icon');

                if (!textEl) return;

                if (btn.classList.contains('expanded')) {
                    // Сворачиваем
                    textEl.textContent = btn.dataset.short;
                    btn.classList.remove('expanded');
                    icon.textContent = '▼';
                    btn.innerHTML = '<span class="toggle-icon">▼</span> Развернуть';
                } else {
                    // Разворачиваем
                    textEl.textContent = btn.dataset.full;
                    btn.classList.add('expanded');
                    icon.textContent = '▲';
                    btn.innerHTML = '<span class="toggle-icon">▲</span> Свернуть';
                }
            });
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function getTypeIcon(type) {
        var icons = {
            'update': '⚙️',
            'event': '🎪',
            'tournament': '🏆',
            'hero': '🦸',
            'feature': '✨'
        };
        return icons[type] || '📰';
    }

    function getTypeColor(type) {
        var colors = {
            'update': '#f0b90b',
            'event': '#ff6b6b',
            'tournament': '#4ecdc4',
            'hero': '#a29bfe',
            'feature': '#fd79a8'
        };
        return colors[type] || '#888';
    }

    function getTypeLabel(type) {
        var labels = {
            'update': 'Обновление',
            'event': 'Событие',
            'tournament': 'Турнир',
            'hero': 'Новый герой',
            'feature': 'Новинка'
        };
        return labels[type] || 'Новость';
    }

    window.fetchNews = fetchNews;

    document.addEventListener('DOMContentLoaded', function() {
        var checkInterval = setInterval(function() {
            var feed = document.getElementById('newsFeed');
            if (feed) {
                clearInterval(checkInterval);
                fetchNews();
            }
        }, 100);

        if (document.getElementById('newsFeed')) {
            clearInterval(checkInterval);
            fetchNews();
        }
    });

    console.log('📰 Модуль новостей загружен');
})();