import typing


Event = typing.NewType("Event", typing.NamedTuple)


class Channel:

    def __init__(self) -> None:
        self._handlers = []
        self._events = []

    @property
    def events(self) -> typing.List[Event]:
        events = self._events.copy()
        self._events.clear()
        return events

    def set_handlers(self, handlers: typing.List[typing.Callable]) -> None:
        self._handlers.extend([
            _h for _h in handlers
            if hasattr(_h, "handle") and hasattr(_h, "fetch_events")
            ])

    def handle(self, event: Event) -> None:
        for handler in self._handlers:
            handler.handle(event)
            self._events.extend(handler.fetch_events())

    def clear(self) -> None:
        self._handlers.clear()
