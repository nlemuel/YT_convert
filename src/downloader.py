import re
from pathlib import Path
from typing import Literal, Optional

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError, ExtractorError

from config import OUTPUT_DIR

# Tipo de formato aceito pela aplicação
FormatoSaida = Literal["mp4", "mp3"]

# Resoluções de vídeo disponíveis para seleção
RESOLUCOES_DISPONIVEIS = ["2160", "1440", "1080", "720", "480", "360", "melhor"]


# ──────────────────────────────────────────────
# Progresso
# ──────────────────────────────────────────────

def _hook_progresso(d: dict) -> None:
    """
    Callback chamado pelo yt-dlp a cada chunk baixado.
    Exibe progresso, velocidade e ETA na mesma linha.
    """
    if d["status"] == "downloading":
        pct = _limpar_ansi(d.get("_percent_str", "??%")).strip()
        vel = _limpar_ansi(d.get("_speed_str", "N/A")).strip()
        eta = _limpar_ansi(d.get("_eta_str", "N/A")).strip()
        print(f"\r  ⬇  {pct:>6}  │  {vel:>12}  │  ETA {eta:>6}", end="", flush=True)

    elif d["status"] == "finished":
        print("\r  ✔  Download concluído. Processando...          ")


def _limpar_ansi(texto: str) -> str:
    """Remove códigos de escape ANSI de strings do yt-dlp."""
    return re.sub(r"\x1b\[[0-9;]*m", "", texto)


# ──────────────────────────────────────────────
# Construção das opções do yt-dlp
# ──────────────────────────────────────────────

def _opcoes_mp4(
    ffmpeg_path: str,
    resolucao: str = "melhor",
    eh_playlist: bool = False,
) -> dict:
    """
    Monta o dicionário de opções para download em MP4.

    Args:
        ffmpeg_path: Caminho absoluto para o executável ffmpeg.
        resolucao:   Resolução desejada ('melhor', '1080', '720', ...).
        eh_playlist: Se True, usa template de nome com índice da playlist.

    Returns:
        Dicionário de opções para YoutubeDL.
    """
    if resolucao == "melhor":
        fmt = "bestvideo+bestaudio/best"
    else:
        # Tenta a resolução pedida; cai para a melhor disponível abaixo dela
        fmt = (
            f"bestvideo[height<={resolucao}]+bestaudio"
            f"/bestvideo[height<={resolucao}]+bestaudio/best"
        )

    template_padrao = str(OUTPUT_DIR / "%(title)s.%(ext)s")
    template_playlist = str(OUTPUT_DIR / "%(playlist_index)s_%(title)s.%(ext)s")

    return {
        "format": fmt,
        "merge_output_format": "mp4",
        "outtmpl": {
            "default": template_padrao,
            "pl_video": template_playlist if eh_playlist else template_padrao,
        },
        # Garante recodificação de áudio compatível com MP4
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
        "postprocessor_args": {
            # Copia stream de vídeo sem recodificar; recodifica áudio para AAC
            "FFmpegVideoConvertor": ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k"],
        },
        "ffmpeg_location": ffmpeg_path,
        "progress_hooks": [_hook_progresso],
        "noplaylist": not eh_playlist,
        "quiet": True,
        "no_warnings": False,
        "ignoreerrors": False,
        # Restaura títulos com caracteres especiais de forma segura
        "restrictfilenames": False,
        "windowsfilenames": True,
    }


def _opcoes_mp3(
    ffmpeg_path: str,
    eh_playlist: bool = False,
) -> dict:
    """
    Monta o dicionário de opções para download em MP3 (melhor qualidade).

    Args:
        ffmpeg_path: Caminho absoluto para o executável ffmpeg.
        eh_playlist: Se True, usa template de nome com índice da playlist.

    Returns:
        Dicionário de opções para YoutubeDL.
    """
    template_padrao = str(OUTPUT_DIR / "%(title)s.%(ext)s")
    template_playlist = str(OUTPUT_DIR / "%(playlist_index)s_%(title)s.%(ext)s")

    return {
        "format": "bestaudio/best",
        "outtmpl": {
            "default": template_padrao,
            "pl_video": template_playlist if eh_playlist else template_padrao,
        },
        "postprocessors": [
            {
                # Extrai e converte para MP3
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "0",  # 0 = VBR máxima qualidade (~320 kbps)
            },
            {
                # Embute metadados (artista, título, capa) no MP3
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                # Incorpora thumbnail como capa do álbum
                "key": "EmbedThumbnail",
            },
        ],
        "ffmpeg_location": ffmpeg_path,
        "writethumbnail": True,          # necessário para EmbedThumbnail
        "progress_hooks": [_hook_progresso],
        "noplaylist": not eh_playlist,
        "quiet": True,
        "no_warnings": False,
        "ignoreerrors": False,
        "windowsfilenames": True,
    }


# ──────────────────────────────────────────────
# Função principal de download
# ──────────────────────────────────────────────

def baixar_video(
    url: str,
    formato: FormatoSaida = "mp4",
    resolucao: str = "melhor",
    ffmpeg_path: Optional[str] = None,
) -> Path:
    """
    Faz o download de um vídeo ou playlist do YouTube e converte para o formato pedido.

    Args:
        url:         URL do vídeo ou playlist.
        formato:     'mp4' para vídeo, 'mp3' para áudio.
        resolucao:   Resolução desejada para MP4 ('melhor', '1080', '720', ...).
                     Ignorado quando formato='mp3'.
        ffmpeg_path: Caminho para o ffmpeg. Se None, yt-dlp usa o do PATH.

    Returns:
        Path do arquivo gerado (ou da pasta output, no caso de playlist).

    Raises:
        DownloadError: Erro do yt-dlp (privado, indisponível, etc.)
        ExtractorError: URL não reconhecida pelo yt-dlp.
        PermissionError: Sem permissão de escrita na pasta de saída.
        RuntimeError: ffmpeg não encontrado.
    """
    if ffmpeg_path is None:
        raise RuntimeError(
            "ffmpeg não encontrado. Instale-o e adicione ao PATH, "
            "ou coloque ffmpeg.exe em tools/."
        )

    eh_playlist = "playlist" in url

    if formato == "mp3":
        opcoes = _opcoes_mp3(ffmpeg_path, eh_playlist)
    else:
        opcoes = _opcoes_mp4(ffmpeg_path, resolucao, eh_playlist)

    try:
        with YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)

            # Playlist → retorna a pasta inteira
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
        raise  # Re-lança para tratamento no main.py