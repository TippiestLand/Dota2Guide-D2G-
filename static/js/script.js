(function() {
    'use strict';

    // ============================================================
    // ЗАГРУЗКА СПИСКА ГЕРОЕВ С СЕРВЕРА
    // ============================================================
    var uniqueHeroes = [];
    var heroList = document.getElementById('heroList');
    var attributeGlow = document.getElementById('attributeGlow');
    var currentFilter = 'all';
    var searchQuery = '';
    var isTransitioning = false;

    function loadHeroesFromServer() {
        console.log('📡 Загрузка списка героев с сервера...');
        fetch('/api/heroes/list')
            .then(function(response) {
                if (!response.ok) throw new Error('Ошибка загрузки: ' + response.status);
                return response.json();
            })
            .then(function(data) {
                uniqueHeroes = data.map(function(hero) {
                    return {
                        name: hero.name,
                        attribute: hero.primary_attr || 'universal',
                        icon: hero.icon,
                        id: hero.id
                    };
                });
                // Сортируем по имени
                uniqueHeroes.sort(function(a, b) {
                    return a.name.localeCompare(b.name);
                });
                renderHeroes();
                console.log('✅ Загружено ' + uniqueHeroes.length + ' героев с сервера');
            })
            .catch(function(error) {
                console.error('❌ Ошибка загрузки героев:', error);
                heroList.innerHTML = '<div class="no-heroes"><p>⚠️ Не удалось загрузить героев. Проверьте соединение с сервером.</p></div>';
            });
    }

    // ============================================================
    // РЕНДЕР ГЕРОЕВ
    // ============================================================
    function getAttributeClass(attribute) {
        var classes = {
            'strength': 'strength',
            'agility': 'agility',
            'intelligence': 'intelligence',
            'universal': 'universal',
            'str': 'strength',
            'agi': 'agility',
            'int': 'intelligence'
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
            html += '        <img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/' + iconFile + '" alt="' + hero.name + '" loading="lazy" onerror="this.style.display=\'none\'">';
            html += '    </div>';
            html += '    <div class="hero-hover">';
            html += '        <div class="name">' + hero.name + '</div>';
            html += '    </div>';
            html += '</div>';
        }
        heroList.innerHTML = html;

        // Добавляем обработчики клика и эффекты
        var items = document.querySelectorAll('.hero-item');
        for (var j = 0; j < items.length; j++) {
            var item = items[j];
            var heroIcon = item.dataset.icon;
            
            // Обработчик клика
            item.addEventListener('click', function() {
                var icon = this.dataset.icon;
                console.log('🖱️ Клик по герою:', icon);
                if (icon) openHeroModal(icon);
            });

            // Эффект наклона
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
        modalBody.innerHTML = '<div class="hero-modal-loading"><div class="loader"></div><p>Загрузка данных...</p></div>';

        console.log('📡 Запрос данных для героя:', heroIcon);
        
        fetch('/api/hero/' + heroIcon)
            .then(function(response) {
                console.log('📡 Статус ответа:', response.status);
                if (!response.ok) {
                    throw new Error('Ошибка загрузки: ' + response.status);
                }
                return response.json();
            })
            .then(function(data) {
                console.log('✅ Данные героя получены');
                renderHeroModal(data, heroIcon);
            })
            .catch(function(error) {
                console.error('❌ Ошибка:', error);
                modalBody.innerHTML = '' +
                    '<div style="text-align:center; padding:40px 20px;">' +
                    '    <p style="color:#ff6b6b; font-size:1.2rem; margin-bottom:12px;">❌ Не удалось загрузить данные героя</p>' +
                    '    <p style="color:#888; font-size:0.9rem;">Попробуйте позже или выберите другого героя</p>' +
                    '    <button onclick="closeHeroModal()" style="margin-top:20px; padding:10px 30px; border-radius:8px; border:1px solid #f0b90b; background:transparent; color:#f0b90b; cursor:pointer;">Закрыть</button>' +
                    '</div>';
            });
    }

    function renderHeroModal(data, heroIcon) {
        var heroData = data.data;
        var abilities = data.abilities || [];

        if (!heroData) {
            modalBody.innerHTML = '<p style="color:#ff6b6b; text-align:center; padding:20px;">Ошибка: данные героя не загружены</p>';
            return;
        }

        // Определяем атрибут
        var primaryAttr = heroData.primary_attr || 'universal';
        var attrClass = {
            'str': 'strength',
            'agi': 'agility',
            'int': 'intelligence',
            'universal': 'universal'
        }[primaryAttr] || 'universal';

        var attrName = {
            'str': 'СИЛА',
            'agi': 'ЛОВКОСТЬ',
            'int': 'ИНТЕЛЛЕКТ',
            'universal': 'УНИВЕРСАЛЬНЫЙ'
        }[primaryAttr] || 'УНИВЕРСАЛЬНЫЙ';

        var heroName = heroData.localized_name || heroIcon;
        var heroImage = heroIcon + '.png';

        // Строим HTML
        var html = '';

        // Верхняя часть с атрибутом и именем
        html += '<div class="hero-modal-header">';
        html += '    <div class="hero-modal-attribute-badge ' + attrClass + '">' + attrName + '</div>';
        html += '    <div class="hero-modal-name">' + heroName + '</div>';
        html += '</div>';

        // Аватар и краткое описание
        html += '<div class="hero-modal-main">';
        html += '    <div class="hero-modal-avatar">';
        html += '        <img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/' + heroImage + '" alt="' + heroName + '" onerror="this.src=\'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect width=\'200\' height=\'200\' fill=\'%23222\'/%3E%3Ctext x=\'100\' y=\'110\' text-anchor=\'middle\' fill=\'%23666\' font-size=\'20\'%3E' + heroName.charAt(0) + '%3C/text%3E%3C/svg%3E\'">';
        html += '    </div>';
        html += '    <div class="hero-modal-bio">';
        
        var bioText = heroData.bio || 'Описание героя временно недоступно.';
        html += '        <p>' + bioText + '</p>';
        
        html += '        <div class="hero-modal-tags">';
        html += '            <span class="tag">' + (heroData.attack_type || 'Ближний бой') + '</span>';
        html += '            <span class="tag">Сложность: ' + (heroData.roles ? heroData.roles.length : 'Средняя') + '</span>';
        html += '        </div>';
        html += '    </div>';
        html += '</div>';

        // Статистика
        html += '<div class="hero-modal-stats">';
        html += '    <div class="stat-block">';
        html += '        <div class="stat-label">АТРИБУТЫ</div>';
        html += '        <div class="stat-values">';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.base_str || '?') + '</span><span class="stat-sub">+ ' + (heroData.str_gain || '?') + '</span><span class="stat-label-small">СИЛА</span></div>';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.base_agi || '?') + '</span><span class="stat-sub">+ ' + (heroData.agi_gain || '?') + '</span><span class="stat-label-small">ЛОВКОСТЬ</span></div>';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.base_int || '?') + '</span><span class="stat-sub">+ ' + (heroData.int_gain || '?') + '</span><span class="stat-label-small">ИНТЕЛЛЕКТ</span></div>';
        html += '        </div>';
        html += '    </div>';
        html += '    <div class="stat-block">';
        html += '        <div class="stat-label">ПОКАЗАТЕЛИ</div>';
        html += '        <div class="stat-values">';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.base_health || '?') + '</span><span class="stat-label-small">ЗДОРОВЬЕ</span></div>';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.base_mana || '?') + '</span><span class="stat-label-small">МАНА</span></div>';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.move_speed || '?') + '</span><span class="stat-label-small">СКОРОСТЬ</span></div>';
        html += '        </div>';
        html += '    </div>';
        html += '    <div class="stat-block">';
        html += '        <div class="stat-label">АТАКА</div>';
        html += '        <div class="stat-values">';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.base_attack_min || '?') + '-' + (heroData.base_attack_max || '?') + '</span><span class="stat-label-small">УРОН</span></div>';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.attack_rate || '?') + '</span><span class="stat-label-small">СКОРОСТЬ</span></div>';
        html += '            <div class="stat-item"><span class="stat-value">' + (heroData.attack_range || '?') + '</span><span class="stat-label-small">ДАЛЬНОСТЬ</span></div>';
        html += '        </div>';
        html += '    </div>';
        html += '</div>';

        // Способности
        if (abilities && abilities.length > 0) {
            html += '<div class="hero-modal-abilities-title">СПОСОБНОСТИ</div>';
            html += '<div class="hero-modal-abilities-grid">';

            for (var i = 0; i < abilities.length; i++) {
                var ability = abilities[i];
                var abilityName = ability.dname || 'Способность';
                var abilityDesc = ability.desc || ability.notes || 'Описание отсутствует';
                
                var imgSrc = ability.img || '';
                if (imgSrc && !imgSrc.startsWith('http')) {
                    imgSrc = 'https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/' + imgSrc;
                }

                html += '<div class="ability-card">';
                html += '    <div class="ability-card-icon">';
                if (imgSrc) {
                    html += '        <img src="' + imgSrc + '" alt="' + abilityName + '" onerror="this.style.display=\'none\'">';
                }
                html += '    </div>';
                html += '    <div class="ability-card-info">';
                html += '        <div class="ability-card-name">' + abilityName + '</div>';
                html += '        <div class="ability-card-desc">' + abilityDesc + '</div>';
                
                if (ability.dmg || ability.mana_cost || ability.cooldown) {
                    html += '        <div class="ability-card-details">';
                    if (ability.dmg) {
                        html += '            <span class="ability-detail">Урон: <strong>' + ability.dmg + '</strong></span>';
                    }
                    if (ability.mana_cost) {
                        html += '            <span class="ability-detail">Мана: <strong>' + ability.mana_cost + '</strong></span>';
                    }
                    if (ability.cooldown) {
                        html += '            <span class="ability-detail">Перезарядка: <strong>' + ability.cooldown + 'с</strong></span>';
                    }
                    html += '        </div>';
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
    // ФИЛЬТРЫ И ПОИСК
    // ============================================================
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

    // ============================================================
    // ЗАПУСК
    // ============================================================
    loadHeroesFromServer();

    console.log('🚀 Dota 2 Guide loaded');
})();