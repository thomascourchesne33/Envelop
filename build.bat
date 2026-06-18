@echo off
echo === FC&F Modeles - Build ===

:: Install dependencies
pip install -r requirements.txt

:: Build executable
pyinstaller --onefile --windowed --name "FCF_Modeles" main.py

echo.
echo Build termine. Executable: dist\FCF_Modeles.exe
pause
