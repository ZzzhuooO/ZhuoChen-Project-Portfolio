@echo off
cd /d "%~dp0"
py -3 canele_temperature_toy.py
if errorlevel 1 pause
