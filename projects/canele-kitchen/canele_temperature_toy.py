"""Six-step canele kitchen. Run with Python 3; no third-party packages needed."""

import argparse
import time
import tkinter as tk
from tkinter import ttk

from canele_art import ACCENT, BG, MUTED, PANEL, TEXT, draw_scene
from canele_model import MOLD_COUNT, RECIPE, STEPS, KitchenState


INTRO = (
    "牛奶 276g、黄油 28g、香草荚 2 根：煮沸 10 秒，关火浸泡 15 分钟。",
    "全蛋 56g、蛋黄 22g、糖 138g 迅速打散，再拌入过筛低筋面粉 56g。",
    "香草牛奶重新加热至微温，冲入蛋糊拌匀；放凉后再加入朗姆酒 22g。",
    "玻璃碗内的面糊贴面覆盖保鲜膜，冷藏静置 48 小时。",
    "面糊先回拌、过筛，再装入 6 个铜模，每个 80g。",
    "预热后以 200–220°C 起烤，约 50 分钟检查；按颜色降温或追加 10 分钟，最后冷却 45 分钟。",
)


class CaneleToy:
    def __init__(self, root):
        self.root = root
        self.state = KitchenState()
        self.busy = False
        self.progress = 0.0
        self._animation_id = None
        self._resize_id = None
        self._closed = False
        root.title("可露丽小厨房 · 六步制作")
        root.configure(bg=BG)
        root.geometry("1080x830")
        root.minsize(940, 740)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.build()
        self.render()

    def button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command,
                         bg=ACCENT if primary else "#30312b",
                         fg=BG if primary else TEXT,
                         activebackground="#f5c989" if primary else "#41443b",
                         activeforeground=BG if primary else TEXT,
                         disabledforeground="#716b60", relief="flat", bd=0,
                         padx=15, pady=10, cursor="hand2", takefocus=True,
                         font=("Microsoft YaHei UI", 10, "bold" if primary else "normal"))

    def build(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Kitchen.Horizontal.TScale", background=BG,
                        troughcolor="#51493c", sliderthickness=18)
        style.configure("Kitchen.Horizontal.TProgressbar", troughcolor="#373b34",
                        background=ACCENT, borderwidth=0, lightcolor=ACCENT,
                        darkcolor=ACCENT)

        outer = tk.Frame(self.root, bg=BG, padx=24, pady=20)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x")
        tk.Label(header, text="可露丽 · 小厨房", bg=BG, fg=TEXT,
                 font=("Microsoft YaHei UI", 23, "bold")).pack(side="left")
        self.button(header, "查看配方", self.show_recipe).pack(side="right")
        tk.Label(outer, text="六步慢慢做，等待加速演示。目标：薄脆外壳，内部蜂窝明显。",
                 bg=BG, fg=MUTED, font=("Microsoft YaHei UI", 10),
                 anchor="w").pack(fill="x", pady=(3, 16))

        nav = tk.Frame(outer, bg=BG)
        nav.pack(fill="x", pady=(0, 14))
        self.step_buttons = []
        for i, title in enumerate(STEPS):
            nav.columnconfigure(i, weight=1, uniform="steps")
            btn = tk.Button(nav, text=f"{i+1:02d}  {title}", command=lambda j=i: self.visit(j),
                            relief="flat", bd=0, pady=11, cursor="hand2",
                            font=("Microsoft YaHei UI", 10), disabledforeground="#716b60")
            btn.grid(row=0, column=i, sticky="ew", padx=(0, 5 if i < 5 else 0))
            self.step_buttons.append(btn)

        self.heading = tk.Label(outer, bg=BG, fg=TEXT, anchor="w",
                                font=("Microsoft YaHei UI", 14, "bold"))
        self.heading.pack(fill="x")
        self.description = tk.Label(outer, bg=BG, fg=MUTED, anchor="w", justify="left",
                                    wraplength=980, font=("Microsoft YaHei UI", 10))
        self.description.pack(fill="x", pady=(5, 12))

        # A small requested height lets pack reserve room for the oven controls;
        # expand fills all remaining space on larger windows.
        self.canvas = tk.Canvas(outer, height=200, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.schedule_draw)

        status_frame = tk.Frame(outer, bg=PANEL, padx=16, pady=10)
        status_frame.pack(fill="x")
        self.status = tk.Label(status_frame, bg=PANEL, fg=TEXT, anchor="w",
                               font=("Microsoft YaHei UI", 11, "bold"))
        self.status.pack(fill="x")
        self.detail = tk.Label(status_frame, bg=PANEL, fg=MUTED, anchor="w",
                               font=("Microsoft YaHei UI", 9))
        self.detail.pack(fill="x", pady=(5, 8))
        self.bar = ttk.Progressbar(status_frame, maximum=1,
                                   style="Kitchen.Horizontal.TProgressbar")
        self.bar.pack(fill="x")

        self.temp_frame = tk.Frame(outer, bg=BG)
        self.temp_label = tk.Label(self.temp_frame, bg=BG, fg=ACCENT, width=11,
                                   anchor="w", font=("Microsoft YaHei UI", 17, "bold"))
        self.temp_label.pack(side="left")
        self.scale = ttk.Scale(self.temp_frame, from_=160, to=240,
                               style="Kitchen.Horizontal.TScale", orient="horizontal",
                               command=self.on_temperature)
        self.scale.pack(side="left", fill="x", expand=True, padx=12)
        self.lower_button = self.button(self.temp_frame, "降温 10°C", self.lower_temperature)
        self.lower_button.pack(side="right")

        self.actions_frame = tk.Frame(outer, bg=BG)
        self.actions_frame.pack(fill="x", pady=(14, 10))
        self.action_button = self.button(self.actions_frame, "", self.act, primary=True)
        self.action_button.pack(side="left")
        self.extra_button = self.button(self.actions_frame, "再烤 10 分钟", lambda: self.bake(10))
        self.next_button = self.button(self.actions_frame, "下一步 →", self.next_step)
        self.next_button.pack(side="right")
        self.back_button = self.button(self.actions_frame, "← 上一步", self.previous_step)
        self.back_button.pack(side="right", padx=8)

        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill="x")
        tk.Label(footer, text="状态变化仅作示意 · 配方按本次讨论记录 · 等待约用几秒演示完成",
                 bg=BG, fg="#827c72", font=("Microsoft YaHei UI", 9)).pack(side="left")
        tk.Button(footer, text="重新制作", command=self.reset, bg=BG, fg=MUTED,
                  activebackground=BG, activeforeground=TEXT, relief="flat", bd=0,
                  cursor="hand2", font=("Microsoft YaHei UI", 9)).pack(side="right")
        # Set only after every callback target exists.
        self.scale.set(self.state.oven_setting)

    def show_recipe(self):
        win = tk.Toplevel(self.root)
        win.title("本次配方 · 六个铜模")
        win.configure(bg=PANEL)
        win.resizable(False, False)
        win.transient(self.root)
        body = tk.Frame(win, bg=PANEL, padx=30, pady=24)
        body.pack()
        tk.Label(body, text="本次配方", bg=PANEL, fg=TEXT,
                 font=("Microsoft YaHei UI", 17, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 12))
        items = [("香草荚", "2 根")] + [(name, f"{grams} g") for name, grams in RECIPE.items()]
        for row, (name, amount) in enumerate(items, 1):
            tk.Label(body, text=name, bg=PANEL, fg=TEXT,
                     font=("Microsoft YaHei UI", 11)).grid(row=row, column=0, sticky="w", padx=(0, 70), pady=4)
            tk.Label(body, text=amount, bg=PANEL, fg=ACCENT,
                     font=("Microsoft YaHei UI", 11)).grid(row=row, column=1, sticky="e")
        tk.Label(body, text="面糊理论总量 598g（不计香草荚）\n六模 × 80g = 480g，理论余量 118g\n以上未扣除加热、过筛和挂壁损耗。",
                 bg=PANEL, fg=MUTED, justify="left",
                 font=("Microsoft YaHei UI", 10)).grid(row=9, column=0, columnspan=2, pady=(16, 0))

    def schedule_draw(self, event=None):
        if event is not None:
            self.description.config(wraplength=max(400, event.width))
        if self._resize_id is not None:
            self.root.after_cancel(self._resize_id)

        def draw_resized():
            self._resize_id = None
            self.redraw()

        self._resize_id = self.root.after(30, draw_resized)

    def redraw(self):
        draw_scene(self.canvas, self.state, self.progress, self.busy)

    def visit(self, step):
        if not self.busy and self.state.can_visit(step):
            self.state.step = step
            self.progress = 0
            self.render()

    def next_step(self):
        self.visit(self.state.step+1)

    def previous_step(self):
        self.visit(self.state.step-1)

    def on_temperature(self, value):
        self.state.oven_setting = round(float(value))
        self.temp_label.config(text=f"设定 {self.state.oven_setting:.0f}°C")
        if hasattr(self, "status"):
            self.render()

    def lower_temperature(self):
        self.scale.set(max(160, self.state.oven_setting-10))

    def status_copy(self):
        s = self.state
        step, phase = s.step, s.phases[s.step]
        completed = step in s.completed
        if step == 0:
            titles = ("加热香草牛奶", "关火，让香草继续浸香", "香草牛奶准备好了")
            detail = "沸腾后保持 10 秒" if phase == 0 else "离火浸香 15 分钟"
            return titles[min(phase, 2)], detail
        if step == 1:
            titles = ("加入全蛋、蛋黄和糖", "迅速打散，不需要打发", "加入过筛面粉，拌至均匀", "蛋糊准备好了")
            return titles[min(phase, 3)], "全蛋 56g · 蛋黄 22g · 糖 138g · 低筋面粉 56g"
        if step == 2:
            titles = ("微温牛奶冲入蛋糊", "等待面糊放凉", "放凉后加入朗姆酒", "面糊合并完成")
            return titles[min(phase, 3)], "香草牛奶重新加热至微温；朗姆酒固定 22g"
        if step == 3:
            hours = 48 if completed else self.progress*48
            return ("48 小时冷藏完成" if completed else "贴膜冷藏，等待面糊静置",
                    f"已冷藏 {hours:.1f} / 48 小时")
        if step == 4:
            title = "先回拌面糊并过筛" if phase == 0 else f"已装好 {s.filled} / 6 个铜模"
            return title, f"每模 80g · 已分装 {s.filled*80}g · 理论余量 {s.remaining_grams}g（未扣损耗）"
        if s.oven_phase in ("cold", "preheating"):
            return "先预热烤箱", f"当前设定 {s.oven_setting:.0f}°C · 推荐起始范围 200–220°C"
        if s.oven_phase == "ready":
            return "预热完成，可以开始烤了", "先烤约 50 分钟，再根据颜色决定是否追加时间"
        if s.oven_phase == "baking":
            return f"正在烘烤 · {s.bake_minutes:.1f} 分钟", "可拖动温度滑杆，或按“降温 10°C”调整后续加热"
        if s.oven_phase == "check":
            return f"看看颜色 · 当前为{s.color_name}", "可以调低温度再烤 10 分钟，或满意后进入冷却"
        if s.oven_phase == "cooling":
            return f"冷却中 · {s.cooling_minutes:.0f} / 45 分钟", "烘烤已经结束，等待外壳冷却后的状态"
        return "六步完成 · 可以品尝啦", "冷却 45 分钟完成 · 六个可露丽，每个使用面糊 80g"

    def action_text(self):
        s = self.state
        if s.step in s.completed:
            return "本步已完成"
        labels = (
            ("加热 · 沸腾保持 10 秒", "关火 · 浸香 15 分钟"),
            ("加入全蛋、蛋黄与糖", "迅速打散", "筛入 56g 面粉并拌匀"),
            ("微温牛奶冲入蛋糊", "放凉面糊", "加入 22g 朗姆酒"),
            ("贴膜 · 冷藏 48 小时",),
            ("回拌面糊并过筛", f"装第 {s.filled+1} 模 · 80g"),
        )
        if s.step < 5:
            return labels[s.step][s.phases[s.step]]
        return {"cold": "预热烤箱", "preheating": "正在预热…", "ready": "开始烘烤 50 分钟",
                "baking": "正在烘烤…", "check": "颜色满意 · 冷却 45 分钟",
                "cooling": "正在冷却…", "done": "制作完成"}[s.oven_phase]

    def render(self):
        s = self.state
        for i, button in enumerate(self.step_buttons):
            active = i == s.step
            button.config(text=f"{'✓' if i in s.completed else f'{i+1:02d}'}  {STEPS[i]}",
                          bg=ACCENT if active else "#30312b", fg=BG if active else TEXT,
                          activebackground=ACCENT if active else "#41443b",
                          state="normal" if s.can_visit(i) and not self.busy else "disabled")
        self.heading.config(text=f"{s.step+1:02d}  {STEPS[s.step]}")
        self.description.config(text=INTRO[s.step])
        title, detail = self.status_copy()
        self.status.config(text=title)
        self.detail.config(text=detail)
        self.bar["value"] = self.progress if self.busy else (1 if s.step in s.completed else 0)
        self.action_button.config(text=self.action_text(),
                                  state="disabled" if self.busy or s.step in s.completed else "normal")
        self.back_button.config(state="normal" if s.step > 0 and not self.busy else "disabled")
        self.next_button.config(text="六步完成 ✓" if s.step == 5 and 5 in s.completed else "下一步 →",
                                state="normal" if s.step < 5 and s.step in s.completed and not self.busy else "disabled")
        if s.step == 5:
            if not self.temp_frame.winfo_manager():
                self.temp_frame.pack(fill="x", pady=(10, 0), before=self.actions_frame)
            can_adjust = s.oven_phase not in ("cooling", "done")
            self.scale.config(state="normal" if can_adjust else "disabled")
            self.lower_button.config(state="normal" if can_adjust else "disabled")
        else:
            self.temp_frame.pack_forget()
        if s.step == 5 and s.oven_phase == "check" and not self.busy:
            if not self.extra_button.winfo_manager():
                self.extra_button.pack(side="left", padx=10)
        else:
            self.extra_button.pack_forget()
        self.redraw()

    def animate(self, seconds, finished, frame=None):
        if self.busy:
            return
        self.busy = True
        self.progress = 0
        started = time.perf_counter()

        def tick():
            self._animation_id = None
            if self._closed:
                return
            self.progress = min(1.0, (time.perf_counter()-started)/seconds)
            if frame:
                frame(self.progress)
            if self.progress >= 1:
                self.busy = False
                self.progress = 0
                finished()
                self.render()
            else:
                self.render()
                self._animation_id = self.root.after(40, tick)

        tick()

    def phase_done(self, complete=False):
        self.state.phases[self.state.step] += 1
        if complete:
            self.state.finish_step()

    def act(self):
        s = self.state
        if self.busy or s.step in s.completed:
            return
        phase = s.phases[s.step]
        if s.step == 0:
            self.animate(2.0 if phase == 0 else 3.0,
                         lambda: self.phase_done(complete=phase == 1))
        elif s.step == 1:
            self.animate(3.0 if phase == 0 else 2.5 if phase == 2 else 1.7,
                         lambda: self.phase_done(complete=phase == 2))
        elif s.step == 2:
            self.animate(2.0, lambda: self.phase_done(complete=phase == 2))
        elif s.step == 3:
            self.animate(4.0, lambda: self.phase_done(complete=True))
        elif s.step == 4:
            if phase == 0:
                self.animate(1.6, self.phase_done)
            else:
                self.animate(.9, s.fill_one)
        elif s.oven_phase == "cold":
            s.oven_phase = "preheating"
            initial = s.oven_actual

            def warming(fraction):
                s.oven_actual = initial+(s.oven_setting-initial)*fraction

            def ready():
                s.oven_actual = s.oven_setting
                s.oven_phase = "ready"

            self.animate(2.4, ready, warming)
        elif s.oven_phase == "ready":
            self.bake(50)
        elif s.oven_phase == "check":
            s.oven_phase = "cooling"

            def cooling(fraction):
                s.cooling_minutes = 45*fraction
                s.oven_actual = 22+(s.oven_setting-22)*(1-fraction)

            def cooled():
                s.cooling_minutes = 45
                s.oven_phase = "done"
                s.finish_step()

            self.animate(4.0, cooled, cooling)

    def bake(self, minutes):
        s = self.state
        if self.busy or s.step != 5 or s.oven_phase not in ("ready", "check"):
            return
        s.oven_phase = "baking"
        s.bake_caption = ""
        initial = s.bake_minutes

        def advance(fraction):
            target = initial+minutes*fraction
            s.advance_bake(max(0, target-s.bake_minutes))

        def baked():
            s.oven_phase = "check"
            if s.oven_setting < 200:
                s.bake_caption = "低于200°C......没有上色！"
            elif s.oven_setting > 220:
                s.bake_caption = "超过220°C！烤糊啦！"

        self.animate(6.0 if minutes == 50 else 2.5, baked, advance)

    def reset(self):
        if self._animation_id is not None:
            self.root.after_cancel(self._animation_id)
            self._animation_id = None
        self.busy = False
        self.progress = 0
        self.state = KitchenState()
        self.scale.set(210)
        self.render()

    def close(self):
        self._closed = True
        for job in (self._animation_id, self._resize_id):
            if job is not None:
                self.root.after_cancel(job)
        self.root.destroy()


def main():
    parser = argparse.ArgumentParser(description="可露丽小厨房")
    parser.add_argument("--preview-step", type=int, choices=range(1, 7),
                        help="直接预览某一步（1–6）；可点“重新制作”从头开始")
    args = parser.parse_args()
    root = tk.Tk()
    app = CaneleToy(root)
    if args.preview_step:
        target = args.preview_step-1
        app.state.completed = set(range(target))
        app.state.phases = [2 if target > 0 else 0, 3 if target > 1 else 0,
                            3 if target > 2 else 0, 1 if target > 3 else 0,
                            1 if target > 4 else 0, 0]
        app.state.filled = MOLD_COUNT if target > 4 else 0
        app.state.step = target
        app.render()
    root.mainloop()


if __name__ == "__main__":
    main()
