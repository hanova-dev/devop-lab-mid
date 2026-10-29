@echo off
cd /d "%~dp0"
python -m pytest -v
pause
