@echo off
setlocal enabledelayedexpansion
title HI MARKET - POS VE YONETIM SISTEMI
cd /d "%~dp0"

echo ==========================================================
echo          HI MARKET - KASA VE YONETIM SISTEMI
echo ==========================================================
echo.

:: 1. Eski surecler temizleniyor
echo 1. Eski surecler kontrol ediliyor...
taskkill /F /IM HiMarket.API.exe >nul 2>&1

:: 2. Python kontrol ediliyor
set "PY_CMD="
where python >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=py"
    )
)

if "%PY_CMD%"=="" (
    echo.
    echo [HATA] Bilgisayarinizda Python kurulu bulunamadi!
    echo Lutfen https://www.python.org/downloads/ adresinden Python kurunuz.
    echo Kurulum yaparken "Add Python to PATH" secenegini isaretlemeyi unutmayiniz.
    echo.
    pause
    exit /b 1
)

:: 3. Python paketleri ve bagimlilik kontrolu
%PY_CMD% -c "import django, requests" >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo [BILGI] Ilk calistirma tespit edildi. Gerekli paketler yukleniyor...
    echo Bu islem bir defaya mahsustur, lutfen bekleyiniz...
    echo.
    %PY_CMD% -m pip install -r "%~dp0requirements.txt"
    if !errorlevel! neq 0 (
        echo [UYARI] Paket yuklemede sorun olustu, yine de devam ediliyor...
    )
    echo [BILGI] Veritabani tablolari guncelleniyor...
    %PY_CMD% "%~dp0manage.py" migrate
)

:: 4. C# Backend API baslatiliyor (Port: 5000)
echo.
echo 2. C# Backend API baslatiliyor (Port: 5000)...
if exist "%~dp0publish\HiMarket.API.exe" (
    start "HiMarket C# API" /d "%~dp0publish" "%~dp0publish\HiMarket.API.exe"
) else (
    where dotnet >nul 2>&1
    if !errorlevel! equ 0 (
        echo [BILGI] Publish exe bulunamadi, .NET SDK ile baslatiliyor...
        start "HiMarket C# API" dotnet run --project "%~dp0src\HiMarket.API\HiMarket.API.csproj"
    ) else (
        echo [BILGI] C# API baslatilamadi, sistem yerel Python modunda devam edecek.
    )
)

:: 5. Tarayici acilisi hazirlaniyor
echo 3. Tarayici acilisi hazirlaniyor...
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000/login/'"

:: 6. Wi-Fi Yerel IP Adresi Tespiti
set "LOCAL_IP="
for /f "usebackq tokens=*" %%a in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object InterfaceAlias -notlike '*Loopback*' | Where-Object IPAddress -like '192.168.*' | Select-Object -ExpandProperty IPAddress -First 1)"`) do set "LOCAL_IP=%%a"
if "%LOCAL_IP%"=="" set "LOCAL_IP=127.0.0.1"

echo.
echo 4. Python Django Sunucusu baslatiliyor (Port: 8000)...
echo.
echo ==========================================================
echo   Sunucu aktif ediliyor!
echo   Bilgisayar Ekrani: http://127.0.0.1:8000/login/
echo   Telefon / Wi-Fi:   http://%LOCAL_IP%:8000/login/
echo.
echo   BU PENCEREYI KAPATMAYINIZ!
echo ==========================================================
echo.

%PY_CMD% "%~dp0manage.py" runserver 0.0.0.0:8000

if !errorlevel! neq 0 (
    echo.
    echo [HATA] Sunucu baslatilamadi!
    echo Lutfen yukaridaki hata mesajini kontrol ediniz.
    pause
)
