<div align="center">

# ⬡ PyEx

**A lightweight mod loader for PyGame games — inspired by BepInEx**

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![PyGame](https://img.shields.io/badge/PyGame-2.x-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)

</div>

---

## What is PyEx?

PyEx is a mod loader for PyGame games. It lets players install `.py` mods without recompiling the game, and lets developers integrate it in **4 lines of code**.

Think of it like BepInEx, but for Python.

---

## Features

- **4-line integration** — drop PyEx into any existing PyGame game
- **Auto mod discovery** — place a folder in `mods/` and it loads automatically
- **Event hooks** — intercept any pygame event, update tick, or draw call
- **Inter-mod communication** — event bus with `on()` / `emit()`
- **Game context** — mods can read and write game variables
- **Built-in mod manager** — press `F9` in-game to enable/disable mods
- **Colored logs** — console + file logging out of the box
- **Dependency resolution** — declare mod dependencies in `mod_info.json`

---

## Project Structure

```
PyEx/
├── src/
│   ├── pyex/                  ← The engine (ship this with your game)
│   │   ├── __init__.py        ← Public API: boot(), update(), draw()
│   │   ├── engine.py          ← Core: loads mods, orchestrates everything
│   │   ├── base_mod.py        ← Base class all mods must inherit
│   │   ├── logger.py          ← Colored console + file logging
│   │   ├── event_bus.py       ← Inter-mod pub/sub event system
│   │   ├── hook_manager.py    ← Dispatches pygame events / update / draw
│   │   └── mod_ui.py          ← Built-in F9 overlay to manage mods
│   └── game/
│       ├── main.py            ← Your game
│       └── mods/
│           └── speed_mod/     ← Example mod
│               ├── mod.py
│               └── mod_info.json
└── README.md
```

---

## Integration

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import pyex
    PYEX_AVAILABLE = True
except ImportError:
    PYEX_AVAILABLE = False

# After creating screen and clock:
if PYEX_AVAILABLE:
    pyex.boot(screen=screen, clock=clock, game_context=game_context)

# In your game loop:
if PYEX_AVAILABLE:
    game_context["score"] = self.score
    game_context["speed"] = self.speed
    pyex.update(events, dt)
    self.speed = game_context.get("speed", self.speed)  # read mod changes

# After drawing your game:
if PYEX_AVAILABLE:
    pyex.draw(screen)
```

PyEx is **opt-in** — if the `pyex/` folder is missing, the game runs normally.

---

## Creating a Mod

```
mods/
└── my_mod/
    ├── mod.py
    └── mod_info.json
```

**mod_info.json**
```json
{
    "name": "MyMod",
    "version": "1.0.0",
    "author": "YourName",
    "entry_point": "mod.py",
    "dependencies": []
}
```

**mod.py**
```python
import pygame
from pyex.base_mod import BaseMod

class MyMod(BaseMod):

    def on_load(self):
        self.log.success("MyMod loaded!")

    def on_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F2:
            self.log.info("F2 pressed!")
            return True  # consume the event
        return False

    def on_update(self, dt: float):
        score = self.get_context("score", 0)

    def on_draw(self, screen):
        pass  # draw overlays here
```

---

## BaseMod API

| Method | Description |
|---|---|
| `on_load()` | Called once when the mod is loaded |
| `on_unload()` | Called when the mod is disabled |
| `on_event(event)` | Receives every pygame event — return `True` to consume it |
| `on_update(dt)` | Called every frame, `dt` in seconds |
| `on_draw(screen)` | Called after the game draws — use for overlays |
| `self.emit(name, data)` | Emit an inter-mod event |
| `self.on(name, callback)` | Subscribe to an inter-mod event |
| `self.get_context(key)` | Read a game variable |
| `self.set_context(key, val)` | Write a game variable |
| `self.get_mod(name)` | Get another mod's instance |

---

## Logging

Logs appear in the console (colored) and in `logs/pyex_YYYY-MM-DD_HH-MM-SS.log`.

```
12:34:56.789 [INF] [PyEx.Engine]  ── Chargement des mods ──
12:34:56.800 [INF] [PyEx.Mods.SpeedMod] ✓ v1.0.0 by YourName — ready
12:34:56.801 [INF] [PyEx.ModUI] ✓ ModUI ready (F9 to open)
```

```python
from pyex.logger import get_logger
log = get_logger("MyMod")
log.info("Hello!")
log.warn("Something feels off")
log.error("Something broke")
log.success("All good")
```

---

## Keybinds

| Key | Action |
|---|---|
| `F9` | Open / close the mod manager overlay |
| `Escape` | Close the overlay |
| `Scroll` | Scroll the mod list |
| `Click` | Enable / disable a mod |

---

## License

MIT — do whatever you want with it.