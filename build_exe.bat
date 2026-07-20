@echo off
title Build Standalone EXE - Piper AI Desktop Reader
color 0B
echo =======================================================
echo   Đang Tạo File PiperDesktopReader.exe Standalone
echo =======================================================
echo.
echo 1. Dang kiem tra PyInstaller & Pygame...
py -m pip install pygame edge-tts pyinstaller

echo.
echo 2. Dang dong goi piper_desktop_app.py thanh file EXE duy nhat...
py -m PyInstaller --noconsole --onefile piper_desktop_app.py --name "PiperDesktopReader"

echo.
echo =======================================================
echo   HOAN THANH! File PiperDesktopReader.exe da đuoc tao:
echo   -> File EXE: dist\PiperDesktopReader.exe
echo =======================================================
pause
