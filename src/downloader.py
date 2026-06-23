"""
downloader.py — Lógica de download e conversão via yt-dlp + ffmpeg.

Suporta:
  • MP4 com áudio AAC garantido (sem Opus)
  • MP3 com VBR máxima qualidade, metadados e capa
  • Playlists em ordem
  • Barra de progresso via callback (funciona em CLI e GUI)
  • Cancelamento limpo via threading.Event
  • Pasta de destino configurável por chamada
"""

import re
import threading
from pathlib import Path
from typing import Callable, Literal, Optional

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from config import get_output_dir

FormatoSaida = Literal["mp4", "mp3"]
RESOLUCOES_DISPONIVEIS = ["2160", "1440", "1080", "720", "480", "360", "melhor"]


# ── Cancelamento ──────────────────────────────────────────────────────────────

class CanceladoException(Exception):
    """Levantada quando o usuário cancela o download."""


# ── Progresso ─────────────────────────────────────────────────────────────────

def _limpar_ansi(texto: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", texto)


def _criar_hook(
    cancel_event: threading.Event,
    callback: Optional[Callable[[float, str, str], None]],
) -> Callable:
    """
    Retorna um hook de progresso configurado.

    O callback recebe: (percentual_float, velocidade_str, eta_str)
    Útil para atualizar tanto o terminal quanto a GUI.
    """
    def hook(d: dict) -> None:
        # Verifica cancelamento a cada chunk
        if cancel_event.is_set():
            raise CanceladoException("Download cancelado pelo usuário.")

        if d["status"] == "downloading":
            pct_str = _limpar_ansi(d.get("_percent_str", "0%")).strip().replace("%", "")
            vel     = _limpar_ansi(d.get("_speed_str", "N/A")).strip()
            eta     = _limpar_ansi(d.get("_eta_str",   "N/A")).strip()

            try:
                pct_float = float(pct_str)
            except ValueError:
                pct_float = 0.0

            if callback:
                callback(pct_float, vel, eta)
            else:
                print(
                    f"\r  ⬇  {pct_float:>5.1f}%  │  {vel:>12}  │  ETA {eta:>6}",
                    end="", flush=True,
                )

        elif d["status"] == "finished":
            if callback:
                callback(100.0, "", "")
            else:
                print("\r  ✔  Download concluído. Processando...          ")

    return hook


# ── Opções ────────────────────────────────────────────────────────────────────

def _opcoes_mp4(
    ffmpeg_path: str,
    output_dir: Path,
    resolucao: str,
    eh_playlist: bool,
    hook: Callable,
) -> dict:
    if resolucao == "melhor":
        fmt = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
            "/bestvideo+bestaudio[acodec=mp4a]"
            "/bestvideo+bestaudio/best"
        )
    else:
        fmt = (
            f"bestvideo[height<={resolucao}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={resolucao}]+bestaudio[acodec=mp4a]"
            f"/bestvideo[height<={resolucao}]+bestaudio"
            f"/best[height<={resolucao}]/best"
        )

    tpl  = str(output_dir / "%(title)s.%(ext)s")
    tpl_pl = str(output_dir / "%(playlist_index)s_%(title)s.%(ext)s")

    return {
        "format": fmt,
        "merge_output_format": "mp4",
        "outtmpl": {"default": tpl, "pl_video": tpl_pl if eh_playlist else tpl},
        "postprocessor_args": {
            "default": ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"],
        },
        "ffmpeg_location": ffmpeg_path,
        "progress_hooks": [hook],
        "noplaylist": not eh_playlist,
        "quiet": True,
        "no_warnings": False,
        "ignoreerrors": False,
        "windowsfilenames": True,
    }


def _opcoes_mp3(
    ffmpeg_path: str,
    output_dir: Path,
    eh_playlist: bool,
    hook: Callable,
) -> dict:
    tpl    = str(output_dir / "%(title)s.%(ext)s")
    tpl_pl = str(output_dir / "%(playlist_index)s_%(title)s.%(ext)s")

    return {
        "format": "bestaudio/best",
        "outtmpl": {"default": tpl, "pl_video": tpl_pl if eh_playlist else tpl},
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"},
            {"key": "FFmpegMetadata", "add_metadata": True},
            {"key": "EmbedThumbnail"},
        ],
        "ffmpeg_location": ffmpeg_path,
        "writethumbnail": True,
        "progress_hooks": [hook],
        "noplaylist": not eh_playlist,
        "quiet": True,
        "no_warnings": False,
        "ignoreerrors": False,
        "windowsfilenames": True,
    }


# ── API pública ───────────────────────────────────────────────────────────────

def baixar_video(
    url: str,
    formato: FormatoSaida = "mp4",
    resolucao: str = "melhor",
    ffmpeg_path: Optional[str] = None,
    output_dir: Optional[Path] = None,
    cancel_event: Optional[threading.Event] = None,
    progresso_callback: Optional[Callable[[float, str, str], None]] = None,
) -> Path:
    """
    Faz download e conversão de um vídeo ou playlist do YouTube.

    Args:
        url:                URL do vídeo ou playlist.
        formato:            'mp4' ou 'mp3'.
        resolucao:          Resolução desejada ('melhor', '1080', '720', ...).
        ffmpeg_path:        Caminho para o executável ffmpeg.
        output_dir:         Pasta de destino. Se None, usa a preferência salva.
        cancel_event:       threading.Event; quando setado, interrompe o download.
        progresso_callback: Função (pct: float, vel: str, eta: str) → None.
                            Se None, imprime no terminal.

    Returns:
        Path do arquivo gerado, ou da pasta output em caso de playlist.

    Raises:
        RuntimeError:        ffmpeg não encontrado.
        CanceladoException:  Usuário cancelou.
        PermissionError:     Sem permissão de escrita.
        DownloadError / ExtractorError: erros do yt-dlp.
    """
    if ffmpeg_path is None:
        raise RuntimeError(
            "ffmpeg não encontrado. Instale-o e adicione ao PATH, "
            "ou coloque ffmpeg.exe em tools/."
        )

    dest = output_dir or get_output_dir()
    dest.mkdir(parents=True, exist_ok=True)

    ev = cancel_event or threading.Event()
    hook = _criar_hook(ev, progresso_callback)
    eh_playlist = "playlist" in url

    if formato == "mp3":
        opcoes = _opcoes_mp3(ffmpeg_path, dest, eh_playlist, hook)
    else:
        opcoes = _opcoes_mp4(ffmpeg_path, dest, resolucao, eh_playlist, hook)

    try:
        with YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)

            if "entries" in info:
                return dest

            nome_base = ydl.prepare_filename(info)
            return Path(nome_base).with_suffix(".mp3" if formato == "mp3" else ".mp4")

    except CanceladoException:
        raise
    except PermissionError:
        raise PermissionError(
            f"Sem permissão para salvar em: {dest}\n"
            "Verifique as permissões da pasta ou execute como administrador."
        )
    except (DownloadError, ExtractorError):
        raise
