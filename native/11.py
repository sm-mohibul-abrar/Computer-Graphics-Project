"""
DICTATOR'S DASH 3D  v3  -  CSE423 Computer Graphics Project

Aladdin runs down the royal road: jump barriers, slide under beams, shoot crates and the
dictator's clone guards and drones, grab coins and power-ups.

NEW in v3
  * Start menu: pick a DIFFICULTY (Easy / Medium / Hard) and a LOCATION (4 worlds)
  * Every location has its own scenery, road, sky, fog, lighting and weather odds
  * The road now bends left/right. You still run in lanes - the whole world curves
  * Modern look: gradient sky, sun glow, far-mountain / skyline backdrop, neon road edges,
    soft shadows, rounded glass HUD, vignette, speed lines, custom reticle

Controls
  Menu:  Up/Down or 1-3 = difficulty   Left/Right or A/D = location   Enter/Space/click = start
  A/D or Left/Right  change lane          Space / W  jump        S  slide (in air: fast-fall)
  Mouse aims.  Left-click: aimed shot     F: straight shot       G / Right-click (hold): FLAMETHROWER
  V camera: chase / first-person / overhead     Q / E  slower / faster
  N time of day   M weather   B back to menu   P pause   R restart   Esc quit
"""
import sys, os, json, math, random, threading
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

try:
    import winsound
except ImportError:
    winsound = None

LANES, LW = 5, 2.2                      # 5 lanes, 2.2 units wide each
# when frozen with PyInstaller, keep the high-score file next to the .exe (not in the temp dir)
BASE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
    else os.path.dirname(os.path.abspath(__file__))
SAVE = os.path.join(BASE, "highscore.json")
GOLD = (0.95, 0.75, 0.15)
WIN = [1100, 700]
NR = 75                                  # road samples, 2 units apart (150 units of visible road)
TODN = ("Day", "Dusk", "Night", "Auto cycle")
WN = ("Clear", "Rain", "Snow", "Sandstorm")
WM = ("Auto",) + WN
VN = ("Chase", "First-person", "Overhead")

# ------------------------------------------------------------------ difficulty presets
DIFFS = (
    dict(name="Easy", col=(0.35, 0.85, 0.50),
         desc="Relaxed pace, gentle curves, forgiving hits. Great for learning the moves.",
         hp=130, dmg=0.6, heal=40, v0=12.0, vmin0=10.0, vgrow=0.12, vcap=22.0, vmax=34.0,
         gap0=28.0, gapmin=16.0, gaps=0.08, nobs=(1, 1, 1, 2), clone_p=0.18, clone_max=2,
         drone_t=30.0, drone_max=1, drone_p=0.12, drone_cap=0.25, ecd=1.5, item_p=0.20, curve=0.7),
    dict(name="Medium", col=(1.00, 0.78, 0.20),
         desc="The classic Dictator's Dash experience. Balanced speed, enemies and curves.",
         hp=100, dmg=1.0, heal=30, v0=14.0, vmin0=12.0, vgrow=0.20, vcap=30.0, vmax=42.0,
         gap0=24.0, gapmin=13.0, gaps=0.12, nobs=(1, 1, 2, 3), clone_p=0.28, clone_max=3,
         drone_t=12.0, drone_max=3, drone_p=0.20, drone_cap=0.45, ecd=1.0, item_p=0.12, curve=1.0),
    dict(name="Hard", col=(1.00, 0.30, 0.25),
         desc="Fast, dense, aggressive drones and sharp bends. Every hit hurts.",
         hp=80, dmg=1.4, heal=25, v0=17.0, vmin0=15.0, vgrow=0.28, vcap=34.0, vmax=48.0,
         gap0=21.0, gapmin=12.0, gaps=0.15, nobs=(2, 2, 3, 3), clone_p=0.40, clone_max=4,
         drone_t=6.0, drone_max=4, drone_p=0.30, drone_cap=0.60, ecd=0.7, item_p=0.08, curve=1.25),
)

# ------------------------------------------------------------------ locations
# tint/tw: sky colour pushed toward 'tint' with weight tw.  night: bias toward the night palette.
# fog: fog distance multiplier.  curve: how twisty the road is.  wt: weather odds (clear, rain, snow, sand)
LOCS = (
    dict(name="Agrabah", tag="Desert highway", kind="desert",
         desc="Golden domes, palms and warm dust. Sandstorms roll in without warning.",
         pv=(0.97, 0.62, 0.35), ground=(0.86, 0.70, 0.45), road=(0.42, 0.10, 0.12),
         edge=(0.95, 0.75, 0.15), dash=(0.95, 0.90, 0.80), lamp=(1.0, 0.9, 0.4), far=(0.80, 0.58, 0.34),
         tint=(1.0, 0.7, 0.35), tw=0.0, night=0.0, fog=1.0, curve=1.0, wt=(5, 1, 0, 3),
         torch=(1.0, 0.7, 0.35), glow=0.0, acc=(0.95, 0.75, 0.15)),
    dict(name="Neon City", tag="Cyber night", kind="city",
         desc="A rain-slick skyline that never sleeps. Neon everywhere, mostly after dark.",
         pv=(0.28, 0.08, 0.40), ground=(0.07, 0.07, 0.10), road=(0.10, 0.10, 0.14),
         edge=(0.20, 0.90, 1.00), dash=(0.90, 0.45, 1.00), lamp=(0.3, 0.9, 1.0), far=(0.14, 0.10, 0.28),
         tint=(0.8, 0.2, 0.7), tw=0.5, night=0.85, fog=0.85, curve=0.6, wt=(2, 5, 1, 0),
         torch=(0.8, 0.3, 1.0), glow=0.45, acc=(0.35, 0.9, 1.0)),
    dict(name="Frozen Peaks", tag="Snow and ice", kind="snow",
         desc="A winding alpine pass under pale skies. Snow falls often, bends are tight.",
         pv=(0.72, 0.86, 1.0), ground=(0.92, 0.95, 1.0), road=(0.27, 0.30, 0.38),
         edge=(0.60, 0.85, 1.00), dash=(0.95, 0.97, 1.0), lamp=(0.7, 0.85, 1.0), far=(0.72, 0.80, 0.92),
         tint=(0.7, 0.85, 1.0), tw=0.35, night=0.0, fog=0.9, curve=1.3, wt=(2, 0, 6, 0),
         torch=(0.7, 0.85, 1.0), glow=0.0, acc=(0.6, 0.85, 1.0)),
    dict(name="Emerald Vale", tag="Misty forest", kind="forest",
         desc="A twisty valley road through dense trees and drifting mist. Often rainy.",
         pv=(0.50, 0.75, 0.62), ground=(0.20, 0.45, 0.20), road=(0.36, 0.28, 0.19),
         edge=(0.60, 0.88, 0.40), dash=(0.95, 0.92, 0.75), lamp=(1.0, 0.85, 0.5), far=(0.18, 0.40, 0.34),
         tint=(0.45, 0.8, 0.6), tw=0.3, night=0.0, fog=0.78, curve=1.5, wt=(3, 5, 0, 0),
         torch=(1.0, 0.8, 0.45), glow=0.0, acc=(0.55, 0.9, 0.45)),
)

PAL = [
    dict(sky=(0.55, 0.78, 0.95), top=(0.16, 0.40, 0.85), dif=(1.0, 0.97, 0.88), amb=(0.50, 0.50, 0.52),
         sun=(1, 1, 0.85), sy=46.0, stars=0.0, night=0.0),
    dict(sky=(0.97, 0.60, 0.33), top=(0.30, 0.20, 0.52), dif=(1.0, 0.85, 0.65), amb=(0.42, 0.36, 0.40),
         sun=(1, 0.9, 0.5), sy=24.0, stars=0.0, night=0.0),
    dict(sky=(0.03, 0.04, 0.13), top=(0.005, 0.005, 0.04), dif=(0.30, 0.35, 0.60), amb=(0.14, 0.15, 0.26),
         sun=(0.9, 0.92, 1), sy=40.0, stars=1.0, night=1.0),
]
ORDER = [0, 1, 2, 1]
STARS = [(random.uniform(-230, 230), random.uniform(20, 190), -245, random.uniform(.4, 1)) for _ in range(190)]


def lerp(a, b, f):
    if isinstance(a, tuple):
        return tuple(x + (y - x) * f for x, y in zip(a, b))
    return a + (b - a) * f


def env():
    L = g.loc
    if g.tod < 3:
        e = dict(PAL[g.tod])
    else:
        ph = (g.clock % 120) / 30.0                 # 30 s per stage, 2 min per full day
        i, f = int(ph), ph - int(ph)
        f = f * f * (3 - 2 * f)
        a, b = PAL[ORDER[i]], PAL[ORDER[(i + 1) % 4]]
        e = {k: lerp(a[k], b[k], f) for k in a}
    if L["night"] > 0:                              # location bias toward night (Neon City)
        n2 = PAL[2]
        e = {k: lerp(e[k], n2[k], L["night"]) for k in e}
    if L["tw"] > 0:                                 # location colour grading
        bright = 1 - 0.65 * e["night"]
        tint = tuple(c * bright for c in L["tint"])
        e["sky"] = lerp(e["sky"], tint, L["tw"])
        e["top"] = lerp(e["top"], tuple(c * 0.6 for c in tint), L["tw"])
        e["amb"] = lerp(e["amb"], tuple(c * 0.45 for c in L["tint"]), L["tw"] * 0.5)
    fm = L["fog"]
    e["fs"], e["fe"] = 25.0 * fm, 105.0 * fm
    w, k = g.weather, g.wk
    if w and k > 0:
        grey = ((0.45, 0.47, 0.5), (0.8, 0.83, 0.88), (0.78, 0.62, 0.4))[w - 1]
        day = 0.25 + 0.75 * (1 - e["stars"])
        e["sky"] = lerp(e["sky"], tuple(c * day for c in grey), 0.65 * k)
        e["top"] = lerp(e["top"], e["sky"], 0.7 * k)
        e["dif"] = tuple(c * lerp(1.0, (0.6, 0.7, 0.8)[w - 1], k) for c in e["dif"])
        e["sun"] = lerp(e["sun"], e["sky"], 0.75 * k)
        e["stars"] *= lerp(1.0, 0.15, k)
        fs, fe = ((15, 70), (18, 75), (6, 40))[w - 1]
        e["fs"], e["fe"] = lerp(e["fs"], float(fs * fm), k), lerp(e["fe"], float(fe * fm), k)
    return e


