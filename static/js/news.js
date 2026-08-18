(function() {
    'use strict';

    // ===== ПЕРЕКЛЮЧЕНИЕ ВКЛАДОК =====
    var tabBtns = document.querySelectorAll('.tab-btn');
    var tabContents = document.querySelectorAll('.tab-content');

    for (var i = 0; i < tabBtns.length; i++) {
        tabBtns[i].addEventListener('click', function() {
            var tabId = this.dataset.tab;
            
            for (var j = 0; j < tabBtns.length; j++) {
                tabBtns[j].classList.remove('active');
            }
            for (var k = 0; k < tabContents.length; k++) {
                tabContents[k].classList.remove('active');
            }
            
            this.classList.add('active');
            var target = document.getElementById('tab-' + tabId);
            if (target) {
                target.classList.add('active');
            }
        });
    }

    // ===== НОВОСТИ =====
    var API_URL = '/api/news';
    var newsFeed = document.getElementById('newsFeed');

    function fetchNews() {
        if (!newsFeed) return;

        newsFeed.innerHTML = '' +
            '<div class="news-loading">' +
            '    <div class="loader"></div>' +
            '    <p>Загрузка новостей...</p>' +
            '</div>';

        fetch(API_URL + '?t=' + Date.now())
            .then(function(response) {
                if (!response.ok) throw new Error('Ошибка загрузки: ' + response.status);
                return response.json();
            })
            .then(function(data) {
                if (data && data.length > 0) {
                    renderNews(data);
                } else {
                    newsFeed.innerHTML = '' +
                        '<div class="news-empty">' +
                        '    <p>Новостей пока нет</p>' +
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

            var plainText = newsContent.replace(/<[^>]+>/g, '');
            var isLong = plainText.length > 500;

            var shortContent = newsContent;
            if (isLong) {
                var shortPlain = plainText.substring(0, 500) + '...';
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
                html += '            <button class="news-toggle-btn" data-id="' + newsId + '">';
                html += '                <span class="toggle-icon">▼</span> Развернуть';
                html += '            </button>';
                html += '            <div style="display:none;" class="news-full-content" data-full="' + escapeHtml(newsContent) + '" data-short="' + shortContent + '"></div>';
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

        var toggleBtns = document.querySelectorAll('.news-toggle-btn');
        for (var j = 0; j < toggleBtns.length; j++) {
            toggleBtns[j].addEventListener('click', function() {
                var btn = this;
                var id = btn.dataset.id;
                var textEl = document.getElementById('news-text-' + id);
                var fullContentEl = btn.parentElement.querySelector('.news-full-content');

                if (!textEl || !fullContentEl) return;

                var fullContent = fullContentEl.dataset.full;
                var shortContent = fullContentEl.dataset.short;

                if (btn.classList.contains('expanded')) {
                    textEl.innerHTML = shortContent;
                    btn.classList.remove('expanded');
                    btn.innerHTML = '<span class="toggle-icon">▼</span> Развернуть';
                } else {
                    textEl.innerHTML = fullContent;
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
    });

    console.log('Модуль новостей загружен');
})();