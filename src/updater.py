"""
updater.py — Atualização automática do yt-dlp na inicialização.

Estratégia:
  • Verifica a data do último update em prefs.json
  • Se faz mais de INTERVALO_DIAS dias (ou nunca atualizou), roda o update
  • Update é silencioso: não bloqueia, não trava a UI
  • Erros são ignorados — ausência de internet não impede o uso do programa
"""

import subprocess
import sys
from datetime import date, datetime
from typing import Callable, Optional

from config import carregar_prefs, salvar_prefs

# Atualiza no máximo uma vez por dia
INTERVALO_DIAS: int = 1


def _ultima_atualizacao() -> Optional[date]:
    """Retorna a data do último update, ou None se nunca atualizou."""
    prefs = carregar_prefs()
    raw = prefs.get("ytdlp_last_update")
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            pass
    return None


def _registrar_atualizacao() -> None:
    prefs = carregar_prefs()
    prefs["ytdlp_last_update"] = date.today().isoformat()
    salvar_prefs(prefs)


def _precisa_atualizar() -> bool:
    ultima = _ultima_atualizacao()
    if ultima is None:
        return True
    return (date.today() - ultima).days >= INTERVALO_DIAS


def atualizar_ytdlp(callback: Optional[Callable[[str], None]] = None) -> None:
    """
    Atualiza o yt-dlp se necessário.

    Args:
        callback: Função opcional que recebe strings de status para exibir
                  na UI (ex: label da GUI ou print no terminal).
                  Se None, usa print().
    """
    log = callback if callback else print

    if not _precisa_atualizar():
        return

    log("  🔄  Verificando atualização do yt-dlp...")

    try:
        # Usa o mesmo executável Python do ambiente atual para garantir
        # que o pacote correto seja atualizado (venv ou sistema)
        resultado = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp", "--quiet"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if resultado.returncode == 0:
            _registrar_atualizacao()
            log("  ✔  yt-dlp atualizado.")
        else:
            # Falha no pip — não é crítico, continua normalmente
            log("  ⚠  Não foi possível atualizar o yt-dlp (sem internet?).")

    except subprocess.TimeoutExpired:
        log("  ⚠  Timeout na atualização do yt-dlp. Continuando...")
    except Exception:
        log("  ⚠  Atualização ignorada. Continuando...")
