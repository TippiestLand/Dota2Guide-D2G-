(function() {
    'use strict';

    const heroesData = [
        // ===== СИЛА =====
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
        { name: 'Largo', attribute: 'strength', icon: 'largo' },
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
        
        // ===== ЛОВКОСТЬ =====
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
        { name: 'Kez', attribute: 'agility', icon: 'kez' },
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
        
        // ===== ИНТЕЛЛЕКТ =====
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
        
        // ===== УНИВЕРСАЛЬНЫЕ =====
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
        { name: 'Nature\'s Prophet', attribute: 'universal', icon: 'furion' },
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

    const heroMap = new Map();
    heroesData.forEach(hero => {
        if (heroMap.has(hero.name)) {
            const existing = heroMap.get(hero.name);
            if (hero.attribute === 'universal') heroMap.set(hero.name, hero);
        } else {
            heroMap.set(hero.name, hero);
        }
    });
    
    const uniqueHeroes = Array.from(heroMap.values());
    uniqueHeroes.sort((a, b) => a.name.localeCompare(b.name));

    const heroList = document.getElementById('heroList');
    const attributeGlow = document.getElementById('attributeGlow');
    let currentFilter = 'all';
    let searchQuery = '';
    let isTransitioning = false;

    function getAttributeClass(attribute) {
        const classes = { 'strength': 'strength', 'agility': 'agility', 'intelligence': 'intelligence', 'universal': 'universal' };
        return classes[attribute] || '';
    }

    function renderHeroes() {
        const filtered = uniqueHeroes.filter(hero => {
            const matchesFilter = currentFilter === 'all' || hero.attribute === currentFilter;
            const matchesSearch = hero.name.toLowerCase().includes(searchQuery.toLowerCase());
            return matchesFilter && matchesSearch;
        });

        if (filtered.length === 0) {
            heroList.innerHTML = `<div class="no-heroes"><p>Герои не найдены</p></div>`;
            return;
        }

        heroList.innerHTML = filtered.map(hero => {
            const iconFile = hero.icon + '.png';
            const attrClass = getAttributeClass(hero.attribute);
            return `
                <div class="hero-item ${attrClass}" data-hero="${hero.name}" data-attribute="${hero.attribute}">
                    <div class="tilt-wrap">
                        <img src="/assets/icons/${iconFile}" alt="${hero.name}" loading="lazy" 
                             onerror="this.style.display='none'; this.parentElement.innerHTML='<span style=\\'font-size:2rem;color:#fff;display:flex;align-items:center;justify-content:center;height:100%;\\'>${hero.name.charAt(0)}</span>'">
                    </div>
                    <div class="hero-hover">
                        <div class="name">${hero.name}</div>
                    </div>
                </div>
            `;
        }).join('');

        document.querySelectorAll('.hero-item').forEach(item => {
            const tiltWrap = item.querySelector('.tilt-wrap');
            item.addEventListener('mousemove', (e) => {
                const rect = item.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width;
                const y = (e.clientY - rect.top) / rect.height;
                if (tiltWrap) {
                    const rotateX = (y - 0.5) * 25;
                    const rotateY = (x - 0.5) * -25;
                    tiltWrap.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
                }
                const shineX = x * 100;
                const shineY = y * 100;
                item.style.setProperty('--shine-x', shineX + '%');
                item.style.setProperty('--shine-y', shineY + '%');
            });
            item.addEventListener('mouseleave', () => {
                if (tiltWrap) tiltWrap.style.transform = 'rotateX(0) rotateY(0)';
            });
        });
    }

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const filterValue = btn.dataset.filter;
            if (btn.classList.contains('active')) {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                currentFilter = 'all';
                attributeGlow.className = 'attribute-glow';
                isTransitioning = true;
                heroList.style.opacity = '0';
                heroList.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    renderHeroes();
                    heroList.style.opacity = '1';
                    heroList.style.transform = 'scale(1)';
                    setTimeout(() => { isTransitioning = false; }, 300);
                }, 300);
                return;
            }
            if (isTransitioning) return;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = filterValue;
            attributeGlow.className = 'attribute-glow';
            if (currentFilter !== 'all') attributeGlow.classList.add(currentFilter);
            isTransitioning = true;
            heroList.style.opacity = '0';
            heroList.style.transform = 'scale(0.95)';
            setTimeout(() => {
                renderHeroes();
                heroList.style.opacity = '1';
                heroList.style.transform = 'scale(1)';
                setTimeout(() => { isTransitioning = false; }, 300);
            }, 300);
        });
    });

    const style = document.createElement('style');
    style.textContent = `.hero-grid { transition: opacity 0.3s ease, transform 0.3s ease; }`;
    document.head.appendChild(style);

    document.getElementById('heroSearch').addEventListener('input', (e) => {
        searchQuery = e.target.value;
        renderHeroes();
    });

    renderHeroes();

    const cursor = document.createElement('div');
    cursor.className = 'custom-cursor';
    document.body.appendChild(cursor);

    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
    });

    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles';
    document.body.prepend(particlesContainer);

    function createParticle() {
        const particle = document.createElement('div');
        particle.className = 'particle';
        const size = Math.random() * 3 + 1;
        const left = Math.random() * 100;
        const duration = Math.random() * 20 + 15;
        const delay = Math.random() * 10;
        particle.style.width = size + 'px';
        particle.style.height = size + 'px';
        particle.style.left = left + '%';
        particle.style.animationDuration = duration + 's';
        particle.style.animationDelay = delay + 's';
        particle.style.opacity = Math.random() * 0.5 + 0.1;
        particlesContainer.appendChild(particle);
        setTimeout(() => { particle.remove(); }, (duration + delay) * 1000);
    }
    setInterval(createParticle, 200);

    const navLinks = document.querySelectorAll('nav a');
    const pages = {
        home: document.getElementById('page-home'),
        heroes: document.getElementById('page-heroes'),
        items: document.getElementById('page-items'),
        news: document.getElementById('page-news'),
        guides: document.getElementById('page-guides')
    };

    function navigateTo(pageId) {
        Object.values(pages).forEach(page => { if (page) page.classList.remove('active'); });
        if (pages[pageId]) pages[pageId].classList.add('active');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.dataset.page === pageId) link.classList.add('active');
        });
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = link.dataset.page;
            if (pageId) navigateTo(pageId);
        });
    });

    document.querySelectorAll('[data-page]').forEach(el => {
        el.addEventListener('click', (e) => {
            e.preventDefault();
            const pageId = el.dataset.page;
            if (pageId) navigateTo(pageId);
        });
    });

    const authModal = document.getElementById('authModal');
    const openAuth = document.getElementById('openAuth');
    const closeAuth = document.getElementById('closeAuth');
    const authTabs = document.querySelectorAll('.auth-tab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // Авторизация уже обрабатывается в auth.js

    const fadeElements = document.querySelectorAll('.scroll-fade');
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) entry.target.classList.add('visible');
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });
        fadeElements.forEach(el => observer.observe(el));
    } else {
        fadeElements.forEach(el => el.classList.add('visible'));
    }

    console.log('Dota 2 Guide loaded successfully');

    if (localStorage.getItem('dotaGuideVisits')) {
        let visits = parseInt(localStorage.getItem('dotaGuideVisits')) + 1;
        localStorage.setItem('dotaGuideVisits', visits);
    } else {
        localStorage.setItem('dotaGuideVisits', '1');
    }
})();