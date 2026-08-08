(function() {
    'use strict';

    // ============================================================
    // ЛОКАЛЬНЫЕ ДАННЫЕ ГЕРОЕВ (для фильтров и отображения)
    // ============================================================
    var heroesData = [
        { name: 'Alchemist', attribute: 'strength', icon: 'alchemist' },
        { name: 'Axe', attribute: 'strength', icon: 'axe' },
        { name: 'Bristleback', attribute: 'strength', icon: 'bristleback' },
        { name: 'Centaur Warrunner', attribute: 'strength', icon: 'centaur' },
        { name: 'Chaos Knight', attribute: 'strength', icon: 'chaos_knight' },
        { name: 'Clockwerk', attribute: 'strength', icon: 'rattletrap' },
        { name: 'Dawnbreaker', attribute: 'strength', icon: 'dawnbreaker' },
        { name: 'Doom', attribute: 'strength', icon: 'doom_bringer' },
        { name: 'Dragon Knight', attribute: 'strength', icon: 'dragon_knight' },
        { name: 'Earth Spirit', attribute: 'strength', icon: 'earth_spirit' },
        { name: 'Earthshaker', attribute: 'strength', icon: 'earthshaker' },
        { name: 'Elder Titan', attribute: 'strength', icon: 'elder_titan' },
        { name: 'Huskar', attribute: 'strength', icon: 'huskar' },
        { name: 'Kunkka', attribute: 'strength', icon: 'kunkka' },
        { name: 'Legion Commander', attribute: 'strength', icon: 'legion_commander' },
        { name: 'Lifestealer', attribute: 'strength', icon: 'life_stealer' },
        { name: 'Lycan', attribute: 'strength', icon: 'lycan' },
        { name: 'Mars', attribute: 'strength', icon: 'mars' },
        { name: 'Night Stalker', attribute: 'strength', icon: 'night_stalker' },
        { name: 'Ogre Magi', attribute: 'strength', icon: 'ogre_magi' },
        { name: 'Omniknight', attribute: 'strength', icon: 'omniknight' },
        { name: 'Phoenix', attribute: 'strength', icon: 'phoenix' },
        { name: 'Primal Beast', attribute: 'strength', icon: 'primal_beast' },
        { name: 'Pudge', attribute: 'strength', icon: 'pudge' },
        { name: 'Slardar', attribute: 'strength', icon: 'slardar' },
        { name: 'Spirit Breaker', attribute: 'strength', icon: 'spirit_breaker' },
        { name: 'Sven', attribute: 'strength', icon: 'sven' },
        { name: 'Tidehunter', attribute: 'strength', icon: 'tidehunter' },
        { name: 'Timbersaw', attribute: 'strength', icon: 'shredder' },
        { name: 'Tiny', attribute: 'strength', icon: 'tiny' },
        { name: 'Treant Protector', attribute: 'strength', icon: 'treant' },
        { name: 'Tusk', attribute: 'strength', icon: 'tusk' },
        { name: 'Underlord', attribute: 'strength', icon: 'abyssal_underlord' },
        { name: 'Undying', attribute: 'strength', icon: 'undying' },
        { name: 'Wraith King', attribute: 'strength', icon: 'skeleton_king' },
        { name: 'Anti-Mage', attribute: 'agility', icon: 'antimage' },
        { name: 'Bloodseeker', attribute: 'agility', icon: 'bloodseeker' },
        { name: 'Bounty Hunter', attribute: 'agility', icon: 'bounty_hunter' },
        { name: 'Broodmother', attribute: 'agility', icon: 'broodmother' },
        { name: 'Clinkz', attribute: 'agility', icon: 'clinkz' },
        { name: 'Drow Ranger', attribute: 'agility', icon: 'drow_ranger' },
        { name: 'Ember Spirit', attribute: 'agility', icon: 'ember_spirit' },
        { name: 'Faceless Void', attribute: 'agility', icon: 'faceless_void' },
        { name: 'Gyrocopter', attribute: 'agility', icon: 'gyrocopter' },
        { name: 'Hoodwink', attribute: 'agility', icon: 'hoodwink' },
        { name: 'Juggernaut', attribute: 'agility', icon: 'juggernaut' },
        { name: 'Lone Druid', attribute: 'agility', icon: 'lone_druid' },
        { name: 'Luna', attribute: 'agility', icon: 'luna' },
        { name: 'Medusa', attribute: 'agility', icon: 'medusa' },
        { name: 'Meepo', attribute: 'agility', icon: 'meepo' },
        { name: 'Mirana', attribute: 'agility', icon: 'mirana' },
        { name: 'Monkey King', attribute: 'agility', icon: 'monkey_king' },
        { name: 'Morphling', attribute: 'agility', icon: 'morphling' },
        { name: 'Naga Siren', attribute: 'agility', icon: 'naga_siren' },
        { name: 'Phantom Assassin', attribute: 'agility', icon: 'phantom_assassin' },
        { name: 'Phantom Lancer', attribute: 'agility', icon: 'phantom_lancer' },
        { name: 'Razor', attribute: 'agility', icon: 'razor' },
        { name: 'Riki', attribute: 'agility', icon: 'riki' },
        { name: 'Shadow Fiend', attribute: 'agility', icon: 'nevermore' },
        { name: 'Slark', attribute: 'agility', icon: 'slark' },
        { name: 'Sniper', attribute: 'agility', icon: 'sniper' },
        { name: 'Spectre', attribute: 'agility', icon: 'spectre' },
        { name: 'Templar Assassin', attribute: 'agility', icon: 'templar_assassin' },
        { name: 'Terrorblade', attribute: 'agility', icon: 'terrorblade' },
        { name: 'Troll Warlord', attribute: 'agility', icon: 'troll_warlord' },
        { name: 'Ursa', attribute: 'agility', icon: 'ursa' },
        { name: 'Vengeful Spirit', attribute: 'agility', icon: 'vengefulspirit' },
        { name: 'Viper', attribute: 'agility', icon: 'viper' },
        { name: 'Weaver', attribute: 'agility', icon: 'weaver' },
        { name: 'Ancient Apparition', attribute: 'intelligence', icon: 'ancient_apparition' },
        { name: 'Chen', attribute: 'intelligence', icon: 'chen' },
        { name: 'Crystal Maiden', attribute: 'intelligence', icon: 'crystal_maiden' },
        { name: 'Dark Seer', attribute: 'intelligence', icon: 'dark_seer' },
        { name: 'Dark Willow', attribute: 'intelligence', icon: 'dark_willow' },
        { name: 'Disruptor', attribute: 'intelligence', icon: 'disruptor' },
        { name: 'Enchantress', attribute: 'intelligence', icon: 'enchantress' },
        { name: 'Grimstroke', attribute: 'intelligence', icon: 'grimstroke' },
        { name: 'Invoker', attribute: 'intelligence', icon: 'invoker' },
        { name: 'Jakiro', attribute: 'intelligence', icon: 'jakiro' },
        { name: 'Keeper of the Light', attribute: 'intelligence', icon: 'keeper_of_the_light' },
        { name: 'Leshrac', attribute: 'intelligence', icon: 'leshrac' },
        { name: 'Lich', attribute: 'intelligence', icon: 'lich' },
        { name: 'Lina', attribute: 'intelligence', icon: 'lina' },
        { name: 'Lion', attribute: 'intelligence', icon: 'lion' },
        { name: 'Muerta', attribute: 'intelligence', icon: 'muerta' },
        { name: 'Necrophos', attribute: 'intelligence', icon: 'necrolyte' },
        { name: 'Oracle', attribute: 'intelligence', icon: 'oracle' },
        { name: 'Outworld Destroyer', attribute: 'intelligence', icon: 'obsidian_destroyer' },
        { name: 'Puck', attribute: 'intelligence', icon: 'puck' },
        { name: 'Pugna', attribute: 'intelligence', icon: 'pugna' },
        { name: 'Queen of Pain', attribute: 'intelligence', icon: 'queenofpain' },
        { name: 'Ringmaster', attribute: 'intelligence', icon: 'ringmaster' },
        { name: 'Rubick', attribute: 'intelligence', icon: 'rubick' },
        { name: 'Shadow Demon', attribute: 'intelligence', icon: 'shadow_demon' },
        { name: 'Shadow Shaman', attribute: 'intelligence', icon: 'shadow_shaman' },
        { name: 'Silencer', attribute: 'intelligence', icon: 'silencer' },
        { name: 'Skywrath Mage', attribute: 'intelligence', icon: 'skywrath_mage' },
        { name: 'Storm Spirit', attribute: 'intelligence', icon: 'storm_spirit' },
        { name: 'Tinker', attribute: 'intelligence', icon: 'tinker' },
        { name: 'Warlock', attribute: 'intelligence', icon: 'warlock' },
        { name: 'Winter Wyvern', attribute: 'intelligence', icon: 'winter_wyvern' },
        { name: 'Witch Doctor', attribute: 'intelligence', icon: 'witch_doctor' },
        { name: 'Zeus', attribute: 'intelligence', icon: 'zuus' },
        { name: 'Abaddon', attribute: 'universal', icon: 'abaddon' },
        { name: 'Arc Warden', attribute: 'universal', icon: 'arc_warden' },
        { name: 'Bane', attribute: 'universal', icon: 'bane' },
        { name: 'Batrider', attribute: 'universal', icon: 'batrider' },
        { name: 'Beastmaster', attribute: 'universal', icon: 'beastmaster' },
        { name: 'Brewmaster', attribute: 'universal', icon: 'brewmaster' },
        { name: 'Dazzle', attribute: 'universal', icon: 'dazzle' },
        { name: 'Death Prophet', attribute: 'universal', icon: 'death_prophet' },
        { name: 'Enigma', attribute: 'universal', icon: 'enigma' },
        { name: 'Io', attribute: 'universal', icon: 'wisp' },
        { name: 'Magnus', attribute: 'universal', icon: 'magnataur' },
        { name: 'Marci', attribute: 'universal', icon: 'marci' },
        { name: "Nature's Prophet", attribute: 'universal', icon: 'furion' },
        { name: 'Nyx Assassin', attribute: 'universal', icon: 'nyx_assassin' },
        { name: 'Pangolier', attribute: 'universal', icon: 'pangolier' },
        { name: 'Sand King', attribute: 'universal', icon: 'sand_king' },
        { name: 'Snapfire', attribute: 'universal', icon: 'snapfire' },
        { name: 'Techies', attribute: 'universal', icon: 'techies' },
        { name: 'Venomancer', attribute: 'universal', icon: 'venomancer' },
        { name: 'Visage', attribute: 'universal', icon: 'visage' },
        { name: 'Void Spirit', attribute: 'universal', icon: 'void_spirit' },
        { name: 'Windranger', attribute: 'universal', icon: 'windrunner' }
    ];

    // Убираем дубликаты
    var heroMap = new Map();
    for (var i = 0; i < heroesData.length; i++) {
        var hero = heroesData[i];
        if (!heroMap.has(hero.name)) {
            heroMap.set(hero.name, hero);
        }
    }
    var uniqueHeroes = Array.from(heroMap.values());
    uniqueHeroes.sort(function(a, b) {
        return a.name.localeCompare(b.name);
    });

    var heroList = document.getElementById('heroList');
    var attributeGlow = document.getElementById('attributeGlow');
    var currentFilter = 'all';
    var searchQuery = '';
    var isTransitioning = false;

    // ============================================================
    // МОДАЛЬНОЕ ОКНО
    // ============================================================
    var modal = document.getElementById('heroModal');
    var modalBody = document.getElementById('heroModalBody');
    var modalClose = document.getElementById('heroModalClose');

    function openHeroModal(heroIcon) {
        if (!modal) {
            console.error('❌ Модальное окно не найдено!');
            return;
        }
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
        modalBody.innerHTML = '<div class="hero-modal-loading"><div class="loader"></div><p>Загрузка...</p></div>';

        var hero = uniqueHeroes.find(function(h) { return h.icon === heroIcon; });
        if (!hero) {
            modalBody.innerHTML = '<p style="color:#ff6b6b; text-align:center; padding:20px;">Герой не найден</p>';
            return;
        }

        console.log('📡 Запрос данных для героя:', heroIcon);

        fetch('/api/hero/' + heroIcon)
            .then(function(response) {
                if (!response.ok) throw new Error('Ошибка загрузки: ' + response.status);
                return response.json();
            })
            .then(function(data) {
                console.log('✅ Данные героя получены');
                renderHeroModal(data, hero);
            })
            .catch(function(error) {
                console.error('❌ Ошибка:', error);
                modalBody.innerHTML = '<p style="color:#ff6b6b; text-align:center; padding:20px;">Не удалось загрузить данные героя</p>';
            });
    }

    function renderHeroModal(data, hero) {
        var heroData = data.data;
        var abilities = data.abilities || [];

        if (!heroData) {
            modalBody.innerHTML = '<p style="color:#ff6b6b; text-align:center; padding:20px;">Ошибка: данные героя не загружены</p>';
            return;
        }

        var primaryAttr = heroData.primary_attr || hero.attribute;
        var attrClass = {
            'str': 'strength',
            'agi': 'agility',
            'int': 'intelligence',
            'universal': 'universal',
            'strength': 'strength',
            'agility': 'agility',
            'intelligence': 'intelligence'
        }[primaryAttr] || 'universal';

        var attrName = {
            'str': 'СИЛА',
            'agi': 'ЛОВКОСТЬ',
            'int': 'ИНТЕЛЛЕКТ',
            'universal': 'УНИВЕРСАЛЬНЫЙ',
            'strength': 'СИЛА',
            'agility': 'ЛОВКОСТЬ',
            'intelligence': 'ИНТЕЛЛЕКТ'
        }[primaryAttr] || 'УНИВЕРСАЛЬНЫЙ';

        var heroName = heroData.localized_name || hero.name;
        var heroIcon = hero.icon;

        var html = '';

        // ===== ВЕРХНЯЯ ЧАСТЬ =====
        html += '<div class="hero-modal-header">';
        html += '    <div class="hero-modal-avatar">';
        html += '        <img src="/static/assets/icons/' + heroIcon + '.png" alt="' + heroName + '" onerror="this.src=\'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'100\' height=\'100\'%3E%3Crect width=\'100\' height=\'100\' fill=\'%23222\'/%3E%3Ctext x=\'50\' y=\'55\' text-anchor=\'middle\' fill=\'%23666\' font-size=\'18\' font-family=\'sans-serif\'%3E' + heroName.charAt(0) + '%3C/text%3E%3C/svg%3E\'">';
        html += '    </div>';
        html += '    <div class="hero-modal-title">';
        html += '        <div class="hero-modal-attribute ' + attrClass + '">' + attrName + '</div>';
        html += '        <div class="hero-modal-name"><span class="highlight">' + heroName + '</span></div>';
        html += '    </div>';
        html += '</div>';

        // ===== ОПИСАНИЕ =====
        var bioText = heroData.bio || 'Описание героя временно недоступно.';
        html += '<p class="hero-modal-description">' + bioText + '</p>';

        // ===== СТАТИСТИКА =====
        html += '<div class="hero-modal-stats">';

        // Атака
        html += '    <div class="hero-modal-stat-block">';
        html += '        <div class="hero-modal-stat-block-title">АТАКА</div>';
        html += '        <div class="hero-modal-stat-block-values">';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">' + (heroData.base_attack_min || '?') + '-' + (heroData.base_attack_max || '?') + '</div><div class="hero-modal-stat-item-label">УРОН</div></div>';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">' + (heroData.attack_rate || '?') + '</div><div class="hero-modal-stat-item-label">СКОРОСТЬ</div></div>';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">' + (heroData.attack_range || '?') + '</div><div class="hero-modal-stat-item-label">ДАЛЬНОСТЬ</div></div>';
        html += '        </div>';
        html += '    </div>';

        // Защита
        html += '    <div class="hero-modal-stat-block">';
        html += '        <div class="hero-modal-stat-block-title">ЗАЩИТА</div>';
        html += '        <div class="hero-modal-stat-block-values">';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">' + (heroData.base_health || '?') + '</div><div class="hero-modal-stat-item-label">ЗДОРОВЬЕ</div></div>';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">' + (heroData.base_mana || '?') + '</div><div class="hero-modal-stat-item-label">МАНА</div></div>';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">' + (heroData.base_armor || '?') + '</div><div class="hero-modal-stat-item-label">БРОНЯ</div></div>';
        html += '        </div>';
        html += '    </div>';

        // Мобильность
        html += '    <div class="hero-modal-stat-block">';
        html += '        <div class="hero-modal-stat-block-title">МОБИЛЬНОСТЬ</div>';
        html += '        <div class="hero-modal-stat-block-values">';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">' + (heroData.move_speed || '?') + '</div><div class="hero-modal-stat-item-label">СКОРОСТЬ</div></div>';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">1800</div><div class="hero-modal-stat-item-label">ОБЗОР (ДЕНЬ)</div></div>';
        html += '            <div class="hero-modal-stat-item"><div class="hero-modal-stat-item-value">800</div><div class="hero-modal-stat-item-label">ОБЗОР (НОЧЬ)</div></div>';
        html += '        </div>';
        html += '    </div>';
        html += '</div>';

        // ===== АТРИБУТЫ =====
        html += '<div class="hero-modal-attributes">';
        html += '    <div class="hero-modal-attribute-item"><span class="attr-label">СИЛА</span><span class="attr-value">' + (heroData.base_str || '?') + ' +' + (heroData.str_gain || '?') + '</span></div>';
        html += '    <div class="hero-modal-attribute-item"><span class="attr-label">ЛОВКОСТЬ</span><span class="attr-value">' + (heroData.base_agi || '?') + ' +' + (heroData.agi_gain || '?') + '</span></div>';
        html += '    <div class="hero-modal-attribute-item"><span class="attr-label">ИНТЕЛЛЕКТ</span><span class="attr-value">' + (heroData.base_int || '?') + ' +' + (heroData.int_gain || '?') + '</span></div>';
        html += '</div>';

        // ===== СПОСОБНОСТИ =====
        if (abilities && abilities.length > 0) {
            html += '<div class="hero-modal-abilities-title"><span>СПОСОБНОСТИ</span></div>';
            html += '<div class="hero-modal-abilities-grid" style="justify-content: center;">';

            for (var i = 0; i < abilities.length; i++) {
                var ability = abilities[i];
                var abilityName = ability.dname || 'Способность';
                var abilityDesc = ability.desc || ability.notes || 'Описание отсутствует';

                var imgSrc = ability.img || '';
                if (imgSrc && !imgSrc.startsWith('http')) {
                    imgSrc = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/' + imgSrc;
                }

                html += '<div class="hero-modal-ability">';
                html += '    <div class="hero-modal-ability-icon">';
                if (imgSrc) {
                    html += '        <img src="' + imgSrc + '" alt="' + abilityName + '" onerror="this.style.display=\'none\'">';
                }
                html += '    </div>';
                html += '    <div class="hero-modal-ability-name">' + abilityName + '</div>';
                html += '    <div class="hero-modal-ability-tooltip">';
                html += '        <div class="ability-tooltip-name">' + abilityName + '</div>';
                html += '        <div class="ability-tooltip-desc">' + abilityDesc + '</div>';
                
                if (ability.dmg || ability.mana_cost || ability.cooldown) {
                    html += '    <div class="ability-tooltip-details">';
                    if (ability.dmg) {
                        html += '        <div class="ability-tooltip-detail">Урон: <span>' + ability.dmg + '</span></div>';
                    }
                    if (ability.mana_cost) {
                        html += '        <div class="ability-tooltip-detail">Мана: <span>' + ability.mana_cost + '</span></div>';
                    }
                    if (ability.cooldown) {
                        html += '        <div class="ability-tooltip-detail">Перезарядка: <span>' + ability.cooldown + 'с</span></div>';
                    }
                    html += '    </div>';
                }
                
                html += '    </div>';
                html += '</div>';
            }

            html += '</div>';
        }

        modalBody.innerHTML = html;
    }

    function closeHeroModal() {
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    if (modalClose) {
        modalClose.addEventListener('click', closeHeroModal);
    }

    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closeHeroModal();
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeHeroModal();
    });

    // ============================================================
    // РЕНДЕР ГЕРОЕВ
    // ============================================================
    function getAttributeClass(attribute) {
        var classes = {
            'strength': 'strength',
            'agility': 'agility',
            'intelligence': 'intelligence',
            'universal': 'universal'
        };
        return classes[attribute] || '';
    }

    function renderHeroes() {
        if (!heroList) return;
        var filtered = [];
        for (var i = 0; i < uniqueHeroes.length; i++) {
            var hero = uniqueHeroes[i];
            var matchesFilter = currentFilter === 'all' || hero.attribute === currentFilter;
            var matchesSearch = hero.name.toLowerCase().indexOf(searchQuery.toLowerCase()) !== -1;
            if (matchesFilter && matchesSearch) {
                filtered.push(hero);
            }
        }

        if (filtered.length === 0) {
            heroList.innerHTML = '<div class="no-heroes"><p>Герои не найдены</p></div>';
            return;
        }

        var html = '';
        for (var i = 0; i < filtered.length; i++) {
            var hero = filtered[i];
            var iconFile = hero.icon + '.png';
            var attrClass = getAttributeClass(hero.attribute);

            html += '<div class="hero-item ' + attrClass + '" data-hero="' + hero.name + '" data-attribute="' + hero.attribute + '" data-icon="' + hero.icon + '" style="cursor:pointer;">';
            html += '    <div class="tilt-wrap">';
            html += '        <img src="/static/assets/icons/' + iconFile + '" alt="' + hero.name + '" loading="lazy" onerror="this.style.display=\'none\'; this.parentElement.innerHTML=\'<span style=\\\'font-size:2rem;color:#fff;display:flex;align-items:center;justify-content:center;height:100%;\\\'>' + hero.name.charAt(0) + '</span>\'">';
            html += '    </div>';
            html += '    <div class="hero-hover">';
            html += '        <div class="name">' + hero.name + '</div>';
            html += '    </div>';
            html += '</div>';
        }
        heroList.innerHTML = html;

        var items = document.querySelectorAll('.hero-item');
        for (var j = 0; j < items.length; j++) {
            var item = items[j];
            var heroIcon = item.dataset.icon;

            item.removeEventListener('click', item._clickHandler);
            
            item._clickHandler = function() {
                var icon = this.dataset.icon;
                console.log('🖱️ Клик по герою:', icon);
                if (icon) openHeroModal(icon);
            };
            item.addEventListener('click', item._clickHandler);

            var tiltWrap = item.querySelector('.tilt-wrap');
            item.addEventListener('mousemove', function(e) {
                var rect = this.getBoundingClientRect();
                var x = (e.clientX - rect.left) / rect.width;
                var y = (e.clientY - rect.top) / rect.height;
                var tiltWrap2 = this.querySelector('.tilt-wrap');
                if (tiltWrap2) {
                    var rotateX = (y - 0.5) * 25;
                    var rotateY = (x - 0.5) * -25;
                    tiltWrap2.style.transform = 'rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg)';
                }
                var shineX = x * 100;
                var shineY = y * 100;
                this.style.setProperty('--shine-x', shineX + '%');
                this.style.setProperty('--shine-y', shineY + '%');
            });
            item.addEventListener('mouseleave', function() {
                var tiltWrap3 = this.querySelector('.tilt-wrap');
                if (tiltWrap3) {
                    tiltWrap3.style.transform = 'rotateX(0) rotateY(0)';
                }
            });
        }
        
        console.log('✅ Рендер героев завершён, карточек:', items.length);
    }

    var filterBtns = document.querySelectorAll('.filter-btn');
    for (var k = 0; k < filterBtns.length; k++) {
        filterBtns[k].addEventListener('click', function() {
            var filterValue = this.dataset.filter;

            if (this.classList.contains('active')) {
                var allBtns = document.querySelectorAll('.filter-btn');
                for (var b = 0; b < allBtns.length; b++) {
                    allBtns[b].classList.remove('active');
                }
                currentFilter = 'all';
                attributeGlow.className = 'attribute-glow';
            } else {
                var allBtns2 = document.querySelectorAll('.filter-btn');
                for (var b2 = 0; b2 < allBtns2.length; b2++) {
                    allBtns2[b2].classList.remove('active');
                }
                this.classList.add('active');
                currentFilter = filterValue;
                attributeGlow.className = 'attribute-glow';
                if (currentFilter !== 'all') {
                    attributeGlow.classList.add(currentFilter);
                }
            }

            isTransitioning = true;
            heroList.style.opacity = '0';
            heroList.style.transform = 'scale(0.95)';
            setTimeout(function() {
                renderHeroes();
                heroList.style.opacity = '1';
                heroList.style.transform = 'scale(1)';
                setTimeout(function() {
                    isTransitioning = false;
                }, 300);
            }, 300);
        });
    }

    var searchInput = document.getElementById('heroSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            searchQuery = e.target.value;
            renderHeroes();
        });
    }

    var styleEl = document.createElement('style');
    styleEl.textContent = '.hero-grid { transition: opacity 0.3s ease, transform 0.3s ease; }';
    document.head.appendChild(styleEl);

    // ============================================================
    // ПЕРВЫЙ РЕНДЕР
    // ============================================================
    renderHeroes();

    // ============================================================
    // НАВИГАЦИЯ
    // ============================================================
    var navLinks = document.querySelectorAll('nav a');
    var pages = {
        home: document.getElementById('page-home'),
        heroes: document.getElementById('page-heroes'),
        items: document.getElementById('page-items'),
        news: document.getElementById('page-news'),
        guides: document.getElementById('page-guides')
    };

    function navigateTo(pageId) {
        var pageKeys = Object.keys(pages);
        for (var pk = 0; pk < pageKeys.length; pk++) {
            var key = pageKeys[pk];
            if (pages[key]) {
                pages[key].classList.remove('active');
            }
        }
        if (pages[pageId]) {
            pages[pageId].classList.add('active');
        }
        for (var nl = 0; nl < navLinks.length; nl++) {
            navLinks[nl].classList.remove('active');
            if (navLinks[nl].dataset.page === pageId) {
                navLinks[nl].classList.add('active');
            }
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    for (var nl2 = 0; nl2 < navLinks.length; nl2++) {
        navLinks[nl2].addEventListener('click', function(e) {
            e.preventDefault();
            var pageId = this.dataset.page;
            if (pageId) {
                navigateTo(pageId);
            }
        });
    }

    // ============================================================
    // КАСТОМНЫЙ КУРСОР
    // ============================================================
    var cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    document.body.appendChild(cursor);

    var targetX = 0;
    var targetY = 0;
    document.addEventListener('mousemove', function(e) {
        targetX = e.clientX;
        targetY = e.clientY;
        cursor.style.left = targetX + 'px';
        cursor.style.top = targetY + 'px';
    });

    if ('ontouchstart' in window) {
        cursor.style.display = 'none';
        document.body.style.cursor = 'default';
    }

    var hoverEls = document.querySelectorAll('a, button, .glass-card, .hero-item, .item-card, .guide-card, .news-card-vk');
    for (var he = 0; he < hoverEls.length; he++) {
        hoverEls[he].addEventListener('mouseenter', function() {
            cursor.classList.add('hover');
        });
        hoverEls[he].addEventListener('mouseleave', function() {
            cursor.classList.remove('hover');
        });
    }

    // ============================================================
    // ЧАСТИЦЫ
    // ============================================================
    var particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles';
    document.body.prepend(particlesContainer);

    var isMobile = window.innerWidth < 768;
    var particleCount = isMobile ? 5 : 12;
    var particleInterval = isMobile ? 800 : 300;

    function createParticle() {
        var particle = document.createElement('div');
        particle.className = 'particle';
        var size = Math.random() * 2 + 1;
        var left = Math.random() * 100;
        var duration = Math.random() * 15 + 10;
        var delay = Math.random() * 10;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.left = left + '%';
        particle.style.animationDuration = duration + 's';
        particle.style.animationDelay = delay + 's';
        particle.style.opacity = Math.random() * 0.3 + 0.1;
        particlesContainer.appendChild(particle);
        setTimeout(function() {
            particle.remove();
        }, (duration + delay) * 1000);
    }

    for (var pc = 0; pc < particleCount; pc++) {
        setTimeout(createParticle, pc * 100);
    }
    setInterval(createParticle, particleInterval);

    // ============================================================
    // СКРОЛЛ АНИМАЦИЯ
    // ============================================================
    var fadeElements = document.querySelectorAll('.scroll-fade');
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function(entries) {
            for (var fe = 0; fe < entries.length; fe++) {
                if (entries[fe].isIntersecting) {
                    entries[fe].target.classList.add('visible');
                }
            }
        }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });
        for (var fe2 = 0; fe2 < fadeElements.length; fe2++) {
            observer.observe(fadeElements[fe2]);
        }
    } else {
        for (var fe3 = 0; fe3 < fadeElements.length; fe3++) {
            fadeElements[fe3].classList.add('visible');
        }
    }

    console.log('🚀 Dota 2 Guide loaded');
})();