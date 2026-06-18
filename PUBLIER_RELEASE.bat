@echo off
cd /d "%~dp0"
echo ============================================
echo  Envelop - Publier une mise a jour
echo ============================================
echo.
echo IMPORTANT : Avant de continuer, assure-toi d'avoir
echo augmente le numero dans version.py (ex: 1.2.0 -^> 1.3.0)
echo.
pause

for /f "delims=" %%v in ('python -c "from version import APP_VERSION; print(APP_VERSION)"') do set VERSION=%%v
echo.
echo Version a publier : %VERSION%
echo.

where gh >nul 2>&1
if errorlevel 1 set PATH=%PATH%;C:\Program Files\GitHub CLI

git tag -l "v%VERSION%" | findstr "v%VERSION%" >nul
if not errorlevel 1 (
    echo ERREUR : la version v%VERSION% existe deja sur GitHub.
    echo Augmente le numero dans version.py avant de publier.
    pause
    exit /b 1
)

echo [1/5] Fermeture d'Envelop en cours...
taskkill /IM Envelop.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul

echo [2/5] Compilation du nouveau .exe...
python -m PyInstaller --onefile --windowed --name "Envelop" --icon "icon.ico" --add-data "envelop_logo.svg;." --add-data "icon.ico;." main.py

if not exist "dist\Envelop.exe" (
    echo ERREUR : La compilation a echoue.
    pause
    exit /b 1
)
echo     OK - dist\Envelop.exe cree.

echo [3/5] Creation de l'installateur...
set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
    echo ERREUR : Inno Setup n'est pas installe.
    pause
    exit /b 1
)

%ISCC% /DAppVersion=%VERSION% Envelop_Installateur\envelop_setup.iss

if not exist "Envelop_Installateur\Envelop_Setup.exe" (
    echo ERREUR : La creation de l'installateur a echoue.
    pause
    exit /b 1
)
echo     OK - installateur cree.

echo [4/5] Publication du code source sur GitHub...
git add -A
git commit -m "Version %VERSION%" >nul 2>&1
git push origin main

echo [5/5] Creation de la release GitHub v%VERSION%...
gh release create v%VERSION% "Envelop_Installateur\Envelop_Setup.exe" --title "Envelop v%VERSION%" --notes "Mise a jour automatique vers la version %VERSION%."

if errorlevel 1 (
    echo ERREUR : La creation de la release GitHub a echoue.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Publication terminee !
echo  Tous les postes installes recevront
echo  automatiquement la mise a jour v%VERSION%
echo  au prochain demarrage d'Envelop (ou dans
echo  les 6 heures s'il tourne deja).
echo ============================================
pause
