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
    echo  ERRO: src\main.py nao encontrado.
    pause & exit /b 1
)

:: Garante pastas necessárias
if not exist tools  mkdir tools
if not exist assets mkdir assets

call venv\Scripts\activate.bat

where pyinstaller >nul 2>&1
if errorlevel 1 ( pip install pyinstaller )

echo  Limpando builds anteriores...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist
if exist release rmdir /s /q release
mkdir release

echo  Gerando .exe...
echo.

:: Flags importantes:
::
::  --windowed     → sem janela de CMD / console (corrige o loop reportado)
::                   a GUI Tkinter abre direto, sem terminal por trás
::
::  --icon         → ícone do .exe e da barra de tarefas
::                   coloque icon.ico em assets\ antes de buildar
::
::  --add-data assets;assets  → inclui a pasta assets\ no bundle
::                              para a GUI encontrar o icon.ico em runtime
::
::  --add-data tools;tools    → inclui ffmpeg.exe bundled
::
::  --hidden-import tkinter*  → PyInstaller não detecta Tkinter
::                              automaticamente quando importado
::                              de forma condicional no main.py

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "YT_Convert" ^
    --icon "%CD%\assets\icon.ico" ^
    --add-data "%CD%\assets;assets" ^
    --add-data "%CD%\tools;tools" ^
    --paths "%CD%\src" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.messagebox" ^
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
