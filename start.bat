@echo off
chcp 65001 >nul
title Dota 2 Guide
echo ========================================
echo    DOTA 2 GUIDE — ЗАПУСК
echo ========================================
echo.
echo 🚀 Запускаю сервер...
echo.
echo 🌐 Сайт: http://localhost:8000
echo 🔗 API:  http://localhost:8000/api/news
echo 👤 Логин: admin
echo 🔑 Пароль: admin123
echo.
echo Для остановки нажми CTRL+C
echo.
python api_server.py
pause