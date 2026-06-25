import pygame
from pyex.base_mod import BaseMod
from pyex.logger import get_logger

log = get_logger("PyEx.ModUI")

TOGGLE_KEY   = pygame.K_F9
BG_COLOR     = (15, 15, 20, 220)
BORDER_COLOR = (80, 130, 255)
TITLE_COLOR  = (80, 130, 255)
TEXT_COLOR   = (220, 220, 220)
DIM_COLOR    = (120, 120, 120)
OK_COLOR     = (80, 200, 120)
ERR_COLOR    = (220, 80, 80)
HOVER_COLOR  = (40, 40, 60, 180)
PANEL_W      = 420
PANEL_H      = 380
PADDING      = 18
ROW_H        = 38


class ModUI(BaseMod):
    def __init__(self, engine, info, log):
        super().__init__(engine, info, log)
        self._visible     = False
        self._font_title  = None
        self._font_body   = None
        self._font_small  = None
        self._scroll      = 0
        self._hovered     = -1

    def on_load(self):
        if not pygame.font.get_init():
            pygame.font.init()
        self._font_title = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_body  = pygame.font.SysFont("consolas", 15)
        self._font_small = pygame.font.SysFont("consolas", 12)
        self.log.success("ModUI prêt (F9 pour ouvrir)")

    def on_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == TOGGLE_KEY:
            self._visible = not self._visible
            log.info(f"ModUI {'ouvert' if self._visible else 'fermé'}")
            return True

        if not self._visible:
            return False

        if event.type == pygame.MOUSEWHEEL:
            self._scroll = max(0, self._scroll - event.y * ROW_H)
            return True
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._on_click(event.pos)
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._visible = False
            return True
        return True

    def on_update(self, dt: float):
        pass

    def on_draw(self, screen: pygame.Surface):
        if not self._visible:
            return

        sw, sh = screen.get_size()
        px = (sw - PANEL_W) // 2
        py = (sh - PANEL_H) // 2

        panel = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panel.fill(BG_COLOR)
        pygame.draw.rect(panel, BORDER_COLOR, (0, 0, PANEL_W, PANEL_H), 2, border_radius=8)

        title = self._font_title.render("⬡  PyEx — Gestionnaire de mods", True, TITLE_COLOR)
        panel.blit(title, (PADDING, PADDING))

        sub = self._font_small.render(f"F9 fermer  •  {len(self.engine.mods)} mod(s) chargé(s)", True, DIM_COLOR)
        panel.blit(sub, (PADDING, PADDING + 24))

        pygame.draw.line(panel, BORDER_COLOR, (PADDING, 56), (PANEL_W - PADDING, 56), 1)
        self._draw_mod_list(panel)

        hint = self._font_small.render("Clic pour activer/désactiver • Scroll pour défiler", True, DIM_COLOR)
        panel.blit(hint, (PADDING, PANEL_H - 24))

        screen.blit(panel, (px, py))

    def _draw_mod_list(self, panel: pygame.Surface):
        mods = list(self.engine.mods.items())
        clip_top = 64
        clip_h = PANEL_H - clip_top - 34
        list_surf = pygame.Surface((PANEL_W, max(len(mods) * ROW_H + 10, clip_h)), pygame.SRCALPHA)

        for i, (mod_name, mod) in enumerate(mods):
            y = i * ROW_H + 4
            if i == self._hovered:
                hs = pygame.Surface((PANEL_W - PADDING * 2, ROW_H - 4), pygame.SRCALPHA)
                hs.fill(HOVER_COLOR)
                list_surf.blit(hs, (PADDING, y + 2))

            active = getattr(mod, "_pyex_active", True)
            pygame.draw.circle(list_surf, OK_COLOR if active else ERR_COLOR, (PADDING + 8, y + ROW_H // 2), 5)

            name_surf = self._font_body.render(mod.name, True, TEXT_COLOR if active else DIM_COLOR)
            list_surf.blit(name_surf, (PADDING + 22, y + 6))

            meta = self._font_small.render(f"v{mod.version}  •  {mod.author}", True, DIM_COLOR)
            list_surf.blit(meta, (PADDING + 22, y + 22))

            if i < len(mods) - 1:
                pygame.draw.line(list_surf, (40, 40, 55), (PADDING, y + ROW_H - 2), (PANEL_W - PADDING, y + ROW_H - 2), 1)

        view = list_surf.subsurface(pygame.Rect(0, min(self._scroll, max(0, list_surf.get_height() - clip_h)), PANEL_W, clip_h))
        panel.blit(view, (0, clip_top))

    def _panel_rect(self, screen_size) -> pygame.Rect:
        sw, sh = screen_size
        return pygame.Rect((sw - PANEL_W) // 2, (sh - PANEL_H) // 2, PANEL_W, PANEL_H)

    def _update_hover(self, pos):
        screen = pygame.display.get_surface()
        if screen is None:
            return
        pr = self._panel_rect(screen.get_size())
        rel_y = pos[1] - pr.y - 64 + self._scroll
        idx = rel_y // ROW_H
        mods = list(self.engine.mods.keys())
        self._hovered = idx if 0 <= idx < len(mods) else -1

    def _on_click(self, pos):
        screen = pygame.display.get_surface()
        if screen is None:
            return
        pr = self._panel_rect(screen.get_size())
        rel_y = pos[1] - pr.y - 64 + self._scroll
        idx = rel_y // ROW_H
        mods = list(self.engine.mods.values())
        if 0 <= idx < len(mods):
            mod = mods[idx]
            mod._pyex_active = not getattr(mod, "_pyex_active", True)
            state = "activé" if mod._pyex_active else "désactivé"
            self.log.info(f"Mod '{mod.name}' {state} via UI")
            self.engine.event_bus.emit("pyex.mod_toggled", {"name": mod.name, "active": mod._pyex_active})
