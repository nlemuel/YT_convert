"""
downloader.py — Lógica de download e conversão via yt-dlp + ffmpeg.

Suporta:
  • Download de vídeo em MP4 com áudio AAC (sem Opus)
  • Download de áudio em MP3 (máxima qualidade, VBR ~320 kbps)
  • Playlists
  • Barra de progresso no terminal
"""

import re
from pathlib import Path
from typing import Literal, Optional

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from config import OUTPUT_DIR

FormatoSaida = Literal["mp4", "mp3"]

RESOLUCOES_DISPONIVEIS = ["2160", "1440", "1080", "720", "480", "360", "melhor"]


# ──────────────────────────────────────────────
# Progresso
# ──────────────────────────────────────────────

def _limpar_ansi(texto: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", texto)


def _hook_progresso(d: dict) -> None:
    if d["status"] == "downloading":
        pct = _limpar_ansi(d.get("_percent_str", "??%")).strip()
        vel = _limpar_ansi(d.get("_speed_str", "N/A")).strip()
        eta = _limpar_ansi(d.get("_eta_str", "N/A")).strip()
        print(f"\r  ⬇  {pct:>6}  │  {vel:>12}  │  ETA {eta:>6}", end="", flush=True)
    elif d["status"] == "finished":
        print("\r  ✔  Download concluído. Processando...          ")


# ──────────────────────────────────────────────
# Opções MP4
# ──────────────────────────────────────────────

def _opcoes_mp4(ffmpeg_path: str, resolucao: str = "melhor", eh_playlist: bool = False) -> dict:
    """
    Estratégia para MP4 com áudio AAC garantido:

    O YouTube serve áudio em Opus (webm). Para forçar AAC no MP4 final,
    usamos o postprocessor FFmpegVideoRemuxer + 'postprocessor_args' com
    a chave especial 'default' — que o yt-dlp aplica a TODAS as chamadas
    ffmpeg, incluindo o merge. Isso é mais confiável que tentar interceptar
    apenas o FFmpegMerger, cujo nome interno pode variar entre versões.

    Alternativa mais robusta: baixar o áudio já em m4a (codec AAC nativo)
    usando o seletor de formato [acodec=mp4a], evitando recodificação.
    """
    if resolucao == "melhor":
        # Prefere áudio m4a (AAC nativo) para evitar recodificação Opus→AAC
        fmt = (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]"
            "/bestvideo+bestaudio[acodec=mp4a]"
            "/bestvideo+bestaudio"
            "/best"
        )
    else:
        fmt = (
            f"bestvideo[height<={resolucao}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={resolucao}]+bestaudio[acodec=mp4a]"
            f"/bestvideo[height<={resolucao}]+bestaudio"
            f"/best[height<={resolucao}]"
            "/best"
        )

    template_padrao  = str(OUTPUT_DIR / "%(title)s.%(ext)s")
    template_playlist = str(OUTPUT_DIR / "%(playlist_index)s_%(title)s.%(ext)s")

    return {
        "format": fmt,
        "merge_output_format": "mp4",
        "outtmpl": {
            "default": template_padrao,
            "pl_video": template_playlist if eh_playlist else template_padrao,
        },
        # 'postprocessor_args' com chave "default" é aplicado a TODA chamada
        # ffmpeg feita pelo yt-dlp — merge incluso. Garante AAC mesmo quando
        # o stream de áudio baixado é Opus (fallback da seleção acima).
        "postprocessor_args": {
            "default": ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"],
        },
        "ffmpeg_location": ffmpeg_path,
        "progress_hooks": [_hook_progresso],
        "noplaylist": not eh_playlist,
        "quiet": True,
        "no_warnings": False,
        "ignoreerrors": False,
        "windowsfilenames": True,
    }


# ──────────────────────────────────────────────
# Opções MP3
# ──────────────────────────────────────────────

def _opcoes_mp3(ffmpeg_path: str, eh_playlist: bool = False) -> dict:
    template_padrao   = str(OUTPUT_DIR / "%(title)s.%(ext)s")
    template_playlist = str(OUTPUT_DIR / "%(playlist_index)s_%(title)s.%(ext)s")

    return {
        "format": "bestaudio/best",
        "outtmpl": {
            "default": template_padrao,
            "pl_video": template_playlist if eh_playlist else template_padrao,
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",   # VBR máxima (~320 kbps)
            },
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                "key": "EmbedThumbnail",
            },
        ],
        "ffmpeg_location": ffmpeg_path,
        "writethumbnail": True,
        "progress_hooks": [_hook_progresso],
        "noplaylist": not eh_playlist,
        "quiet": True,
        "no_warnings": False,
        "ignoreerrors": False,
        "windowsfilenames": True,
    }


# ──────────────────────────────────────────────
# Função pública
# ──────────────────────────────────────────────

def baixar_video(
    url: str,
    formato: FormatoSaida = "mp4",
    resolucao: str = "melhor",
    ffmpeg_path: Optional[str] = None,
) -> Path:
    """
    Faz download e conversão de um vídeo ou playlist do YouTube.

    Returns:
        Path do arquivo gerado, ou da pasta output em caso de playlist.
    """
    if ffmpeg_path is None:
        raise RuntimeError(
            "ffmpeg não encontrado. Instale-o e adicione ao PATH, "
            "ou coloque ffmpeg.exe em tools/."
        )

    eh_playlist = "playlist" in url
    opcoes = _opcoes_mp3(ffmpeg_path, eh_playlist) if formato == "mp3" \
             else _opcoes_mp4(ffmpeg_path, resolucao, eh_playlist)

    try:
        with YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)

            if "entries" in info:
                return OUTPUT_DIR

            nome_base = ydl.prepare_filename(info)
            sufixo = ".mp3" if formato == "mp3" else ".mp4"
            return Path(nome_base).with_suffix(sufixo)

    except PermissionError:
        raise PermissionError(
            f"Sem permissão para salvar em: {OUTPUT_DIR}\n"
            "Verifique as permissões da pasta ou execute como administrador."
        )
    except (DownloadError, ExtractorError):
        raise
