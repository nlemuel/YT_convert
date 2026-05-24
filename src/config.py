import sys
from pathlib import Path


def _resolve_base_dir() -> Path:
    """Retorna o diretório base correto para modo script e modo .exe."""
    if getattr(sys, "frozen", False):
        # Executando como .exe gerado pelo PyInstaller
        return Path(sys.executable).parent
    else:
        # Executando como script Python normal
        return Path(__file__).resolve().parent.parent


BASE_DIR: Path = _resolve_base_dir()
OUTPUT_DIR: Path = BASE_DIR / "output"
TOOLS_DIR: Path = BASE_DIR / "tools"

# Garante que a pasta de saída existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)