import pygame
from pyex.base_mod import BaseMod


class SpeedMod(BaseMod):

    def on_load(self):
        self.multiplier = 1.0
        self.active = False
        self.log.success("SpeedMod prêt — F1 pour activer le boost x5")

    def on_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.active = not self.active
            self.multiplier = 5.0 if self.active else 1.0
            self.log.info(f"Speed boost {'ON x5' if self.active else 'OFF'}")
            return True
        return False

    def on_update(self, dt: float):
        base = 5.0 + self.get_context("score", 0) * 0.003
        self.set_context("speed", base * self.multiplier)

    def on_draw(self, screen: pygame.Surface):
        font = pygame.font.SysFont("consolas", 14)
        if self.active:
            color, label = (255, 80, 80), "⚡ SPEED x5  [F1 OFF]"
        else:
            color, label = (80, 180, 80), "F1 : Speed boost x5"
        screen.blit(font.render(label, True, color), (16, 80))