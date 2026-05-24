import sys
from pathlib import Path
from yt_dlp.utils import DownloadError, ExtractorError

from config import OUTPUT_DIR
from downloader import baixar_video, RESOLUCOES_DISPONIVEIS, FormatoSaida
from utils import validar_url, verificar_ffmpeg, cabecalho, linha_separadora


# ──────────────────────────────────────────────
# Helpers de entrada
# ──────────────────────────────────────────────

def _pedir_url() -> str:
    """Solicita a URL ao usuário e valida no loop."""
    while True:
        url = input("\n  Cole a URL do YouTube: ").strip()
        if validar_url(url):
            return url
        print("  ✖  URL inválida. Use um link do youtube.com ou youtu.be.")


def _pedir_formato() -> FormatoSaida:
    """Solicita o formato de saída (MP4 ou MP3)."""
    print("\n  Formato de saída:")
    print("    [1] MP4 — vídeo (padrão)")
    print("    [2] MP3 — apenas áudio (melhor qualidade)")

    while True:
        escolha = input("\n  Escolha [1/2, Enter=1]: ").strip()
        if escolha in ("", "1"):
            return "mp4"
        if escolha == "2":
            return "mp3"
        print("  ✖  Opção inválida. Digite 1 ou 2.")


def _pedir_resolucao() -> str:
    """Solicita a resolução desejada para vídeo MP4."""
    opcoes_exibidas = [r if r != "melhor" else "melhor (padrão)" for r in RESOLUCOES_DISPONIVEIS]

    print("\n  Resolução de vídeo:")
    for i, op in enumerate(opcoes_exibidas, 1):
        print(f"    [{i}] {op}p" if "melhor" not in op else f"    [{i}] {op}")

    while True:
        escolha = input(f"\n  Escolha [1-{len(RESOLUCOES_DISPONIVEIS)}, Enter=melhor]: ").strip()
        if escolha == "":
            return "melhor"
        if escolha.isdigit():
            idx = int(escolha) - 1
            if 0 <= idx < len(RESOLUCOES_DISPONIVEIS):
                return RESOLUCOES_DISPONIVEIS[idx]
        print(f"  ✖  Opção inválida. Digite um número entre 1 e {len(RESOLUCOES_DISPONIVEIS)}.")


# ──────────────────────────────────────────────
# Tratamento de erros do yt-dlp
# ──────────────────────────────────────────────

def _tratar_erro(e: Exception) -> None:
    """Exibe mensagem amigável baseada no tipo/mensagem do erro."""
    msg = str(e).lower()

    if isinstance(e, RuntimeError):
        print(f"\n  ✖  {e}")
    elif isinstance(e, PermissionError):
        print(f"\n  ✖  {e}")
    elif "private" in msg:
        print("\n  ✖  Este vídeo é privado e não pode ser baixado.")
    elif "unavailable" in msg:
        print("\n  ✖  Vídeo indisponível (removido, bloqueado por região, etc.).")
    elif "sign in" in msg or "login" in msg:
        print("\n  ✖  Este conteúdo exige login. Não é possível baixar.")
    elif "network" in msg or "connection" in msg or "urlopen" in msg:
        print("\n  ✖  Sem conexão com a internet. Verifique sua rede e tente novamente.")
    elif isinstance(e, (DownloadError, ExtractorError)):
        print(f"\n  ✖  Erro ao baixar: {e}")
    else:
        print(f"\n  ✖  Erro inesperado: {e}")


# ──────────────────────────────────────────────
# Fluxo principal
# ──────────────────────────────────────────────

def main() -> None:
    """Ponto de entrada da aplicação."""
    cabecalho()

    # 1. Verifica ffmpeg ─────────────────────────
    ffmpeg = verificar_ffmpeg()
    if not ffmpeg:
        print("\n  ✖  ffmpeg não encontrado.")
        print("     • Coloque ffmpeg.exe na pasta tools/")
        print("     • Ou instale e adicione ao PATH do sistema.")
        print("     • Consulte o README para o passo a passo.")
        _aguardar_saida()
        return

    print(f"\n  ✔  ffmpeg: {ffmpeg}")

    # 2. Coleta inputs do usuário ────────────────
    url = _pedir_url()
    formato = _pedir_formato()
    resolucao = _pedir_resolucao() if formato == "mp4" else "melhor"

    # 3. Resumo antes de iniciar ─────────────────
    print()
    print(linha_separadora())
    print(f"  URL:      {url}")
    print(f"  Formato:  {formato.upper()}")
    if formato == "mp4":
        res_exibida = "Melhor disponível" if resolucao == "melhor" else f"{resolucao}p"
        print(f"  Resolução: {res_exibida}")
    print(f"  Destino:  {OUTPUT_DIR}")
    print(linha_separadora())

    confirmacao = input("\n  Iniciar download? [Enter=sim / N=cancelar]: ").strip().lower()
    if confirmacao in ("n", "nao", "não", "no"):
        print("\n  Cancelado.")
        _aguardar_saida()
        return

    # 4. Download ────────────────────────────────
    print()
    try:
        arquivo = baixar_video(
            url=url,
            formato=formato,
            resolucao=resolucao,
            ffmpeg_path=ffmpeg,
        )

        print()
        print(linha_separadora())
        print("  ✔  Concluído com sucesso!")
        print(f"  📁 Salvo em: {arquivo}")
        print(linha_separadora())

    except Exception as e:
        _tratar_erro(e)

    _aguardar_saida()


def _aguardar_saida() -> None:
    """
    Quando executando como .exe, aguarda tecla antes de fechar,
    para o usuário poder ler a mensagem final.
    """
    import getattr as _ga  # noqa: F401
    if getattr(sys, "frozen", False):
        input("\n  Pressione Enter para fechar...")


if __name__ == "__main__":
    main()
