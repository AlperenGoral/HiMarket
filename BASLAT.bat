@echo off
title HI MARKET - POS VE YONETIM SISTEMI
cd /d "%~dp0"

echo ==========================================================
echo          HI MARKET - KASA VE YONETIM SISTEMI
echo ==========================================================
echo.
echo 1. Eski surecler temizleniyor...
taskkill /F /IM HiMarket.API.exe >nul 2>&1

echo 2. C# Backend API baslatiliyor (Port: 5000)...
if exist "%~dp0publish\HiMarket.API.exe" (
    start "" "%~dp0publish\HiMarket.API.exe"
)

echo 3. Tarayici acilisi hazirlaniyor...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000/login/'"

echo 4. Python Django Sunucusu baslatiliyor (Port: 8000)...
echo.
echo ==========================================================
echo   Sunucu aktif ediliyor!
echo   Bilgisayar Ekrani: http://127.0.0.1:8000/login/
echo   Telefon / Wi-Fi:   http://192.168.1.103:8000/login/
echo.
echo   BU PENCEREYI KAPATMAYINIZ!
echo ==========================================================
echo.

python manage.py runserver 0.0.0.0:8000

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Sunucu baslatilamadi!
    echo Lutfen acik pencereleri kontrol ediniz.
    pause
)
