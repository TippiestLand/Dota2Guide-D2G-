// ===== js/auth.js =====
(function() {
    'use strict';

    const authModal = document.getElementById('authModal');
    const openAuthBtn = document.getElementById('openAuth');
    const closeAuthBtn = document.getElementById('closeAuth');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const authTabs = document.querySelectorAll('.auth-tab');

    let currentUser = null;
    let currentToken = null;

    // ===== УВЕДОМЛЕНИЯ =====
    function showNotification(text, type = 'success') {
        const old = document.querySelector('.auth-notification');
        if (old) old.remove();
        const notif = document.createElement('div');
        notif.className = 'auth-notification';
        notif.style.cssText = `
            position: fixed; top: 80px; left: 50%; transform: translateX(-50%);
            padding: 16px 32px; border-radius: 12px;
            background: ${type === 'success' ? 'rgba(78, 205, 196, 0.95)' : 'rgba(255, 107, 107, 0.95)'};
            color: #fff; font-weight: 600; font-size: 1.1rem; z-index: 10000;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            animation: slideDown 0.5s ease forwards;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        `;
        notif.textContent = text;
        document.body.appendChild(notif);
        setTimeout(() => {
            notif.style.animation = 'slideUp 0.5s ease forwards';
            setTimeout(() => notif.remove(), 500);
        }, 3000);
    }

    // ===== ОБНОВЛЕНИЕ UI =====
    function updateUI(user) {
        if (user) {
            currentUser = user;
            localStorage.setItem('user', JSON.stringify(user));
            localStorage.setItem('token', user.token);
            openAuthBtn.textContent = user.username;
            openAuthBtn.style.borderColor = '#4ecdc4';
            
            const adminBtn = document.getElementById('adminBtn');
            if (adminBtn && user.role === 'admin') {
                adminBtn.style.display = 'block';
            }
            
            authModal.classList.remove('active');
            if (window.fetchNews) window.fetchNews();
            showNotification(`👋 Добро пожаловать, ${user.username}!`, 'success');
        } else {
            currentUser = null;
            localStorage.removeItem('user');
            localStorage.removeItem('token');
            openAuthBtn.textContent = 'Вход';
            openAuthBtn.style.borderColor = '';
            const adminBtn = document.getElementById('adminBtn');
            if (adminBtn) adminBtn.style.display = 'none';
        }
    }

    // ===== ПРОВЕРКА СОХРАНЁННОГО ПОЛЬЗОВАТЕЛЯ =====
    function checkSavedUser() {
        try {
            const saved = localStorage.getItem('user');
            const token = localStorage.getItem('token');
            if (saved && token) {
                const user = JSON.parse(saved);
                fetch('/api/verify', {
                    headers: { 'X-Admin-Auth': token }
                })
                .then(res => res.json())
                .then(data => {
                    if (data.valid) {
                        updateUI({ ...user, token: token });
                    } else {
                        updateUI(null);
                    }
                })
                .catch(() => updateUI(null));
            }
        } catch (e) {
            updateUI(null);
        }
    }

    // ===== ОТКРЫТЬ/ЗАКРЫТЬ МОДАЛКУ =====
    function openAuth() {
        authModal.classList.add('active');
        document.getElementById('loginEmail').value = '';
        document.getElementById('loginPassword').value = '';
        document.getElementById('regUsername').value = '';
        document.getElementById('regEmail').value = '';
        document.getElementById('regPassword').value = '';
        document.getElementById('regConfirm').value = '';
    }

    function closeAuth() {
        authModal.classList.remove('active');
    }

    // ===== РЕГИСТРАЦИЯ =====
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('regUsername').value.trim();
        const email = document.getElementById('regEmail').value.trim();
        const password = document.getElementById('regPassword').value;
        const confirm = document.getElementById('regConfirm').value;

        if (password !== confirm) {
            showNotification('❌ Пароли не совпадают!', 'error');
            return;
        }
        if (password.length < 6) {
            showNotification('❌ Пароль должен быть минимум 6 символов', 'error');
            return;
        }

        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });
            const data = await res.json();
            if (res.ok) {
                closeAuth();
                updateUI({
                    username: data.user.username,
                    email: data.user.email,
                    role: data.user.role,
                    token: data.token
                });
                setTimeout(() => {
                    document.querySelector('[data-page="home"]')?.click();
                }, 500);
            } else {
                showNotification('❌ ' + (data.error || 'Ошибка регистрации'), 'error');
            }
        } catch (e) {
            showNotification('❌ Ошибка соединения с сервером', 'error');
        }
    });

    // ===== ВХОД =====
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const username = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (res.ok) {
                closeAuth();
                updateUI({
                    username: data.user.username,
                    email: data.user.email,
                    role: data.user.role,
                    token: data.token
                });
                setTimeout(() => {
                    document.querySelector('[data-page="home"]')?.click();
                }, 500);
            } else {
                showNotification('❌ ' + (data.error || 'Ошибка входа'), 'error');
            }
        } catch (e) {
            showNotification('❌ Ошибка соединения с сервером', 'error');
        }
    });

    // ===== ВЫХОД =====
    window.logout = async function() {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                await fetch('/api/logout', {
                    method: 'POST',
                    headers: { 'X-Admin-Auth': token }
                });
            } catch (e) {}
        }
        updateUI(null);
        showNotification('👋 Вы вышли из аккаунта', 'success');
    };

    // ===== ПЕРЕКЛЮЧЕНИЕ ТАБОВ =====
    authTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            authTabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            const tabName = this.dataset.tab;
            if (tabName === 'login') {
                loginForm.classList.add('active');
                registerForm.classList.remove('active');
                document.getElementById('authTitle').textContent = 'Добро пожаловать';
                document.getElementById('authSubtitle').textContent = 'Войдите в аккаунт';
            } else {
                registerForm.classList.add('active');
                loginForm.classList.remove('active');
                document.getElementById('authTitle').textContent = 'Создать аккаунт';
                document.getElementById('authSubtitle').textContent = 'Присоединяйтесь к Dota Guide';
            }
        });
    });

    // ===== СОБЫТИЯ =====
    openAuthBtn.addEventListener('click', function() {
        if (currentUser) {
            if (confirm('Выйти из аккаунта?')) {
                window.logout();
            }
        } else {
            openAuth();
        }
    });

    closeAuthBtn.addEventListener('click', closeAuth);
    authModal.addEventListener('click', (e) => {
        if (e.target === authModal) closeAuth();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeAuth();
    });

    // ===== СТИЛИ ДЛЯ УВЕДОМЛЕНИЙ =====
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown { 0% { opacity: 0; transform: translateX(-50%) translateY(-30px); } 100% { opacity: 1; transform: translateX(-50%) translateY(0); } }
        @keyframes slideUp { 0% { opacity: 1; transform: translateX(-50%) translateY(0); } 100% { opacity: 0; transform: translateX(-50%) translateY(-30px); } }
    `;
    document.head.appendChild(style);

    // ===== ИНИЦИАЛИЗАЦИЯ =====
    checkSavedUser();

})();