"""
main.py — Launcher da aplicação.

Modo .exe (usuário final):  abre sempre a GUI, sem CMD, sem loop.
Modo script (dev):          abre GUI se Tkinter disponível, senão CLI.

A separação entre frozen/script é feita ANTES de qualquer import pesado
para evitar que o PyInstaller em modo --windowed tente criar um console.
"""

import sys


def _eh_frozen() -> bool:
    """True quando rodando como .exe gerado pelo PyInstaller."""
    return getattr(sys, "frozen", False)


def _rodar_gui() -> None:
    """Abre a janela principal. Qualquer erro vira messagebox, nunca traceback."""
    import tkinter as tk
    from tkinter import messagebox

    try:
        from gui import App
        app = App()
        app.mainloop()
    except Exception as exc:
        # Último recurso: janela de erro simples antes de fechar
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro ao iniciar", str(exc))
        root.destroy()


def _rodar_cli() -> None:
    """CLI completa — usada apenas por devs via terminal."""
    import signal
    import threading
    from pathlib import Path
    from yt_dlp.utils import DownloadError, ExtractorError

    from config import get_output_dir, set_output_dir
    from downloader import baixar_video, CanceladoException, RESOLUCOES_DISPONIVEIS, FormatoSaida
    from updater import atualizar_ytdlp
    from utils import validar_url, verificar_ffmpeg, cabecalho, linha_separadora

    cabecalho()
    atualizar_ytdlp()

    ffmpeg = verificar_ffmpeg()
    if not ffmpeg:
        print("\n  ✖  ffmpeg não encontrado.")
        print("     • Coloque ffmpeg.exe na pasta tools/")
        print("     • Ou instale e adicione ao PATH do sistema.")
        return

    print(f"\n  ✔  ffmpeg: {ffmpeg}")

    pasta_atual = get_output_dir()
    print(f"\n  📁  Pasta de destino: {pasta_atual}")
    if input("     Alterar? [S/Enter=manter]: ").strip().lower() == "s":
        nova = input("     Novo caminho: ").strip()
        if nova:
            try:
                set_output_dir(Path(nova))
                pasta_atual = Path(nova)
            except Exception as e:
                print(f"  ⚠  Mantendo pasta anterior. ({e})")
                pasta_atual = get_output_dir()

    while True:
        url = input("\n  Cole a URL do YouTube: ").strip()
        if validar_url(url):
            break
        print("  ✖  URL inválida.")

    print("\n  Formato:  [1] MP4 — vídeo   [2] MP3 — áudio")
    while True:
        f = input("  Escolha [1/2, Enter=1]: ").strip()
        if f in ("", "1"):
            formato: FormatoSaida = "mp4"; break
        if f == "2":
            formato = "mp3"; break
        print("  ✖  Digite 1 ou 2.")

    resolucao = "melhor"
    if formato == "mp4":
        print("\n  Resolução:")
        for i, r in enumerate(RESOLUCOES_DISPONIVEIS, 1):
            print(f"    [{i}] {'melhor (padrão)' if r == 'melhor' else r + 'p'}")
        while True:
            r = input(f"  Escolha [1-{len(RESOLUCOES_DISPONIVEIS)}, Enter=melhor]: ").strip()
            if r == "":
                break
            if r.isdigit() and 1 <= int(r) <= len(RESOLUCOES_DISPONIVEIS):
                resolucao = RESOLUCOES_DISPONIVEIS[int(r) - 1]; break
            print("  ✖  Opção inválida.")

    print()
    print(linha_separadora())
    print(f"  URL:     {url}")
    print(f"  Formato: {formato.upper()}")
    if formato == "mp4":
        print(f"  Resolução: {'Melhor disponível' if resolucao == 'melhor' else resolucao + 'p'}")
    print(f"  Destino: {pasta_atual}")
    print(linha_separadora())

    if input("\n  Iniciar? [Enter=sim / N=cancelar]: ").strip().lower() in ("n", "não", "no"):
        print("\n  Cancelado.")
        return

    cancel_event = threading.Event()

    def _sig(sig, frame):
        print("\n\n  ⏹  Cancelando...")
        cancel_event.set()

    signal.signal(signal.SIGINT, _sig)
    print("\n  Pressione Ctrl+C para cancelar.\n")

    try:
        arquivo = baixar_video(
            url=url, formato=formato, resolucao=resolucao,
            ffmpeg_path=ffmpeg, output_dir=pasta_atual, cancel_event=cancel_event,
        )
        print()
        print(linha_separadora())
        print("  ✔  Concluído!")
        print(f"  📁 Salvo em: {arquivo}")
        print(linha_separadora())
    except CanceladoException:
        print("\n  ✖  Cancelado.")
    except PermissionError as e:
        print(f"\n  ✖  {e}")
    except (DownloadError, ExtractorError) as e:
        msg = str(e).lower()
        if "private"     in msg: print("\n  ✖  Vídeo privado.")
        elif "unavailable" in msg: print("\n  ✖  Vídeo indisponível.")
        elif "sign in"   in msg: print("\n  ✖  Conteúdo exige login.")
        elif "network"   in msg or "urlopen" in msg: print("\n  ✖  Sem internet.")
        else: print(f"\n  ✖  Erro: {e}")
    except Exception as e:
        print(f"\n  ✖  Erro inesperado: {e}")


def main() -> None:
    if _eh_frozen():
        # .exe → sempre GUI, sem fallback para CLI (evita loop de console)
        _rodar_gui()
    else:
        # Script dev → tenta GUI; se não tiver Tkinter, usa CLI
        try:
            import tkinter  # noqa: F401
            _rodar_gui()
        except ImportError:
            _rodar_cli()


if __name__ == "__main__":
    # Obrigatório no Windows para executáveis PyInstaller --onefile que
    # usam threading/subprocess internamente (yt-dlp, ffmpeg, pip).
    # Sem isso, cada processo filho relança o main() → loop de janelas.
    import multiprocessing
    multiprocessing.freeze_support()
    main()
