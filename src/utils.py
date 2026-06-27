"""
utils.py — Funções utilitárias: validação de URL, detecção de ffmpeg,
sanitização de nomes e helpers de terminal.
"""

import re
import shutil
import sys
from pathlib import Path
from typing import Optional

from config import TOOLS_DIR


def validar_url(url: str) -> bool:
    if not url or not url.strip():
        return False
    return url.strip().startswith(("http://", "https://"))


def verificar_ffmpeg() -> Optional[str]:
    """
    Localiza o ffmpeg, priorizando a pasta local tools/.

    Returns:
        Caminho absoluto para o ffmpeg, ou None se não encontrado.
    """
    local = TOOLS_DIR / "ffmpeg.exe"
    if local.exists():
        return str(local)
    return shutil.which("ffmpeg")


def sanitizar_nome(nome: str, max_len: int = 120) -> str:
    """Remove caracteres inválidos e trunca nomes de arquivo."""
    nome = re.sub(r'[\\/*?:"<>|]', "", nome)
    nome = re.sub(r"\s+", " ", nome).strip()
    return nome[:max_len]


def linha_separadora(char: str = "─", largura: int = 52) -> str:
    return char * largura


def cabecalho() -> None:
    print(linha_separadora("═"))
    print("  🎬  YouTube Downloader  •  MP4 / MP3")
    print(linha_separadora("═"))
