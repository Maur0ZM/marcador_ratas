# ui.py
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import re, pygame, os, sys
from PIL import Image, ImageTk
from styles import setup_styles, ArrowIndicator
from logic import GameState, START_SECONDS

def resource_path(relative_path):
    """ Devuelve ruta válida tanto en .py como en .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class Scoreboard(tk.Tk):
    def __init__(self):
        super().__init__()
        setup_styles(self)

        pygame.mixer.init()
        beep_path = resource_path("assets/beep.wav")
        self.tone = pygame.mixer.Sound(beep_path)
        self.tone.set_volume(1.0)
        
        # --- Modelo ---
        self.state = GameState()
        self.state.apply_minutes()

        # --- Ventana base ---
        self.title("Marcador de Básquet")
        self.configure(bg="#000000")
        self.resizable(True, True)
        self._configurar_grid(self, 3, 3)
        self.grid_columnconfigure(0, weight=1, uniform="main")
        self.grid_columnconfigure(1, weight=3, uniform="main")
        self.grid_columnconfigure(2, weight=1, uniform="main")
        self.fullscreen = False  
        
        # --- Fuentes escalables ---
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.base_w, self.base_h = sw, sh
        family_big = "DS-Digital" if "DS-Digital" in tkfont.families() else "Arial"
        self.f_small  = tkfont.Font(family="Arial",    size=24,  weight="bold")
        self.f_medium = tkfont.Font(family="Arial",    size=36,  weight="bold")
        self.f_big    = tkfont.Font(family=family_big, size=140, weight="bold")
        self.f_red    = tkfont.Font(family="Arial",    size=64,  weight="bold")
        self._fontsizes = [
            (self.f_small,  24),
            (self.f_medium, 40),
            (self.f_big,   140),
            (self.f_red,    94),
        ]

        # --- UI ---
        self._build_ui()
        self._refresh_all()

        # --- Hotkeys y resize ---
        self._bind_keys()
        self.bind("<Configure>", self._on_resize)

        # --- Loop de ticks (UI dirige el reloj) ---
        self._schedule_ticks()
        
    def _play_tun(self, times=1, gap_ms=180):
        self.tone.play()
        if times > 1:
            self.after(gap_ms, lambda: self._play_tun(times-1, gap_ms))

    # ----------------- Construcción UI -----------------
    def _configurar_grid(self, widget, rows, cols):
        for r in range(rows):
            widget.grid_rowconfigure(r, weight=1, minsize=40)
        for c in range(cols):
            widget.grid_columnconfigure(c, weight=1, minsize=60)

    def _build_ui(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
            
        img = Image.open(resource_path("assets/bandera-roja.png"))
        img = img.resize((80, 80), Image.LANCZOS)
        self.flag_img = ImageTk.PhotoImage(img)

        self.window_toolbar = tk.Frame(self, bg="#000")
        self.window_toolbar.grid(row=0, column=0, columnspan=3, sticky="nsew")
        
        left_bar  = tk.Frame(self, bg="#000"); left_bar.grid(row=1, column=0, rowspan=2, sticky="nsew")
        right_bar = tk.Frame(self, bg="#000"); right_bar.grid(row=1, column=2, rowspan=2, sticky="nsew")
        center    = tk.Frame(self, bg="#000"); center.grid(row=1, column=1, rowspan=2, sticky="nsew")
        self._configurar_grid(left_bar,  5, 1)
        self._configurar_grid(right_bar, 5, 1)
        self._configurar_grid(center, 4, 3)

        ttk.Button(self.window_toolbar, text="MENU",  command=self.show_menu,
                takefocus=False, style="Menu.TButton").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        ttk.Button(self.window_toolbar, text="EDITAR", command=self.edit_config,
                takefocus=False, style="Menu.TButton").grid(row=0, column=1, sticky="w", padx=8, pady=8)

        # Izquierda
        self.arrow_left = ArrowIndicator(left_bar, side="left", on=False,
                                        active="#00d4ff", inactive="#303030",
                                        width=150, height=150,
                                        command=self._on_arrow_left)
        self.arrow_left.grid(row=0, column=0)
        self.score_left  = tk.Label(left_bar, text="0", bg="#000", fg="#00ff7f", font=self.f_big)
        self.score_left.grid(row=2, column=0, padx=12, pady=10)
        
        FM_frame_left = tk.Frame(left_bar, bg="#000")
        FM_frame_left.grid(row=3, column=0, columnspan=3, pady=5)


        # ---- FALTAS ----
        self.foul_left = tk.Label(FM_frame_left, text="Faltas:", bg="#000", fg="#00ff7f", font=self.f_small)
        self.foul_left.grid(row=0, column=0, sticky="e", padx=(0,5))  # col 0

        self.foul_left_value = tk.Label(FM_frame_left, text="0", bg="#000", fg="#00ff7f", font=self.f_medium)
        self.foul_left_value.grid(row=0, column=1, padx=(0,10))         # col 1

        self.flag_left_box = tk.Frame(FM_frame_left, bg="#000", width=80, height=80)
        self.flag_left_box.grid(row=0, column=2, padx=(0,0))
        self.flag_left_box.grid_propagate(False)  # no reduzcas el frame al tamaño del hijo
        
        self.label_imgI = tk.Label(self.flag_left_box, image=self.flag_img, bg="#000")
                
        # ---- MINUTOS ----
        self.minutes_left_label = tk.Label(FM_frame_left, text="Minutos:", bg="#000", fg="#00ff7f", font=self.f_small)
        self.minutes_left_label.grid(row=1, column=0, sticky="e", padx=(0,5))  # fila 1, col 0

        self.minutes_left_value = tk.Label(FM_frame_left, text="", bg="#000", fg="#00ff7f", font=self.f_medium)
        self.minutes_left_value.grid(row=1, column=1, sticky="w")               # fila 1, col 1

        # Derecha
        self.arrow_right = ArrowIndicator(right_bar, side="right", on=False,
                                        active="#00d4ff", inactive="#303030",
                                        width=150, height=150,
                                        command=self._on_arrow_right)
        
        self.arrow_right.grid(row=0, column=0)
        self.score_right = tk.Label(right_bar, text="0", bg="#000", fg="#00ff7f", font=self.f_big)
        self.score_right.grid(row=2, column=0, padx=12, pady=10)

        FM_frame_right = tk.Frame(right_bar, bg="#000")
        FM_frame_right.grid(row=3, column=0, columnspan=3, pady=5)

        # ---- FALTAS ----
        self.foul_right = tk.Label(FM_frame_right, text="Faltas:", bg="#000", fg="#00ff7f", font=self.f_small)
        self.foul_right.grid(row=0, column=0, sticky="e", padx=(0,5))  # col 0

        self.foul_right_value = tk.Label(FM_frame_right, text="0", bg="#000", fg="#00ff7f", font=self.f_medium)
        self.foul_right_value.grid(row=0, column=1, padx=(0,10))         # col 1

        self.flag_right_box = tk.Frame(FM_frame_right, bg="#000", width=80, height=80)
        self.flag_right_box.grid(row=0, column=2, padx=(0,0))
        self.flag_right_box.grid_propagate(False)
        
        self.label_imgD = tk.Label(self.flag_right_box, image=self.flag_img, bg="#000")

        # ---- MINUTOS ----
        self.minutes_right_label = tk.Label(FM_frame_right, text="Minutos:", bg="#000", fg="#00ff7f", font=self.f_small)
        self.minutes_right_label.grid(row=1, column=0, sticky="e", padx=(0,5))  # fila 1, col 0

        self.minutes_right_value = tk.Label(FM_frame_right, text="", bg="#000", fg="#00ff7f", font=self.f_medium)
        self.minutes_right_value.grid(row=1, column=1, sticky="w")

        # Centro
        self.period_lbl = tk.Label(center, text="1º", bg="#000", fg="#ffd700", font=self.f_red)
        self.period_lbl.grid(row=0, column=1, sticky="n")

        self.time_lbl = tk.Label(center, text="10:00", bg="#000", fg="white", font=self.f_big)
        self.time_lbl.grid(row=1, column=1, sticky="n")

        FM_frame_center = tk.Frame(center, bg="#000")
        FM_frame_center.grid(row=2, column=0, columnspan=3, pady=5)
        
        self.names_label = tk.Label(
            FM_frame_center,
            text=f"{self.state.team_names[0]} - {self.state.team_names[1]}",
            bg="#000", fg="white", font=self.f_medium
        )
        self.names_label.grid(row=0, column=0, columnspan=3, sticky="n")

        self.shot_lbl = tk.Label(center, text="24", bg="#000", fg="#ffd700", font=self.f_red)
        self.shot_lbl.grid(row=3, column=1, sticky="s", pady=6)

    # ----------------- Callbacks flechas -----------------
    def _on_arrow_left(self, widget, is_on):
        if is_on and self.arrow_right.is_on():
            self.arrow_right.set_on(False)

    def _on_arrow_right(self, widget, is_on):
        if is_on and self.arrow_left.is_on():
            self.arrow_left.set_on(False)

    # ----------------- Render -----------------
    def _refresh_all(self):
        s = self.state
        self.score_left.config(text=str(s.scores[0]))
        self.score_right.config(text=str(s.scores[1]))
        self.minutes_left_value.config(text=str(s.minutes[0]))
        self.minutes_right_value.config(text=str(s.minutes[1]))
        self.names_label.config(text=f"{s.team_names[0]} - {s.team_names[1]}")
        self.period_lbl.config(text=s.period_str())
        self.time_lbl.config(text=s.time_str())
        self.shot_lbl.config(text=s.shot_str())
        
        # Lado izquierdo
        self.foul_left_value.config(text=str(s.fouls[0]))
        if s.fouls[0] >= 5:
            if not self.label_imgI.winfo_ismapped():
                self.label_imgI.pack(expand=True)  # ocupa su caja
        else:
            if self.label_imgI.winfo_ismapped():
                self.label_imgI.pack_forget()

        # Lado derecho
        self.foul_right_value.config(text=str(s.fouls[1]))
        if s.fouls[1] >= 5:
            if not self.label_imgD.winfo_ismapped():
                self.label_imgD.pack(expand=True)
        else:
            if self.label_imgD.winfo_ismapped():
                self.label_imgD.pack_forget()

    # ----------------- Ticks dirigidos por la UI -----------------
    def _schedule_ticks(self):
        # Juego
        ended = self.state.tick_game_1s()
        if ended:
            self._blink_time()
            
        # 24s
        evt = self.state.tick_shot_1s()
        if evt == "shot10":
            self._play_tun(times=1)       
        elif evt == "shot5":
            self._play_tun(times=2, gap_ms=500) 
            
        self._refresh_all()
        # reprogramo
        self.after(1000, self._schedule_ticks)

    def _blink_time(self, count=6):
        if count <= 0:
            self.time_lbl.config(fg="#ff2b2b"); return
        current = self.time_lbl.cget("fg")
        self.time_lbl.config(fg="white" if current == "#ff2b2b" else "#ff2b2b")
        self.after(250, lambda: self._blink_time(count - 1))

    def _blink_widget(self, widget, end_color="#ff2b2b", times=6, interval=250):
        # simple parpadeo
        if times <= 0:
            widget.config(fg=end_color); return
        current = widget.cget("fg")
        widget.config(fg="white" if current == end_color else end_color)
        self.after(interval, lambda: self._blink_widget(widget, end_color, times-1, interval))

    # ----------------- Ventanas -----------------
    def edit_config(self):
        if getattr(self, "edit_win", None) and self.edit_win.winfo_exists():
            self.edit_win.deiconify(); self.edit_win.lift(); self.edit_win.focus_force(); return

        win = tk.Toplevel(self); self.edit_win = win
        win.title("Configuración"); win.resizable(False, False); win.transient(self); win.grab_set()

        # Nombres de equipos
        ttk.Label(win, text="Nombre Equipos", font=self.f_small).grid(row=0, column=0, columnspan=2, pady=(8,4))
        
        ttk.Label(win, text="Equipo izquierda:").grid(row=1, column=0, padx=6, pady=4, sticky="e")
        ttk.Label(win, text="Equipo derecha:").grid(row=2, column=0, padx=6, pady=4, sticky="e")

        v1 = tk.StringVar(master=win, value=self.state.team_names[0])
        v2 = tk.StringVar(master=win, value=self.state.team_names[1])
        e1 = ttk.Entry(win, textvariable=v1, width=22); e1.grid(row=1, column=1, padx=6, pady=4)
        e2 = ttk.Entry(win, textvariable=v2, width=22); e2.grid(row=2, column=1, padx=6, pady=4)

        # Tiempo
        ttk.Label(win, text="Tiempo", font=self.f_small).grid(row=3, column=0, columnspan=2, pady=(8,4))
        
        ttk.Label(win, text="Tiempo (MM:SS):").grid(row=4, column=0, padx=6, pady=4, sticky="e")
        v3 = tk.StringVar(master=win, value=self.state.time_str())
        vcmd = (self.register(lambda s: bool(re.fullmatch(r"\d{0,2}(:\d{0,2})?", s or ""))), "%P")
        e3 = ttk.Entry(win, textvariable=v3, width=6, justify="center", validate="key", validatecommand=vcmd)
        e3.grid(row=4, column=1, padx=6, pady=4)

        ttk.Label(win, text="24SG:").grid(row=5, column=0, padx=6, pady=4, sticky="e")
        v4 = tk.StringVar(master=win, value=self.state.shot_str())
        vcmd2 = (self.register(lambda s: bool(re.fullmatch(r"\d{0,2}", s or ""))), "%P")
        e4 = ttk.Entry(win, textvariable=v4, width=6, justify="center", validate="key", validatecommand=vcmd2)
        e4.grid(row=5, column=1, padx=6, pady=4)

        # Puntos
        ttk.Label(win, text="Puntos", font=self.f_small).grid(row=6, column=0, columnspan=2, pady=(8,4))
        
        vcmd3 = (self.register(lambda s: bool(re.fullmatch(r"\d{0,3}", s or ""))), "%P")
        
        ttk.Label(win, text="Equipo izquierda:").grid(row=7, column=0, pady=1, sticky="w")
        self.v5 = tk.StringVar(master=win, value=str(self.state.scores[0]))
        e5L = ttk.Entry(win, textvariable=self.v5, width=6, justify="center", validate="key", validatecommand=vcmd3); e5L.grid(row=7, column=1, pady=1)

        ttk.Label(win, text="Equipo derecha:").grid(row=8, column=0, pady=2, sticky="w")
        self.v6 = tk.StringVar(master=win, value=str(self.state.scores[1]))
        e5R = ttk.Entry(win, textvariable=self.v6, width=6, justify="center", validate="key", validatecommand=vcmd3); e5R.grid(row=8, column=1, pady=1)

        def save():
            try:
                self.state.set_names(v1.get(), v2.get())
                self.state.set_game_time_from_text(v3.get().strip())
                self.state.set_shot_time(v4.get().strip())
                self.state.set_points(int(self.v5.get().strip()), int(self.v6.get().strip()))
            except ValueError as ex:
                messagebox.showerror("Formato inválido", str(ex)); return
            self._refresh_all(); on_close()

        ttk.Button(win, text="Guardar", command=save).grid(row=9, column=0, columnspan=2, pady=8)

        def on_close():
            try: win.grab_release()
            except Exception: pass
            self.edit_win = None; win.destroy()

        win.bind("<Return>", lambda e: save())  
        win.protocol("WM_DELETE_WINDOW", on_close)

    def show_menu(self):
        if getattr(self, "menu_win", None) and self.menu_win.winfo_exists():
            self.menu_win.deiconify(); self.menu_win.lift(); self.menu_win.focus_force(); return

        win = tk.Toplevel(self); self.menu_win = win
        win.title("Menú"); win.resizable(False, False); win.transient(self); win.grab_set()
        ttk.Button(win, text="Reiniciar marcador", command=lambda:(self.state.reset_scores(), self._refresh_all())).grid(row=0, column=0, padx=12, pady=12, sticky="ew")
        ttk.Button(win, text="Reiniciar tiempo",   command=lambda:(self.state.reset_time(),   self._refresh_all())).grid(row=1, column=0, padx=12, pady=12, sticky="ew")
        ttk.Button(win, text="Reiniciar todo",     command=lambda:(self.state.reset_all(),    self._refresh_all())).grid(row=2, column=0, padx=12, pady=12, sticky="ew")

        def on_close():
            try: win.grab_release()
            except Exception: pass
            self.menu_win = None; win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)

        if self.fullscreen:
            # Oculta barra y colapsa la fila 0
            self.window_toolbar.grid_remove()
            self.grid_rowconfigure(0, weight=0, minsize=0)
        else:
            # Muestra barra y restaura su alto
            self.window_toolbar.grid()
            self.grid_rowconfigure(0, weight=0, minsize=56)  # o el alto que quieras

    # ----------------- Hotkeys -----------------
    def _bind_keys(self):
        self.bind("<space>",  lambda e: (self.state.toggle_game(), self._refresh_all()))
        self.bind("<Return>", lambda e: (self.state.next_period(), self._refresh_all()))
        self.bind("z", lambda e: (self.state.add_points(0, +1), self._refresh_all()))
        self.bind("x", lambda e: (self.state.add_points(0, -1), self._refresh_all()))
        self.bind("n", lambda e: (self.state.add_points(1, +1), self._refresh_all()))
        self.bind("m", lambda e: (self.state.add_points(1, -1), self._refresh_all()))
        self.bind("a", lambda e: (self.state.add_fouls(0, +1), self._refresh_all()))
        self.bind("s", lambda e: (self.state.add_fouls(0, -1), self._refresh_all()))
        self.bind("k", lambda e: (self.state.add_fouls(1, +1), self._refresh_all()))
        self.bind("l", lambda e: (self.state.add_fouls(1, -1), self._refresh_all()))
        self.bind("q", lambda e: (self.state.add_minutes(0, +1), self._refresh_all()))
        self.bind("w", lambda e: (self.state.add_minutes(0, -1), self._refresh_all()))
        self.bind("o", lambda e: (self.state.add_minutes(1, +1), self._refresh_all()))
        self.bind("p", lambda e: (self.state.add_minutes(1, -1), self._refresh_all()))
        self.bind("2", lambda e: (self.state.reset_shot_14(), self._refresh_all()))
        self.bind("3", lambda e: (self.state.reset_shot_24(), self._refresh_all()))
        self.bind("<Shift_L>", lambda e: (self.state.toggle_shot(), self._refresh_all()))
        self.bind("f", self.toggle_fullscreen)
    
    # ----------------- Escalado -----------------
    def _on_resize(self, event):
        w = max(self.winfo_width(), 1); h = max(self.winfo_height(), 1)
        factor = max(0.6, min(1.0, min(w / self.base_w, h / self.base_h)))
        for fnt, base in self._fontsizes:
            new_size = max(8, int(round(base * factor)))
            if fnt.cget("size") != new_size:
                fnt.configure(size=new_size)

if __name__ == "__main__":
    app = Scoreboard()
    app.mainloop()
