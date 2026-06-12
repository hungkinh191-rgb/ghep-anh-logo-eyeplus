@echo off
REM === TU DONG THEO DOI THU MUC (Windows) ===
REM Nhan dup file nay de bat. Lan dau se tu cai thu vien can thiet.
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

%PY% -c "import PIL" >nul 2>&1
if errorlevel 1 (
  echo Lan dau chay - dang cai thu vien xu ly anh ^(can mang^)...
  %PY% -m pip install --quiet Pillow
)

%PY% watch_logo.py
pause
