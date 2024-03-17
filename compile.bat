@echo off
cd /d %~dp0
pip install pyinstaller
pyinstaller --onefile --name "Spotle Unlimited" script.py