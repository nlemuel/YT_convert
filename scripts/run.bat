@echo off
setlocal

:: ─────────────────────────────────────────────────────
::  run.bat  —  Executa a aplicação em modo dev
::  Pode ser executado com duplo clique ou via terminal.
:: ─────────────────────────────────────────────────────

:: Vai para a pasta PAI de scripts\ → raiz do projeto
cd /d "%~dp0.."
echo.
echo  Raiz do projeto: %CD%
echo.

:: Verifica venv
if not exist "venv\Scripts\activate.bat" (
    echo  ERRO: venv nao encontrado.
    echo  Execute:  python -m venv venv
    echo            venv\Scripts\activate
    echo            pip install -r requirements.txt
    pause & exit /b 1
)

:: Verifica src\main.py
if not exist "src\main.py" (
    echo  ERRO: src\main.py nao encontrado em %CD%
    pause & exit /b 1
)

:: Ativa venv e roda
call venv\Scripts\activate.bat
python src\main.py

echo.
pause
endlocal
