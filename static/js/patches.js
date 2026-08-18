(function() {
    'use strict';

    var patchesFeed = document.getElementById('patchesFeed');

    function fetchPatches() {
        if (!patchesFeed) {
            console.warn('Элемент #patchesFeed не найден');
            return;
        }

        patchesFeed.innerHTML = '' +
            '<div class="news-loading">' +
            '    <div class="loader"></div>' +
            '    <p>Загрузка патчей...</p>' +
            '</div>';

        fetch('/api/patches')
            .then(function(response) {
                if (!response.ok) throw new Error('Ошибка загрузки: ' + response.status);
                return response.json();
            })
            .then(function(data) {
                console.log('📦 Получены патчи:', data);
                if (data && data.length > 0) {
                    renderPatches(data);
                } else {
                    patchesFeed.innerHTML = '' +
                        '<div class="news-empty">' +
                        '    <p>Патчи не найдены</p>' +
                        '    <p style="font-size:0.8rem; color:#666; margin-top:8px;">' +
                        '        Информация о патчах появится позже' +
                        '    </p>' +
                        '</div>';
                }
            })
            .catch(function(error) {
                console.error('❌ Ошибка загрузки патчей:', error);
                patchesFeed.innerHTML = '' +
                    '<div class="news-empty">' +
                    '    <p>Не удалось загрузить патчи</p>' +
                    '    <button onclick="fetchPatches()" ' +
                    '            class="btn btn-secondary" ' +
                    '            style="margin-top:15px; padding:8px 24px; font-size:0.8rem;">' +
                    '        Обновить' +
                    '    </button>' +
                    '</div>';
            });
    }

    function renderPatches(patches) {
        if (!patchesFeed) return;

        var html = '';
        for (var i = 0; i < patches.length; i++) {
            var patch = patches[i];
            
            var patchType = patch.type || 'minor';
            var typeClass = patchType === 'major' ? 'major' : 'minor';
            var typeLabel = patchType === 'major' ? '⭐ Мажорный' : '🔄 Минорный';

            var description = patch.description || '';
            var shortDesc = description.length > 200 ? description.substring(0, 200) + '...' : description;

            var stats = patch.stats || {};
            var heroesCount = stats.heroes || 0;
            var itemsCount = stats.items || 0;
            var generalCount = stats.general || 0;

            html += '<div class="patch-card" data-id="' + (patch.id || i) + '">';
            
            html += '    <div class="patch-header">';
            html += '        <span class="patch-version">' + escapeHtml(patch.version) + '</span>';
            html += '        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">';
            html += '            <span class="patch-date">📅 ' + escapeHtml(patch.date) + '</span>';
            html += '            <span class="patch-type ' + typeClass + '">' + typeLabel + '</span>';
            html += '        </div>';
            html += '    </div>';
            
            if (patch.title) {
                html += '    <div class="patch-title">' + escapeHtml(patch.title) + '</div>';
            }
            
            html += '    <div class="patch-description" id="patch-desc-' + i + '" data-full="' + escapeHtml(description) + '">' + shortDesc + '</div>';
            
            html += '    <div class="patch-stats">';
            if (heroesCount > 0) {
                html += '        <span class="patch-stat"><span class="stat-icon">⚔️</span> Героев: <span class="stat-value">' + heroesCount + '</span></span>';
            }
            if (itemsCount > 0) {
                html += '        <span class="patch-stat"><span class="stat-icon">📦</span> Предметов: <span class="stat-value">' + itemsCount + '</span></span>';
            }
            if (generalCount > 0) {
                html += '        <span class="patch-stat"><span class="stat-icon">📋</span> Общих: <span class="stat-value">' + generalCount + '</span></span>';
            }
            if (patch.days_since_prev) {
                html += '        <span class="patch-stat"><span class="stat-icon">📅</span> Дней: <span class="stat-value">' + patch.days_since_prev + '</span></span>';
            }
            html += '    </div>';
            
            if (patch.heroes && patch.heroes.length > 0) {
                html += '    <div class="patch-heroes">';
                var heroList = patch.heroes;
                for (var j = 0; j < Math.min(heroList.length, 8); j++) {
                    html += '        <span class="patch-hero-tag">' + escapeHtml(heroList[j]) + '</span>';
                }
                if (heroList.length > 8) {
                    html += '        <span class="patch-hero-tag">+' + (heroList.length - 8) + ' ещё</span>';
                }
                html += '    </div>';
            }
            
            html += '    <button class="patch-expand-btn" data-id="' + i + '">';
            html += '        <span class="toggle-icon">▼</span> Подробнее';
            html += '    </button>';
            
            html += '    <div class="patch-full-content" id="patch-full-' + i + '">';
            html += '        <div class="patch-section">';
            html += '            <div class="patch-section-title">📝 Полное описание</div>';
            html += '            <div class="patch-section-item">' + escapeHtml(description) + '</div>';
            html += '        </div>';
            html += '    </div>';
            html += '</div>';
        }

        patchesFeed.innerHTML = html;

        var expandBtns = document.querySelectorAll('.patch-expand-btn');
        for (var e = 0; e < expandBtns.length; e++) {
            expandBtns[e].addEventListener('click', function() {
                var id = this.dataset.id;
                var fullContent = document.getElementById('patch-full-' + id);
                var desc = document.getElementById('patch-desc-' + id);
                
                if (!fullContent) return;
                
                if (fullContent.classList.contains('open')) {
                    fullContent.classList.remove('open');
                    this.innerHTML = '<span class="toggle-icon">▼</span> Подробнее';
                    if (desc) {
                        var fullText = desc.dataset.full || desc.textContent;
                        desc.textContent = fullText.length > 200 ? fullText.substring(0, 200) + '...' : fullText;
                    }
                } else {
                    fullContent.classList.add('open');
                    this.innerHTML = '<span class="toggle-icon">▲</span> Свернуть';
                    if (desc) {
                        var fullText = desc.dataset.full || desc.textContent;
                        desc.textContent = fullText;
                    }
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

    window.fetchPatches = fetchPatches;

    document.addEventListener('DOMContentLoaded', function() {
        var checkInterval = setInterval(function() {
            var feed = document.getElementById('patchesFeed');
            if (feed) {
                clearInterval(checkInterval);
                fetchPatches();
            }
        }, 100);
    });

    console.log('🔄 Модуль патчей загружен');
})();