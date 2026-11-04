@echo off
title J.A.R.V.I.S. // System Voice Monitor
cls
echo ====================================================================
echo             J.A.R.V.I.S. VOICE MONITOR ^& DESKTOP CONTROLLER
echo ====================================================================
echo.
echo Initializing audio monitor and accessibility drivers...
cd /d "%~dp0"
python jarvis.py
pause

