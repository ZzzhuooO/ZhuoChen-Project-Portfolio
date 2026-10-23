"""Recipe and state for the six-step canele toy (illustrative, not predictive)."""

from dataclasses import dataclass, field


RECIPE = {
    "牛奶": 276, "黄油": 28, "全蛋": 56, "蛋黄": 22,
    "糖": 138, "低筋面粉": 56, "朗姆酒": 22,
}
BATCH_GRAMS = sum(RECIPE.values())
MOLD_GRAMS = 80
MOLD_COUNT = 6
STEPS = ("香草浸香", "混合蛋糊", "合并面糊", "冷藏静置", "装入铜模", "烘烤与冷却")


@dataclass
class KitchenState:
    step: int = 0
    completed: set = field(default_factory=set)
    phases: list = field(default_factory=lambda: [0] * 6)
    progress: float = 0.0
    filled: int = 0
    oven_setting: float = 210.0
    oven_actual: float = 22.0
    oven_phase: str = "cold"
    bake_minutes: float = 0.0
    heat_dose: float = 0.0
    color_dose: float = 0.0
    uniform_caramel: bool = False
    cooling_minutes: float = 0.0
    bake_caption: str = ""

    @property
    def remaining_grams(self):
        # Bookkeeping excludes evaporation and material left on the tools.
        return BATCH_GRAMS - self.filled * MOLD_GRAMS

    @property
    def unlocked(self):
        return min(len(self.completed), 5)

    def finish_step(self):
        self.completed.add(self.step)

    def can_visit(self, step):
        return 0 <= step < len(STEPS) and step <= self.unlocked

    def fill_one(self):
        if self.filled >= MOLD_COUNT:
            raise ValueError("All six molds are already filled")
        self.filled += 1
        if self.filled == MOLD_COUNT:
            self.finish_step()

    def advance_bake(self, minutes):
        if minutes < 0:
            raise ValueError("Baking time cannot run backwards")
        # Heating and crumb structure retain the original response. Color uses
        # the toy's explicit setting boundaries, independently of thermal lag.
        self.oven_actual += (self.oven_setting - self.oven_actual) * min(1.0, minutes / 4)
        dose = max(0, (self.oven_actual - 150) / 60) * minutes
        self.heat_dose += dose
        self.bake_minutes += minutes
        if minutes > 0:
            if self.oven_setting > 220:
                self.color_dose = 50.0
                self.uniform_caramel = True
            elif self.oven_setting >= 200:
                self.color_dose += dose
            # Below 200, keep the last colors, including a browned interior.

    @property
    def color_name(self):
        if self.color_dose < 22:
            return "浅金色"
        if self.color_dose < 40:
            return "金棕色"
        if self.color_dose < 62:
            return "焦糖棕"
        if self.color_dose < 80:
            return "深棕色"
        return "颜色很深"
