(function() {
    'use strict';

    const API_URL = '/api';
    let adminToken = null;
    let isAdmin = false;

    function showToast(message, type = 'success') {
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            toast.style.cssText = `
                position: fixed; bottom: 30px; right: 30px;
                padding: 14px 24px; border-radius: 10px;
                background: #2d2d3d; border: 1px solid rgba(240,185,11,0.3);
                color: #fff; opacity: 0; transition: opacity 0.3s ease;
                z-index: 9999;
            `;
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.style.borderColor = type === 'success' ? '#4ecdc4' : '#ff6b6b';
        toast.style.opacity = '1';
        clearTimeout(toast._timeout);
        toast._timeout = setTimeout(() => { toast.style.opacity = '0'; }, 3000);
    }

    async function checkAdminStatus() {
        try {
            const token = localStorage.getItem('adminToken');
            if (!token) return false;
            const res = await fetch(API_URL + '/admin/verify', {
                headers: { 'X-Admin-Auth': token }
            });
            if (res.ok) {
                adminToken = token;
                isAdmin = true;
                return true;
            }
        } catch (e) {}
        return false;
    }

    function showAdminPanel(show) {
        const panel = document.getElementById('adminPanel');
        const adminBtn = document.getElementById('adminBtn');
        if (panel) panel.style.display = show ? 'block' : 'none';
        if (adminBtn) {
            adminBtn.textContent = show ? '🚪 Выйти' : '🔐 Админка';
            adminBtn.style.borderColor = show ? '#ff6b6b' : '#4ecdc4';
            adminBtn.style.color = show ? '#ff6b6b' : '#4ecdc4';
        }
        if (show) loadAdminNews();
    }

    async function loadAdminNews() {
        const list = document.getElementById('adminNewsList');
        const count = document.getElementById('newsCount');
        if (!list) return;
        try {
            const res = await fetch(API_URL + '/news');
            const data = await res.json();
            if (count) count.textContent = `(${data.length})`;
            if (!data || data.length === 0) {
                list.innerHTML = '<p style="color:#888; text-align:center; padding:10px;">Новостей нет</p>';
                return;
            }
            list.innerHTML = data.map(n => `
                <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.03); border-radius:8px; padding:10px 14px; margin-bottom:6px; border-left:3px solid ${n.source === 'rss' ? '#4ecdc4' : '#f0b90b'};">
                    <div style="flex:1; min-width:0;">
                        <div style="font-weight:500; font-size:0.85rem; color:#e8e6e3; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${escapeHtml(n.title)}</div>
                        <div style="font-size:0.65rem; color:#888;">
                            ${n.date} · ${n.source === 'rss' ? '📡 RSS' : '✏️ Ручная'}
                        </div>
                    </div>
                    <button class="delete-news-btn" data-id="${n.id}" style="padding:4px 14px; border-radius:6px; border:1px solid #ff6b6b; background:transparent; color:#ff6b6b; cursor:pointer; font-size:0.7rem; flex-shrink:0;">Удалить</button>
                </div>
            `).join('');
            list.querySelectorAll('.delete-news-btn').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const id = this.dataset.id;
                    if (!confirm('Удалить новость?')) return;
                    try {
                        const res = await fetch(API_URL + '/news/' + id, {
                            method: 'DELETE',
                            headers: { 'X-Admin-Auth': adminToken }
                        });
                        if (res.ok) {
                            showToast('Новость удалена');
                            loadAdminNews();
                            if (window.refreshNews) window.refreshNews();
                        } else {
                            showToast('Ошибка удаления', 'error');
                        }
                    } catch (e) {
                        showToast('Ошибка', 'error');
                    }
                });
            });
        } catch (e) {
            list.innerHTML = '<p style="color:#888; text-align:center; padding:10px;">Ошибка загрузки</p>';
        }
    }

    async function addNews(title, content, type, link) {
        try {
            const res = await fetch(API_URL + '/news', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Admin-Auth': adminToken
                },
                body: JSON.stringify({ title, content, type, link })
            });
            const data = await res.json();
            if (res.ok) {
                showToast('Новость добавлена!');
                loadAdminNews();
                if (window.refreshNews) window.refreshNews();
                return true;
            } else {
                showToast(data.error || 'Ошибка', 'error');
                return false;
            }
        } catch (e) {
            showToast('Ошибка соединения', 'error');
            return false;
        }
    }

    async function updateRSS() {
        try {
            const res = await fetch(API_URL + '/admin/update_rss', {
                method: 'POST',
                headers: { 'X-Admin-Auth': adminToken }
            });
            const data = await res.json();
            if (res.ok) {
                showToast(`📡 Добавлено ${data.added || 0} новостей из RSS`);
                loadAdminNews();
                if (window.refreshNews) window.refreshNews();
            } else {
                showToast('Ошибка обновления RSS', 'error');
            }
        } catch (e) {
            showToast('Ошибка соединения', 'error');
        }
    }

    async function adminLogin(username, password) {
        try {
            const res = await fetch(API_URL + '/admin/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (res.ok) {
                adminToken = data.token;
                isAdmin = true;
                localStorage.setItem('adminToken', adminToken);
                document.getElementById('adminAuthModal').classList.remove('active');
                showAdminPanel(true);
                showToast('Вход в админ-панель выполнен!');
                return true;
            } else {
                document.getElementById('adminLoginError').style.display = 'block';
                return false;
            }
        } catch (e) {
            document.getElementById('adminLoginError').style.display = 'block';
            return false;
        }
    }

    function adminLogout() {
        adminToken = null;
        isAdmin = false;
        localStorage.removeItem('adminToken');
        showAdminPanel(false);
        showToast('Выход из админ-панели');
    }

    document.addEventListener('DOMContentLoaded', function() {
        checkAdminStatus().then(admin => { if (admin) showAdminPanel(true); });

        const adminBtn = document.getElementById('adminBtn');
        if (adminBtn) {
            adminBtn.addEventListener('click', function() {
                if (isAdmin) { adminLogout(); }
                else {
                    document.getElementById('adminAuthModal').classList.add('active');
                    document.getElementById('adminLoginError').style.display = 'none';
                }
            });
        }

        document.getElementById('closeAdminAuth').addEventListener('click', () => {
            document.getElementById('adminAuthModal').classList.remove('active');
            document.getElementById('adminLoginError').style.display = 'none';
        });

        document.getElementById('adminAuthModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                document.getElementById('adminAuthModal').classList.remove('active');
                document.getElementById('adminLoginError').style.display = 'none';
            }
        });

        document.getElementById('adminLoginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const login = document.getElementById('adminLogin').value;
            const password = document.getElementById('adminPassword').value;
            adminLogin(login, password);
        });

        document.getElementById('addNewsBtn').addEventListener('click', function() {
            const title = document.getElementById('newsTitle').value.trim();
            const content = document.getElementById('newsContent').value.trim();
            const type = document.getElementById('newsType').value;
            const link = document.getElementById('newsLink').value.trim();
            if (!title || !content) {
                showToast('Заполните заголовок и текст', 'error');
                return;
            }
            addNews(title, content, type, link).then(success => {
                if (success) {
                    document.getElementById('newsTitle').value = '';
                    document.getElementById('newsContent').value = '';
                    document.getElementById('newsLink').value = '';
                }
            });
        });

        document.getElementById('updateRssBtn').addEventListener('click', function() {
            updateRSS();
        });

        window.refreshNews = function() {
            if (window.fetchNews) window.fetchNews();
        };
    });

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
})();