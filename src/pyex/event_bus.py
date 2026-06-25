import traceback
from collections import defaultdict
from typing import Callable
from pyex.logger import get_logger

log = get_logger("PyEx.EventBus")


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)
        self._once: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_name: str, callback: Callable):
        if callback not in self._listeners[event_name]:
            self._listeners[event_name].append(callback)
            log.debug(f"Listener ajouté : '{event_name}' → {callback.__qualname__}")

    def once(self, event_name: str, callback: Callable):
        if callback not in self._once[event_name]:
            self._once[event_name].append(callback)

    def off(self, event_name: str, callback: Callable):
        if callback in self._listeners[event_name]:
            self._listeners[event_name].remove(callback)
            log.debug(f"Listener retiré : '{event_name}' → {callback.__qualname__}")
        if callback in self._once[event_name]:
            self._once[event_name].remove(callback)

    def off_all(self, event_name: str):
        count = len(self._listeners[event_name]) + len(self._once[event_name])
        self._listeners[event_name].clear()
        self._once[event_name].clear()
        if count:
            log.debug(f"Tous les listeners retirés pour '{event_name}' ({count})")

    def emit(self, event_name: str, data: dict = None):
        payload = data or {}
        listeners = list(self._listeners.get(event_name, []))
        once_listeners = list(self._once.get(event_name, []))
        if listeners or once_listeners:
            log.debug(f"emit '{event_name}' → {len(listeners) + len(once_listeners)} listener(s)")
        for cb in listeners:
            self._call_safe(cb, event_name, payload)
        for cb in once_listeners:
            self._call_safe(cb, event_name, payload)
        self._once[event_name].clear()

    def _call_safe(self, callback: Callable, event_name: str, data: dict):
        try:
            callback(data)
        except Exception:
            log.error(f"Exception dans '{event_name}' ({callback.__qualname__}) :\n{traceback.format_exc()}")

    def list_events(self) -> list[str]:
        events = set(self._listeners.keys()) | set(self._once.keys())
        return sorted(e for e in events if self._listeners[e] or self._once[e])

    def listener_count(self, event_name: str) -> int:
        return len(self._listeners[event_name]) + len(self._once[event_name])

    def __repr__(self):
        events = self.list_events()
        return f"<EventBus {len(events)} event(s): {events}>"
