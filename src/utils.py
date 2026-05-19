from pathlib import Path
import shutil
import sys
import re


def validar_url(url: str) -> bool:
    regex = (
        r"(https?://)?(www\.)?"
        r"(youtube\.com|youtu\.be)/.+"
    )

    return bool(re.match(regex, url))


def verificar_ffmpeg():
    # Quando executado como .exe (PyInstaller)
    if getattr(sys, "frozen", False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).resolve().parent

    # Procura ffmpeg local
    local = base_path / "tools" / "ffmpeg.exe"

    if local.exists():
        return str(local)

    # Procura no PATH do sistema
    return shutil.which("ffmpeg")