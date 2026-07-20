@echo off
title Build Standalone EXE - Đọc Truyện AI Pro (VietVoice Studio)
color 0B
echo =======================================================
echo   Đang Tạo File DocTruyenAI.exe Standalone
echo =======================================================
echo.
echo 1. Dang kiem tra PyInstaller & Pygame...
py -m pip install pygame edge-tts pyinstaller pillow

echo.
echo 2. Dang tao icon app_icon.ico...
py create_icon.py

echo.
echo 3. Dang đóng gói piper_desktop_app.py thanh DocTruyenAI.exe...
py -m PyInstaller --noconsole --onefile --icon=app_icon.ico piper_desktop_app.py --name "DocTruyenAI"

echo.
echo 4. Dang copy cac file model, icon va piper.exe sang thư muc dist...
if not exist "dist\piper" mkdir "dist\piper"
xcopy /E /I /Y "piper" "dist\piper"
copy /Y "*.onnx" "dist\"
copy /Y "*.json" "dist\"
copy /Y "app_icon.ico" "dist\"

echo.
echo =======================================================
echo   HOAN THANH! Thư muc dist da sẵn sang:
echo   -> File thuc thi: dist\DocTruyenAI.exe
echo =======================================================
pause
