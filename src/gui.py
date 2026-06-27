"""
gui.py — Interface gráfica Tkinter para o YouTube Downloader.

Layout:
  ┌─────────────────────────────────────────────┐
  │  🎬 Título                       │
  ├─────────────────────────────────────────────┤
  │  URL  [_________________________________]    │
  │  Formato  ◉ MP4  ○ MP3                       │
  │  Resolução  [▼ Melhor disponível]            │
  │  Destino  [C:\...\output]  [Alterar]         │
  ├─────────────────────────────────────────────┤
  │  [████████░░░░░░░░]  47%  •  2.3 MB/s       │
  │  status...                                   │
  ├─────────────────────────────────────────────┤
  │  [  Baixar  ]  [  Cancelar  ]               │
  └─────────────────────────────────────────────┘

Threading: o download roda em thread separada para não travar a UI.
"""

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from yt_dlp.utils import DownloadError, ExtractorError

from config import BASE_DIR, get_output_dir, set_output_dir

# Ícone da janela — coloque icon.ico em assets/ antes de buildar
_ICON_PATH: Path = BASE_DIR / "assets" / "icon.ico"
from downloader import (
    RESOLUCOES_DISPONIVEIS,
    CanceladoException,
    FormatoSaida,
    baixar_video,
)
from updater import atualizar_ytdlp
from utils import validar_url, verificar_ffmpeg

