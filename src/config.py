"""
config.py — Configurações e preferências globais da aplicação.
Detecta automaticamente modo script (dev) vs modo .exe (PyInstaller).
"""

import json
import sys
from pathlib import Path


# ── Diretório base ────────────────────────────────────────────────────────────

def _resolve_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent   # pasta onde o .exe está
    return Path(__file__).resolve().parent.parent  # raiz do projeto


BASE_DIR:  Path = _resolve_base_dir()
TOOLS_DIR: Path = BASE_DIR / "tools"

# Arquivo de preferências persistentes (pasta de destino escolhida, etc.)
PREFS_FILE: Path = BASE_DIR / "prefs.json"

# ── Preferências ──────────────────────────────────────────────────────────────

_DEFAULTS: dict = {
    "output_dir": str(BASE_DIR / "output"),
}


def carregar_prefs() -> dict:
    """Lê prefs.json; retorna defaults se o arquivo não existir ou estiver corrompido."""
    if PREFS_FILE.exists():
        try:
            dados = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
            # Mescla com defaults para garantir chaves novas em versões futuras
            return {**_DEFAULTS, **dados}
        except Exception:
            pass
    return dict(_DEFAULTS)


def salvar_prefs(prefs: dict) -> None:
    """Persiste o dicionário de preferências em prefs.json."""
    try:
        PREFS_FILE.write_text(
            json.dumps(prefs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # falha silenciosa — não crítico


def get_output_dir() -> Path:
    """Retorna a pasta de destino salva (ou o padrão output/)."""
    prefs = carregar_prefs()
    pasta = Path(prefs["output_dir"])
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def set_output_dir(pasta: Path) -> None:
    """Salva nova pasta de destino nas preferências."""
    prefs = carregar_prefs()
    prefs["output_dir"] = str(pasta)
    salvar_prefs(prefs)
    pasta.mkdir(parents=True, exist_ok=True)