def sfx(freq, ms):
    if winsound:
        threading.Thread(target=winsound.Beep, args=(freq, ms), daemon=True).start()


def load_hi():
    try:
        with open(SAVE) as f:
            b = json.load(f)["best"]
        if isinstance(b, dict):
            return [int(b.get(d["name"], 0)) for d in DIFFS]
        return [0, int(b), 0]                       # old single-score file counts as Medium
    except Exception:
        return [0, 0, 0]


def save_hi(v):
    try:
        with open(SAVE, "w") as f:
            json.dump({"best": {d["name"]: int(x) for d, x in zip(DIFFS, v)}}, f)
    except Exception:
        pass


# ----------------------------------------------------------------- game state
class Game:
    def __init__(s):
        s.his = load_hi()
        s.t, s.D = 0.0, 0.0
        s.di, s.li = 1, 0                           # difficulty / location index
        s.tod, s.wmode, s.view = 3, 0, 0
        s.weather = s.wnext = 0
        s.wk, s.wtimer, s.clock, s.wx, s.bolt = 1.0, 30.0, 0.0, [], 0.0
        s.mx, s.my, s.aim = WIN[0] // 2, WIN[1] // 2, (0.0, 0.0, -1.0)
        s.roll, s.rt, s.k0, s.cdir = 0.0, [0.0] * (NR + 1), 0.0, 1
        s.new_track(40)
        s.randomize_env()
        s.reset()
        s.state = "menu"
        s.build_road()

    @property
    def dd(s):
        return DIFFS[s.di]

    @property
    def loc(s):
        return LOCS[s.li]

    @property
    def hi(s):
        return s.his[s.di]

    def reset(s):
        prev = getattr(s, "state", "menu")
        d = s.dd
        s.state, s.time, s.speed = "play", 0.0, d["v0"]
        s.lane, s.px, s.py, s.vy, s.slide = 2, 0.0, 0.0, 0.0, 0.0
        s.hpmax = d["hp"]
        s.health, s.shield, s.rapid, s.chain = s.hpmax, False, 0.0, 0
        s.score, s.coins, s.kills = 0.0, 0, 0
        s.invuln = s.shake = s.flash = s.fire_cd = s.phase = 0.0
        s.obs, s.cns, s.items, s.clones = [], [], [], []
        s.drones = []
        s.pb, s.cb, s.parts, s.flames = [], [], [], []
        s.target, s.fuel, s.heat, s.fire_on = d["v0"], 100.0, False, False
        if prev != "menu":
            s.randomize_env()          # every new run: new time of day / weather
            s.new_track(160)
        s.next_spawn = s.D + 20

    def to_menu(s):
        s.reset()
        s.state = "menu"
        s.new_track(30)

    @property
    def mult(s):
        return 1 + min(s.chain // 5, 4)

    # ---- menu helpers
    def set_diff(s, i):
        s.di = max(0, min(len(DIFFS) - 1, i))

    def set_loc(s, i):
        s.li = i % len(LOCS)
        s.reroll_weather()

    def ui(s, a):
        k = a[0]
        if k == "diff":
            s.set_diff(a[1])
        elif k == "loc":
            s.set_loc(a[1])
        elif k in ("start", "restart"):
            s.reset()
        elif k == "menu":
            s.to_menu()
        elif k == "resume":
            s.pause()

    # ---- curved road: lane-space logic stays straight, rendering/aiming add off(z)
    def new_track(s, lead=160):
        s.segs, s.cend = [], s.D + lead

    def curv(s, d):                                 # road curvature at track distance d
        while s.cend < d + 220:
            a = s.cend + random.uniform(60, 190)
            ln = random.uniform(110, 240)
            sg = -s.cdir if random.random() < 0.65 else s.cdir
            s.cdir = sg
            s.segs.append((a, ln, sg * random.uniform(1.8e-3, 3.5e-3)))
            s.cend = a + ln
        f = s.dd["curve"] * s.loc["curve"]
        for a, ln, pk in s.segs:
            if a <= d < a + ln:
                return pk * f * math.sin(math.pi * (d - a) / ln) ** 2
        return 0.0

    def build_road(s):                              # lateral offset table, 2 units apart, ahead of Aladdin
        ds, h, x = 2.0, 0.0, 0.0
        s.k0 = s.curv(s.D)
        s.rt[0] = 0.0
        for i in range(1, NR + 1):
            k = s.curv(s.D + (i - 0.5) * ds)
            h2 = h + k * ds
            x += (h + h2) * 0.5 * ds
            h = h2
            s.rt[i] = x

    def off(s, z):                                  # sideways road offset at depth z
        d = -z
        if d <= 0:
            return 0.5 * s.k0 * d * d
        i = d * 0.5
        n = int(i)
        if n >= NR:
            return s.rt[NR]
        return s.rt[n] + (s.rt[n + 1] - s.rt[n]) * (i - n)

    def rx(s, x, z):                                # lane x -> rendered world x
        return x + s.off(z)

    def update_road(s, dt):
        s.segs = [q for q in s.segs if q[0] + q[1] > s.D - 40]
        s.build_road()
        tgt = max(-0.08, min(0.08, s.curv(s.D + 25) * 18))
        s.roll += (tgt - s.roll) * min(1.0, 4 * dt)

    # ---- actions
    def move(s, d):
        if s.state == "play":
            s.lane = max(0, min(LANES - 1, s.lane + d))

    def jump(s):
        if s.state == "play" and s.py <= 0.01:
            s.vy, s.slide = 9.0, 0.0

    def duck(s):
        if s.state != "play":
            return
        if s.py > 0.05:
            s.vy = -14.0
        else:
            s.slide = 0.7

    def shoot(s, straight=False):
        if s.state == "play" and s.fire_cd <= 0:
            hx, hy, hz = s.hand
            d = (0.0, 0.0, -1.0) if straight else s.aim
            s.pb.append({"x": hx, "y": hy, "z": hz, "dx": d[0] * 50, "dy": d[1] * 50, "dz": d[2] * 50})
            s.fire_cd = 0.1 if s.rapid > 0 else 0.28

    def burst(s, x, y, z, c, n=14):
        for _ in range(n):
            s.parts.append([x, y, z, random.uniform(-3, 3), random.uniform(1, 6),
                            random.uniform(-3, 3), random.uniform(.4, .9), c])

    def hurt(s, dmg):
        if s.invuln > 0:
            return
        dmg = max(1, int(round(dmg * s.dd["dmg"])))
        s.invuln, s.shake = 1.0, 0.5
        if s.shield:
            s.shield = False
            s.burst(s.px, 1, 0, (0.3, 0.7, 1), 25)
            sfx(500, 80)
            return
        s.health -= dmg
        s.chain, s.flash = 0, 0.35
        s.burst(s.px, 1, 0, (1, 0.2, 0.1), 20)
        sfx(180, 140)
        if s.health <= 0:
            s.state = "over"
            s.shake = s.invuln = s.flash = 0.0      # nothing may shake/blink on the game-over screen
            s.flames, s.fire_on = [], False
            if int(s.score) > s.his[s.di]:
                s.his[s.di] = int(s.score)
                save_hi(s.his)

    @property
    def vmin(s):                                    # minimum speed rises with time
        d = s.dd
        return min(d["vmin0"] + s.time * d["vgrow"], d["vcap"])

    def speed_adj(s, d):
        if s.state == "play":
            s.target = max(s.vmin, min(s.dd["vmax"], s.target + d))

    def cycle_tod(s):
        s.tod = (s.tod + 1) % 4

    @property
    def hand(s):                                    # where bullets and flames leave Aladdin
        low = 0.6 if s.slide > 0 else None
        if s.view == 1:
            return (s.px + 0.35, s.py + (low or 1.45), -0.5)
        return (s.px + 0.5, s.py + (low or 1.25), -0.4)

    def in_cone(s, x, y, z):                        # is a point inside the flame cone?
        hx, hy, hz = s.hand
        d = s.aim
        vx, vy, vz = x - hx, y - hy, z - hz
        al = vx * d[0] + vy * d[1] + vz * d[2]
        if not 0.5 < al < 15:
            return False
        r = 1.1 + al * 0.1
        return vx * vx + vy * vy + vz * vz - al * al < r * r

    # ---- environment
    def pick_weather(s, excl=None):
        ws = s.loc["wt"]
        ch = [w for w in range(4) if w != excl and ws[w] > 0] or [0]
        return random.choices(ch, [ws[w] for w in ch])[0]

    def reroll_weather(s):
        s.weather = s.wnext = s.pick_weather() if s.wmode == 0 else s.wmode - 1
        s.wk, s.wtimer = 1.0, random.uniform(25, 50)
        s.seed_weather()

    def randomize_env(s):
        if s.tod == 3:
            s.clock = random.uniform(0, 120)
        s.reroll_weather()

    def seed_weather(s):
        n = (0, 450, 320, 380)[s.weather]
        s.wx = [[random.uniform(-16, 16), random.uniform(0, 14), random.uniform(-45, 8)] for _ in range(n)]

    def cycle_weather(s):
        s.wmode = (s.wmode + 1) % 5
        s.wnext = s.pick_weather() if s.wmode == 0 else s.wmode - 1
        s.wtimer = random.uniform(25, 50)

    def weather_tick(s, dt):
        if s.wmode == 0:                            # auto: change every 25-50 s (odds depend on location)
            s.wtimer -= dt
            if s.wtimer <= 0:
                s.wtimer = random.uniform(25, 50)
                s.wnext = s.pick_weather(s.wnext)
        if s.weather != s.wnext:                    # fade old weather out, then new one in
            s.wk -= dt / 1.5
            if s.wk <= 0 or s.weather == 0:
                s.weather, s.wk = s.wnext, 0.0
                s.seed_weather()
        else:
            s.wk = min(1.0, s.wk + dt / 3)
        sp, w = s.speed, s.weather
        for p in s.wx:
            if w == 1:
                p[1] -= 24 * dt; p[2] += sp * 0.4 * dt
            elif w == 2:
                p[1] -= 2.2 * dt; p[0] += math.sin(s.t * 1.5 + p[2]) * 0.6 * dt; p[2] += sp * 0.6 * dt
            else:
                p[0] += 16 * dt; p[1] += math.sin(s.t * 3 + p[0]) * 0.5 * dt; p[2] += sp * 0.7 * dt
            if p[1] < 0: p[1] = 14
            if p[1] > 14: p[1] = 0.2
            if p[2] > 8: p[2] = -45
            if p[0] > 16: p[0] = -16
        s.bolt = max(0, s.bolt - dt)
        if w == 1 and s.wk > 0.5 and random.random() < 0.15 * dt:
            s.bolt = 0.18

    def drone_down(s, dr):
        dr["dead"] = True
        s.kills += 1
        s.chain += 1
        s.score += 75 * s.mult
        x = s.rx(dr["x"], dr["z"])
        s.burst(x, dr["y"], dr["z"], (0.5, 0.85, 1.0), 20)
        s.burst(x, dr["y"], dr["z"], (1.0, 0.6, 0.1), 14)
        sfx(450, 80)

    def pause(s):
        if s.state in ("play", "paused"):
            s.state = "paused" if s.state == "play" else "play"

    # ---- spawning
    def spawn_row(s):
        d = s.dd
        z = -100.0
        lanes = list(range(LANES))
        random.shuffle(lanes)
        for i in lanes[:random.choice(d["nobs"])]:
            s.obs.append({"x": (i - 2) * LW, "z": z, "k": random.choice(("barrier", "beam", "crate"))})
        free = lanes[3:] or lanes[-1:]
        cx = (random.choice(free) - 2) * LW
        for n in range(random.randint(3, 6)):
            s.cns.append([cx, z - n * 2.2])
        r = random.random()
        if r < d["clone_p"] and len(s.clones) < d["clone_max"]:
            s.clones.append({"x": (random.randrange(LANES) - 2) * LW, "z": z - 6, "cd": random.uniform(.5, 1.5)})
        elif r > 1 - d["item_p"]:
            s.items.append({"x": (random.randrange(LANES) - 2) * LW, "z": z - 10,
                            "k": random.choice(("shield", "rapid", "heal"))})
        if s.time > d["drone_t"] and len(s.drones) < d["drone_max"] and \
                random.random() < min(d["drone_cap"], d["drone_p"] + s.time * 0.003):
            s.drones.append({"x": (random.randrange(LANES) - 2) * LW, "y": 3.2, "z": z - 12,
                             "cd": random.uniform(0.8, 1.6), "ph": random.uniform(0, 6.28), "rot": 0.0})

    # ---- per-frame update
    def update(s, dt):
        s.t += dt
        if s.state != "paused":
            s.clock += dt
            s.weather_tick(dt)
        if s.state == "menu":
            s.D += 5 * dt
            s.phase += 4 * dt
            s.update_road(dt)
            return
        if s.state != "play":
            return
        d, rx = s.dd, s.rx
        s.time += dt
        s.target = max(s.vmin, min(d["vmax"], s.target))
        s.speed += (s.target - s.speed) * min(1, 3 * dt)
        sp = s.speed
        s.D += sp * dt
        s.update_road(dt)
        s.score += sp * dt * 0.2 * (sp / 14)
        s.phase += sp * dt * 0.7
        s.px += (((s.lane - 2) * LW) - s.px) * min(1, (12, 8, 9, 12)[s.weather] * dt)
        if s.py > 0 or s.vy > 0:
            s.vy -= 24 * dt
            s.py = max(0.0, s.py + s.vy * dt)
            if s.py == 0.0:
                s.vy = 0.0
        s.slide = max(0, s.slide - dt)
        s.invuln = max(0, s.invuln - dt)
        s.rapid = max(0, s.rapid - dt)
        s.shake = max(0, s.shake - dt * 1.5)
        s.flash = max(0, s.flash - dt)
        s.fire_cd -= dt
        if s.D >= s.next_spawn:
            s.spawn_row()
            s.next_spawn = s.D + max(d["gapmin"], d["gap0"] - s.time * d["gaps"])

        top = s.py + (0.9 if s.slide > 0 else 1.9)

        # flamethrower: streams toward the mouse aim
        if s.heat and s.fuel > 25:
            s.heat = False
        if s.fire_on and not s.heat:
            s.fuel -= 38 * dt
            if s.fuel <= 0:
                s.fuel, s.heat = 0.0, True
            hx, hy, hz = s.hand
            a = s.aim
            for _ in range(7):
                L, v = random.uniform(.4, .7), random.uniform(18, 27)
                s.flames.append([hx, hy, hz, a[0] * v + random.uniform(-1.6, 1.6),
                                 a[1] * v + random.uniform(-1.0, 1.2), a[2] * v + random.uniform(-1.6, 1.6), L, L])
            for o in s.obs:
                cy = {"crate": 0.9, "barrier": 0.45, "beam": 1.5}[o["k"]]
                ox = rx(o["x"], o["z"])
                if not o.get("dead") and s.in_cone(ox, cy, o["z"]):
                    o["burn"] = o.get("burn", 0) + dt
                    s.flames.append([ox + random.uniform(-.7, .7), 0.8, o["z"], 0, 2.5, 0, .4, .4])
                    if o["burn"] > {"crate": .35, "barrier": .5, "beam": .7}[o["k"]]:
                        o["dead"] = True
                        s.score += 15 * s.mult
                        s.burst(ox, 1, o["z"], (1, 0.5, 0.1), 18)
            for c in s.clones:
                cx_ = rx(c["x"], c["z"])
                if not c.get("dead") and s.in_cone(cx_, 1.1, c["z"]):
                    c["burn"] = c.get("burn", 0) + dt
                    s.flames.append([cx_ + random.uniform(-.4, .4), 1.2, c["z"], 0, 2.5, 0, .4, .4])
                    if c["burn"] > 0.5:
                        c["dead"] = True
                        s.kills += 1
                        s.chain += 1
                        s.score += 50 * s.mult
                        s.burst(cx_, 1.2, c["z"], (1, 0.4, 0.1), 26)
                        sfx(600, 50)
            for dr in s.drones:
                dx_ = rx(dr["x"], dr["z"])
                if not dr.get("dead") and s.in_cone(dx_, dr["y"], dr["z"]):
                    dr["burn"] = dr.get("burn", 0) + dt
                    s.flames.append([dx_ + random.uniform(-.4, .4), dr["y"], dr["z"], 0, 2.0, 0, .35, .35])
                    if dr["burn"] > 0.4:
                        s.drone_down(dr)
        else:
            s.fuel = min(100.0, s.fuel + 14 * dt)

        # player bullets (aimed at the mouse; 3 sub-steps so fast bullets cannot tunnel)
        for b in s.pb:
            for _ in range(3):
                b["x"] += b["dx"] * dt / 3
                b["y"] += b["dy"] * dt / 3
                b["z"] += b["dz"] * dt / 3
                for o in s.obs:
                    if o["k"] == "crate" and not o.get("dead") and \
                       (rx(o["x"], o["z"]) - b["x"]) ** 2 + (0.9 - b["y"]) ** 2 + (o["z"] - b["z"]) ** 2 < 1.3:
                        o["dead"] = b["dead"] = True
                        s.score += 20 * s.mult
                        s.burst(rx(o["x"], o["z"]), 1, o["z"], (0.7, 0.45, 0.2), 18)
                for c in s.clones:
                    if not c.get("dead") and \
                       (rx(c["x"], c["z"]) - b["x"]) ** 2 + (1.1 - b["y"]) ** 2 + (c["z"] - b["z"]) ** 2 < 1.0:
                        c["dead"] = b["dead"] = True
                        s.kills += 1
                        s.chain += 1
                        s.score += 50 * s.mult
                        s.burst(rx(c["x"], c["z"]), 1.2, c["z"], (0.9, 0.1, 0.1), 24)
                        sfx(700, 60)
                for dr in s.drones:
                    if not dr.get("dead") and \
                       (rx(dr["x"], dr["z"]) - b["x"]) ** 2 + (dr["y"] - b["y"]) ** 2 + (dr["z"] - b["z"]) ** 2 < 1.1:
                        b["dead"] = True
                        s.drone_down(dr)
                if b.get("dead"):
                    break
            if b["z"] < -110 or b["y"] < 0 or b["y"] > 40 or abs(b["x"]) > 60:
                b["dead"] = True

        # obstacles
        for o in s.obs:
            o["z"] += sp * dt
            if abs(o["z"]) < 1.0 and abs(o["x"] - s.px) < 1.0 and not o.get("dead"):
                k = o["k"]
                hit = (k == "barrier" and s.py < 0.9) or (k == "crate" and s.py < 1.8) or \
                      (k == "beam" and top > 1.1 and s.py < 2.2)
                if hit:
                    o["dead"] = True
                    s.hurt(20)
                    s.burst(o["x"], 1, o["z"], (0.9, 0.5, 0.1), 14)
            if o["z"] > 6:
                o["dead"] = True

        # coins & items
        for c in s.cns:
            c[1] += sp * dt
            if abs(c[1]) < 1.0 and abs(c[0] - s.px) < 1.0 and s.py < 2.2:
                c.append(1)
                s.coins += 1
                s.chain += 1
                s.score += 10 * s.mult
                s.burst(c[0], 1, c[1], GOLD, 6)
                sfx(1300, 30)
        for it in s.items:
            it["z"] += sp * dt
            if abs(it["z"]) < 1.2 and abs(it["x"] - s.px) < 1.2:
                it["dead"] = True
                if it["k"] == "shield":
                    s.shield = True
                elif it["k"] == "rapid":
                    s.rapid = 8
                else:
                    s.health = min(s.hpmax, s.health + d["heal"])
                s.burst(it["x"], 1, it["z"], (1, 1, 1), 20)
                sfx(900, 90)
            if it["z"] > 6:
                it["dead"] = True

        # clone guards
        for c in s.clones:
            c["z"] += sp * 0.55 * dt
            if c["z"] > -30:
                c["x"] += max(-1, min(1, s.px - c["x"])) * 1.6 * dt
            c["cd"] -= dt
            if -60 < c["z"] < -8 and c["cd"] <= 0:
                s.cb.append({"x": c["x"], "z": c["z"] + 1})
                c["cd"] = random.uniform(1.3, 2.2) * d["ecd"]
            if abs(c["z"]) < 1.2 and abs(c["x"] - s.px) < 1.2 and not c.get("dead"):
                c["dead"] = True
                s.hurt(30)
            if c["z"] > 6:
                c["dead"] = True
        for b in s.cb:
            if "vx" in b:                                   # drone shot: flies straight at where you were
                b["x"] += b["vx"] * dt; b["y"] += b["vy"] * dt; b["z"] += b["vz"] * dt
                cy = s.py + (0.45 if s.slide > 0 else 0.95)
                if (b["x"] - s.px) ** 2 + (b["y"] - cy) ** 2 + b["z"] ** 2 < 0.8:
                    b["dead"] = True
                    s.hurt(12)
                if b["z"] > 8 or b["y"] < 0:
                    b["dead"] = True
                continue
            b["z"] += (sp + 22) * dt
            if abs(b["z"]) < 0.8 and abs(b["x"] - s.px) < 0.8 and top > 0.95 and s.py < 1.45:
                b["dead"] = True
                s.hurt(15)
            if b["z"] > 8:
                b["dead"] = True

        # flying drones: hover high, strafe toward you, shoot, then dive (slide under or shoot them)
        for dr in s.drones:
            dr["z"] += sp * 0.5 * dt
            dr["x"] += max(-1, min(1, s.px - dr["x"])) * 2.2 * dt
            dr["rot"] += 900 * dt
            dr["cd"] -= dt
            if dr["z"] > -22:
                dr["y"] += (1.45 - dr["y"]) * min(1, 1.2 * dt)
            else:
                dr["y"] = 3.2 + 0.25 * math.sin(s.t * 3 + dr["ph"])
            if -55 < dr["z"] < -10 and dr["cd"] <= 0:
                wx_ = rx(dr["x"], dr["z"])
                tx, ty, tz = s.px - wx_, s.py + 0.9 - dr["y"], -dr["z"]
                n = math.sqrt(tx * tx + ty * ty + tz * tz) or 1.0
                s.cb.append({"x": wx_, "y": dr["y"], "z": dr["z"],
                             "vx": tx / n * 26, "vy": ty / n * 26, "vz": tz / n * 26})
                dr["cd"] = random.uniform(1.4, 2.2) * d["ecd"]
            if abs(dr["z"]) < 1.2 and abs(dr["x"] - s.px) < 1.1 and not dr.get("dead") \
                    and s.py - 0.3 < dr["y"] < top + 0.3:
                s.drone_down(dr)
                s.score = max(0.0, s.score - 75 * s.mult)    # crashing into you gives no points
                s.kills -= 1
                s.hurt(25)
            if dr["z"] > 6:
                dr["dead"] = True

        # particles
        for p in s.parts:
            p[0] += p[3] * dt
            p[1] = max(0, p[1] + p[4] * dt)
            p[2] += (p[5] + sp) * dt
            p[4] -= 9 * dt
            p[6] -= dt
        for f in s.flames:
            f[0] += f[3] * dt; f[1] += f[4] * dt; f[2] += f[5] * dt; f[6] -= dt
        s.flames = [f for f in s.flames if f[6] > 0]
        for name in ("obs", "items", "clones", "drones", "pb", "cb"):
            setattr(s, name, [e for e in getattr(s, name) if not e.get("dead")])
        s.cns = [c for c in s.cns if len(c) == 2 and c[1] < 6]
        s.parts = [p for p in s.parts if p[6] > 0]


g = Game()


# ------------------------------------------------------------ drawing helpers
def box(x, y, z, sx, sy, sz, c, glow=False):
    glColor3f(*c)
    if glow: glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glutSolidCube(1)
    glPopMatrix()
    if glow: glEnable(GL_LIGHTING)


def ball(x, y, z, r, c, sx=1, sy=1, sz=1, glow=False):
    glColor3f(*c)
    if glow: glDisable(GL_LIGHTING)
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(sx, sy, sz)
    glutSolidSphere(r, 20, 14)
    glPopMatrix()
    if glow: glEnable(GL_LIGHTING)


def quad(x0, x1, z0, z1, y, c):
    glColor3f(*c)
    glNormal3f(0, 1, 0)
    glBegin(GL_QUADS)
    glVertex3f(x0, y, z0); glVertex3f(x1, y, z0); glVertex3f(x1, y, z1); glVertex3f(x0, y, z1)
    glEnd()


def shadow(x, z, r, a=0.35):                    # soft contact shadow
    glDisable(GL_LIGHTING); glEnable(GL_BLEND); glDepthMask(GL_FALSE)
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(0, 0, 0, a); glVertex3f(x, 0.03, z)
    glColor4f(0, 0, 0, 0)
    for k in range(13):
        an = k * math.pi / 6
        glVertex3f(x + math.cos(an) * r, 0.03, z + math.sin(an) * r * 1.3)
    glEnd()
    glDepthMask(GL_TRUE); glDisable(GL_BLEND); glEnable(GL_LIGHTING)


def halo(x, y, z, r, c, a):                     # additive glow billboard
    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE); glDepthMask(GL_FALSE)
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(*c, a); glVertex3f(x, y, z)
    glColor4f(*c, 0)
    for k in range(25):
        an = k * math.pi / 12
        glVertex3f(x + math.cos(an) * r, y + math.sin(an) * r, z)
    glEnd()
    glDepthMask(GL_TRUE); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA); glDisable(GL_BLEND)


