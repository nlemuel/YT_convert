Setup Dev
## Requisitos
- Python 3.13+
- FFmpeg instalado

## Instalação

git clone <repo>
cd YT_convert

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

Rodar:

python main.py

Ou:

run.bat

Build:

build.bat
README para usuário final

User final:

# Como usar

1. Baixe a pasta release
2. Abra `YT_Converter.exe`
3. Cole a URL do YouTube
4. Aguarde download/conversão
5. Arquivo salvo em `output/`

## IMPORTANTE PARA GERAR O .EXE PARA O USUÁRIO: 
python -m PyInstaller --onefile src\main.py

### Instalação (dev)

1. criar ambiente

python -m venv venv

2. ativar Windows:
venv\Scripts\activate

3. Instalar dependências
pip install -r requirements.txt

4. instalar ffmpeg

- Baixar:

FFmpeg Windows builds

- Depois:

C:\ffmpeg\bin

Adicionar ao PATH.

- Teste:

ffmpeg -version
Como rodar

- Dev:

python src/main.py

ou:

scripts\run.bat
Gerar .exe

Comando:

pyinstaller --onefile --icon=app.ico src/main.py

melhor:

scripts\build.bat
Onde fica o .exe
release/
   YT_Convert.exe

- Esse é o arquivo para entregar ao usuário. Ele só precisa de um duplo clique.

### Distribuição para usuário final

Entregar apenas:

release/
 └── YT_Convert.exe

(opcional)

release/
 ├── YT_Convert.exe
 └── output/