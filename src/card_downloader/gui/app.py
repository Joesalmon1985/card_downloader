import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from card_downloader.gui.options import DEFAULT_OUTPUT_DIR, GuiRunOptions
from card_downloader.gui.runner import RunResult, execute_run


class CardDownloaderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Card Downloader")
        self.root.minsize(520, 480)

        self._running = False
        self._last_result: RunResult | None = None
        self._widgets: list[tk.Widget] = []

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}
        main = ttk.Frame(self.root, padding=8)
        main.pack(fill=tk.BOTH, expand=True)

        # Decklist
        ttk.Label(main, text="Decklist:").grid(row=0, column=0, sticky=tk.W, **pad)
        self.decklist_var = tk.StringVar()
        deck_frame = ttk.Frame(main)
        deck_frame.grid(row=0, column=1, sticky=tk.EW, **pad)
        main.columnconfigure(1, weight=1)
        self.decklist_entry = ttk.Entry(deck_frame, textvariable=self.decklist_var)
        self.decklist_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(deck_frame, text="Browse…", command=self._browse_decklist).pack(side=tk.LEFT, padx=(4, 0))

        # Output
        ttk.Label(main, text="Output folder:").grid(row=1, column=0, sticky=tk.W, **pad)
        self.output_var = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        out_frame = ttk.Frame(main)
        out_frame.grid(row=1, column=1, sticky=tk.EW, **pad)
        self.output_entry = ttk.Entry(out_frame, textvariable=self.output_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_frame, text="Browse…", command=self._browse_output).pack(side=tk.LEFT, padx=(4, 0))

        # Options
        opts_frame = ttk.LabelFrame(main, text="Options", padding=8)
        opts_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, **pad)

        ttk.Label(opts_frame, text="Image size:").grid(row=0, column=0, sticky=tk.W)
        self.size_var = tk.StringVar(value="png")
        size_combo = ttk.Combobox(
            opts_frame, textvariable=self.size_var, values=["png", "large", "normal"], state="readonly", width=10
        )
        size_combo.grid(row=0, column=1, sticky=tk.W, padx=(4, 16))

        ttk.Label(opts_frame, text="Paper:").grid(row=0, column=2, sticky=tk.W)
        self.paper_var = tk.StringVar(value="a4")
        paper_combo = ttk.Combobox(
            opts_frame, textvariable=self.paper_var, values=["a4", "letter"], state="readonly", width=10
        )
        paper_combo.grid(row=0, column=3, sticky=tk.W, padx=4)

        ttk.Label(opts_frame, text="DPI:").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        self.dpi_var = tk.StringVar(value="300")
        ttk.Entry(opts_frame, textvariable=self.dpi_var, width=8).grid(row=1, column=1, sticky=tk.W, pady=(8, 0))

        ttk.Label(opts_frame, text="Gap (mm):").grid(row=1, column=2, sticky=tk.W, pady=(8, 0))
        self.gap_var = tk.StringVar(value="1.0")
        ttk.Entry(opts_frame, textvariable=self.gap_var, width=8).grid(row=1, column=3, sticky=tk.W, pady=(8, 0))

        self.build_pdf_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="Build PDF proxy sheets", variable=self.build_pdf_var).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(8, 0)
        )

        self.allow_ub_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="Allow Universes Beyond printings", variable=self.allow_ub_var).grid(
            row=3, column=0, columnspan=2, sticky=tk.W
        )

        self.allow_wb_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="Allow white-bordered printings", variable=self.allow_wb_var).grid(
            row=4, column=0, columnspan=2, sticky=tk.W
        )

        self.allow_promo_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts_frame, text="Allow promo / special printings", variable=self.allow_promo_var).grid(
            row=5, column=0, columnspan=2, sticky=tk.W
        )

        # Run + status
        run_frame = ttk.Frame(main)
        run_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, **pad)
        self.run_btn = ttk.Button(run_frame, text="Download & Build Proxies", command=self._on_run)
        self.run_btn.pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(run_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=(12, 0))

        # Log
        ttk.Label(main, text="Log:").grid(row=4, column=0, sticky=tk.NW, **pad)
        self.log_text = scrolledtext.ScrolledText(main, height=12, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.grid(row=4, column=1, sticky=tk.NSEW, **pad)
        main.rowconfigure(4, weight=1)

        # Actions
        action_frame = ttk.Frame(main)
        action_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, **pad)
        self.open_folder_btn = ttk.Button(action_frame, text="Open output folder", command=self._open_folder, state=tk.DISABLED)
        self.open_folder_btn.pack(side=tk.LEFT)
        self.open_pdf_btn = ttk.Button(action_frame, text="Open PDF", command=self._open_pdf, state=tk.DISABLED)
        self.open_pdf_btn.pack(side=tk.LEFT, padx=(8, 0))

        self._widgets = [
            self.decklist_entry,
            self.output_entry,
            size_combo,
            paper_combo,
            self.run_btn,
        ]

    def _browse_decklist(self) -> None:
        path = filedialog.askopenfilename(
            title="Select decklist",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if path:
            self.decklist_var.set(path)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            self.output_var.set(path)

    def _collect_options(self) -> GuiRunOptions:
        return GuiRunOptions(
            decklist_path=Path(self.decklist_var.get()),
            output_dir=Path(self.output_var.get()),
            image_size=self.size_var.get(),
            paper=self.paper_var.get(),
            dpi=int(self.dpi_var.get()),
            gap_mm=float(self.gap_var.get()),
            build_pdf=self.build_pdf_var.get(),
            allow_ub=self.allow_ub_var.get(),
            allow_white_border=self.allow_wb_var.get(),
            allow_promo=self.allow_promo_var.get(),
        )

    def _append_log(self, line: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {line}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _set_running(self, running: bool) -> None:
        self._running = running
        state = tk.DISABLED if running else tk.NORMAL
        self.run_btn.configure(state=state)
        for w in self._widgets:
            if w is not self.run_btn:
                try:
                    w.configure(state=state)
                except tk.TclError:
                    pass
        self.status_var.set("Running…" if running else "Ready")

    def _on_run(self) -> None:
        if self._running:
            return
        try:
            opts = self._collect_options()
        except ValueError as exc:
            messagebox.showerror("Card Downloader", f"Invalid option: {exc}")
            return

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self._set_running(True)
        self.open_folder_btn.configure(state=tk.DISABLED)
        self.open_pdf_btn.configure(state=tk.DISABLED)

        def log_cb(line: str) -> None:
            self.root.after(0, lambda: self._append_log(line))

        def worker() -> None:
            result = execute_run(opts, on_log=log_cb)
            self.root.after(0, lambda: self._on_complete(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_complete(self, result: RunResult) -> None:
        self._last_result = result
        self._set_running(False)
        if result.success:
            self.status_var.set("Done")
            self.open_folder_btn.configure(state=tk.NORMAL)
            if result.pdf_path and result.pdf_path.is_file():
                self.open_pdf_btn.configure(state=tk.NORMAL)
            messagebox.showinfo("Card Downloader", result.message)
        else:
            self.status_var.set("Failed")
            messagebox.showerror("Card Downloader", result.message)

    def _open_folder(self) -> None:
        if self._last_result and self._last_result.out_dir:
            webbrowser.open(self._last_result.out_dir.resolve().as_uri())

    def _open_pdf(self) -> None:
        if self._last_result and self._last_result.pdf_path and self._last_result.pdf_path.is_file():
            webbrowser.open(self._last_result.pdf_path.resolve().as_uri())
