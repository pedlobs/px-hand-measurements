"""Entry point for the aplication"""

import tkinter as tk
from src.config import AppConfig
from src.ui.app_window import PxHandAppWindow


def main() -> None:
    config = AppConfig()
    root = tk.Tk()
    PxHandAppWindow(root, config=config)
    root.mainloop()


if __name__ == "__main__":
    main()
