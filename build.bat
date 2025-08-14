@echo off
REM Install PyInstaller if not already installed
pip install pyinstaller

REM Build EXE with icon and no console window
pyinstaller --noconfirm --onefile --windowed ^
    --icon=assets/icon.ico ^
    run_breathe3.py

echo.
echo Build complete! Your EXE is in the "dist" folder.
pause
