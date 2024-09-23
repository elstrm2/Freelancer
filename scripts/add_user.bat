@echo off
cd ..
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%PYTHONPATH%;..
python -m scripts.add_user
pause
