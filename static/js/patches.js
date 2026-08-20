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
                console.log('Получены патчи:', data);
                if (data && data.length > 0) {
                    renderPatches(data);
                } else {
                    patchesFeed.innerHTML = '' +
                        '<div class="news-empty">' +
                        '    <p>Патчи не найдены</p>' +
                        '</div>';
                }
            })
            .catch(function(error) {
                console.error('Ошибка загрузки патчей:', error);
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
            
            var stats = patch.stats || {};
            var heroesCount = stats.heroes || 0;
            var itemsCount = stats.items || 0;
            var neutralCount = stats.neutral_items || 0;

            html += '<div class="patch-card" data-id="' + (patch.id || i) + '">';
            
            // WHAT CHANGED IN X.XX
            html += '    <div class="patch-title-main">WHAT CHANGED IN ' + escapeHtml(patch.version) + '</div>';
            
            // Статистика изменений
            html += '    <div class="patch-stats-summary">';
            if (heroesCount > 0) {
                html += '        <span class="patch-stat-badge">HERO CHANGES <span class="stat-number">' + heroesCount + '</span></span>';
            }
            if (itemsCount > 0) {
                html += '        <span class="patch-stat-badge">ITEM CHANGES <span class="stat-number">' + itemsCount + '</span></span>';
            }
            if (neutralCount > 0) {
                html += '        <span class="patch-stat-badge">NEUTRAL ITEM CHANGES <span class="stat-number">' + neutralCount + '</span></span>';
            }
            html += '    </div>';
            
            // Hero Changes с иконками
            if (patch.hero_changes && patch.hero_changes.length > 0) {
                html += '    <div class="patch-section-title">HERO CHANGES</div>';
                html += '    <div class="patch-hero-changes">';
                for (var h = 0; h < patch.hero_changes.length; h++) {
                    var change = patch.hero_changes[h];
                    html += '        <div class="patch-hero-change" data-hero="' + escapeHtml(change.hero) + '">';
                    if (change.hero_icon) {
                        html += '            <img src="' + escapeHtml(change.hero_icon) + '" alt="' + escapeHtml(change.hero) + '" class="patch-hero-icon" onerror="this.style.display=\'none\'">';
                    }
                    html += '            <span class="patch-hero-name">' + escapeHtml(change.hero) + '</span>';
                    if (change.change_value) {
                        var valueClass = change.change_value.startsWith('-') ? 'negative' : 'positive';
                        html += '            <span class="patch-hero-value ' + valueClass + '">' + escapeHtml(change.change_value) + '</span>';
                    }
                    if (change.description) {
                        html += '            <span class="patch-hero-desc">' + escapeHtml(change.description) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Item Changes
            if (patch.item_changes && patch.item_changes.length > 0) {
                html += '    <div class="patch-section-title">ITEM CHANGES</div>';
                html += '    <div class="patch-item-changes">';
                for (var it = 0; it < patch.item_changes.length; it++) {
                    var change = patch.item_changes[it];
                    html += '        <div class="patch-item-change">';
                    if (change.item_icon) {
                        html += '            <img src="' + escapeHtml(change.item_icon) + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.style.display=\'none\'">';
                    }
                    html += '            <span class="patch-item-name">' + escapeHtml(change.item) + '</span>';
                    if (change.old_value && change.new_value) {
                        html += '            <span class="patch-item-values">' + escapeHtml(change.old_value) + ' → ' + escapeHtml(change.new_value) + '</span>';
                    }
                    if (change.description) {
                        html += '            <span class="patch-item-desc">' + escapeHtml(change.description) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Neutral Item Changes
            if (patch.neutral_item_changes && patch.neutral_item_changes.length > 0) {
                html += '    <div class="patch-section-title">NEUTRAL ITEM CHANGES</div>';
                html += '    <div class="patch-item-changes">';
                for (var n = 0; n < patch.neutral_item_changes.length; n++) {
                    var change = patch.neutral_item_changes[n];
                    html += '        <div class="patch-item-change">';
                    if (change.item_icon) {
                        html += '            <img src="' + escapeHtml(change.item_icon) + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.style.display=\'none\'">';
                    }
                    html += '            <span class="patch-item-name">' + escapeHtml(change.item) + '</span>';
                    if (change.old_value && change.new_value) {
                        html += '            <span class="patch-item-values">' + escapeHtml(change.old_value) + ' → ' + escapeHtml(change.new_value) + '</span>';
                    }
                    if (change.description) {
                        html += '            <span class="patch-item-desc">' + escapeHtml(change.description) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            html += '</div>';
        }

        patchesFeed.innerHTML = html;
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

    console.log('Patch module loaded');
})();