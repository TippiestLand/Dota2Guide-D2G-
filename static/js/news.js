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
            var newsDate = escapeHtml(news.date);
            var newsTitle = escapeHtml(news.title);
            var newsContent = news.content || '';
            var newsLink = news.link ? escapeHtml(news.link) : '';
            var newsId = news.id || i;

            var linkHtml = '';
            if (newsLink) {
                linkHtml = '<a href="' + newsLink + '" target="_blank" class="news-read-more">Steam →</a>';
            }

            // Проверяем длину (без HTML тегов для подсчёта)
            var plainText = newsContent.replace(/<[^>]+>/g, '');
            var isLong = plainText.length > 500;
            
            // Для короткого текста — обрезаем по словам
            var shortContent = newsContent;
            if (isLong) {
                var shortPlain = plainText.substring(0, 500) + '...';
                // Вставляем короткий текст в HTML
                shortContent = shortPlain.replace(/\n/g, '<br>');
            }

            html += '<div class="news-card-vk" data-id="' + newsId + '">';
            html += '    <div class="news-card-header">';
            html += '        <div class="news-date">' + newsDate + '</div>';
            html += '    </div>';
            html += '    <div class="news-card-body">';
            html += '        <h3 class="news-title">' + newsTitle + '</h3>';
            html += '        <div class="news-content">';

            if (isLong) {
                html += '            <div class="news-preview" id="news-text-' + newsId + '">' + shortContent + '</div>';
                html += '            <button class="news-toggle-btn" data-id="' + newsId + '" data-full="' + escapeHtml(newsContent) + '" data-short="' + shortContent + '">';
                html += '                <span class="toggle-icon">▼</span> Развернуть';
                html += '            </button>';
            } else {
                html += '            <div class="news-preview">' + newsContent + '</div>';
            }

            html += '        </div>';
            html += '    </div>';
            html += '    <div class="news-card-footer">';
            html += '        ' + linkHtml;
            html += '    </div>';
            html += '</div>';
        }

        newsFeed.innerHTML = html;

        // Обработчики для кнопок "Развернуть/Свернуть"
        var toggleBtns = document.querySelectorAll('.news-toggle-btn');
        for (var j = 0; j < toggleBtns.length; j++) {
            toggleBtns[j].addEventListener('click', function() {
                var btn = this;
                var id = btn.dataset.id;
                var textEl = document.getElementById('news-text-' + id);

                if (!textEl) return;

                if (btn.classList.contains('expanded')) {
                    textEl.innerHTML = btn.dataset.short;
                    btn.classList.remove('expanded');
                    btn.innerHTML = '<span class="toggle-icon">▼</span> Развернуть';
                } else {
                    textEl.innerHTML = btn.dataset.full;
                    btn.classList.add('expanded');
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