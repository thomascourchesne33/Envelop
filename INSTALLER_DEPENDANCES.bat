@echo off
echo ============================================
echo  FC^&F Modeles - Installation des dependances
echo ============================================
echo.

:: Verify Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe.
    echo.
    echo Installez Python 3.11+ depuis : https://www.python.org/downloads/
    echo Cochez "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)

echo Python detecte :
python --version
echo.

echo Installation des dependances...
python -m pip install --upgrade pip
python -m pip install PyQt6>=6.6.0 keyboard>=0.13.5 openpyxl>=3.1.2 pywin32>=306 watchdog>=4.0.0

echo.
echo Dependances installee avec succes !
echo.
echo Pour lancer l'application :
echo   python main.py
echo.
echo Pour compiler en .exe :
echo   python -m pip install pyinstaller
echo   pyinstaller --onefile --windowed --name "FCF_Modeles" main.py
echo.
pause
