@echo off
cd /d "%~dp0"
echo ============================================
echo  Envelop - Mise a jour
echo ============================================
echo.

:: ── 1. Fermer l'application si elle tourne ──────────────────────────────────
echo [1/3] Fermeture d'Envelop en cours...
taskkill /IM Envelop.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul

:: ── 2. Recompiler le .exe ───────────────────────────────────────────────────
echo [2/3] Compilation du nouveau .exe...
python -m PyInstaller --onefile --windowed --name "Envelop" --icon "icon.ico" --add-data "envelop_logo.svg;." --add-data "icon.ico;." main.py

if not exist "dist\Envelop.exe" (
    echo.
    echo ERREUR : La compilation a echoue.
    pause
    exit /b 1
)
echo     OK - dist\Envelop.exe cree.

:: ── 3. Recompiler l'installateur ────────────────────────────────────────────
echo [3/3] Creation du nouvel installateur...

set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
    echo ERREUR : Inno Setup n'est pas installe.
    echo Telechargez-le sur : https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

%ISCC% Envelop_Installateur\envelop_setup.iss

if exist "Envelop_Installateur\Envelop_Setup.exe" (
    echo.
    echo ============================================
    echo  Mise a jour terminee !
    echo.
    echo  Fichier a envoyer aux employes :
    echo  Envelop_Installateur\Envelop_Setup.exe
    echo ============================================
    explorer Envelop_Installateur
) else (
    echo ERREUR : La creation de l'installateur a echoue.
)

pause
