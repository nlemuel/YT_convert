# YT_Convert — YouTube Downloader (MP4 / MP3)

Download de vídeos do YouTube em MP4 (até 4K) e músicas em MP3 (máxima qualidade).

---

## Estrutura do projeto

```
YT_convert/
│
├── src/
│   ├── main.py          ← ponto de entrada
│   ├── downloader.py    ← lógica de download/conversão
│   ├── utils.py         ← validação, detecção de ffmpeg, helpers
│   └── config.py        ← caminhos e configurações globais
│
├── scripts/
│   ├── run.bat          ← atalho para rodar (dev)
│   └── build.bat        ← gera o .exe
│
├── tools/
│   └── ffmpeg.exe       ← ffmpeg bundled (opcional, ver abaixo)
│
├── output/              ← arquivos baixados ficam aqui
├── release/             ← .exe gerado pelo build fica aqui
├── venv/
├── requirements.txt
├── app.ico              ← ícone do .exe (coloque aqui)
└── README.md
```
gui.py — Interface gráfica Tkinter para o YouTube Downloader.

Layout:
  ┌─────────────────────────────────────────────┐
  │  🎬 YouTube Downloader                      
  ├─────────────────────────────────────────────┤
  │  URL  [_________________________________]   │
  │  Formato  ◉ MP4  ○ MP3                     
  │  Resolução  [▼ Melhor disponível]           │
  │  Destino  [C:\...\output]  [Alterar]        │
  ├─────────────────────────────────────────────┤
  │  [████████░░░░░░░░]  47%  •  2.3 MB/s       │
  │  status...                                  │
  ├─────────────────────────────────────────────┤
  │  [  Baixar  ]  [  Cancelar  ]               │
  └─────────────────────────────────────────────┘

---

## Instalação (dev)

### Requisitos
- Python 3.13+
- ffmpeg instalado (ver abaixo)

### Passo a passo

```bash
git clone <repo>
cd YT_convert

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
```

### Instalar ffmpeg

**Opção 1 — PATH do sistema (recomendado para dev):**

1. Baixe em: https://www.gyan.dev/ffmpeg/builds/ (pegue o `ffmpeg-release-essentials.zip`)
2. Extraia e copie `ffmpeg.exe` para `C:\ffmpeg\bin\`
3. Adicione `C:\ffmpeg\bin` ao PATH do Windows
4. Teste: `ffmpeg -version`

**Opção 2 — Bundled na pasta tools/ (recomendado para .exe):**

1. Baixe o `ffmpeg.exe` (mesma fonte acima)
2. Coloque em `tools/ffmpeg.exe`
3. O `build.bat` já inclui essa pasta no `.exe` automaticamente

---

## Como rodar (dev)

```bash
python src/main.py
```

Ou via atalho:

```
scripts\run.bat
```

---

## Gerar o .exe

```
scripts\build.bat
```

O executável fica em:

```
release\YT_Convert.exe
```

### O que o build.bat faz:
- Limpa builds anteriores
- Roda o PyInstaller com `--onefile` (tudo num único arquivo)
- Inclui a pasta `tools/` (ffmpeg bundled)
- Cria a pasta `release/output/` para os downloads do usuário final

### Comando manual equivalente:

```bash
pyinstaller --onefile --console --name "YT_Convert" --icon app.ico --add-data "tools;tools" src/main.py
```

---

## Uso (usuário final)

1. Baixe a pasta `release/`
2. Dê duplo clique em `YT_Convert.exe`
3. Cole a URL do YouTube
4. Escolha o formato: **MP4** (vídeo) ou **MP3** (áudio)
5. Se MP4: escolha a resolução (ou Enter para a melhor disponível)
6. Confirme e aguarde
7. Arquivo salvo em `output/` (na mesma pasta do .exe)

---

## Funcionalidades

| Feature | Status |
|---|---|
| Download MP4 (vídeo + áudio merged) | ✅ |
| Download MP3 (áudio, VBR máxima qualidade) | ✅ |
| Melhor qualidade automática (4K, 1080p...) | ✅ |
| Seleção de resolução | ✅ |
| Progresso com % e velocidade | ✅ |
| Suporte a playlists | ✅ |
| Metadados e capa no MP3 | ✅ |
| Tratamento de erros (privado, indisponível...) | ✅ |
| Funciona como .exe sem Python instalado | ✅ |

---

## Possíveis melhorias futuras

- Interface gráfica (Tkinter ou PyQt6)
- Fila de downloads (múltiplas URLs em sequência)
- Seleção de pasta de destino pelo usuário
- Histórico de downloads
- Atualização automática do yt-dlp embutida
- Suporte a outros sites (SoundCloud, Vimeo, etc.)
