@echo off
:: ============================================================
::  build.bat — Gera o YT_Convert.exe via PyInstaller
::  Execute na raiz do projeto com o venv ativado.
:: ============================================================

echo.
echo  === Gerando YT_Convert.exe ===
echo.

:: Limpa builds anteriores
if exist build   rmdir /s /q build
if exist release rmdir /s /q release
mkdir release

:: Gera o executável
::   --onefile        → tudo em um único .exe
::   --console        → mantém janela de terminal (CLI app)
::   --icon           → ícone do .exe (coloque app.ico na raiz)
::   --name           → nome do executável final
::   --add-data       → inclui a pasta tools/ (ffmpeg.exe bundled)
pyinstaller ^
    --onefile ^
    --console ^
    --name "YT_Convert" ^
    --icon "app.ico" ^
    --add-data "tools;tools" ^
    --distpath "release" ^
    "src/main.py"

:: Cria pasta output dentro de release para o usuário final
if not exist release\output mkdir release\output

echo.
echo  === Build concluído! ===
echo  Arquivo: release\YT_Convert.exe
echo.
pause
