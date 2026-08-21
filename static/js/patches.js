(function() {
    'use strict';

    var patchesFeed = document.getElementById('patchesFeed');

    // Русские заголовки
    var ruTitles = {
        'HERO CHANGES': 'ИЗМЕНЕНИЯ ГЕРОЕВ',
        'ITEM CHANGES': 'ИЗМЕНЕНИЯ ПРЕДМЕТОВ',
        'NEUTRAL ITEM CHANGES': 'ИЗМЕНЕНИЯ НЕЙТРАЛЬНЫХ ПРЕДМЕТОВ',
        'WHAT CHANGED IN': 'ЧТО ИЗМЕНИЛОСЬ В'
    };

    // Базовые URL для иконок
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
            
            // Заголовок
            html += '    <div class="patch-title-main">' + ruTitles['WHAT CHANGED IN'] + ' ' + escapeHtml(patch.version) + '</div>';
            html += '    <div class="patch-date">' + escapeHtml(patch.date) + ' | ' + (patch.type === 'major' ? 'МАЖОРНЫЙ' : 'МИНОРНЫЙ') + '</div>';
            
            // Hero Changes
            if (patch.hero_changes && patch.hero_changes.length > 0) {
                html += '    <div class="patch-section-title">' + ruTitles['HERO CHANGES'] + ' <span class="patch-count">' + patch.hero_changes.length + '</span></div>';
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
                    
                    html += '        <div class="patch-hero-change" data-hero="' + escapeHtml(change.hero) + '" data-detail="' + escapeHtml(change.detail || '') + '" data-ability="' + escapeHtml(change.ability || '') + '">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.hero) + '" class="patch-hero-icon" onerror="this.src=\'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'40\' height=\'40\'%3E%3Crect width=\'40\' height=\'40\' fill=\'%23333\'/%3E%3Ctext x=\'20\' y=\'25\' text-anchor=\'middle\' fill=\'%23666\' font-size=\'12\'%3E' + escapeHtml(change.hero.charAt(0)) + '%3C/text%3E%3C/svg%3E\'">';
                    html += '            <span class="patch-hero-name">' + escapeHtml(change.hero) + '</span>';
                    if (change.change) {
                        html += '            <span class="patch-hero-value ' + valueClass + '">' + escapeHtml(change.change) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Item Changes
            if (patch.item_changes && patch.item_changes.length > 0) {
                html += '    <div class="patch-section-title">' + ruTitles['ITEM CHANGES'] + ' <span class="patch-count">' + patch.item_changes.length + '</span></div>';
                html += '    <div class="patch-item-changes">';
                for (var it = 0; it < patch.item_changes.length; it++) {
                    var change = patch.item_changes[it];
                    var itemIcon = change.item ? change.item.toLowerCase().replace(/\s+/g, '_') : 'unknown';
                    var iconUrl = ITEM_ICON_BASE + itemIcon + '.png';
                    
                    html += '        <div class="patch-item-change" data-item="' + escapeHtml(change.item) + '" data-detail="' + escapeHtml(change.detail || '') + '">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.src=\'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'40\' height=\'40\'%3E%3Crect width=\'40\' height=\'40\' fill=\'%23333\'/%3E%3Ctext x=\'20\' y=\'25\' text-anchor=\'middle\' fill=\'%23666\' font-size=\'12\'%3E' + escapeHtml(change.item.charAt(0)) + '%3C/text%3E%3C/svg%3E\'">';
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
                html += '    <div class="patch-section-title">' + ruTitles['NEUTRAL ITEM CHANGES'] + ' <span class="patch-count">' + patch.neutral_item_changes.length + '</span></div>';
                html += '    <div class="patch-item-changes">';
                for (var n = 0; n < patch.neutral_item_changes.length; n++) {
                    var change = patch.neutral_item_changes[n];
                    var itemIcon = change.item ? change.item.toLowerCase().replace(/\s+/g, '_') : 'unknown';
                    var iconUrl = ITEM_ICON_BASE + itemIcon + '.png';
                    
                    html += '        <div class="patch-item-change" data-item="' + escapeHtml(change.item) + '" data-detail="' + escapeHtml(change.detail || '') + '">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.src=\'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'40\' height=\'40\'%3E%3Crect width=\'40\' height=\'40\' fill=\'%23333\'/%3E%3Ctext x=\'20\' y=\'25\' text-anchor=\'middle\' fill=\'%23666\' font-size=\'12\'%3E' + escapeHtml(change.item.charAt(0)) + '%3C/text%3E%3C/svg%3E\'">';
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

        // Добавляем всплывающие подсказки при наведении на героев
        var heroChanges = document.querySelectorAll('.patch-hero-change');
        for (var hc = 0; hc < heroChanges.length; hc++) {
            (function(el) {
                el.addEventListener('mouseenter', function(e) {
                    var detail = this.dataset.detail;
                    var ability = this.dataset.ability;
                    var hero = this.dataset.hero;
                    if (detail) {
                        var tooltip = document.createElement('div');
                        tooltip.className = 'patch-tooltip';
                        tooltip.innerHTML = '<strong>' + escapeHtml(hero) + '</strong>' + 
                            (ability ? ' — ' + escapeHtml(ability) : '') + 
                            '<br><span style="color:#b0b0c0;font-size:0.85rem;">' + escapeHtml(detail) + '</span>';
                        tooltip.style.position = 'fixed';
                        tooltip.style.left = (e.clientX + 15) + 'px';
                        tooltip.style.top = (e.clientY - 15) + 'px';
                        tooltip.style.background = 'rgba(10,10,18,0.95)';
                        tooltip.style.color = '#fff';
                        tooltip.style.padding = '10px 16px';
                        tooltip.style.borderRadius = '8px';
                        tooltip.style.border = '1px solid rgba(240,185,11,0.25)';
                        tooltip.style.fontSize = '0.85rem';
                        tooltip.style.maxWidth = '320px';
                        tooltip.style.pointerEvents = 'none';
                        tooltip.style.zIndex = '9999';
                        tooltip.style.backdropFilter = 'blur(8px)';
                        tooltip.style.boxShadow = '0 8px 32px rgba(0,0,0,0.6)';
                        tooltip.style.lineHeight = '1.5';
                        tooltip.id = 'patch-tooltip';
                        document.body.appendChild(tooltip);
                    }
                });
                el.addEventListener('mousemove', function(e) {
                    var tooltip = document.getElementById('patch-tooltip');
                    if (tooltip) {
                        tooltip.style.left = (e.clientX + 15) + 'px';
                        tooltip.style.top = (e.clientY - 15) + 'px';
                        // Если тултип выходит за правый край
                        if (e.clientX + 320 > window.innerWidth) {
                            tooltip.style.left = (e.clientX - 330) + 'px';
                        }
                        // Если тултип выходит за нижний край
                        if (e.clientY + 100 > window.innerHeight) {
                            tooltip.style.top = (e.clientY - 100) + 'px';
                        }
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

        // Добавляем всплывающие подсказки при наведении на предметы
        var itemChanges = document.querySelectorAll('.patch-item-change');
        for (var ic = 0; ic < itemChanges.length; ic++) {
            (function(el) {
                el.addEventListener('mouseenter', function(e) {
                    var detail = this.dataset.detail;
                    var item = this.dataset.item;
                    if (detail) {
                        var tooltip = document.createElement('div');
                        tooltip.className = 'patch-tooltip';
                        tooltip.innerHTML = '<strong>' + escapeHtml(item) + '</strong><br><span style="color:#b0b0c0;font-size:0.85rem;">' + escapeHtml(detail) + '</span>';
                        tooltip.style.position = 'fixed';
                        tooltip.style.left = (e.clientX + 15) + 'px';
                        tooltip.style.top = (e.clientY - 15) + 'px';
                        tooltip.style.background = 'rgba(10,10,18,0.95)';
                        tooltip.style.color = '#fff';
                        tooltip.style.padding = '10px 16px';
                        tooltip.style.borderRadius = '8px';
                        tooltip.style.border = '1px solid rgba(240,185,11,0.25)';
                        tooltip.style.fontSize = '0.85rem';
                        tooltip.style.maxWidth = '320px';
                        tooltip.style.pointerEvents = 'none';
                        tooltip.style.zIndex = '9999';
                        tooltip.style.backdropFilter = 'blur(8px)';
                        tooltip.style.boxShadow = '0 8px 32px rgba(0,0,0,0.6)';
                        tooltip.style.lineHeight = '1.5';
                        tooltip.id = 'patch-tooltip-item';
                        document.body.appendChild(tooltip);
                    }
                });
                el.addEventListener('mousemove', function(e) {
                    var tooltip = document.getElementById('patch-tooltip-item');
                    if (tooltip) {
                        tooltip.style.left = (e.clientX + 15) + 'px';
                        tooltip.style.top = (e.clientY - 15) + 'px';
                        if (e.clientX + 320 > window.innerWidth) {
                            tooltip.style.left = (e.clientX - 330) + 'px';
                        }
                        if (e.clientY + 100 > window.innerHeight) {
                            tooltip.style.top = (e.clientY - 100) + 'px';
                        }
                    }
                });
                el.addEventListener('mouseleave', function() {
                    var tooltip = document.getElementById('patch-tooltip-item');
                    if (tooltip) {
                        tooltip.remove();
                    }
                });
            })(itemChanges[ic]);
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