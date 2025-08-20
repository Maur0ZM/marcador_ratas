import tkinter.ttk as ttk
import tkinter as tk

def setup_styles(root):
    style = ttk.Style(root)
    style.theme_use("clam")  # base que sí respeta colores

    # ---- Botón lateral ----
    style.configure("Side.TButton",
        font=("Arial", 14, "bold"),
        foreground="white",
        background="#333333",
        padding=(10, 6),
        relief="flat"
    )
    style.map("Side.TButton",
        background=[("active", "#ff8800")],
        foreground=[("active", "black")]
    )

    # ---- Botón de peligro ----
    style.configure("Danger.TButton",
        font=("Arial", 14, "bold"),
        foreground="white",
        background="#771d1d",
        padding=(10, 6),
        relief="raised"
    )
    style.map("Danger.TButton",
        background=[("active", "#a62b2b")],
        foreground=[("active", "white")]
    )

    # ---- Botón menú ----
    style.configure("Menu.TButton",
        font=("Arial", 16, "bold"),
        foreground="white",
        background="#004488",
        padding=(12, 8),
        relief="ridge"
    )
    style.map("Menu.TButton",
        background=[("active", "#3399ff")],
        foreground=[("active", "black")]
    )

import tkinter as tk

class ArrowIndicator(tk.Canvas):
    """
    Flecha de posesión individual (izq o der) con estado on/off.
    - side: 'left' o 'right'
    - on: bool (encendido/apagado)
    - command: callback opcional -> command(self, self.on)
    """
    def __init__(self, parent, side="left", on=False,
                active="#00d4ff", inactive="#303030",
                width=160, height=60, bg=None, command=None):
        super().__init__(parent, width=width, height=height,
                        highlightthickness=0, bg=(bg or parent["bg"]))
        assert side in ("left", "right")
        self.side = side
        self.on = bool(on)
        self.active = active
        self.inactive = inactive
        self.command = command

        self.bind("<Button-1>", self._click)
        self.bind("<Configure>", lambda e: self._draw())
        self._draw()

    # API pública
    def set_on(self, value: bool):
        self.on = bool(value)
        self._draw()

    def toggle(self):
        self.set_on(not self.on)

    def is_on(self) -> bool:
        return self.on

    # Internos
    def _click(self, _evt=None):
        self.toggle()
        if self.command:
            self.command(self, self.on)

    def _draw(self):
        w = self.winfo_width()  or int(self.cget("width"))
        h = self.winfo_height() or int(self.cget("height"))
        m = 6
        self.delete("all")

        color = self.active if self.on else self.inactive

        if self.side == "left":
            pts = [m, h/2,  w-m, m,  w-m, h-m]   # triángulo apuntando a la izq
        else:
            pts = [w-m, h/2,  m, m,  m, h-m]     # triángulo apuntando a la der

        self.create_polygon(pts, fill=color, outline="")
    
