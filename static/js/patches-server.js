const express = require('express');
const cors = require('cors');
const dota2 = require('dota2-datawrapper');

const app = express();
const PORT = process.env.PATCHES_PORT || 5001;

app.use(cors());
app.use(express.json());

// Получение списка всех патчей
app.get('/api/patches/list', async (req, res) => {
    try {
        const patches = await dota2.getPatchList();
        res.json(patches);
    } catch (error) {
        console.error('Ошибка получения списка патчей:', error);
        res.status(500).json({ error: 'Failed to fetch patches list' });
    }
});

// Получение деталей конкретного патча
app.get('/api/patches/:version', async (req, res) => {
    try {
        const version = req.params.version;
        const patchNotes = await dota2.getPatchNotes(version);
        res.json(patchNotes);
    } catch (error) {
        console.error(`Ошибка получения патча ${req.params.version}:`, error);
        res.status(500).json({ error: 'Failed to fetch patch notes' });
    }
});

// Получение последних патчей (для главной страницы)
app.get('/api/patches/latest/:count', async (req, res) => {
    try {
        const count = parseInt(req.params.count) || 6;
        const patches = await dota2.getPatchList();
        const latest = patches.slice(0, count);
        const result = [];
        
        for (const patch of latest) {
            try {
                const details = await dota2.getPatchNotes(patch.version);
                result.push({
                    version: patch.version,
                    date: patch.date,
                    type: patch.type || 'minor',
                    ...details
                });
            } catch (e) {
                console.warn(`Не удалось получить детали для ${patch.version}`);
                result.push({
                    version: patch.version,
                    date: patch.date,
                    type: patch.type || 'minor',
                    hero_changes: [],
                    item_changes: [],
                    neutral_item_changes: []
                });
            }
        }
        
        res.json(result);
    } catch (error) {
        console.error('Ошибка получения последних патчей:', error);
        res.status(500).json({ error: 'Failed to fetch latest patches' });
    }
});

app.listen(PORT, () => {
    console.log(`✅ Патч-сервер запущен на порту ${PORT}`);
});