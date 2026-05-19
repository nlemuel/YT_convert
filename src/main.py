from downloader import baixar_video
from utils import validar_url, verificar_ffmpeg

def main():
    print("=" * 50)
    print(" YouTube -> MP4 Downloader")
    print("=" * 50)

    if not verificar_ffmpeg():
        print("\nERRO: ffmpeg não encontrado.")
        print("Instale e adicione ao PATH. Consulte o README para seguir o passo a passo.")
        return

    url = input("\nCole a URL do YouTube: ").strip()

    if not validar_url(url):
        print("\nERRO: URL inválida.")
        return

    try:
        arquivo = baixar_video(url)

        print("\n")
        print("Sucesso!")
        print(f"Arquivo salvo em:\n{arquivo}")

    except Exception as e:
        erro = str(e).lower()

        if "private" in erro:
            print("Vídeo privado.")
        elif "unavailable" in erro:
            print("Vídeo indisponível.")
        elif "permission" in erro:
            print("Sem permissão para salvar arquivo.")
        else:
            print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    main()