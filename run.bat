@echo off
cd /d E:\cloudvault
call venv\Scripts\activate
start http://localhost:5000
python app.py
pause