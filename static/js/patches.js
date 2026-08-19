(function() {
    'use strict';

    var patchesFeed = document.getElementById('patchesFeed');

    // Перевод на русский
    var translations = {
        'Patch': 'Патч',
        'Heroes': 'Героев',
        'Items': 'Предметов',
        'Neutral Items': 'Нейтральных предметов',
        'General': 'Общих',
        'days ago': 'дней назад',
        'days after prev': 'дней после предыдущего',
        'MOST PICKED HEROES': 'САМЫЕ ПОПУЛЯРНЫЕ ГЕРОИ',
        'Pick Rate': 'Пикрейт',
        'Win Rate': 'Винрейт',
        'WR Delta': 'Изменение винрейта',
        'HERO CHANGES': 'ИЗМЕНЕНИЯ ГЕРОЕВ',
        'ITEM CHANGES': 'ИЗМЕНЕНИЯ ПРЕДМЕТОВ',
        'NEUTRAL ITEM CHANGES': 'ИЗМЕНЕНИЯ НЕЙТРАЛЬНЫХ ПРЕДМЕТОВ',
        'GENERAL CHANGES': 'ОБЩИЕ ИЗМЕНЕНИЯ',
        'Major': 'Мажорный',
        'Minor': 'Минорный'
    };

    function t(text) {
        return translations[text] || text;
    }

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
            var typeLabel = patchType === 'major' ? t('Major') : t('Minor');

            var stats = patch.stats || {};

            html += '<div class="patch-card" data-id="' + (patch.id || i) + '">';
            
            // Шапка патча
            html += '    <div class="patch-header">';
            html += '        <div class="patch-version">' + escapeHtml(patch.version) + '</div>';
            html += '        <div class="patch-meta">';
            html += '            <span class="patch-date">' + escapeHtml(patch.date) + '</span>';
            if (patch.days_ago) {
                html += '            <span class="patch-days">' + patch.days_ago + ' ' + t('days ago') + '</span>';
            }
            if (patch.days_after_prev) {
                html += '            <span class="patch-days">' + patch.days_after_prev + ' ' + t('days after prev') + '</span>';
            }
            html += '            <span class="patch-type ' + typeClass + '">' + typeLabel + '</span>';
            html += '        </div>';
            html += '    </div>';
            
            // Статистика патча
            html += '    <div class="patch-stats">';
            if (stats.heroes) {
                html += '        <span class="patch-stat">' + t('Heroes') + ': <span class="stat-value">' + stats.heroes + '</span></span>';
            }
            if (stats.items) {
                html += '        <span class="patch-stat">' + t('Items') + ': <span class="stat-value">' + stats.items + '</span></span>';
            }
            if (stats.neutral_items) {
                html += '        <span class="patch-stat">' + t('Neutral Items') + ': <span class="stat-value">' + stats.neutral_items + '</span></span>';
            }
            if (stats.general) {
                html += '        <span class="patch-stat">' + t('General') + ': <span class="stat-value">' + stats.general + '</span></span>';
            }
            html += '    </div>';
            
            // Описание патча
            if (patch.description) {
                html += '    <div class="patch-description">' + escapeHtml(patch.description) + '</div>';
            }
            
            // Самые популярные герои
            if (patch.heroes_stats && patch.heroes_stats.length > 0) {
                html += '    <div class="patch-section-title">' + t('MOST PICKED HEROES') + '</div>';
                html += '    <div class="patch-heroes-grid">';
                for (var h = 0; h < patch.heroes_stats.length; h++) {
                    var hero = patch.heroes_stats[h];
                    html += '        <div class="patch-hero-card">';
                    html += '            <div class="patch-hero-name">' + escapeHtml(hero.name) + '</div>';
                    if (hero.pick_rate) {
                        html += '            <div class="patch-hero-stat">' + t('Pick Rate') + ': <span>' + hero.pick_rate + '</span></div>';
                    }
                    if (hero.win_rate) {
                        html += '            <div class="patch-hero-stat">' + t('Win Rate') + ': <span>' + hero.win_rate + '</span></div>';
                    }
                    if (hero.wr_delta) {
                        var deltaClass = hero.wr_delta.startsWith('+') ? 'positive' : 'negative';
                        html += '            <div class="patch-hero-stat ' + deltaClass + '">' + t('WR Delta') + ': <span>' + hero.wr_delta + '</span></div>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Изменения героев
            if (patch.hero_changes && patch.hero_changes.length > 0) {
                html += '    <div class="patch-section-title">' + t('HERO CHANGES') + '</div>';
                html += '    <div class="patch-changes-list">';
                for (var hc = 0; hc < patch.hero_changes.length; hc++) {
                    var change = patch.hero_changes[hc];
                    html += '        <div class="patch-change-item">';
                    if (change.hero) {
                        html += '            <strong>' + escapeHtml(change.hero) + '</strong>';
                    }
                    if (change.ability) {
                        html += '            <span class="change-ability">' + escapeHtml(change.ability) + '</span>';
                    }
                    if (change.changes && change.changes.length > 0) {
                        html += '            <ul class="change-details">';
                        for (var c = 0; c < change.changes.length; c++) {
                            html += '                <li>' + escapeHtml(change.changes[c]) + '</li>';
                        }
                        html += '            </ul>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Изменения предметов
            if (patch.item_changes && patch.item_changes.length > 0) {
                html += '    <div class="patch-section-title">' + t('ITEM CHANGES') + '</div>';
                html += '    <div class="patch-changes-list">';
                for (var ic = 0; ic < patch.item_changes.length; ic++) {
                    var change = patch.item_changes[ic];
                    html += '        <div class="patch-change-item">';
                    if (change.item) {
                        html += '            <strong>' + escapeHtml(change.item) + '</strong>';
                    }
                    if (change.changes && change.changes.length > 0) {
                        html += '            <ul class="change-details">';
                        for (var c2 = 0; c2 < change.changes.length; c2++) {
                            html += '                <li>' + escapeHtml(change.changes[c2]) + '</li>';
                        }
                        html += '            </ul>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Изменения нейтральных предметов
            if (patch.neutral_item_changes && patch.neutral_item_changes.length > 0) {
                html += '    <div class="patch-section-title">' + t('NEUTRAL ITEM CHANGES') + '</div>';
                html += '    <div class="patch-changes-list">';
                for (var nc = 0; nc < patch.neutral_item_changes.length; nc++) {
                    var change = patch.neutral_item_changes[nc];
                    html += '        <div class="patch-change-item">';
                    if (change.item) {
                        html += '            <strong>' + escapeHtml(change.item) + '</strong>';
                    }
                    if (change.changes && change.changes.length > 0) {
                        html += '            <ul class="change-details">';
                        for (var c3 = 0; c3 < change.changes.length; c3++) {
                            html += '                <li>' + escapeHtml(change.changes[c3]) + '</li>';
                        }
                        html += '            </ul>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Общие изменения
            if (patch.general_changes && patch.general_changes.length > 0) {
                html += '    <div class="patch-section-title">' + t('GENERAL CHANGES') + '</div>';
                html += '    <div class="patch-changes-list">';
                for (var gc = 0; gc < patch.general_changes.length; gc++) {
                    html += '        <div class="patch-change-item">' + escapeHtml(patch.general_changes[gc]) + '</div>';
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