def figure(ph, vest, pants, skin, hair, enemy=False):
    sw = math.sin(ph) * 40
    for side in (-1, 1):
        glPushMatrix(); glTranslatef(side * 0.2, 0.9, 0); glRotatef(side * sw, 1, 0, 0)
        box(0, -0.45, 0, 0.24, 0.9, 0.26, pants); glPopMatrix()
        glPushMatrix(); glTranslatef(side * 0.5, 1.6, 0); glRotatef(-side * sw, 1, 0, 0)
        box(0, -0.35, 0, 0.18, 0.75, 0.18, skin); glPopMatrix()
    box(0, 1.3, 0, 0.75, 0.75, 0.38, vest)
    box(0, 0.98, 0, 0.78, 0.14, 0.42, GOLD)
    ball(0, 1.9, 0, 0.27, skin)
    ball(0, 1.98, 0.04, 0.3, hair, 1, 0.75, 1)
    if enemy:
        box(-0.1, 1.92, -0.26, 0.08, 0.06, 0.04, (1, 0, 0))
        box(0.1, 1.92, -0.26, 0.08, 0.06, 0.04, (1, 0, 0))
        box(0.38, 1.2, -0.45, 0.1, 0.12, 0.7, (0.3, 0.3, 0.3))


def draw_player():
    if g.view == 1 or (g.state == "play" and g.invuln > 0 and int(g.t * 20) % 2):
        return
    shadow(g.px, 0, 0.7 / (1 + g.py * 0.3), 0.4 / (1 + g.py * 0.4))
    glPushMatrix()
    glTranslatef(g.px, g.py, 0)
    if g.slide > 0:
        glTranslatef(0, 0.35, 0)
        glRotatef(-70, 1, 0, 0)
    figure(g.phase, (0.75, 0.1, 0.15), (0.95, 0.95, 0.9), (0.8, 0.55, 0.35), (0.08, 0.06, 0.05))
    glPopMatrix()
    if g.shield:
        glEnable(GL_BLEND)
        glColor4f(0.3, 0.7, 1, 0.28)
        glPushMatrix(); glTranslatef(g.px, g.py + 1, 0); glutSolidSphere(1.4, 24, 16); glPopMatrix()
        glDisable(GL_BLEND)


