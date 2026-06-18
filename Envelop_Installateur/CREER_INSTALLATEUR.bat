@echo off
echo ============================================
echo  Envelop - Creation de l'installateur
echo ============================================
echo.

set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist %ISCC% (
    echo ERREUR : Inno Setup n'est pas installe.
    echo.
    echo Telechargez-le sur : https://jrsoftware.org/isdl.php
    echo Puis relancez ce fichier.
    pause
    exit /b 1
)

echo Creation de l'installateur en cours...
%ISCC% envelop_setup.iss

if exist "Envelop_Setup.exe" (
    echo.
    echo ============================================
    echo  Succes ! Fichier cree : Envelop_Setup.exe
    echo  Envoyez ce fichier a vos employes.
    echo ============================================
    explorer .
) else (
    echo ERREUR lors de la creation.
)

pause
