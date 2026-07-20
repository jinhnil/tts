@echo off
title Build Standalone EXE - Piper TTS Reader
color 0B
echo =======================================================
echo   Tao File PiperTTSReader.exe Standalone Đoc Sách 
echo =======================================================
echo.
echo 1. Dang cai dat PyInstaller...
pip install pyinstaller

echo.
echo 2. Dang dong goi piper_app.py thanh file EXE duy nhat...
pyinstaller --noconsole --onefile piper_app.py --name "PiperTTSReader"

echo.
echo =======================================================
echo   HOAN THANH! File PiperTTSReader.exe da đuoc tao:
echo   -> Thư muc: dist\PiperTTSReader.exe
echo =======================================================
pause
