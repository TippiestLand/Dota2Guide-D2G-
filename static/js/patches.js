(function() {
    'use strict';

    var patchesFeed = document.getElementById('patchesFeed');

    // Словарь перевода категорий
    var ruTitles = {
        'HERO CHANGES': 'ИЗМЕНЕНИЯ ГЕРОЕВ',
        'ITEM CHANGES': 'ИЗМЕНЕНИЯ ПРЕДМЕТОВ',
        'NEUTRAL ITEM CHANGES': 'ИЗМЕНЕНИЯ НЕЙТРАЛЬНЫХ ПРЕДМЕТОВ',
        'WHAT CHANGED IN': 'ЧТО ИЗМЕНИЛОСЬ В'
    };

    // Базовый URL для иконок (CDN Dota 2)
    var ICON_BASE = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/';
    var ITEM_ICON_BASE = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/';

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
            
            html += '<div class="patch-card" data-id="' + (patch.id || i) + '">';
            
            // WHAT CHANGED IN X.XX (русский)
            html += '    <div class="patch-title-main">' + ruTitles['WHAT CHANGED IN'] + ' ' + escapeHtml(patch.version) + '</div>';
            
            // Hero Changes
            if (patch.hero_changes && patch.hero_changes.length > 0) {
                html += '    <div class="patch-section-title">' + ruTitles['HERO CHANGES'] + '</div>';
                html += '    <div class="patch-hero-changes">';
                for (var h = 0; h < patch.hero_changes.length; h++) {
                    var change = patch.hero_changes[h];
                    var heroIcon = change.hero ? change.hero.toLowerCase().replace(/\s+/g, '_') : 'unknown';
                    var iconUrl = ICON_BASE + heroIcon + '.png';
                    
                    var valueClass = '';
                    if (change.change && change.change.startsWith('-')) {
                        valueClass = 'negative';
                    } else if (change.change && (change.change.startsWith('+') || change.change === 'NEW' || change.change === 'REWORK')) {
                        valueClass = 'positive';
                    }
                    
                    html += '        <div class="patch-hero-change" data-hero="' + escapeHtml(change.hero) + '" data-detail="' + escapeHtml(change.detail || '') + '">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.hero) + '" class="patch-hero-icon" onerror="this.style.display=\'none\'">';
                    html += '            <span class="patch-hero-name">' + escapeHtml(change.hero) + '</span>';
                    if (change.change) {
                        html += '            <span class="patch-hero-value ' + valueClass + '">' + escapeHtml(change.change) + '</span>';
                    }
                    if (change.detail) {
                        html += '            <span class="patch-hero-desc">' + escapeHtml(change.detail) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Item Changes
            if (patch.item_changes && patch.item_changes.length > 0) {
                html += '    <div class="patch-section-title">' + ruTitles['ITEM CHANGES'] + '</div>';
                html += '    <div class="patch-item-changes">';
                for (var it = 0; it < patch.item_changes.length; it++) {
                    var change = patch.item_changes[it];
                    var itemIcon = change.item ? change.item.toLowerCase().replace(/\s+/g, '_') : 'unknown';
                    var iconUrl = ITEM_ICON_BASE + itemIcon + '.png';
                    
                    html += '        <div class="patch-item-change">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.style.display=\'none\'">';
                    html += '            <span class="patch-item-name">' + escapeHtml(change.item) + '</span>';
                    if (change.old && change.new) {
                        html += '            <span class="patch-item-values">' + escapeHtml(change.old) + ' → ' + escapeHtml(change.new) + '</span>';
                    }
                    if (change.detail) {
                        html += '            <span class="patch-item-desc">' + escapeHtml(change.detail) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Neutral Item Changes
            if (patch.neutral_item_changes && patch.neutral_item_changes.length > 0) {
                html += '    <div class="patch-section-title">' + ruTitles['NEUTRAL ITEM CHANGES'] + '</div>';
                html += '    <div class="patch-item-changes">';
                for (var n = 0; n < patch.neutral_item_changes.length; n++) {
                    var change = patch.neutral_item_changes[n];
                    var itemIcon = change.item ? change.item.toLowerCase().replace(/\s+/g, '_') : 'unknown';
                    var iconUrl = ITEM_ICON_BASE + itemIcon + '.png';
                    
                    html += '        <div class="patch-item-change">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.style.display=\'none\'">';
                    html += '            <span class="patch-item-name">' + escapeHtml(change.item) + '</span>';
                    if (change.old && change.new) {
                        html += '            <span class="patch-item-values">' + escapeHtml(change.old) + ' → ' + escapeHtml(change.new) + '</span>';
                    }
                    if (change.detail) {
                        html += '            <span class="patch-item-desc">' + escapeHtml(change.detail) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            html += '</div>';
        }

        patchesFeed.innerHTML = html;

        // Добавляем всплывающие подсказки при наведении
        var heroChanges = document.querySelectorAll('.patch-hero-change');
        for (var hc = 0; hc < heroChanges.length; hc++) {
            (function(el) {
                el.addEventListener('mouseenter', function(e) {
                    var detail = this.dataset.detail;
                    if (detail) {
                        var tooltip = document.createElement('div');
                        tooltip.className = 'patch-tooltip';
                        tooltip.textContent = detail;
                        tooltip.style.position = 'fixed';
                        tooltip.style.left = (e.clientX + 10) + 'px';
                        tooltip.style.top = (e.clientY - 10) + 'px';
                        tooltip.style.background = 'rgba(10,10,18,0.95)';
                        tooltip.style.color = '#fff';
                        tooltip.style.padding = '8px 14px';
                        tooltip.style.borderRadius = '6px';
                        tooltip.style.border = '1px solid rgba(240,185,11,0.2)';
                        tooltip.style.fontSize = '0.8rem';
                        tooltip.style.maxWidth = '300px';
                        tooltip.style.pointerEvents = 'none';
                        tooltip.style.zIndex = '9999';
                        tooltip.style.backdropFilter = 'blur(8px)';
                        tooltip.id = 'patch-tooltip';
                        document.body.appendChild(tooltip);
                    }
                });
                el.addEventListener('mousemove', function(e) {
                    var tooltip = document.getElementById('patch-tooltip');
                    if (tooltip) {
                        tooltip.style.left = (e.clientX + 10) + 'px';
                        tooltip.style.top = (e.clientY - 10) + 'px';
                    }
                });
                el.addEventListener('mouseleave', function() {
                    var tooltip = document.getElementById('patch-tooltip');
                    if (tooltip) {
                        tooltip.remove();
                    }
                });
            })(heroChanges[hc]);
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

    console.log('Patch module loaded');
})();