def draw_drone(dr):
    x, y, z = dr["x"] + g.off(dr["z"]), dr["y"], dr["z"]
    shadow(x, z, 0.7, 0.35)
    glPushMatrix()
    glTranslatef(x, y, z)
    ball(0, 0, 0, 0.5, (0.22, 0.24, 0.3), 1, 0.6, 1)
    ball(0, 0, 0.38, 0.14, (1, 0.1, 0.1), glow=True)                    # red eye faces the player
    box(0, -0.3, 0, 0.3, 0.12, 0.5, (0.15, 0.15, 0.18))
    box(0, 0.28, 0, 0.08, 0.2, 0.08, (0.3, 0.3, 0.3))
    for k in (0, 90):
        glPushMatrix(); glTranslatef(0, 0.4, 0); glRotatef(dr["rot"] + k, 0, 1, 0)
        box(0, 0, 0, 1.5, 0.04, 0.12, (0.7, 0.7, 0.75)); glPopMatrix()
    glPopMatrix()


def draw_obstacle(o):
    x, z = o["x"] + g.off(o["z"]), o["z"]
    if o["k"] == "barrier":
        box(x, 0.45, z, 1.9, 0.9, 0.5, (0.95, 0.5, 0.1))
        box(x, 0.45, z, 1.95, 0.2, 0.55, (1, 1, 1))
    elif o["k"] == "beam":
        for sx in (-0.95, 0.95):
            box(x + sx, 1.15, z, 0.2, 2.3, 0.3, (0.25, 0.15, 0.1))
        box(x, 1.65, z, 2.1, 1.1, 0.5, (0.7, 0.2, 0.1))
        box(x, 1.65, z, 2.15, 0.2, 0.55, GOLD)
    else:
        box(x, 0.9, z, 1.7, 1.8, 1.2, (0.55, 0.36, 0.18))
        box(x, 0.9, z, 1.75, 0.2, 1.25, (0.3, 0.18, 0.08))
        box(x, 0.9, z, 0.2, 1.85, 1.25, (0.3, 0.18, 0.08))


# ---- location scenery
def lamp(side, z, c):
    box(side * 5.9, 1.2, z, 0.1, 2.4, 0.1, (0.2, 0.15, 0.1))
    ball(side * 5.9, 2.5, z, 0.22, c, glow=True)


def scn_desert(side, h, j, z, e):
    bx, bh = side * (9 + (h >> 3) % 4), 3 + (h >> 5) % 6
    box(bx, bh / 2, z, 3, bh, 3, (0.85 - (h % 3) * .06, 0.7 - (h % 3) * .05, 0.5))
    if h % 2:
        ball(bx, bh + 0.2, z, 1.3, GOLD, 1, 0.9, 1)
    box(bx - side * 1.52, bh * 0.6, z, 0.05, 0.8, 0.6, (1, 0.85, 0.4), True)
    px_ = side * 6.9
    box(px_, 1.5, z + 3, 0.3, 3, 0.3, (0.4, 0.25, 0.1))
    for fx, fz in ((.7, 0), (-.7, 0), (0, .7), (0, -.7)):
        ball(px_ + fx, 3.1, z + 3 + fz, 0.9, (0.1, 0.5, 0.15), 1, 0.25, 1)
    ball(px_, 3.3, z + 3, 0.4, (0.1, 0.45, 0.12))


