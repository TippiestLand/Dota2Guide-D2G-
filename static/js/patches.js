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
            var typeLabel = patchType === 'major' ? 'MAJOR PATCH' : 'MINOR PATCH';

            var stats = patch.stats || {};
            var heroesCount = stats.heroes || 0;
            var itemsCount = stats.items || 0;
            var neutralCount = stats.neutral_items || 0;
            var generalCount = stats.general || 0;

            html += '<div class="patch-card" data-id="' + (patch.id || i) + '">';
            
            // Header
            html += '    <div class="patch-header">';
            html += '        <div class="patch-version">' + escapeHtml(patch.version) + '</div>';
            html += '        <div class="patch-meta">';
            html += '            <span class="patch-date">' + escapeHtml(patch.date) + '</span>';
            html += '            <span class="patch-type ' + typeClass + '">' + typeLabel + '</span>';
            html += '        </div>';
            html += '    </div>';
            
            // Stats
            html += '    <div class="patch-stats">';
            if (patch.days_since_prev) {
                html += '        <span class="patch-stat">Days after prev: <span class="stat-value">' + patch.days_since_prev + '</span></span>';
            }
            if (patch.days_active) {
                html += '        <span class="patch-stat">Active: <span class="stat-value">' + patch.days_active + ' days</span></span>';
            }
            if (heroesCount > 0) {
                html += '        <span class="patch-stat">Heroes: <span class="stat-value">' + heroesCount + '</span></span>';
            }
            if (itemsCount > 0) {
                html += '        <span class="patch-stat">Items: <span class="stat-value">' + itemsCount + '</span></span>';
            }
            if (neutralCount > 0) {
                html += '        <span class="patch-stat">Neutral Items: <span class="stat-value">' + neutralCount + '</span></span>';
            }
            if (generalCount > 0) {
                html += '        <span class="patch-stat">General: <span class="stat-value">' + generalCount + '</span></span>';
            }
            html += '    </div>';
            
            // Description
            if (patch.description) {
                html += '    <div class="patch-description">' + escapeHtml(patch.description) + '</div>';
            }
            
            // Most picked heroes
            if (patch.heroes && patch.heroes.length > 0) {
                html += '    <div class="patch-section-title">MOST PICKED HEROES</div>';
                html += '    <div class="patch-heroes">';
                for (var j = 0; j < patch.heroes.length; j++) {
                    html += '        <span class="patch-hero-tag">' + escapeHtml(patch.heroes[j]) + '</span>';
                }
                html += '    </div>';
            }
            
            // Hero changes
            if (patch.hero_changes && patch.hero_changes.length > 0) {
                html += '    <div class="patch-section-title">HERO CHANGES</div>';
                html += '    <div class="patch-changes-list">';
                for (var h = 0; h < patch.hero_changes.length; h++) {
                    var change = patch.hero_changes[h];
                    html += '        <div class="patch-change-item">';
                    if (change.hero) {
                        html += '            <strong>' + escapeHtml(change.hero) + '</strong>';
                    }
                    if (change.ability) {
                        html += '            <span class="change-ability">' + escapeHtml(change.ability) + '</span>';
                    }
                    if (change.old_value && change.new_value) {
                        html += '            <span class="change-values">' + escapeHtml(change.old_value) + ' → ' + escapeHtml(change.new_value) + '</span>';
                    }
                    if (change.description) {
                        html += '            <span class="change-desc">' + escapeHtml(change.description) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Item changes
            if (patch.item_changes && patch.item_changes.length > 0) {
                html += '    <div class="patch-section-title">ITEM CHANGES</div>';
                html += '    <div class="patch-changes-list">';
                for (var it = 0; it < patch.item_changes.length; it++) {
                    var change = patch.item_changes[it];
                    html += '        <div class="patch-change-item">';
                    if (change.item) {
                        html += '            <strong>' + escapeHtml(change.item) + '</strong>';
                    }
                    if (change.old_value && change.new_value) {
                        html += '            <span class="change-values">' + escapeHtml(change.old_value) + ' → ' + escapeHtml(change.new_value) + '</span>';
                    }
                    if (change.description) {
                        html += '            <span class="change-desc">' + escapeHtml(change.description) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // Neutral item changes
            if (patch.neutral_item_changes && patch.neutral_item_changes.length > 0) {
                html += '    <div class="patch-section-title">NEUTRAL ITEM CHANGES</div>';
                html += '    <div class="patch-changes-list">';
                for (var n = 0; n < patch.neutral_item_changes.length; n++) {
                    var change = patch.neutral_item_changes[n];
                    html += '        <div class="patch-change-item">';
                    if (change.item) {
                        html += '            <strong>' + escapeHtml(change.item) + '</strong>';
                    }
                    if (change.old_value && change.new_value) {
                        html += '            <span class="change-values">' + escapeHtml(change.old_value) + ' → ' + escapeHtml(change.new_value) + '</span>';
                    }
                    if (change.description) {
                        html += '            <span class="change-desc">' + escapeHtml(change.description) + '</span>';
                    }
                    html += '        </div>';
                }
                html += '    </div>';
            }
            
            // General changes
            if (patch.general_changes && patch.general_changes.length > 0) {
                html += '    <div class="patch-section-title">GENERAL CHANGES</div>';
                html += '    <div class="patch-changes-list">';
                for (var g = 0; g < patch.general_changes.length; g++) {
                    html += '        <div class="patch-change-item">' + escapeHtml(patch.general_changes[g]) + '</div>';
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