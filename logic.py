# logic.py
from dataclasses import dataclass, field
import re

START_SECONDS = 10 * 60  # 10:00
START_24SG    = 24

def clamp(n, lo, hi): 
    return max(lo, min(hi, n))

@dataclass
class GameState:
    team_names: list[str] = field(default_factory=lambda: ["Team 1", "Team 2"])
    scores:     list[int] = field(default_factory=lambda: [0, 0])
    period:     int = 1
    time_left:  int = START_SECONDS
    shot_time:  int = START_24SG
    fouls:      list[int] = field(default_factory=lambda: [0, 0])
    minutes:    list[int] = field(default_factory=lambda: [0, 0])  
    running:       bool = False
    shot_running:  bool = False
    minutes_having: bool = False
    minutes_penalized: bool = False

    # ---------- Util ----------
    @staticmethod
    def format_mmss(secs: int) -> str:
        m = secs // 60
        s = secs % 60
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def parse_mmss(txt: str) -> int:
        # Acepta M:SS o MM:SS
        if not re.fullmatch(r"\d{1,2}:[0-5]\d", txt):
            raise ValueError("Formato inválido (usa MM:SS, ej: 10:00)")
        m, s = map(int, txt.split(":"))
        return m * 60 + s

    # ---------- Lecturas para la UI ----------
    def time_str(self) -> str:
        return self.format_mmss(self.time_left)

    def shot_str(self) -> str:
        return f"{clamp(int(self.shot_time), 0, 99):02d}"

    def period_str(self) -> str:
        return f"{self.period}º" if self.period <= 4 else f"OT {self.period - 4}"
    
    # ---------- Mutaciones de estado (sin Tk) ----------
    def set_names(self, left: str, right: str):
        self.team_names = [left.strip() or "Team 1", right.strip() or "Team 2"]

    def set_game_time_from_text(self, mmss: str):
        self.time_left = self.parse_mmss(mmss)

    def set_shot_time(self, seconds_text: str):
        if not re.fullmatch(r"\d{1,2}", seconds_text):
            raise ValueError("24SG debe ser 0–99")
        v = int(seconds_text)
        if v > 24:
            raise ValueError("24SG máximo 24")
        self.shot_time = v

    def set_points(self, left: int, right: int):
        self.scores = [clamp(left, 0, 99), clamp(right, 0, 99)]

    def add_points(self, team: int, pts: int):
        self.scores[team] = max(0, self.scores[team] + pts)
        
    def add_fouls(self, team: int, count: int):
        self.fouls[team] = max(0, min(5, self.fouls[team] + count))

    def apply_minutes(self):
        if self.period <= 2 and not self.minutes_having:
            self.minutes[0] += 2
            self.minutes[1] += 2
            self.minutes_having = True

        elif self.period == 3:
            self.minutes[0] = 3
            self.minutes[1] = 3
            
        if (
            self.period == 4
            and self.minutes[0] == 3
            and self.minutes[1] == 3
            and self.time_left < 2 * 60
            and not self.minutes_penalized
        ):
            self.minutes[0] -= 1
            self.minutes[1] -= 1
            self.minutes_penalized = True


    def add_minutes(self, team: int, count: int):
        if count < 0:
            self.shot_time = 60
            self.shot_running= True
            self.tick_shot_1s()
        self.minutes[team] = max(0, min(5, self.minutes[team] + count))
        
    def reset_scores(self):
        self.scores = [0, 0]

    def reset_time(self):
        self.time_left = START_SECONDS
        self.reset_shot_24()
        self.running = False
        self.shot_running = False

    def reset_shot_24(self):
        self.shot_time = 24

    def reset_shot_14(self):
        self.shot_time = 14

    def next_period(self):
        self.period += 1
        self.fouls = [0, 0]
        self.reset_time()

    def reset_all(self):
        self.scores = [0, 0]
        self.team_names = ["Team 1", "Team 2"]
        self.period = 1
        self.reset_time()
    
    # ---------- “Ticks” de 1 segundo (la UI los llama con after) ----------
    # Devuelven flags para que la UI sepa si debe parpadear, etc.
    def tick_game_1s(self) -> bool:
        if not self.running:
            return False
        if self.time_left > 0:
            self.time_left -= 1
            return False
        else:
            self.running = False
            return True  # llegó a 0

    def tick_shot_1s(self) -> bool:
        self.apply_minutes()
        if not self.shot_running:
            return False
        if self.shot_time > 0:
            self.shot_time -= 1
            return False
        else:
            self.shot_running = False
            return True  # llegó a 0

    def toggle_game(self):
        self.running = not self.running
        # opcional: sincronizar con 24s
        if self.running and not self.shot_running:
            self.shot_running = True

    def toggle_shot(self):
        self.shot_running = not self.shot_running
