from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyex.engine import PyExEngine
    from pyex.logger import PyExLogger


class BaseMod:
    def __init__(self, engine: "PyExEngine", info: dict, log: "PyExLogger"):
        self.engine = engine
        self.info = info
        self.log = log
        self.name: str = info.get("name", "UnknownMod")
        self.version: str = info.get("version", "0.0.0")
        self.author: str = info.get("author", "inconnu")
        self.dependencies: list[str] = info.get("dependencies", [])

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def on_event(self, event):
        pass

    def on_update(self, dt: float):
        pass

    def on_draw(self, screen):
        pass

    def emit(self, event_name: str, data: dict = None):
        self.engine.event_bus.emit(event_name, data or {})

    def on(self, event_name: str, callback):
        self.engine.event_bus.on(event_name, callback)

    def get_mod(self, name: str):
        return self.engine.get_mod(name)

    def get_context(self, key: str, default=None):
        return self.engine.get_context(key, default)

    def set_context(self, key: str, value):
        self.engine.set_context(key, value)

    def __repr__(self):
        return f"<Mod '{self.name}' v{self.version} by {self.author}>"