# ── Paleta de cores ───────────────────────────────────────────────────────────
COR_BG       = "#1e1e2e"   # fundo principal
COR_SURFACE  = "#2a2a3e"   # painéis internos
COR_BORDA    = "#3a3a5c"   # bordas sutis
COR_TEXTO    = "#cdd6f4"   # texto principal
COR_SUBTEXTO = "#6c7086"   # texto secundário
COR_ACCENT   = "#89b4fa"   # azul destaque
COR_SUCESSO  = "#a6e3a1"   # verde
COR_ERRO     = "#f38ba8"   # vermelho
COR_AVISO    = "#f9e2af"   # amarelo
COR_BTN_DL   = "#89b4fa"   # botão baixar
COR_BTN_STOP = "#f38ba8"   # botão cancelar
COR_BTN_TXT  = "#1e1e2e"   # texto dos botões


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Oculta a janela enquanto constrói para evitar flash de posição
        self.withdraw()

        self.title("Bibi's Download")
        self.resizable(False, False)
        self.configure(bg=COR_BG)

        # Ícone da janela e da barra de tarefas
        if _ICON_PATH.exists():
            try:
                self.iconbitmap(str(_ICON_PATH))
            except Exception:
                pass  # ícone inválido não deve travar a aplicação

        # Estado interno
        self._cancel_event  = threading.Event()
        self._baixando      = False
        self._ffmpeg: Optional[str] = None
        self._output_dir    = get_output_dir()

        self._build_ui()
        self._centralizar()

        # Exibe a janela já centralizada (sem flash)
        self.deiconify()

        # Verificações em background (ffmpeg + update yt-dlp)
        threading.Thread(target=self._inicializar, daemon=True).start()

    # ── Construção da UI ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        pad = {"padx": 18, "pady": 6}

        # Título
        tk.Label(
            self, text="🎬  Bibi's Download",
            font=("Segoe UI", 14, "bold"),
            bg=COR_BG, fg=COR_ACCENT,
        ).pack(pady=(18, 4))

        tk.Label(
            self, text="MP4 • MP3 • Playlists",
            font=("Segoe UI", 9), bg=COR_BG, fg=COR_SUBTEXTO,
        ).pack(pady=(0, 12))

        # Separador
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        # Frame principal
        frame = tk.Frame(self, bg=COR_BG)
        frame.pack(fill="x", **pad)

        # ── URL ──────────────────────────────────────────────────────────────
        self._label_row(frame, "Bibi, baixa para mim esse link:")
        self._url_var = tk.StringVar()
        self._entry_url = tk.Entry(
            frame, textvariable=self._url_var, width=52,
            bg=COR_SURFACE, fg=COR_TEXTO, insertbackground=COR_TEXTO,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=1, highlightbackground=COR_BORDA,
            highlightcolor=COR_ACCENT,
        )
        self._entry_url.pack(fill="x", pady=(2, 10))

        # ── Formato ───────────────────────────────────────────────────────────
        self._label_row(frame, "O formato tem que ser:")
        fmt_frame = tk.Frame(frame, bg=COR_BG)
        fmt_frame.pack(fill="x", pady=(2, 10))

        self._fmt_var = tk.StringVar(value="mp4")
        for val, txt in [("mp4", "🎬  MP4 — Vídeo"), ("mp3", "🎵  MP3 — Áudio")]:
            rb = tk.Radiobutton(
                fmt_frame, text=txt, variable=self._fmt_var, value=val,
                command=self._ao_mudar_formato,
                bg=COR_BG, fg=COR_TEXTO, selectcolor=COR_SURFACE,
                activebackground=COR_BG, activeforeground=COR_ACCENT,
                font=("Segoe UI", 10),
            )
            rb.pack(side="left", padx=(0, 16))

        # ── Resolução ─────────────────────────────────────────────────────────
        self._label_row(frame, "Resolução  (apenas MP4)")
        opcoes_res = ["Melhor disponível"] + [f"{r}p" for r in RESOLUCOES_DISPONIVEIS if r != "melhor"]
        self._res_var = tk.StringVar(value="Melhor disponível")
        self._combo_res = ttk.Combobox(
            frame, textvariable=self._res_var,
            values=opcoes_res, state="readonly", width=24,
            font=("Segoe UI", 10),
        )
        self._combo_res.pack(anchor="w", pady=(2, 10))

        # ── Pasta de destino ──────────────────────────────────────────────────
        self._label_row(frame, "Deixa guardado na pasta:")
        dest_frame = tk.Frame(frame, bg=COR_BG)
        dest_frame.pack(fill="x", pady=(2, 10))

        self._dest_var = tk.StringVar(value=str(self._output_dir))
        tk.Entry(
            dest_frame, textvariable=self._dest_var,
            bg=COR_SURFACE, fg=COR_TEXTO, relief="flat",
            font=("Segoe UI", 9), state="readonly",
            readonlybackground=COR_SURFACE,
            highlightthickness=1, highlightbackground=COR_BORDA,
            width=38,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            dest_frame, text="Alterar",
            command=self._escolher_pasta,
            bg=COR_SURFACE, fg=COR_ACCENT, relief="flat",
            font=("Segoe UI", 9), cursor="hand2",
            activebackground=COR_BORDA, activeforeground=COR_TEXTO,
            padx=10,
        ).pack(side="left")

        # Separador
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16, pady=4)

        # ── Progresso ─────────────────────────────────────────────────────────
        prog_frame = tk.Frame(self, bg=COR_BG)
        prog_frame.pack(fill="x", padx=18, pady=4)

        self._progress = ttk.Progressbar(
            prog_frame, orient="horizontal", mode="determinate", length=420,
        )
        self._progress.pack(fill="x", pady=(4, 4))

        info_frame = tk.Frame(prog_frame, bg=COR_BG)
        info_frame.pack(fill="x")

        self._pct_label = tk.Label(
            info_frame, text="", font=("Segoe UI", 9, "bold"),
            bg=COR_BG, fg=COR_ACCENT, width=8, anchor="w",
        )
        self._pct_label.pack(side="left")

        self._vel_label = tk.Label(
            info_frame, text="", font=("Segoe UI", 9),
            bg=COR_BG, fg=COR_SUBTEXTO,
        )
        self._vel_label.pack(side="left", padx=8)

        self._status_label = tk.Label(
            self, text="Aguardando...", font=("Segoe UI", 9),
            bg=COR_BG, fg=COR_SUBTEXTO, wraplength=430, justify="left",
        )
        self._status_label.pack(padx=18, pady=(0, 8), anchor="w")

        # Separador
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        # ── Botões ────────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=COR_BG)
        btn_frame.pack(pady=14)

        self._btn_baixar = tk.Button(
            btn_frame, text="⬇   Baixar",
            command=self._iniciar_download,
            bg=COR_BTN_DL, fg=COR_BTN_TXT,
            font=("Segoe UI", 11, "bold"), relief="flat",
            cursor="hand2", padx=28, pady=8,
            activebackground=COR_ACCENT, activeforeground=COR_BTN_TXT,
        )
        self._btn_baixar.pack(side="left", padx=8)

        self._btn_cancelar = tk.Button(
            btn_frame, text="⏹   Cancelar",
            command=self._cancelar_download,
            bg=COR_SURFACE, fg=COR_SUBTEXTO,
            font=("Segoe UI", 11), relief="flat",
            cursor="hand2", padx=20, pady=8,
            state="disabled",
            activebackground=COR_BTN_STOP, activeforeground=COR_BTN_TXT,
        )
        self._btn_cancelar.pack(side="left", padx=8)

        # Estilo ttk
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Horizontal.TProgressbar",
                        troughcolor=COR_SURFACE,
                        background=COR_ACCENT,
                        bordercolor=COR_BG,
                        lightcolor=COR_ACCENT,
                        darkcolor=COR_ACCENT)
        style.configure("TCombobox",
                        fieldbackground=COR_SURFACE,
                        background=COR_SURFACE,
                        foreground=COR_TEXTO,
                        selectbackground=COR_BORDA,
                        selectforeground=COR_TEXTO)
        style.map("TCombobox", fieldbackground=[("readonly", COR_SURFACE)])

    def _label_row(self, parent: tk.Frame, texto: str) -> None:
        tk.Label(
            parent, text=texto, font=("Segoe UI", 9),
            bg=COR_BG, fg=COR_SUBTEXTO, anchor="w",
        ).pack(fill="x")

    def _centralizar(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    # ── Inicialização assíncrona ───────────────────────────────────────────────

    def _inicializar(self) -> None:
        """Roda em thread: verifica ffmpeg e atualiza yt-dlp."""
        self._set_status("Verificando ffmpeg...", COR_SUBTEXTO)
        self._ffmpeg = verificar_ffmpeg()

        if not self._ffmpeg:
            self._set_status(
                "❌  ffmpeg não encontrado. Coloque ffmpeg.exe em tools/ ou instale no PATH.",
                COR_ERRO,
            )
            self.after(0, lambda: self._btn_baixar.config(state="disabled"))
            return

        self._set_status("🔄  Verificando atualização do yt-dlp...", COR_SUBTEXTO)
        atualizar_ytdlp(callback=lambda msg: self._set_status(msg, COR_SUBTEXTO))
        self._set_status("✔  Pronto. Cole uma URL e clique em Baixar.", COR_SUCESSO)

    # ── Eventos de UI ─────────────────────────────────────────────────────────

    def _ao_mudar_formato(self) -> None:
        estado = "readonly" if self._fmt_var.get() == "mp4" else "disabled"
        self._combo_res.config(state=estado)

    def _escolher_pasta(self) -> None:
        pasta = filedialog.askdirectory(
            title="Escolha a pasta de destino",
            initialdir=str(self._output_dir),
        )
        if pasta:
            self._output_dir = Path(pasta)
            set_output_dir(self._output_dir)
            self._dest_var.set(str(self._output_dir))

    # ── Download ──────────────────────────────────────────────────────────────

    def _iniciar_download(self) -> None:
        if self._baixando:
            return

        url = self._url_var.get().strip()
        if not validar_url(url):
            messagebox.showerror("URL inválida", "Cole uma URL válida do YouTube.")
            return

        if not self._ffmpeg:
            messagebox.showerror(
                "ffmpeg não encontrado",
                "Coloque ffmpeg.exe na pasta tools/ ou instale no PATH do sistema.",
            )
            return

        formato: FormatoSaida = self._fmt_var.get()  # type: ignore
        res_txt = self._res_var.get()
        resolucao = "melhor" if res_txt == "Melhor disponível" else res_txt.replace("p", "")

        self._cancel_event.clear()
        self._baixando = True
        self._progress["value"] = 0
        self._pct_label.config(text="")
        self._vel_label.config(text="")
        self._btn_baixar.config(state="disabled")
        self._btn_cancelar.config(state="normal", bg=COR_BTN_STOP, fg=COR_BTN_TXT)
        self._set_status("⬇  Iniciando download...", COR_ACCENT)

        threading.Thread(
            target=self._thread_download,
            args=(url, formato, resolucao),
            daemon=True,
        ).start()

    def _thread_download(self, url: str, formato: FormatoSaida, resolucao: str) -> None:
        """Roda em thread separada para não travar a UI."""
        try:
            arquivo = baixar_video(
                url=url,
                formato=formato,
                resolucao=resolucao,
                ffmpeg_path=self._ffmpeg,
                output_dir=self._output_dir,
                cancel_event=self._cancel_event,
                progresso_callback=self._cb_progresso,
            )
            self.after(0, self._ao_concluir, arquivo)

        except CanceladoException:
            self.after(0, self._ao_cancelar_ui)
        except (DownloadError, ExtractorError) as e:
            self.after(0, self._ao_erro, str(e))
        except PermissionError as e:
            self.after(0, self._ao_erro, str(e))
        except Exception as e:
            self.after(0, self._ao_erro, f"Erro inesperado: {e}")

    def _cb_progresso(self, pct: float, vel: str, eta: str) -> None:
        """Callback chamado pelo downloader — atualiza UI via after() (thread-safe)."""
        def _update():
            self._progress["value"] = pct
            self._pct_label.config(text=f"{pct:.0f}%")
            info = f"{vel}  •  ETA {eta}" if vel and vel != "N/A" else ""
            self._vel_label.config(text=info)
            if pct >= 100:
                self._set_status("⚙  Processando (ffmpeg)...", COR_AVISO)
            else:
                self._set_status(f"⬇  Pera aí que eu já tô baixando...  {pct:.1f}%", COR_ACCENT)
        self.after(0, _update)

    def _cancelar_download(self) -> None:
        if self._baixando:
            self._cancel_event.set()
            self._set_status("⏹  Cancelando...", COR_AVISO)
            self._btn_cancelar.config(state="disabled")

    # ── Callbacks de conclusão ────────────────────────────────────────────────

    def _ao_concluir(self, arquivo: Path) -> None:
        self._baixando = False
        self._progress["value"] = 100
        self._pct_label.config(text="100%")
        self._vel_label.config(text="")
        self._set_status(f"✔  Salvo em: {arquivo}", COR_SUCESSO)
        self._resetar_botoes()
        messagebox.showinfo("Concluído! Mais alguma coisa?", f"Arquivo salvo em:\n{arquivo}")

    def _ao_cancelar_ui(self) -> None:
        self._baixando = False
        self._progress["value"] = 0
        self._pct_label.config(text="")
        self._vel_label.config(text="")
        self._set_status("✖  Download cancelado.", COR_AVISO)
        self._resetar_botoes()

    def _ao_erro(self, msg: str) -> None:
        self._baixando = False
        self._progress["value"] = 0
        msg_lower = msg.lower()
        if "private"    in msg_lower: amigavel = "Vídeo privado."
        elif "unavailable" in msg_lower: amigavel = "Vídeo indisponível."
        elif "sign in"  in msg_lower: amigavel = "Este conteúdo exige login."
        elif "network"  in msg_lower or "urlopen" in msg_lower: amigavel = "Sem conexão com a internet."
        else: amigavel = msg
        self._set_status(f"❌  {amigavel}", COR_ERRO)
        self._resetar_botoes()
        messagebox.showerror("Erro no download", amigavel)

    def _resetar_botoes(self) -> None:
        self._btn_baixar.config(state="normal")
        self._btn_cancelar.config(state="disabled", bg=COR_SURFACE, fg=COR_SUBTEXTO)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, cor: str = COR_SUBTEXTO) -> None:
        """Atualiza o label de status (pode ser chamado de qualquer thread via after)."""
        def _update():
            self._status_label.config(text=msg, fg=cor)
        self.after(0, _update)
