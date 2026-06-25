from pyex.logger import get_logger, init_logging, set_log_level, get_log_file

__version__ = "0.1.0"
__all__ = ["boot", "update", "draw", "get_logger", "set_log_level", "get_log_file"]

_engine = None

def boot(screen=None, clock=None, game_context: dict = None, log_dir=None, mods_dir=None):
    import logging
    import inspect
    from pathlib import Path

    caller_dir = Path(inspect.stack()[1].filename).parent

    if log_dir is not None:
        log_dir = Path(log_dir)
        if not log_dir.is_absolute():
            log_dir = caller_dir / log_dir

    if mods_dir is not None:
        mods_dir = Path(mods_dir)
        if not mods_dir.is_absolute():
            mods_dir = caller_dir / mods_dir
    else:
        mods_dir = caller_dir / "mods"

    init_logging(log_dir=log_dir, level=logging.DEBUG, log_to_file=True)

    from pyex.engine import PyExEngine
    global _engine
    _engine = PyExEngine(screen=screen, clock=clock, game_context=game_context or {}, mods_dir=mods_dir)
    _engine.boot()
    return _engine

def update(events=None, dt: float = 0.0):
    if _engine:
        _engine.update(events or [], dt)

def draw(screen=None):
    if _engine:
        _engine.draw(screen)

def get_engine():
    return _engine