@echo off
title AnyDownloader - Universal Multi-Part Downloader
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)

