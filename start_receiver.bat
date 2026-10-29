@echo off
cd /d "%~dp0"
title Report Receiver (port 5001)
python receiver.py
pause