def scn_city(side, h, j, z, e):
    w = 3 + h % 3
    bh = 9 + (h >> 3) % 24
    bx = side * (9.5 + w / 2 + (h >> 6) % 4)
    d = 0.05 + (h % 4) * 0.02
    box(bx, bh / 2, z, w, bh, 4.5, (d, d + 0.01, d + 0.06))
    nc = ((0.2, 0.9, 1.0), (1.0, 0.25, 0.8), (0.7, 0.4, 1.0))[(h >> 4) % 3]
    fx = bx - side * (w / 2 + 0.04)
    glDisable(GL_LIGHTING)                                       # neon + windows are emissive
    box(fx, bh / 2, z + 2.0, 0.12, bh, 0.12, nc)
    lit = 0.35 + 0.65 * e["night"]
    for r in range(int(bh // 2.6)):
        if (h >> (r % 13)) & 1:
            wc = (lit, 0.82 * lit, 0.45 * lit) if (r + h) % 3 else (0.45 * lit, 0.85 * lit, lit)
            box(fx, 1.6 + r * 2.6, z, 0.06, 1.1, 2.6, wc)
    if (h >> 2) & 1:
        box(bx, bh + 0.7, z, w * 0.7, 1.2, 0.3, nc)
    glEnable(GL_LIGHTING)


def pine(x, z, s):
    box(x, 0.6 * s, z, 0.4 * s, 1.2 * s, 0.4 * s, (0.3, 0.2, 0.12))
    for r, hh, y, c in ((1.8, 2.4, 0.9, (0.10, 0.32, 0.22)), (1.4, 2.2, 2.3, (0.14, 0.38, 0.26)),
                        (1.0, 2.0, 3.6, (0.85, 0.92, 0.97))):
        glColor3f(*c)
        glPushMatrix(); glTranslatef(x, y * s, z); glRotatef(-90, 1, 0, 0)
        glutSolidCone(r * s, hh * s, 10, 2)
        glPopMatrix()


def scn_snow(side, h, j, z, e):
    pine(side * (8 + (h >> 3) % 6), z + h % 5, 0.9 + ((h >> 4) % 5) * 0.25)
    pine(side * (13 + (h >> 5) % 7), z + 6 - h % 4, 0.9 + ((h >> 6) % 5) * 0.25)
    ball(side * (7.2 + (h >> 7) % 3), 0.25, z + 3, 1.2, (0.96, 0.98, 1.0), 1.4, 0.35, 1)


def tree(x, z, s, c):
    box(x, 1.2 * s, z, 0.5 * s, 2.4 * s, 0.5 * s, (0.35, 0.24, 0.14))
    ball(x, 3.1 * s, z, 1.6 * s, c, 1, 1.05, 1)
    ball(x, 4.3 * s, z, 1.1 * s, tuple(min(1.0, v * 1.15) for v in c))


def scn_forest(side, h, j, z, e):
    sh = ((0.12, 0.45, 0.18), (0.18, 0.52, 0.22), (0.10, 0.38, 0.25), (0.30, 0.55, 0.15))
    tree(side * (8 + (h >> 3) % 5), z + 1, 0.9 + ((h >> 4) % 4) * 0.18, sh[h % 4])
    tree(side * (13 + (h >> 5) % 6), z + 5, 1.0 + ((h >> 6) % 4) * 0.18, sh[(h >> 2) % 4])
    if h % 3 == 0:
        ball(side * (6.9 + (h >> 6) % 2), 0.4, z + 4, 0.7, (0.45, 0.45, 0.48), 1.2, 0.7, 1)
    if e["night"] > 0.3:                                         # fireflies after dark
        for q in range(2):
            ball(side * (7 + q * 2.5) + math.sin(g.t + h) * 0.5, 1.2 + q * 0.7 + math.sin(g.t * 2 + h + q) * 0.3,
                 z + q * 2, 0.07, (0.9, 1.0, 0.35), glow=True)


SCN = {"desert": scn_desert, "city": scn_city, "snow": scn_snow, "forest": scn_forest}


def draw_road():
    D, L = g.D, g.loc
    rc, ec, dc = L["road"], L["edge"], L["dash"]
    j0 = int(math.floor((D - 10) / 2.0))
    zs = [D - (j0 + i) * 2.0 for i in range(84)]
    os_ = [g.off(z) for z in zs]
    glNormal3f(0, 1, 0)
    glBegin(GL_QUADS)                                            # asphalt, banded so speed is visible
    for i in range(83):
        k = 1.0 if ((j0 + i) // 4) % 2 else 0.88
        glColor3f(rc[0] * k, rc[1] * k, rc[2] * k)
        glVertex3f(os_[i] - 5.5, 0, zs[i]); glVertex3f(os_[i] + 5.5, 0, zs[i])
        glVertex3f(os_[i + 1] + 5.5, 0, zs[i + 1]); glVertex3f(os_[i + 1] - 5.5, 0, zs[i + 1])
    glEnd()
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    for sd in (-1, 1):                                           # neon edge: bright core + soft outer glow
        glBegin(GL_QUADS)
        for i in range(83):
            glColor4f(*ec, 1.0)
            glVertex3f(os_[i] + sd * 5.5, 0.04, zs[i]); glVertex3f(os_[i] + sd * 5.85, 0.04, zs[i])
            glVertex3f(os_[i + 1] + sd * 5.85, 0.04, zs[i + 1]); glVertex3f(os_[i + 1] + sd * 5.5, 0.04, zs[i + 1])
        glEnd()
        glBegin(GL_QUADS)
        for i in range(83):
            glColor4f(*ec, 0.35); glVertex3f(os_[i] + sd * 5.85, 0.03, zs[i])
            glColor4f(*ec, 0.0); glVertex3f(os_[i] + sd * 7.4, 0.03, zs[i])
            glVertex3f(os_[i + 1] + sd * 7.4, 0.03, zs[i + 1])
            glColor4f(*ec, 0.35); glVertex3f(os_[i + 1] + sd * 5.85, 0.03, zs[i + 1])
        glEnd()
    glDisable(GL_BLEND)
    glColor3f(*dc)
    glBegin(GL_QUADS)                                            # lane dashes follow the bend
    j6 = int(D // 6) - 1
    for j in range(j6, j6 + 27):
        za = D - j * 6.0
        zb = za - 2.5
        oa, ob = g.off(za), g.off(zb)
        for lx in (-3.3, -1.1, 1.1, 3.3):
            glVertex3f(oa + lx - 0.06, 0.02, za); glVertex3f(oa + lx + 0.06, 0.02, za)
            glVertex3f(ob + lx + 0.06, 0.02, zb); glVertex3f(ob + lx - 0.06, 0.02, zb)
    glEnd()
    glEnable(GL_LIGHTING)


def draw_scenery(e):
    D, L = g.D, g.loc
    quad(-220, 220, -175, 20, -0.02, L["ground"])
    if L["kind"] == "forest":                                    # a lake on the left
        quad(-220, -30, -175, 20, -0.01, lerp((0.14, 0.34, 0.46), e["sky"], 0.25))
    draw_road()
    fn = SCN[L["kind"]]
    j0 = int(D // 12) - 1
    for j in range(j0, j0 + 14):
        z = D - j * 12
        glPushMatrix()
        glTranslatef(g.off(z), 0, 0)
        for side in (-1, 1):
            h = (j * 73856093 + side * 83492791) & 0xFFFF
            fn(side, h, j, z, e)
            if j % 2 == 0:
                lc = L["lamp"]
                if L["kind"] == "city" and j % 4 == 0:
                    lc = (1.0, 0.3, 0.85)
                lamp(side, z, lc)
        glPopMatrix()


def _r(i):                                                       # deterministic pseudo-random 0..1
    return (((i * 2654435761) >> 7) & 1023) / 1023.0


def draw_backdrop(e):                                            # far silhouettes (mountains / dunes / skyline)
    L, n = g.loc, e["night"]
    base = tuple(c * (1 - 0.65 * n) for c in L["far"])
    col = lerp(base, e["sky"], 0.42)
    kind = L["kind"]
    for i in range(30):
        x = -290 + i * 20 + (_r(i) - 0.5) * 14
        r1, r2 = _r(i + 3), _r(i + 11)
        glPushMatrix()
        glTranslatef(x, -0.5, -165)
        glColor3f(*col)
        if kind == "desert":
            if i % 5 == 0:
                glRotatef(-90, 1, 0, 0); glRotatef(45, 0, 0, 1)
                glutSolidCone(24 + r1 * 14, 26 + r2 * 14, 4, 1)
            else:
                glScalef(1, 0.3, 0.5)
                glutSolidSphere(30 + r1 * 22, 16, 10)
        elif kind == "city":
            w, hh = 8 + r1 * 10, 25 + r2 * 60
            glTranslatef(0, hh / 2, 0)
            glScalef(w, hh, w)
            glutSolidCube(1)
        elif kind == "snow":
            R, H = 28 + r1 * 20, 44 + r2 * 34
            glRotatef(-90, 1, 0, 0)
            glutSolidCone(R, H, 6, 1)
            glColor3f(*lerp((0.97, 0.98, 1.0), e["sky"], 0.3))
            glTranslatef(0, 0, H * 0.6)
            glutSolidCone(R * 0.405, H * 0.405, 6, 1)
        else:
            glScalef(1, 0.4 + r2 * 0.3, 0.6)
            glutSolidSphere(28 + r1 * 20, 16, 10)
        glPopMatrix()
        if kind == "city":                                        # lit windows on the skyline
            w, hh = 8 + r1 * 10, 25 + r2 * 60
            lit = 0.25 + 0.75 * n
            for q in range(5):
                wc = ((1.0, 0.4, 0.9), (0.3, 0.9, 1.0), (1.0, 0.85, 0.5))[q % 3]
                box(x + (_r(i * 7 + q) - 0.5) * w * 0.7, 6 + _r(i * 13 + q) * (hh - 8), -165 + w / 2 + 0.2,
                    1.2, 1.8, 0.1, (wc[0] * lit, wc[1] * lit, wc[2] * lit))


YAW_GAIN = 1.2          # aim assist: widens the firing angle so >60 degrees is easy to reach
MAX_YAW, MIN_PITCH, MAX_PITCH = 85.0, -45.0, 60.0


def camera():
    """Eye, look-at point and vertical FOV for the current view (shared by rendering and aiming)."""
    v = g.view
    if v == 0:                                                    # chase (leans into the bend)
        eye, ctr = (g.px * 0.6, 4.3, 7.5), (g.px * 0.4 + g.off(-14) * 0.45, 1.4, -12.0)
    elif v == 1:                                                  # first person
        ey = g.py + (0.9 if g.slide > 0 else 1.75)
        eye, ctr = (g.px, ey, -0.2), (g.px + g.off(-20) * 0.5, ey - 0.15, -20.0)
    else:                                                         # overhead
        eye, ctr = (g.px * 0.4, 15.0, 9.0), (g.px * 0.4 + g.off(-9) * 0.3, 0.0, -9.0)
    return eye, ctr, (58, 92, 50)[v] + max(0, g.speed - 14) * 0.3


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / n for c in v]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def compute_aim():
    """Unit vector from Aladdin's hand toward the mouse cursor (pure maths, no GL queries)."""
    eye, ctr, fov = camera()
    f = _norm([ctr[i] - eye[i] for i in range(3)])
    r = _norm(_cross(f, (math.sin(g.roll), math.cos(g.roll), 0.0)))   # camera right (includes bank roll)
    u = _cross(r, f)
    th = math.tan(math.radians(fov) / 2)
    nx = 2.0 * g.mx / WIN[0] - 1.0
    ny = 1.0 - 2.0 * g.my / WIN[1]
    d = [f[i] + r[i] * nx * th * WIN[0] / WIN[1] + u[i] * ny * th for i in range(3)]
    hx, hy, hz = g.hand
    T = None
    if d[1] < -1e-3:                                  # ray hits the plane at hand height
        t = (hy - eye[1]) / d[1]
        if t > 0:
            T = [eye[i] + d[i] * t for i in range(3)]
    if T is None and d[2] < -1e-3:                    # cursor above horizon: use a wall 30 units ahead
        t = (-30 - eye[2]) / d[2]
        if t > 0:
            T = [eye[i] + d[i] * t for i in range(3)]
    if T is None:
        return (0.0, 0.0, -1.0)
    v = [T[0] - hx, T[1] - hy, T[2] - hz]
    if math.sqrt(sum(c * c for c in v)) < 1.5:       # target right at our feet: just follow the view ray
        v = d
    yaw = max(-MAX_YAW, min(MAX_YAW, math.degrees(math.atan2(v[0], -v[2])) * YAW_GAIN))
    pit = max(MIN_PITCH, min(MAX_PITCH, math.degrees(math.atan2(v[1], math.hypot(v[0], v[2])))))
    yr, pr = math.radians(yaw), math.radians(pit)
    return (math.sin(yr) * math.cos(pr), math.sin(pr), -math.cos(yr) * math.cos(pr))


def sky_gradient(e):                                              # screen-space gradient behind the world
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, 1, 0, 1)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING); glDisable(GL_FOG)
    sk, tp = e["sky"], e["top"]
    glBegin(GL_QUADS)
    glColor3f(*sk); glVertex2f(0, 0); glVertex2f(1, 0); glVertex2f(1, 0.5); glVertex2f(0, 0.5)
    glColor3f(*sk); glVertex2f(0, 0.5); glVertex2f(1, 0.5)
    glColor3f(*tp); glVertex2f(1, 1); glVertex2f(0, 1)
    glEnd()
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix()


def draw_world():
    e = env()
    L = g.loc
    glClearColor(*e["sky"], 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    sky_gradient(e)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    eye, ctr, fov = camera()
    gluPerspective(fov, WIN[0] / WIN[1], 0.3, 260)                # FOV widens with speed
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    sh = g.shake * 0.8 if g.state == "play" else 0.0              # no shake on pause / game over
    jx, jy = random.uniform(-sh, sh), random.uniform(-sh, sh) * 0.5
    gluLookAt(eye[0] + jx, eye[1] + jy, eye[2], ctr[0], ctr[1], ctr[2],
              math.sin(g.roll), math.cos(g.roll), 0)             # banks into bends
    g.aim = compute_aim()
    glFogfv(GL_FOG_COLOR, (*e["sky"], 1)); glFogf(GL_FOG_START, e["fs"]); glFogf(GL_FOG_END, e["fe"])
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (*e["amb"], 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (*e["dif"], 1))
    glLightfv(GL_LIGHT0, GL_POSITION, (0.4, 1.0, 0.5, 0.0))
    t = max(e["night"] * 0.9, L["glow"], 0.9 if (g.fire_on and not g.heat and g.state == "play") else 0.0)
    tc = L["torch"]
    glEnable(GL_LIGHT1)                                            # torch / flame / neon light
    glLightfv(GL_LIGHT1, GL_POSITION, (g.px, 3.0, 2.0, 1.0))
    glLightfv(GL_LIGHT1, GL_DIFFUSE, (t * tc[0], t * tc[1], t * tc[2], 1))
    glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.08)

    glDisable(GL_LIGHTING); glDisable(GL_FOG)                    # sky bodies + far backdrop
    if e["stars"] > 0.05:
        glPointSize(2)
        glBegin(GL_POINTS)
        for sx, sy_, sz, v in STARS:
            glColor3f(v * e["stars"], v * e["stars"], v * e["stars"])
            glVertex3f(sx, sy_, sz)
        glEnd()
    sr = lerp(16.0, 9.0, e["night"])
    glColor3f(*e["sun"])
    glPushMatrix(); glTranslatef(-38, e["sy"] * 1.5, -190); glutSolidSphere(sr, 28, 18); glPopMatrix()
    halo(-38, e["sy"] * 1.5, -188, sr * 4.2, e["sun"], 0.55 * (1 - 0.85 * g.wk * (1 if g.weather else 0)))
    draw_backdrop(e)
    glEnable(GL_LIGHTING); glEnable(GL_FOG)

    draw_scenery(e)
    for o in g.obs: draw_obstacle(o)
    for x, z in g.cns:
        glPushMatrix(); glTranslatef(x + g.off(z), 1.0 + 0.15 * math.sin(g.t * 4 + z), z)
        glRotatef(g.t * 180, 0, 1, 0); glScalef(1, 1, 0.2)
        glColor3f(*GOLD); glutSolidSphere(0.35, 16, 12); glPopMatrix()
    for it in g.items:
        c = {"shield": (0.3, 0.7, 1), "rapid": (1, 0.5, 0.1), "heal": (0.2, 0.9, 0.3)}[it["k"]]
        glPushMatrix(); glTranslatef(it["x"] + g.off(it["z"]), 1.1 + 0.2 * math.sin(g.t * 3), it["z"])
        glRotatef(g.t * 120, 0, 1, 0)
        ball(0, 0, 0, 0.35, c)
        glRotatef(70, 1, 0, 0); glColor3f(1, 1, 1); glutSolidTorus(0.05, 0.6, 8, 20)
        glPopMatrix()
    for c in g.clones:
        cxx = c["x"] + g.off(c["z"])
        shadow(cxx, c["z"], 0.7, 0.35)
        glPushMatrix(); glTranslatef(cxx, 0, c["z"]); glRotatef(180, 0, 1, 0)
        figure(g.t * 8, (0.12, 0.12, 0.15), (0.05, 0.05, 0.07), (0.5, 0.4, 0.35), (0, 0, 0), True)
        glPopMatrix()
    for dr in g.drones: draw_drone(dr)
    draw_player()

    glDisable(GL_LIGHTING); glDisable(GL_FOG)                    # unlit effects
    for b in g.pb:
        glColor3f(1, 1, 0.3); glPushMatrix(); glTranslatef(b["x"], b["y"], b["z"]); glutSolidSphere(0.18, 10, 8); glPopMatrix()
    for b in g.cb:
        glColor3f(*((1, 0.2, 0.9) if "vx" in b else (1, 0.15, 0.1)))
        bx_ = b["x"] if "vx" in b else b["x"] + g.off(b["z"])
        glPushMatrix(); glTranslatef(bx_, b.get("y", 1.2), b["z"]); glutSolidSphere(0.25, 10, 8); glPopMatrix()
    glPointSize(5)
    glBegin(GL_POINTS)
    for p in g.parts:
        glColor3f(*p[7]); glVertex3f(p[0], p[1], p[2])
    glEnd()
    wl = g.wx[:int(len(g.wx) * g.wk)]
    if wl:                                                         # weather
        if g.weather == 1:
            glColor3f(0.7, 0.8, 1)
            glBegin(GL_LINES)
            for p in wl:
                glVertex3f(p[0], p[1], p[2]); glVertex3f(p[0], p[1] + 0.7, p[2] - 0.15)
            glEnd()
        else:
            glPointSize(4 if g.weather == 2 else 3)
            glColor3f(*((1, 1, 1) if g.weather == 2 else (0.85, 0.7, 0.45)))
            glBegin(GL_POINTS)
            for p in wl:
                glVertex3f(*p)
            glEnd()
    if g.flames:                                                   # fire
        glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        for size, hot in ((11, False), (5, True)):
            glPointSize(size)
            glBegin(GL_POINTS)
            for f in g.flames:
                k = f[6] / f[7]
                glColor4f(1, 0.95 if hot else 0.25 + 0.5 * k, 0.6 if hot else 0.05, k)
                glVertex3f(f[0], f[1], f[2])
            glEnd()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA); glDisable(GL_BLEND)
    glEnable(GL_LIGHTING); glEnable(GL_FOG)


# ------------------------------------------------------------------------ HUD
H10, H12, H18 = GLUT_BITMAP_HELVETICA_10, GLUT_BITMAP_HELVETICA_12, GLUT_BITMAP_HELVETICA_18
T24 = GLUT_BITMAP_TIMES_ROMAN_24
DARK = (0.04, 0.05, 0.09)
DIM = (0.62, 0.66, 0.76)
UI = []                                                            # clickable regions, rebuilt each frame


def text(x, y, s, font=H18, c=(1, 1, 1)):
    glColor3f(*c)
    glRasterPos2f(x, y)
    for ch in s:
        glutBitmapCharacter(font, ord(ch))


def tw_(s, font):
    return sum(glutBitmapWidth(font, ord(ch)) for ch in s)


def text_m(xc, y, s, font=H18, c=(1, 1, 1), sh=True):            # centred on xc, optional drop shadow
    x = xc - tw_(s, font) / 2
    if sh:
        text(x + 1, y - 1, s, font, (0, 0, 0))
    text(x, y, s, font, c)


def text_c(y, s, font=H18, c=(1, 1, 1)):
    text_m(WIN[0] / 2, y, s, font, c)


def stroke_w(s, sc):
    return sum(glutStrokeWidth(GLUT_STROKE_ROMAN, ord(ch)) for ch in s) * sc


def stroke(x, y, s, sc, c, lw=3.0, a=1.0):                       # big scalable title text
    glColor4f(*c, a)
    glLineWidth(lw)
    glPushMatrix(); glTranslatef(x, y, 0); glScalef(sc, sc, 1)
    for ch in s:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(ch))
    glPopMatrix()
    glLineWidth(1)


