@echo off
REM === MO APP CHEN LOGO (Windows) - nhan dup de mo ===
cd /d "%~dp0"

set PY=
where python >nul 2>&1 && set PY=python
if "%PY%"=="" where py >nul 2>&1 && set PY=py
if "%PY%"=="" (
  echo Chua co Python 3. Cai tai: https://www.python.org/downloads/
  echo Khi cai nho TICH chon "Add Python to PATH".
  pause
  exit /b 1
)

%PY% -c "import PIL" >nul 2>&1 || ( echo Dang cai Pillow... & %PY% -m pip install --quiet Pillow )
%PY% -c "import tkinterdnd2" >nul 2>&1 || ( echo Dang cai keo-tha tkinterdnd2... & %PY% -m pip install --quiet tkinterdnd2 )

%PY% app.py
