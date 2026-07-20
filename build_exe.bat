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
echo 2. Dang đóng gói piper_desktop_app.py thanh file EXE duy nhat...
py -m PyInstaller --noconsole --onefile piper_desktop_app.py --name "PiperDesktopReader"

echo.
echo 3. Dang copy cac file model va piper.exe sang thư muc dist...
if not exist "dist\piper" mkdir "dist\piper"
xcopy /E /I /Y "piper" "dist\piper"
copy /Y "*.onnx" "dist\"
copy /Y "*.json" "dist\"

echo.
echo =======================================================
echo   HOAN THANH! Thư muc dist da sẵn sang:
echo   -> Thư muc: dist\PiperDesktopReader.exe
echo =======================================================
pause