def rect(x, y, w, h, c, a=1.0):
    glColor4f(*c, a)
    glBegin(GL_QUADS)
    glVertex2f(x, y); glVertex2f(x + w, y); glVertex2f(x + w, y + h); glVertex2f(x, y + h)
    glEnd()


def rrect(x, y, w, h, r, c, a=1.0):                              # rounded rectangle
    r = max(0.0, min(r, w / 2, h / 2))
    glColor4f(*c, a)
    glBegin(GL_QUADS)
    glVertex2f(x + r, y); glVertex2f(x + w - r, y); glVertex2f(x + w - r, y + h); glVertex2f(x + r, y + h)
    glVertex2f(x, y + r); glVertex2f(x + r, y + r); glVertex2f(x + r, y + h - r); glVertex2f(x, y + h - r)
    glVertex2f(x + w - r, y + r); glVertex2f(x + w, y + r); glVertex2f(x + w, y + h - r); glVertex2f(x + w - r, y + h - r)
    glEnd()
    if r > 0:
        for cx_, cy_, a0 in ((x + r, y + r, 180), (x + w - r, y + r, 270), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90)):
            glBegin(GL_TRIANGLE_FAN)
            glVertex2f(cx_, cy_)
            for k in range(7):
                an = math.radians(a0 + k * 15)
                glVertex2f(cx_ + r * math.cos(an), cy_ + r * math.sin(an))
            glEnd()


