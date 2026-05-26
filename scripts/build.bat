@echo off
setlocal

:: ─────────────────────────────────────────────────────
::  build.bat  —  Gera release\YT_Convert.exe
:: ─────────────────────────────────────────────────────

cd /d "%~dp0.."
echo.
echo  Raiz do projeto: %CD%
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  ERRO: venv nao encontrado.
    echo  Execute:  python -m venv venv  ^&  pip install -r requirements.txt
    pause & exit /b 1
)

if not exist "src\main.py" (
    echo  ERRO: src\main.py nao encontrado em %CD%
    pause & exit /b 1
)

call venv\Scripts\activate.bat

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  PyInstaller nao encontrado. Instalando...
    pip install pyinstaller
)

echo  Limpando builds anteriores...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist
if exist release rmdir /s /q release
mkdir release
if not exist tools mkdir tools

echo  Gerando .exe...
echo.

:: %CD% garante paths absolutos — resolve o bug do PyInstaller
:: que buscava tools\ relativo a build\ (--specpath) em vez da raiz
pyinstaller ^
    --onefile ^
    --console ^
    --name "YT_Convert" ^
    --add-data "%CD%\tools;tools" ^
    --paths "%CD%\src" ^
    --distpath "%CD%\release" ^
    --workpath "%CD%\build" ^
    --specpath "%CD%\build" ^
    "%CD%\src\main.py"

echo.
if exist "release\YT_Convert.exe" (
    if not exist "release\output" mkdir release\output
    echo  ============================================
    echo   Build concluido com sucesso!
    echo   Arquivo: %CD%\release\YT_Convert.exe
    echo  ============================================
) else (
    echo  ============================================
    echo   ERRO: YT_Convert.exe nao foi gerado.
    echo   Leia o log acima para identificar o problema.
    echo  ============================================
)

echo.
pause
endlocal