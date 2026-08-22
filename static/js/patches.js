(function() {
    'use strict';

    var patchesFeed = document.getElementById('patchesFeed');

    var ICON_BASE = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/';
    var ITEM_ICON_BASE = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/';
    var ABILITY_ICON_BASE = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/';

    // ===== РАСШИРЕННЫЙ МАППИНГ ГЕРОЕВ =====
    var HERO_ICON_MAP = {
        'Ancient Apparition': 'ancient_apparition',
        'Anti-Mage': 'antimage',
        'Arc Warden': 'arc_warden',
        'Bounty Hunter': 'bounty_hunter',
        'Centaur Warrunner': 'centaur',
        'Chaos Knight': 'chaos_knight',
        'Crystal Maiden': 'crystal_maiden',
        'Dark Seer': 'dark_seer',
        'Dark Willow': 'dark_willow',
        'Dawnbreaker': 'dawnbreaker',
        'Death Prophet': 'death_prophet',
        'Dragon Knight': 'dragon_knight',
        'Drow Ranger': 'drow_ranger',
        'Earth Spirit': 'earth_spirit',
        'Elder Titan': 'elder_titan',
        'Ember Spirit': 'ember_spirit',
        'Faceless Void': 'faceless_void',
        'Grimstroke': 'grimstroke',
        'Gyrocopter': 'gyrocopter',
        'Hoodwink': 'hoodwink',
        'Juggernaut': 'juggernaut',
        'Keeper of the Light': 'keeper_of_the_light',
        'Legion Commander': 'legion_commander',
        'Lifestealer': 'life_stealer',
        'Lone Druid': 'lone_druid',
        'Monkey King': 'monkey_king',
        'Naga Siren': 'naga_siren',
        "Nature's Prophet": 'furion',
        'Night Stalker': 'night_stalker',
        'Ogre Magi': 'ogre_magi',
        'Omniknight': 'omniknight',
        'Outworld Destroyer': 'obsidian_destroyer',
        'Phantom Assassin': 'phantom_assassin',
        'Phantom Lancer': 'phantom_lancer',
        'Primal Beast': 'primal_beast',
        'Queen of Pain': 'queenofpain',
        'Shadow Fiend': 'nevermore',
        'Shadow Shaman': 'shadow_shaman',
        'Skywrath Mage': 'skywrath_mage',
        'Spirit Breaker': 'spirit_breaker',
        'Storm Spirit': 'storm_spirit',
        'Templar Assassin': 'templar_assassin',
        'Treant Protector': 'treant',
        'Troll Warlord': 'troll_warlord',
        'Vengeful Spirit': 'vengefulspirit',
        'Void Spirit': 'void_spirit',
        'Winter Wyvern': 'winter_wyvern',
        'Witch Doctor': 'witch_doctor',
        'Wraith King': 'skeleton_king',
        'Zeus': 'zuus',
        'Underlord': 'abyssal_underlord',
        'Necrophos': 'necrolyte',
        'Magnus': 'magnataur',
        'Doom': 'doom_bringer',
        'Clockwerk': 'rattletrap',
        'Timbersaw': 'shredder',
        'Io': 'wisp',
        'Windranger': 'windrunner',
        "Nature's Prophet": 'furion',
        'Lina': 'lina',
        'Keeper of the Light': 'keeper_of_the_light'
    };

    // ===== РАСШИРЕННЫЙ МАППИНГ ПРЕДМЕТОВ =====
    var ITEM_ICON_MAP = {
        "Shiva's Guard": 'shivas_guard',
        "Heaven's Halberd": 'heavens_halberd',
        "Crella's Crozier": 'crellas_crozier',
        "Forager's Kit": 'foragers_kit',
        "Conjurer's Catalyst": 'conjurers_catalyst',
        "Enchanter's Bauble": 'enchanters_bauble',
        "Urn of Shadows": 'urn_of_shadows',
        'Eye of Skadi': 'eye_of_skadi',
        'Gleipnir': 'gleipnir',
        'Divine Rapier': 'divine_rapier',
        'Feverish': 'feverish',
        'Greedy': 'greedy',
        'Mage Slayer': 'mage_slayer',
        'Shadow Blade': 'shadow_blade',
        'Harpoon': 'harpoon',
        'Eternal Chains': 'eternal_chains',
        'Dominate': 'dominate',
        'Spirit Vessel': 'spirit_vessel'
    };

    function getHeroIconName(name) {
        if (!name) return 'unknown';
        if (HERO_ICON_MAP[name]) return HERO_ICON_MAP[name];
        return name.toLowerCase().replace(/\s+/g, '_').replace(/'/g, '').replace(/[^a-z0-9_]/g, '');
    }

    function getItemIconName(name) {
        if (!name) return 'unknown';
        if (ITEM_ICON_MAP[name]) return ITEM_ICON_MAP[name];
        return name.toLowerCase().replace(/\s+/g, '_').replace(/'/g, '').replace(/[^a-z0-9_]/g, '');
    }

    function getAbilityIconName(changeText) {
        var abilityMatch = changeText.match(/^([A-Z][a-zA-Z\s']+?)(?::|,|\.|\s+—|\s+–)/);
        if (abilityMatch) {
            var ability = abilityMatch[1].trim();
            return ability.toLowerCase().replace(/\s+/g, '_').replace(/'/g, '').replace(/[^a-z0-9_]/g, '');
        }
        return null;
    }

    function fetchPatches() {
        if (!patchesFeed) return;

        patchesFeed.innerHTML = '<div class="news-loading"><div class="loader"></div><p>Загрузка патчей...</p></div>';

        fetch('/api/patches')
            .then(function(response) {
                if (!response.ok) throw new Error('Ошибка загрузки: ' + response.status);
                return response.json();
            })
            .then(function(data) {
                if (data && data.length > 0) {
                    renderPatches(data);
                } else {
                    patchesFeed.innerHTML = '<div class="news-empty"><p>Патчи не найдены</p></div>';
                }
            })
            .catch(function(error) {
                console.error('Ошибка загрузки патчей:', error);
                patchesFeed.innerHTML = '<div class="news-empty"><p>Не удалось загрузить патчи</p></div>';
            });
    }

    function renderPatches(patches) {
        if (!patchesFeed) return;

        var html = '';
        for (var i = 0; i < patches.length; i++) {
            var patch = patches[i];

            html += '<div class="patch-card" data-id="' + (patch.id || i) + '">';
            html += '    <div class="patch-title-main">ЧТО ИЗМЕНИЛОСЬ В ' + escapeHtml(patch.version) + '</div>';
            html += '    <div class="patch-date">' + escapeHtml(patch.date) + ' | ' + (patch.type === 'major' ? 'МАЖОРНЫЙ' : 'МИНОРНЫЙ') + '</div>';

            // Общие изменения
            if (patch.general_changes && patch.general_changes.length > 0) {
                html += '    <div class="patch-section-title">ОБЩИЕ ИЗМЕНЕНИЯ <span class="patch-count">' + patch.general_changes.length + '</span></div>';
                html += '    <div class="patch-changes-list">';
                for (var g = 0; g < patch.general_changes.length; g++) {
                    html += '        <div class="patch-change-item">' + escapeHtml(patch.general_changes[g]) + '</div>';
                }
                html += '    </div>';
            }

            // Изменения предметов
            if (patch.item_changes && patch.item_changes.length > 0) {
                html += '    <div class="patch-section-title">ИЗМЕНЕНИЯ ПРЕДМЕТОВ <span class="patch-count">' + patch.item_changes.length + '</span></div>';
                html += '    <div class="patch-items-grid">';
                for (var it = 0; it < patch.item_changes.length; it++) {
                    var change = patch.item_changes[it];
                    var iconName = getItemIconName(change.item);
                    var iconUrl = ITEM_ICON_BASE + iconName + '.png';

                    // Подсчет изменений вверх/вниз для предмета
                    var upCount = 0;
                    var downCount = 0;
                    if (change.detail) {
                        if (change.detail.includes('увеличен') || change.detail.includes('увеличена') || change.detail.includes('усилен') || change.detail.includes('усилена')) upCount++;
                        if (change.detail.includes('уменьшен') || change.detail.includes('уменьшена') || change.detail.includes('ослаблен') || change.detail.includes('ослаблена')) downCount++;
                    }
                    if (change.old && change.new && parseInt(change.old) < parseInt(change.new)) upCount++;
                    if (change.old && change.new && parseInt(change.old) > parseInt(change.new)) downCount++;

                    var arrowHtml = '';
                    if (upCount > 0 && downCount === 0) {
                        arrowHtml = '<span class="patch-item-arrow"><span class="arrow-up">↑</span><span class="arrow-count">' + upCount + '</span></span>';
                    } else if (downCount > 0 && upCount === 0) {
                        arrowHtml = '<span class="patch-item-arrow"><span class="arrow-down">↓</span><span class="arrow-count">' + downCount + '</span></span>';
                    } else if (upCount > 0 && downCount > 0) {
                        arrowHtml = '<span class="patch-item-arrow"><span class="arrow-up">↑</span><span class="arrow-count">' + upCount + '</span><span class="arrow-down">↓</span><span class="arrow-count">' + downCount + '</span></span>';
                    }

                    html += '        <div class="patch-item-block" data-item="' + escapeHtml(change.item) + '" data-detail="' + escapeHtml(change.detail || '') + '">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.style.display=\'none\'">';
                    html += '            <span class="patch-item-name">' + escapeHtml(change.item) + '</span>';
                    html += arrowHtml;
                    html += '        </div>';
                }
                html += '    </div>';
            }

            // Изменения нейтральных предметов
            if (patch.neutral_item_changes && patch.neutral_item_changes.length > 0) {
                html += '    <div class="patch-section-title">ИЗМЕНЕНИЯ НЕЙТРАЛЬНЫХ ПРЕДМЕТОВ <span class="patch-count">' + patch.neutral_item_changes.length + '</span></div>';
                html += '    <div class="patch-items-grid">';
                for (var n = 0; n < patch.neutral_item_changes.length; n++) {
                    var change = patch.neutral_item_changes[n];
                    var iconName = getItemIconName(change.item);
                    var iconUrl = ITEM_ICON_BASE + iconName + '.png';

                    // Подсчет изменений для нейтральных предметов
                    var upCount = 0;
                    var downCount = 0;
                    if (change.detail) {
                        if (change.detail.includes('увеличен') || change.detail.includes('увеличена') || change.detail.includes('усилен') || change.detail.includes('усилена')) upCount++;
                        if (change.detail.includes('уменьшен') || change.detail.includes('уменьшена') || change.detail.includes('ослаблен') || change.detail.includes('ослаблена')) downCount++;
                    }
                    if (change.old && change.new && parseInt(change.old) < parseInt(change.new)) upCount++;
                    if (change.old && change.new && parseInt(change.old) > parseInt(change.new)) downCount++;

                    var arrowHtml = '';
                    if (upCount > 0 && downCount === 0) {
                        arrowHtml = '<span class="patch-item-arrow"><span class="arrow-up">↑</span><span class="arrow-count">' + upCount + '</span></span>';
                    } else if (downCount > 0 && upCount === 0) {
                        arrowHtml = '<span class="patch-item-arrow"><span class="arrow-down">↓</span><span class="arrow-count">' + downCount + '</span></span>';
                    } else if (upCount > 0 && downCount > 0) {
                        arrowHtml = '<span class="patch-item-arrow"><span class="arrow-up">↑</span><span class="arrow-count">' + upCount + '</span><span class="arrow-down">↓</span><span class="arrow-count">' + downCount + '</span></span>';
                    }

                    html += '        <div class="patch-item-block" data-item="' + escapeHtml(change.item) + '" data-detail="' + escapeHtml(change.detail || '') + '">';
                    html += '            <img src="' + iconUrl + '" alt="' + escapeHtml(change.item) + '" class="patch-item-icon" onerror="this.style.display=\'none\'">';
                    html += '            <span class="patch-item-name">' + escapeHtml(change.item) + '</span>';
                    html += arrowHtml;
                    html += '        </div>';
                }
                html += '    </div>';
            }

            // Изменения героев
            if (patch.hero_changes && patch.hero_changes.length > 0) {
                html += '    <div class="patch-section-title">ИЗМЕНЕНИЯ ГЕРОЕВ <span class="patch-count">' + patch.hero_changes.length + '</span></div>';
                html += '    <div class="patch-heroes-grid">';
                for (var h = 0; h < patch.hero_changes.length; h++) {
                    var hero = patch.hero_changes[h];
                    var iconName = getHeroIconName(hero.hero);
                    var iconUrl = ICON_BASE + iconName + '.png';

                    var changesText = hero.changes ? hero.changes.join('; ') : '';

                    // Подсчет изменений вверх/вниз для героя
                    var upCount = 0;
                    var downCount = 0;
                    if (changesText) {
                        var changes = changesText.split(';');
                        for (var c = 0; c < changes.length; c++) {
                            var text = changes[c].toLowerCase();
                            if (text.includes('увеличен') || text.includes('увеличена') || text.includes('усилен') || text.includes('усилена')) upCount++;
                            if (text.includes('уменьшен') || text.includes('уменьшена') || text.includes('ослаблен') || text.includes('ослаблена')) downCount++;
                            var match = text.match(/(\d+)\s*→\s*(\d+)/);
                            if (match && parseInt(match[1]) < parseInt(match[2])) upCount++;
                            if (match && parseInt(match[1]) > parseInt(match[2])) downCount++;
                        }
                    }

                    var arrowHtml = '';
                    if (upCount > 0 && downCount === 0) {
                        arrowHtml = '<span class="patch-hero-arrow"><span class="arrow-up">↑</span><span class="arrow-count">' + upCount + '</span></span>';
                    } else if (downCount > 0 && upCount === 0) {
                        arrowHtml = '<span class="patch-hero-arrow"><span class="arrow-down">↓</span><span class="arrow-count">' + downCount + '</span></span>';
                    } else if (upCount > 0 && downCount > 0) {
                        arrowHtml = '<span class="patch-hero-arrow"><span class="arrow-up">↑</span><span class="arrow-count">' + upCount + '</span><span class="arrow-down">↓</span><span class="arrow-count">' + downCount + '</span></span>';
                    }

                    html += '        <div class="patch-hero-block" data-hero="' + escapeHtml(hero.hero) + '" data-detail="' + escapeHtml(changesText) + '">';
                    html += '            <div class="patch-hero-icon-wrap">';
                    html += '                <img src="' + iconUrl + '" alt="' + escapeHtml(hero.hero) + '" class="patch-hero-icon" onerror="this.style.display=\'none\'">';
                    html += '            </div>';
                    html += '            <span class="patch-hero-name">' + escapeHtml(hero.hero) + '</span>';
                    html += arrowHtml;
                    html += '        </div>';
                }
                html += '    </div>';
            }

            html += '</div>';
        }

        patchesFeed.innerHTML = html;
        addTooltips();
    }

    function addTooltips() {
        // Tooltips для героев
        var heroBlocks = document.querySelectorAll('.patch-hero-block');
        for (var h = 0; h < heroBlocks.length; h++) {
            (function(el) {
                el.addEventListener('mouseenter', function(e) {
                    var detail = this.dataset.detail;
                    var hero = this.dataset.hero;

                    if (detail) {
                        var tooltip = document.createElement('div');
                        tooltip.className = 'patch-tooltip hero-tooltip';

                        var changes = detail.split('; ');
                        var content = '<strong>' + escapeHtml(hero) + '</strong>';

                        for (var i = 0; i < changes.length; i++) {
                            var change = changes[i].trim();
                            if (!change) continue;

                            var isTalent = change.toLowerCase().includes('талант') || change.toLowerCase().includes('talent');
                            var abilityIcon = getAbilityIconName(change);
                            var iconUrl = '';
                            var iconHtml = '';

                            if (isTalent) {
                                iconUrl = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/icons/talent_tree.png';
                                iconHtml = '<img src="' + iconUrl + '" alt="талант" class="tooltip-icon" onerror="this.style.display=\'none\'">';
                            } else if (abilityIcon) {
                                iconUrl = ABILITY_ICON_BASE + abilityIcon + '.png';
                                iconHtml = '<img src="' + iconUrl + '" alt="способность" class="tooltip-icon" onerror="this.style.display=\'none\'">';
                            }

                            content += '<div class="tooltip-change-item">';
                            content += iconHtml;
                            content += '<span>' + escapeHtml(change) + '</span>';
                            content += '</div>';
                        }

                        tooltip.innerHTML = content;
                        tooltip.style.position = 'fixed';
                        tooltip.style.left = (e.clientX + 15) + 'px';
                        tooltip.style.top = (e.clientY - 15) + 'px';
                        tooltip.id = 'patch-tooltip-hero';
                        document.body.appendChild(tooltip);
                        positionTooltip(tooltip, e);
                    }
                });

                el.addEventListener('mousemove', function(e) {
                    var tooltip = document.getElementById('patch-tooltip-hero');
                    if (tooltip) positionTooltip(tooltip, e);
                });

                el.addEventListener('mouseleave', function() {
                    var tooltip = document.getElementById('patch-tooltip-hero');
                    if (tooltip) tooltip.remove();
                });
            })(heroBlocks[h]);
        }

        // Tooltips для предметов
        var itemBlocks = document.querySelectorAll('.patch-item-block');
        for (var it = 0; it < itemBlocks.length; it++) {
            (function(el) {
                el.addEventListener('mouseenter', function(e) {
                    var detail = this.dataset.detail;
                    var item = this.dataset.item;
                    if (detail && detail.length > 30) {
                        var tooltip = document.createElement('div');
                        tooltip.className = 'patch-tooltip';
                        tooltip.innerHTML = '<strong>' + escapeHtml(item) + '</strong><span>' + escapeHtml(detail) + '</span>';
                        tooltip.style.position = 'fixed';
                        tooltip.style.left = (e.clientX + 15) + 'px';
                        tooltip.style.top = (e.clientY - 15) + 'px';
                        tooltip.id = 'patch-tooltip-item';
                        document.body.appendChild(tooltip);
                        positionTooltip(tooltip, e);
                    }
                });

                el.addEventListener('mousemove', function(e) {
                    var tooltip = document.getElementById('patch-tooltip-item');
                    if (tooltip) positionTooltip(tooltip, e);
                });

                el.addEventListener('mouseleave', function() {
                    var tooltip = document.getElementById('patch-tooltip-item');
                    if (tooltip) tooltip.remove();
                });
            })(itemBlocks[it]);
        }
    }

    function positionTooltip(tooltip, e) {
        var left = e.clientX + 15;
        var top = e.clientY - 15;
        if (left + 420 > window.innerWidth) left = e.clientX - 420;
        if (left < 10) left = 10;
        if (top + 300 > window.innerHeight) top = e.clientY - 300;
        if (top < 10) top = 10;
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
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
            if (document.getElementById('patchesFeed')) {
                clearInterval(checkInterval);
                fetchPatches();
            }
        }, 100);
    });

    console.log('Patch module loaded');
})();