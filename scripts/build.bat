@echo off
call venv\Scripts\activate

echo Limpando build antigo...
rmdir \s \q build
rmdir \s \q dist

echo Gerando EXE...

python -m Pyinstaller --onefile --name YT_Converter main.py

pause