def tri(x1, y1, x2, y2, x3, y3, c, a=1.0):
    glColor4f(*c, a)
    glBegin(GL_TRIANGLES)
    glVertex2f(x1, y1); glVertex2f(x2, y2); glVertex2f(x3, y3)
    glEnd()


def vignette(a):
    w, h = WIN
    m, n = 0.16 * w, 0.22 * h
    glBegin(GL_QUADS)
    for pts in (((0, 0, a), (m, 0, 0), (m, h, 0), (0, h, a)),
                ((w, 0, a), (w - m, 0, 0), (w - m, h, 0), (w, h, a)),
                ((0, 0, a), (w, 0, a), (w, n, 0), (0, n, 0)),
                ((0, h, a), (w, h, a), (w, h - n, 0), (0, h - n, 0))):
        for px_, py_, pa in pts:
            glColor4f(0, 0, 0, pa); glVertex2f(px_, py_)
    glEnd()


def speed_lines():
    w, h = WIN
    k = min(1.0, (g.speed - 22) / 20)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    for _ in range(int(10 + 20 * k)):
        an = random.uniform(0, 6.2832)
        r0, r1 = random.uniform(0.38, 0.55), random.uniform(0.6, 0.9)
        ca, sa = math.cos(an), math.sin(an)
        glColor4f(1, 1, 1, 0.0); glVertex2f(w / 2 + ca * w * r0, h / 2 + sa * h * r0)
        glColor4f(1, 1, 1, 0.22 * k); glVertex2f(w / 2 + ca * w * r1, h / 2 + sa * h * r1)
    glEnd()
    glLineWidth(1)


def button(x, y, w, h, act, label, col, sel=False, sub=None):
    hov = x <= g.mx <= x + w and y <= WIN[1] - g.my <= y + h
    UI.append((x, y, w, h, act))
    bc = col if (sel or hov) else (0.35, 0.36, 0.42)
    rrect(x - 2, y - 2, w + 4, h + 4, 13, bc, 1.0 if sel else (0.85 if hov else 0.5))
    rrect(x, y, w, h, 11, (0.08, 0.09, 0.13), 0.97)
    if sel:
        rrect(x, y, w, h, 11, col, 0.28)
    lc = (1, 1, 1) if (sel or hov) else (0.75, 0.77, 0.83)
    if sub:
        text_m(x + w / 2, y + h / 2 + 3, label, H18, lc)
        text_m(x + w / 2, y + 8, sub, H10, DIM, False)
    else:
        text_m(x + w / 2, y + h / 2 - 6, label, H18, lc)


def hud_play(w, h):
    d, L = g.dd, g.loc
    acc = L["acc"]
    # health + flamethrower panel
    rrect(14, h - 72, 312, 58, 14, DARK, 0.66)
    hp = max(0, g.health) / g.hpmax
    rrect(24, h - 40, 292, 18, 9, (0.15, 0.16, 0.2), 0.9)
    if hp > 0.01:
        rrect(24, h - 40, max(18, 292 * hp), 18, 9, lerp((0.95, 0.25, 0.2), (0.3, 0.9, 0.5), hp), 1.0)
    text(32, h - 36, f"HP  {max(0, g.health)} / {g.hpmax}", H12)
    rrect(24, h - 62, 200, 9, 4, (0.15, 0.16, 0.2), 0.9)
    if g.fuel > 1:
        rrect(24, h - 62, max(9, 200 * g.fuel / 100), 9, 4, (1, .25, .1) if g.heat else (1, .65, .1), 1.0)
    text(232, h - 62, "OVERHEATED" if g.heat else "FLAME [G]", H10, (1, .35, .25) if g.heat else (1, .8, .4))
    # score
    rrect(w / 2 - 105, h - 70, 210, 56, 16, DARK, 0.66)
    text_m(w / 2, h - 33, "SCORE", H10, DIM, False)
    text_m(w / 2, h - 60, f"{int(g.score)}", T24, GOLD)
    # coins / best / badge
    rrect(w - 226, h - 72, 212, 58, 14, DARK, 0.66)
    glColor3f(*GOLD)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(w - 202, h - 34)
    for k in range(17):
        glVertex2f(w - 202 + 9 * math.cos(k * math.pi / 8), h - 34 + 9 * math.sin(k * math.pi / 8))
    glEnd()
    text(w - 184, h - 40, f"{g.coins}", H18)
    text(w - 124, h - 38, f"Best {g.hi}", H12, DIM)
    text(w - 214, h - 62, f"{d['name'].upper()}  |  {L['name'].upper()}", H10, d["col"])
    # combo
    y = h - 98
    if g.mult > 1:
        text_m(w / 2, y, f"COMBO x{g.mult}", T24, (1, 0.6, 0.1))
        rrect(w / 2 - 60, y - 14, 120, 6, 3, (0.15, 0.16, 0.2), 0.9)
        prog = 1.0 if g.mult >= 5 else (g.chain % 5) / 5
        if prog > 0.02:
            rrect(w / 2 - 60, y - 14, max(6, 120 * prog), 6, 3, (1, 0.6, 0.1), 1.0)
        y -= 38
    # curve warning
    kk = g.curv(g.D + 35)
    if abs(kk) > 0.0007:
        sd = 1 if kk > 0 else -1
        for i in range(3):
            al = 0.35 + 0.65 * max(0.0, math.sin(g.t * 9 - i * 0.9))
            bx = w / 2 + sd * (30 + i * 20)
            tri(bx - sd * 8, y - 3, bx - sd * 8, y + 15, bx + sd * 6, y + 6, acc, al)
        text_m(w / 2, y - 14, "CURVE " + ("RIGHT" if sd > 0 else "LEFT"), H10, (1, 1, 1))
    # speed gauge
    rrect(w / 2 - 150, 16, 300, 38, 14, DARK, 0.66)
    fr = max(0.0, min(1.0, g.speed / d["vmax"]))
    rrect(w / 2 - 138, 24, 276, 9, 4, (0.15, 0.16, 0.2), 0.9)
    rrect(w / 2 - 138, 24, max(9, 276 * fr), 9, 4, lerp((0.3, 0.8, 1.0), (1.0, 0.4, 0.2), fr), 1.0)
    rect(w / 2 - 138 + 276 * g.vmin / d["vmax"], 22, 2, 13, (1, 1, 1), 0.8)
    text_m(w / 2, 39, f"{int(g.speed * 4)} km/h", H12, (1, 1, 1))
    text(w / 2 + 160, 30, "Q / E", H10, DIM)
    # power-ups
    y = 24
    if g.shield:
        rrect(14, y, 112, 30, 15, (0.1, 0.32, 0.55), 0.85)
        text_m(70, y + 10, "SHIELD", H12, (0.7, 0.9, 1)); y += 38
    if g.rapid > 0:
        rrect(14, y, 138, 30, 15, (0.55, 0.28, 0.05), 0.85)
        text_m(83, y + 10, f"RAPID FIRE {g.rapid:.0f}s", H12, (1, 0.85, 0.5))
    # reticle (dark outline + white core so it reads on any background)
    if g.state == "play":
        cx_, cy_ = g.mx, WIN[1] - g.my
        for lw, col, al in ((4.5, (0, 0, 0), 0.55), (2, (1, 1, 1), 1.0)):
            glLineWidth(lw)
            glColor4f(*col, al)
            glBegin(GL_LINE_LOOP)
            for k in range(28):
                glVertex2f(cx_ + 11 * math.cos(k * math.pi / 14), cy_ + 11 * math.sin(k * math.pi / 14))
            glEnd()
            glBegin(GL_LINES)
            for dx_, dy_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                glVertex2f(cx_ + dx_ * 15, cy_ + dy_ * 15); glVertex2f(cx_ + dx_ * 21, cy_ + dy_ * 21)
            glEnd()
        glLineWidth(1)
        rect(cx_ - 2, cy_ - 2, 4, 4, (0, 0, 0), 0.6)
        rect(cx_ - 1.5, cy_ - 1.5, 3, 3, acc, 1.0)


