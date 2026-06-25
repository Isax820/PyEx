import sys
import json
import importlib.util
import traceback
from pathlib import Path
from typing import Any, Optional

from pyex.logger import get_logger
from pyex.event_bus import EventBus
from pyex.hook_manager import HookManager

log = get_logger("PyEx.Engine")


class PyExEngine:
    MOD_INFO_FILE = "mod_info.json"

    def __init__(self, screen=None, clock=None, game_context: dict = None, mods_dir: Path = None):
        self.screen = screen
        self.clock = clock
        self.game_context: dict[str, Any] = game_context or {}
        self.mods: dict[str, Any] = {}
        self._load_order: list[str] = []
        self.MODS_DIR = mods_dir if mods_dir is not None else Path("mods")
        self.event_bus = EventBus()
        self.hooks = HookManager(self.event_bus)

    def boot(self):
        log.section("Chargement des mods")
        log.info(f"Dossier mods : {self.MODS_DIR.resolve()}")

        if not self.MODS_DIR.exists():
            self.MODS_DIR.mkdir(parents=True)
            log.warn(f"Dossier '{self.MODS_DIR}' créé (vide)")
            self._load_internal_ui()
            return

        mod_folders = sorted(p for p in self.MODS_DIR.iterdir() if p.is_dir())

        if not mod_folders:
            log.info("Aucun mod trouvé.")
        else:
            log.info(f"{len(mod_folders)} dossier(s) détecté(s)")
            for folder in mod_folders:
                self._load_mod(folder)
            self._resolve_load_order()
            for mod_name in self._load_order:
                mod = self.mods.get(mod_name)
                if mod:
                    self._call_safe(mod, "on_load", mod_name)
            log.success(f"{len(self.mods)} mod(s) chargé(s) : {list(self.mods.keys())}")

        self._load_internal_ui()
        self.event_bus.emit("pyex.boot_complete", {"mods": list(self.mods.keys())})

    def _load_internal_ui(self):
        from pyex.mod_ui import ModUI
        ui_info = {"name": "PyEx.ModUI", "version": "built-in", "author": "PyEx", "entry_point": "", "dependencies": []}
        ui = ModUI(engine=self, info=ui_info, log=get_logger("PyEx.ModUI"))
        self._call_safe(ui, "on_load", "PyEx.ModUI")
        self.hooks.register_mod(ui, "__pyex_ui__")

    def _load_mod(self, folder: Path):
        mod_name = folder.name
        info_path = folder / self.MOD_INFO_FILE
        log_mod = get_logger(mod_name)

        info = self._read_mod_info(info_path, mod_name, log_mod)
        if info is None:
            return

        entry = folder / info.get("entry_point", "mod.py")
        if not entry.exists():
            log_mod.error(f"Point d'entrée introuvable : {entry}")
            return

        spec = importlib.util.spec_from_file_location(f"pyex_mod_{mod_name}", entry)
        if spec is None:
            log_mod.error(f"Impossible de créer le spec pour {entry}")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[f"pyex_mod_{mod_name}"] = module

        try:
            spec.loader.exec_module(module)
        except Exception:
            log_mod.error(f"Erreur à l'import de {entry} :\n{traceback.format_exc()}")
            return

        mod_class = self._find_mod_class(module, mod_name, log_mod)
        if mod_class is None:
            return

        try:
            instance = mod_class(engine=self, info=info, log=get_logger(info.get("name", mod_name)))
            self.mods[mod_name] = instance
            self.hooks.register_mod(instance, mod_name)
            log_mod.success(f"v{info.get('version', '?')} par {info.get('author', '?')} — prêt")
        except Exception:
            log_mod.error(f"Erreur à l'instanciation :\n{traceback.format_exc()}")

    def _read_mod_info(self, path: Path, mod_name: str, log_mod) -> Optional[dict]:
        if not path.exists():
            log_mod.warn(f"Pas de mod_info.json dans '{mod_name}' — valeurs par défaut")
            return {"name": mod_name, "version": "0.0.0", "author": "inconnu", "entry_point": "mod.py", "dependencies": []}
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            log_mod.error(f"mod_info.json invalide : {e}")
            return None

    def _find_mod_class(self, module, mod_name: str, log_mod):
        from pyex.base_mod import BaseMod
        candidates = []
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            try:
                if isinstance(obj, type) and issubclass(obj, BaseMod) and obj is not BaseMod:
                    candidates.append(obj)
            except TypeError:
                pass
        if not candidates:
            log_mod.error(f"Aucune classe BaseMod trouvée dans '{mod_name}'")
            return None
        if len(candidates) > 1:
            log_mod.warn(f"Plusieurs classes détectées, utilisation de : {candidates[0].__name__}")
        return candidates[0]

    def _resolve_load_order(self):
        resolved = []
        seen = set()

        def visit(name):
            if name in seen:
                return
            seen.add(name)
            mod = self.mods.get(name)
            if mod is None:
                return
            for dep in getattr(mod, "dependencies", []):
                if dep not in self.mods:
                    log.warn(f"Mod '{name}' dépend de '{dep}' non chargé !")
                else:
                    visit(dep)
            resolved.append(name)

        for name in self.mods:
            visit(name)
        self._load_order = resolved

    def update(self, events: list, dt: float):
        for event in events:
            self.hooks.dispatch_event(event)
        self.hooks.dispatch_update(dt)

    def draw(self, screen=None):
        target = screen or self.screen
        if target is None:
            return
        self.hooks.dispatch_draw(target)

    def _call_safe(self, mod, method: str, mod_name: str, *args, **kwargs):
        fn = getattr(mod, method, None)
        if fn and callable(fn):
            try:
                fn(*args, **kwargs)
            except Exception:
                get_logger(mod_name).error(f"Erreur dans {method}() :\n{traceback.format_exc()}")

    def get_mod(self, name: str):
        return self.mods.get(name)

    def get_context(self, key: str, default=None):
        return self.game_context.get(key, default)

    def set_context(self, key: str, value):
        self.game_context[key] = value
        log.debug(f"context['{key}'] mis à jour")