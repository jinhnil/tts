@echo off
title Chay Ung Dung Doc Truyen AI Pro (VietVoice Studio)
if exist "dist\DocTruyenAI.exe" (
    start "" "dist\DocTruyenAI.exe"
) else (
    py piper_desktop_app.py
)
