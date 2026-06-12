@echo off
chcp 65001 >nul
title Tao file EXE - Ghep Anh Logo EyePlus
echo ============================================================
echo    DUC FILE .EXE  -  GHEP ANH LOGO EYEPLUS
echo ============================================================
echo.
echo File nay se tu cai cong cu va tao ra file .exe chay doc lap.
echo Chi can lam 1 lan tren 1 may Windows co Python.
echo Sau do copy file .exe (trong thu muc "dist") sang may khac
echo deu chay duoc, KHONG can cai Python.
echo.
echo (Lan dau can co mang internet de tai cong cu.)
echo ------------------------------------------------------------
echo.

REM --- Tim Python ---
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [LOI] Khong tim thay Python tren may nay.
  echo Hay cai Python 3 tai: https://www.python.org/downloads/
  echo Khi cai NHO tich o "Add Python to PATH".
  echo.
  pause
  exit /b 1
)
echo Da tim thay Python: %PY%
echo.

REM --- Cai cong cu can thiet ---
echo [1/2] Dang cai cong cu (PyInstaller, Pillow, tkinterdnd2)...
%PY% -m pip install --upgrade pip >nul 2>nul
%PY% -m pip install --upgrade pyinstaller pillow tkinterdnd2
if errorlevel 1 (
  echo [LOI] Cai cong cu that bai. Kiem tra ket noi mang roi thu lai.
  echo.
  pause
  exit /b 1
)
echo.

REM --- Dong goi thanh .exe ---
echo [2/2] Dang dong goi thanh file .exe (vui long doi 1-2 phut)...
%PY% -m PyInstaller --noconfirm --onefile --windowed ^
  --name "GhepAnhLogoEyePlus" ^
  --collect-all tkinterdnd2 ^
  app.py
if errorlevel 1 (
  echo [LOI] Dong goi that bai. Doc thong bao loi o tren.
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo    XONG!  File .exe da nam tai:
echo    dist\GhepAnhLogoEyePlus.exe
echo ============================================================
echo.
echo Copy file do sang may Windows khac la chay duoc luon.
echo (Goi y: de file logo.png canh file .exe de app tu nhan logo.)
echo.
explorer dist
pause
