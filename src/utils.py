import re
import shutil
import sys
from pathlib import Path
from typing import Optional

from config import TOOLS_DIR


# ──────────────────────────────────────────────
# Validação de URL
# ──────────────────────────────────────────────

def validar_url(url: str) -> bool:
    """
    Valida se a URL é do YouTube (vídeo, short ou playlist).

    Args:
        url: String com a URL a validar.

    Returns:
        True se válida, False caso contrário.
    """
    if not url or not url.strip():
        return False

    padrao = (
        r"^(https?://)?(www\.)?"
        r"(youtube\.com/(watch\?|shorts/|playlist\?|live/)|youtu\.be/).+"
    )
    return bool(re.match(padrao, url.strip()))


# ──────────────────────────────────────────────
# Detecção do ffmpeg
# ──────────────────────────────────────────────

def verificar_ffmpeg() -> Optional[str]:
    """
    Localiza o executável ffmpeg, priorizando a pasta local /tools.

    Ordem de busca:
      1. <base>/tools/ffmpeg.exe  (bundled junto ao .exe ou ao projeto)
      2. ffmpeg no PATH do sistema

    Returns:
        Caminho absoluto para o ffmpeg, ou None se não encontrado.
    """
    # 1. Verifica ffmpeg local (bundled)
    local = TOOLS_DIR / "ffmpeg.exe"
    if local.exists():
        return str(local)

    # 2. Verifica ffmpeg no PATH do sistema
    no_path = shutil.which("ffmpeg")
    if no_path:
        return no_path

    return None


# ──────────────────────────────────────────────
# Sanitização de nome de arquivo
# ──────────────────────────────────────────────

def sanitizar_nome(nome: str, max_len: int = 120) -> str:
    """
    Remove ou substitui caracteres inválidos em nomes de arquivo Windows/Linux.

    Args:
        nome:    Nome original (geralmente o título do vídeo).
        max_len: Comprimento máximo do nome resultante.

    Returns:
        Nome sanitizado.
    """
    # Remove caracteres proibidos no Windows
    nome = re.sub(r'[\\/*?:"<>|]', "", nome)
    # Substitui múltiplos espaços/tabs por um único espaço
    nome = re.sub(r"\s+", " ", nome).strip()
    # Trunca se necessário
    return nome[:max_len]


# ──────────────────────────────────────────────
# Helpers de terminal
# ──────────────────────────────────────────────

def linha_separadora(char: str = "─", largura: int = 52) -> str:
    """Retorna uma linha separadora para o terminal."""
    return char * largura


def cabecalho() -> None:
    """Imprime o cabeçalho da aplicação."""
    print(linha_separadora("═"))
    print("  🎬  YouTube Downloader  •  MP4 / MP3")
    print(linha_separadora("═"))
