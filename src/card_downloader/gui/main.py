import tkinter as tk

from card_downloader.gui.app import CardDownloaderApp


def main() -> None:
    root = tk.Tk()
    CardDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
