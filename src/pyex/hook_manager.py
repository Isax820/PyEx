import traceback
from typing import TYPE_CHECKING
from pyex.logger import get_logger

if TYPE_CHECKING:
    from pyex.base_mod import BaseMod
    from pyex.event_bus import EventBus

log = get_logger("PyEx.Hooks")


class HookManager:
    def __init__(self, event_bus: "EventBus"):
        self.event_bus = event_bus
        self._mods: list[tuple[str, "BaseMod"]] = []

    def register_mod(self, mod: "BaseMod", name: str):
        self._mods.append((name, mod))
        log.debug(f"Mod '{name}' enregistré")

    def unregister_mod(self, name: str):
        before = len(self._mods)
        self._mods = [(n, m) for n, m in self._mods if n != name]
        if len(self._mods) < before:
            log.debug(f"Mod '{name}' retiré")

    def dispatch_event(self, event) -> bool:
        for name, mod in self._mods:
            if not getattr(mod, "_pyex_active", True):
                continue
            try:
                if mod.on_event(event) is True:
                    log.debug(f"Event {event.type} consommé par '{name}'")
                    return True
            except Exception:
                log.error(f"Erreur on_event() '{name}' :\n{traceback.format_exc()}")
        return False

    def dispatch_update(self, dt: float):
        for name, mod in self._mods:
            if not getattr(mod, "_pyex_active", True):
                continue
            try:
                mod.on_update(dt)
            except Exception:
                log.error(f"Erreur on_update() '{name}' :\n{traceback.format_exc()}")

    def dispatch_draw(self, screen):
        for name, mod in self._mods:
            if not getattr(mod, "_pyex_active", True):
                continue
            try:
                mod.on_draw(screen)
            except Exception:
                log.error(f"Erreur on_draw() '{name}' :\n{traceback.format_exc()}")

    @property
    def mod_names(self) -> list[str]:
        return [n for n, _ in self._mods]

    def __repr__(self):
        return f"<HookManager {len(self._mods)} mod(s): {self.mod_names}>"
