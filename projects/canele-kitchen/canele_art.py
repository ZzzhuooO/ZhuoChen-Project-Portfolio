"""Canvas illustrations: glass kitchenware, copper molds, and the original cutaway."""

import math
from contextlib import contextmanager

from canele_model import MOLD_GRAMS

BG = "#171715"
PANEL = "#22221f"
TEXT = "#f1e9dc"
MUTED = "#aaa398"
ACCENT = "#edb76a"
GLASS = "#b7d7dd"


def mix_color(start, end, amount):
    t = max(0.0, min(1.0, amount))
    a = tuple(int(start[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(end[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def ease(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def pour_pose(progress):
    """Tilt, empty while tilted, then return upright without a liquid stream."""
    tilt = ease(progress / .24) if progress < .24 else 1 - ease((progress - .72) / .28)
    return tilt, ease((progress - .24) / .48)


class TiltedCanvas:
    """Rotate the glass outline and its contents together about one pivot."""

    def __init__(self, canvas, x, y, angle):
        self.canvas = canvas
        self.x, self.y = x, y
        self.angle = angle
        radians = math.radians(angle)
        self.cos, self.sin = math.cos(radians), math.sin(radians)

    def points(self, coords):
        if len(coords) == 1:
            coords = coords[0]
        result = []
        for x, y in zip(coords[::2], coords[1::2]):
            dx, dy = x - self.x, y - self.y
            result.extend((self.x + dx*self.cos - dy*self.sin,
                           self.y + dx*self.sin + dy*self.cos))
        return result

    def create_line(self, *coords, **options):
        return self.canvas.create_line(self.points(coords), **options)

    def create_polygon(self, *coords, **options):
        return self.canvas.create_polygon(self.points(coords), **options)

    def ellipse_points(self, x1, y1, x2, y2, start=0, extent=360):
        count = max(12, round(abs(extent) / 7.5))
        points = []
        for i in range(count + 1):
            a = math.radians(start + extent*i/count)
            points.extend(((x1+x2)/2 + (x2-x1)/2*math.cos(a),
                           (y1+y2)/2 - (y2-y1)/2*math.sin(a)))
        return points

    def create_oval(self, x1, y1, x2, y2, **options):
        options.setdefault("fill", "")
        return self.create_polygon(self.ellipse_points(x1, y1, x2, y2), **options)

    def create_arc(self, x1, y1, x2, y2, start=0, extent=90, style="arc", **options):
        # Glass reflections use open arcs, so keep their strokes open when tilted.
        options["fill"] = options.pop("outline", GLASS)
        return self.create_line(self.ellipse_points(x1, y1, x2, y2, start, extent), **options)

    def create_rectangle(self, x1, y1, x2, y2, **options):
        return self.create_polygon(x1, y1, x2, y1, x2, y2, x1, y2, **options)

    def create_text(self, x, y, **options):
        return self.canvas.create_text(*self.points((x, y)), angle=-self.angle, **options)


class Painter:
    def __init__(self, canvas):
        self.c = canvas
        self.w = max(1, canvas.winfo_width())
        self.h = max(1, canvas.winfo_height())
        self.scale = min(self.w / 960, self.h / 380)
        self.c.delete("all")

    def text(self, x, y, text, size=11, color=TEXT, anchor="center", bold=False):
        self.c.create_text(x, y, text=text, fill=color, anchor=anchor,
                           font=("Microsoft YaHei UI", max(8, round(size * self.scale)),
                                 "bold" if bold else "normal"))

    def finish(self):
        self.c.scale("all", 0, 0, self.scale, self.scale)
        self.c.move("all", (self.w - 960 * self.scale) / 2,
                    (self.h - 380 * self.scale) / 2)

    @contextmanager
    def tilted(self, x, y, angle):
        canvas = self.c
        if angle:
            self.c = TiltedCanvas(canvas, x, y, angle)
        try:
            yield
        finally:
            self.c = canvas

    def glass_bowl(self, x, y, width=225, height=135, fill=0.65, liquid="#dfcd9f", film=False):
        c = self.c
        r = width / 2
        c.create_oval(x-r-6, y+height-6, x+r+6, y+height+14, fill="#191e1c", outline="")
        shape = [x-r, y+8, x-r*.91, y+height*.62, x-r*.63, y+height,
                 x+r*.63, y+height, x+r*.91, y+height*.62, x+r, y+8]
        c.create_polygon(shape, smooth=True, fill="#2c3939", outline=GLASS, width=2)
        if fill > 0:
            level = min(y+height-7, y + height * (1 - min(fill, .92)))
            lr = r * (.68 + .25 * fill)
            shoulder_y = max(level, y+height*.72)
            shoulder_r = r*.83 if level < y+height*.72 else lr
            c.create_polygon(x-lr, level, x-shoulder_r, shoulder_y, x-r*.57, y+height-6,
                             x+r*.57, y+height-6, x+shoulder_r, shoulder_y, x+lr, level,
                             smooth=True, fill=liquid, outline="")
            c.create_oval(x-lr, level-8, x+lr, level+8,
                          fill=mix_color(liquid, "#fff4dd", .18), outline="")
        c.create_oval(x-r, y-8, x+r, y+20, outline=GLASS, width=2)
        c.create_arc(x-r+7, y+2, x+r-7, y+height+2, start=188, extent=43,
                     style="arc", outline="#e6f5f4", width=3)
        c.create_line(x-r*.75, y+29, x-r*.66, y+height*.63, fill="#89afb5", width=3)
        c.create_line(x+r*.77, y+28, x+r*.66, y+height*.67, fill="#6f969f", width=2)
        if film:
            c.create_oval(x-r-3, y-10, x+r+3, y+18, fill="#91b5bb", stipple="gray25",
                          outline="#daedef")
            for i in range(5):
                c.create_line(x-r+15+i*35, y-3, x-r+37+i*35, y+12, fill="#99bdc3")

    def glass_jug(self, x, y, width=125, height=155, fill=.65, liquid="#e5d3ac"):
        c = self.c
        r = width / 2
        c.create_oval(x+r-6, y+29, x+r+38, y+height-26,
                      outline=GLASS, width=4)
        c.create_polygon(x-r-11, y, x+r, y, x+r-6, y+height,
                          x-r+7, y+height, x-r, y+16,
                          fill="#2a3839", outline=GLASS, width=2)
        if fill > 0:
            level = y + height * (1-min(.95, fill))
            c.create_polygon(x-r+5, level, x+r-5, level, x+r-12, y+height-6,
                              x-r+13, y+height-6, fill=liquid, outline="")
            c.create_oval(x-r+5, level-5, x+r-5, level+5,
                          fill=mix_color(liquid, "#fff8e8", .2), outline="")
        c.create_line(x-r+16, y+24, x-r+22, y+height-18, fill="#e3f4f3", width=3)
        for i in range(1, 5):
            yy = y+height-i*height/6
            c.create_line(x+r-27, yy, x+r-10, yy, fill="#83a6b0")
        c.create_line(x-r-11, y, x+r, y, fill="#f0fbfa", width=2)

    def glass_spoon(self, x, y, angle=0):
        dx, dy = math.sin(angle)*34, math.cos(angle)*72
        self.c.create_line(x, y, x+dx, y-dy, fill="#85a9b3", width=9)
        self.c.create_line(x-2, y, x+dx-2, y-dy, fill="#e3f4f4", width=2)
        self.c.create_oval(x-12, y-3, x+12, y+27,
                           fill="#94b3b6", stipple="gray50", outline=GLASS)

    def rum_bottle(self, x, y, fill=1):
        c = self.c
        c.create_polygon(x-14, y+42, x-14, y+9, x+14, y+9, x+14, y+42,
                          x+41, y+63, x+41, y+199, x-41, y+199, x-41, y+63,
                          fill="#263638", outline=GLASS, width=2)
        if fill > 0:
            c.create_rectangle(x-36, y+192-89*fill, x+36, y+192,
                                fill="#80603f", outline="")
        c.create_line(x-29, y+68, x-29, y+182, fill="#c4dde0", width=3)
        c.create_rectangle(x-17, y, x+17, y+13, fill="#334b4d", outline=GLASS)
        self.text(x, y+142, "RUM", bold=True)

    def copper_mold(self, x, y, width=105, height=105, fill=0):
        c = self.c
        left, right = x-width/2, x+width/2
        c.create_oval(left-5, y+height-4, right+5, y+height+12, fill="#191915", outline="")
        c.create_polygon(left, y, right, y, right-width*.1, y+height,
                          left+width*.1, y+height, fill="#995837", outline="#edba84", width=2)
        colors = ["#80452d", "#ad6b43", "#dc9c67", "#ecbd85", "#c28050", "#8c4c31"]
        for i, color in enumerate(colors):
            a = i/6
            b = (i+1)/6
            c.create_polygon(left+width*a, y+5, left+width*b, y+5,
                              left+width*.1+width*.8*b, y+height-2,
                              left+width*.1+width*.8*a, y+height-2,
                              fill=color, outline="")
        c.create_oval(left, y-12, right, y+14, fill="#6a6052", outline="#f0c594", width=3)
        c.create_oval(left+7, y-6, right-7, y+8,
                      fill="#302d29", outline="#afa08a")
        if fill > 0:
            # A recessed surface leaves a visible inner wall above the batter.
            level = max(0, min(1, fill))
            inset = 11 + (1-level)*9
            top = y + 6 - 12*level
            c.create_oval(left+inset, top, right-inset, y+7,
                          fill="#e6ce99", outline="#c4a76f")
        c.create_line(left+width*.3, y+22, left+width*.34, y+height-15,
                       fill="#f8d8ae", width=2)

    def canele(self, x, y, dose, section=False, color_dose=None, uniform_caramel=False):
        c = self.c
        openness = max(.12, min(1, dose/47)) * max(.4, 1-max(0, dose-65)/80)
        shell = mix_color("#bc8653", "#321c19", (dose if color_dose is None else color_dose)/83)
        if not section:
            points = [x-34, y-118, x+34, y-118, x+43, y-96, x+51, y-73,
                      x+60, y+51, x+70, y+94, x+62, y+118, x-62, y+118,
                      x-70, y+94, x-60, y+51, x-51, y-73, x-43, y-96]
            c.create_polygon(points, smooth=True, fill=shell, outline="#f0c180", width=2)
            for offset in (-42, -21, 0, 21, 42):
                c.create_line(x+offset*.72, y-86, x+offset, y+101,
                               fill=mix_color(shell, "#f0c180", .34), width=2)
            c.create_oval(x-49, y+105, x+49, y+121,
                          fill=shell if uniform_caramel else "#241917", outline="")
            return
        rx, ry = 81, 125
        inset = 8 + min(13, max(0, dose-52)*.32)
        c.create_oval(x-rx, y-ry, x+rx, y+ry, fill=shell, outline="#f0c180", width=2)
        c.create_oval(x-rx+inset, y-ry+inset, x+rx-inset, y+ry-inset,
                      fill=shell if uniform_caramel else "#efd39d", outline="")
        # Fixed positions prevent jitter when the temperature control moves.
        for i in range(21):
            angle = i*2.399963
            radius = .78*math.sqrt((i+.5)/21)
            xx = x+math.cos(angle)*64*radius
            yy = y+math.sin(angle)*99*radius
            rr = (2+openness*6.5)*(.7+(i*7 % 5)*.1)
            c.create_oval(xx-rr, yy-rr*1.2, xx+rr, yy+rr*1.2,
                          fill=mix_color(shell, "#321c19", .35) if uniform_caramel else "#9d7048",
                          outline=mix_color(shell, "#f0c180", .25) if uniform_caramel else "#e6c58e")


def draw_scene(canvas, state, progress=0, busy=False):
    p = Painter(canvas)
    c = p.c
    step = state.step
    c.create_line(40, 326, 920, 326, fill="#3b3c34", width=2)
    if step == 0:
        phase = state.phases[0]
        pods_added = 1 if phase > 0 else ease(progress / .38) if busy else 0
        p.text(260, 33, "玻璃奶锅", color=GLASS)
        p.glass_bowl(260, 112, 265, 157, .7, "#eadfc7")
        c.create_line(391, 136, 472, 119, fill=GLASS, width=12)
        c.create_line(393, 132, 468, 115, fill="#ecf8f7", width=2)
        if phase == 0 and busy and pods_added == 1:
            c.create_oval(180, 291, 340, 308, outline=ACCENT, width=3)
        if pods_added > .8:
            for i in range(15):
                xx = 174+(i*41 % 167)
                yy = 184+(i*29 % 63)
                c.create_oval(xx, yy, xx+2, yy+2, fill="#846843", outline="")
        if busy and pods_added == 1:
            for i in range(3):
                xx = 207+i*44
                off = (progress*100+i*13) % 35
                c.create_line(xx, 92-off, xx-7, 78-off, xx+4, 64-off,
                               smooth=True, fill="#829899", width=2)
        p.text(650, 95, "两根香草荚", size=17, bold=True)
        p.text(650, 141, "牛奶 276g  +  黄油 28g", size=14)
        for offset in (-14, 14):
            start = (592, 190+offset, 646, 213+offset, 716, 220+offset)
            end = (201, 176+offset*.6, 246, 189+offset*.6, 311, 182+offset*.6)
            points = [a+(b-a)*pods_added for a, b in zip(start, end)]
            for i in (1, 3, 5):
                points[i] -= 65*math.sin(math.pi*pods_added)
            c.create_line(points, smooth=True, fill="#5b3b27", width=8)
            highlight = [v-2 if i % 2 else v for i, v in enumerate(points)]
            c.create_line(highlight, smooth=True, fill="#b68b56", width=1)
        p.text(650, 276, "煮沸 10 秒 → 关火浸香 15 分钟", color=ACCENT)
    elif step == 1:
        phase = state.phases[1]
        egg_pose, egg_amount = pour_pose(min(1, progress*2)) if phase == 0 and busy else (0, int(phase > 0))
        sugar_pose, sugar_amount = pour_pose(max(0, progress*2-1)) if phase == 0 and busy else (0, int(phase > 0))
        flour_pose, flour_amount = pour_pose(min(1, progress/.58)) if phase == 2 and busy else (0, int(phase > 2))
        bowl_fill = .4*(78*egg_amount + 138*sugar_amount)/216 + .25*flour_amount
        p.text(290, 35, "玻璃搅拌碗与玻璃搅拌匙", color=GLASS)
        p.glass_bowl(290, 153, 280, 144, bowl_fill, mix_color("#dfb868", "#e4c990", flour_amount))
        stirring = busy and (phase == 1 or phase == 2 and progress > .58)
        if phase > 0:
            spoon_y = 153+144*(1-bowl_fill)+14
            p.glass_spoon(300+math.sin(progress*24)*20 if stirring else 300, spoon_y,
                           math.sin(progress*24)*.6 if stirring else -.4)
        p.text(700, 60, "先打散，再拌入面粉", size=16, bold=True)
        for xx, label, color, pose, amount in [
                (585, "全蛋 56g + 蛋黄 22g", "#d6a552", egg_pose, egg_amount),
                (745, "糖 138g", "#f4ead4", sugar_pose, sugar_amount)]:
            x, y = xx+(417-xx)*pose, 123-38*pose
            with p.tilted(x, y+50, -38*pose):
                p.glass_bowl(x, y, 105, 70, .65*(1-amount), color)
            p.text(xx, 220, label, size=10)
        x, y = 675+(417-675)*flour_pose, 260+(93-260)*flour_pose
        with p.tilted(x, y+40, -38*flour_pose):
            p.glass_bowl(x, y, 112, 53, .7*(1-flour_amount), "#eadfc9")
        p.text(675, 347, "低筋面粉 56g · 过筛加入", color=ACCENT)
    elif step == 2:
        phase = state.phases[2]
        milk_pose, milk_amount = pour_pose(progress) if phase == 0 and busy else (0, int(phase > 0))
        rum_pose, rum_amount = pour_pose(progress) if phase == 2 and busy else (0, int(phase > 2))
        p.text(280, 34, "微温香草牛奶 → 蛋糊", color=GLASS)
        p.glass_bowl(300, 189, 235, 118, .38+.37*milk_amount+.03*rum_amount, "#e6ce99")
        p.glass_spoon(315, 229, -.5)
        x, y = 540-75*milk_pose, 85
        with p.tilted(x, y+105, -32*milk_pose):
            p.glass_jug(x, y, 115, 145, .7*(1-milk_amount))
        p.text(540, 271, "香草牛奶", size=10, color=MUTED)
        x, y = 780-285*rum_pose, 83-15*rum_pose
        with p.tilted(x, y+147, -32*rum_pose):
            p.rum_bottle(x, y, 1-rum_amount)
        p.text(745, 328, "晾凉后加入 22g 朗姆酒", color=ACCENT)
    elif step == 3:
        p.text(480, 38, "玻璃储存碗 · 保鲜膜贴面", color=GLASS)
        p.glass_bowl(365, 126, 310, 168, .78, "#ddc48d", film=True)
        elapsed = 48 if 3 in state.completed else progress*48
        p.text(737, 151, f"{elapsed:04.1f}", size=39, color="#b7d7dd", bold=True)
        p.text(737, 201, "小时 / 48 小时", size=13, color=MUTED)
        for xx, yy in ((130, 92), (590, 72), (564, 261)):
            for a in (0, math.pi/3, 2*math.pi/3):
                c.create_line(xx-10*math.cos(a), yy-10*math.sin(a),
                               xx+10*math.cos(a), yy+10*math.sin(a), fill="#638a95")
    elif step == 4:
        filling = busy and state.phases[4] == 1 and state.filled < 6
        pose, amount = pour_pose(progress) if filling else (0, 0)
        remaining = state.remaining_grams - MOLD_GRAMS*amount
        p.text(240, 28, "玻璃量杯", color=GLASS)
        with p.tilted(240, 170, -30*pose):
            p.glass_jug(240, 65, 115, 136, remaining/750)
        p.text(660, 88, "铜制可露丽模具", size=18, color="#edba84", bold=True)
        p.text(660, 133, "每模 80g × 6 个", size=15)
        for i in range(6):
            xx = 130+i*140
            fill = .7 if i < state.filled else .7*amount if i == state.filled else 0
            p.copper_mold(xx, 238, 98, 80, fill)
            p.text(xx, 348, "80g" if i < state.filled else f"第 {i+1} 模",
                   size=10, color=ACCENT if i < state.filled else MUTED)
    else:
        # Keep version one's dark stage, exterior, cutaway, and temperature control.
        p.text(218, 27, "外观", color=MUTED, bold=True)
        p.text(565, 27, "切面示意", color=MUTED, bold=True)
        p.canele(218, 187, state.heat_dose,
                  color_dose=state.color_dose, uniform_caramel=state.uniform_caramel)
        p.canele(565, 187, state.heat_dose, section=True,
                  color_dose=state.color_dose, uniform_caramel=state.uniform_caramel)
        c.create_line(750, 48, 750, 309, fill="#464138")
        cooling = state.oven_phase in ("cooling", "done")
        p.text(844, 91, f"{state.cooling_minutes:.0f} 分钟" if cooling else f"{state.oven_actual:.0f}°C",
               size=24, color=GLASS if cooling else ACCENT, bold=True)
        p.text(844, 124, "冷却 / 45 分钟" if cooling else "炉内示意温度", size=10, color=MUTED)
        p.text(844, 178, f"{state.bake_minutes:.0f} 分钟", size=18)
        p.text(844, 213, state.color_name, size=12, color=ACCENT)
        if state.oven_phase in ("cooling", "done"):
            p.text(844, 274, f"冷却 {state.cooling_minutes:.0f} / 45 分钟", size=10, color=GLASS)
        if state.bake_caption and state.oven_phase in ("check", "cooling", "done"):
            p.text(480, 351, state.bake_caption, size=18, color=ACCENT, bold=True)
    p.finish()
