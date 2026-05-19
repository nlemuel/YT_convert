from pathlib import Path
from yt_dlp import YoutubeDL
from config import OUTPUT_DIR


def mostrar_progresso(d):
    """
    Callback de progresso.
    """
    if d["status"] == "downloading":
        percentual = d.get("_percent_str", "").strip()
        velocidade = d.get("_speed_str", "N/A")
        eta = d.get("_eta_str", "N/A")

        print(
            f"\rBaixando: {percentual} | "
            f"Velocidade: {velocidade} | "
            f"ETA: {eta}",
            end=""
        )

    elif d["status"] == "finished":
        print("\nDownload concluído. Convertendo para MP4...")


def baixar_video(url: str) -> Path:
    """
    Baixa vídeo ou playlist automaticamente.
    """

    # detecta playlist
    noplaylist = "playlist" not in url

    opcoes = {
        "format": "bestvideo+bestaudio",

        # para vídeos e playlists
        "outtmpl": {
            "default": str(OUTPUT_DIR / "%(title)s.%(ext)s"),
            "pl_video": str(OUTPUT_DIR / "%(playlist_index)s_%(title)s.%(ext)s"),
},

        "merge_output_format": "mp4",

        "postprocessor_args": [
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k"
        ],

        "progress_hooks": [mostrar_progresso],

        "noplaylist": noplaylist,

        "quiet": True
    }

    with YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)

        # se for playlist retorna pasta
        if "entries" in info:
            return OUTPUT_DIR

        nome = ydl.prepare_filename(info)

        return Path(nome).with_suffix(".mp4")