def menu_screen(w, h):
    L = g.loc
    cx, cy = w / 2, h / 2
    rect(0, 0, w, h, (0, 0, 0), 0.30)
    pw, ph = 820, 520
    x0, y0 = cx - pw / 2, cy - ph / 2
    top = y0 + ph
    rrect(x0 - 3, y0 - 3, pw + 6, ph + 6, 23, L["acc"], 0.55)
    rrect(x0, y0, pw, ph, 20, DARK, 0.84)
    title = "DICTATOR'S DASH"
    sc = 0.42
    wd = stroke_w(title, sc)
    stroke(cx - wd / 2 + 3, top - 91, title, sc, (0, 0, 0), 5, 0.6)
    stroke(cx - wd / 2, top - 88, title, sc, GOLD, 3)
    text_m(cx, top - 114, "3D EDITION   |   ENDLESS RUNNER", H12, DIM, False)
    rect(x0 + 40, top - 128, pw - 80, 1, (1, 1, 1), 0.12)
    # difficulty
    text_m(cx, top - 152, "SELECT DIFFICULTY", H12, DIM, False)
    bw, gap = 230, 20
    bx0 = cx - (3 * bw + 2 * gap) / 2
    for i, dd in enumerate(DIFFS):
        button(bx0 + i * (bw + gap), top - 212, bw, 46, ("diff", i), dd["name"].upper(), dd["col"],
               i == g.di, f"Best {g.his[i]}")
    text_m(cx, top - 232, g.dd["desc"], H12, g.dd["col"], False)
    # location
    text_m(cx, top - 262, "SELECT LOCATION", H12, DIM, False)
    cw, cg = 176, 14
    cx0 = cx - (4 * cw + 3 * cg) / 2
    for i, Lc in enumerate(LOCS):
        bx, by = cx0 + i * (cw + cg), top - 382
        sel = i == g.li
        hov = bx <= g.mx <= bx + cw and by <= WIN[1] - g.my <= by + 104
        UI.append((bx, by, cw, 104, ("loc", i)))
        rrect(bx - 2, by - 2, cw + 4, 108, 13, Lc["acc"] if sel else (0.35, 0.36, 0.42),
              1.0 if sel else (0.85 if hov else 0.5))
        rrect(bx, by, cw, 104, 11, (0.08, 0.09, 0.13), 0.97)
        glBegin(GL_QUADS)
        glColor3f(*Lc["pv"]); glVertex2f(bx + 6, by + 98); glVertex2f(bx + cw - 6, by + 98)
        glColor3f(*Lc["ground"]); glVertex2f(bx + cw - 6, by + 56); glVertex2f(bx + 6, by + 56)
        glEnd()
        text_m(bx + cw / 2, by + 34, Lc["name"], H18, (1, 1, 1) if (sel or hov) else (0.78, 0.8, 0.86))
        text_m(bx + cw / 2, by + 14, Lc["tag"], H10, Lc["acc"] if sel else DIM, False)
    text_m(cx, top - 402, L["desc"], H12, L["acc"], False)
    button(cx - 150, top - 470, 300, 46, ("start",), "START RUN", (0.4, 1.0, 0.55), True, None)
    text_m(cx, top - 500, "Up/Down: difficulty   Left/Right: location   Enter: start   V view   N time   M weather",
           H10, DIM, False)


def panel_screen(w, h, title, tcol, pw, ph, lines, btns):
    rect(0, 0, w, h, (0, 0, 0), 0.5)
    cx, cy = w / 2, h / 2
    x0, y0 = cx - pw / 2, cy - ph / 2
    rrect(x0 - 3, y0 - 3, pw + 6, ph + 6, 23, tcol, 0.5)
    rrect(x0, y0, pw, ph, 20, DARK, 0.9)
    wd = stroke_w(title, 0.36)
    stroke(cx - wd / 2 + 2, y0 + ph - 78, title, 0.36, (0, 0, 0), 5, 0.6)
    stroke(cx - wd / 2, y0 + ph - 75, title, 0.36, tcol, 3)
    y = y0 + ph - 118
    for s, font, c in lines:
        text_m(cx, y, s, font, c)
        y -= 28
    n = len(btns)
    bw = 200
    bx = cx - (n * bw + (n - 1) * 20) / 2
    for i, (lab, act, col) in enumerate(btns):
        button(bx + i * (bw + 20), y0 + 26, bw, 44, act, lab, col, i == 0)


def draw_hud():
    w, h = WIN
    UI.clear()
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, w, 0, h)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glDisable(GL_DEPTH_TEST); glDisable(GL_LIGHTING); glDisable(GL_FOG); glEnable(GL_BLEND)

    if g.bolt > 0:
        rect(0, 0, w, h, (1, 1, 1), min(.7, g.bolt * 4))
    if g.weather == 3:
        rect(0, 0, w, h, (0.8, 0.6, 0.3), 0.18 * g.wk)
    if g.flash > 0:
        rect(0, 0, w, h, (1, 0, 0), g.flash)
    vignette(0.42)
    if g.state == "play" and g.speed > 22:
        speed_lines()
    if g.state != "menu":
        hud_play(w, h)

    if g.state == "menu":
        menu_screen(w, h)
    elif g.state == "paused":
        panel_screen(w, h, "PAUSED", (0.6, 0.8, 1.0), 460, 220, [("Take a breath. The desert can wait.", H12, DIM)],
                     [("RESUME", ("resume",), (0.4, 1.0, 0.55)), ("MENU", ("menu",), (1.0, 0.75, 0.3))])
    elif g.state == "over":
        nb = int(g.score) >= g.hi and g.hi > 0
        lines = [(f"Score {int(g.score)}      Coins {g.coins}      Guards downed {g.kills}", H18, (1, 1, 1)),
                 (("NEW BEST!  " if nb else "") + f"Best ({g.dd['name']}): {g.hi}", H18, GOLD),
                 (f"{g.dd['name']}  |  {g.loc['name']}", H12, DIM)]
        panel_screen(w, h, "GAME OVER", (1.0, 0.3, 0.25), 600, 300, lines,
                     [("RESTART [R]", ("restart",), (0.4, 1.0, 0.55)), ("MENU [B]", ("menu",), (1.0, 0.75, 0.3))])

    wl_ = WM[g.wmode] + (f" ({WN[g.weather]})" if g.wmode == 0 else "")
    s_ = f"[N] Time: {TODN[g.tod]}    [M] Weather: {wl_}    [V] View: {VN[g.view]}    [B] Menu"
    text(w - tw_(s_, H10) - 14, 6, s_, H10, (0.85, 0.88, 0.95))
    glDisable(GL_BLEND); glEnable(GL_DEPTH_TEST); glEnable(GL_LIGHTING); glEnable(GL_FOG)
    glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW); glPopMatrix()


# ------------------------------------------------------------------ callbacks
def display():
    draw_world()
    draw_hud()
    glutSwapBuffers()


def reshape(w, h):
    WIN[0], WIN[1] = w, max(1, h)
    glViewport(0, 0, w, WIN[1])
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(60, w / WIN[1], 0.5, 260)
    glMatrixMode(GL_MODELVIEW)


last = [0.0]
cursor = [None]


def tick(_):
    now = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    dt = min(now - last[0], 0.033)
    last[0] = now
    g.update(dt)
    want = GLUT_CURSOR_NONE if g.state == "play" else GLUT_CURSOR_LEFT_ARROW   # custom reticle while playing
    if want != cursor[0]:
        cursor[0] = want
        glutSetCursor(want)
    glutPostRedisplay()
    glutTimerFunc(16, tick, 0)


def keyboard(key, x, y):
    k = key.lower()
    if k == b"\x1b":
        sys.exit(0)
    if k == b"v":
        g.view = (g.view + 1) % 3
        return
    if k == b"n":
        g.cycle_tod(); return
    if k == b"m":
        g.cycle_weather(); return
    if g.state == "menu":
        if k in (b"\r", b" "):
            g.reset()
        elif k in (b"1", b"2", b"3"):
            g.set_diff(int(k) - 1)
        elif k == b"a":
            g.set_loc(g.li - 1)
        elif k == b"d":
            g.set_loc(g.li + 1)
        return
    if k == b"b":
        g.to_menu()
    elif k == b"r":
        g.reset()
    elif k == b"p":
        g.pause()
    elif k == b"a": g.move(-1)
    elif k == b"d": g.move(1)
    elif k in (b"w", b" "): g.jump()
    elif k == b"s": g.duck()
    elif k == b"f": g.shoot(straight=True)
    elif k == b"g": g.fire_on = True
    elif k == b"q": g.speed_adj(-3)
    elif k == b"e": g.speed_adj(3)


def keyboard_up(key, x, y):
    if key.lower() == b"g":
        g.fire_on = False


def special(key, x, y):
    if g.state == "menu":
        if key == GLUT_KEY_LEFT: g.set_loc(g.li - 1)
        elif key == GLUT_KEY_RIGHT: g.set_loc(g.li + 1)
        elif key == GLUT_KEY_UP: g.set_diff(g.di - 1)
        elif key == GLUT_KEY_DOWN: g.set_diff(g.di + 1)
        return
    if key == GLUT_KEY_LEFT: g.move(-1)
    elif key == GLUT_KEY_RIGHT: g.move(1)
    elif key == GLUT_KEY_UP: g.jump()
    elif key == GLUT_KEY_DOWN: g.duck()


def motion(x, y):
    g.mx, g.my = x, y


def mouse(button, state, x, y):
    g.mx, g.my = x, y
    if button == GLUT_RIGHT_BUTTON:
        g.fire_on = state == GLUT_DOWN and g.state == "play"
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        if g.state != "play":                                       # menu / pause / game-over buttons
            for bx, by, bw, bh, act in UI:
                if bx <= x <= bx + bw and by <= WIN[1] - y <= by + bh:
                    g.ui(act)
                    return
            return
        g.shoot()


def init_gl():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING); glEnable(GL_LIGHT0); glEnable(GL_NORMALIZE)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.42, 0.36, 0.4, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.85, 0.65, 1))
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    glFogfv(GL_FOG_COLOR, (*SKY_FOG, 1))
    glFogf(GL_FOG_START, 25); glFogf(GL_FOG_END, 105)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_POINT_SMOOTH); glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)


SKY_FOG = (0.97, 0.60, 0.33)


def main():
    glutInit(sys.argv)
    mode = GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH
    if "--msaa" in sys.argv:                       # optional anti-aliasing (not every GPU/driver allows it)
        mode |= GLUT_MULTISAMPLE
    glutInitDisplayMode(mode)
    glutInitWindowSize(*WIN)
    glutInitWindowPosition(60, 40)
    glutCreateWindow(b"Dictator's Dash 3D")
    init_gl()
    if "--msaa" in sys.argv:
        glEnable(GL_MULTISAMPLE)
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutPassiveMotionFunc(motion)
    glutTimerFunc(0, tick, 0)
    glutMainLoop()


if __name__ == "__main__":
    main()
    