import typing
import collections
import inspect


class SelectorError(Exception):
    pass


class ExchangeError(Exception):
    pass


class SchedulerError(Exception):
    pass


class Channel(typing.Protocol):

    def handle(self, event: typing.Any) -> None:
        ...

    @property
    def events(self) -> typing.Any:
        ...


class Selector:

    def __init__(self) -> None:
        self._handlers = {}
        self._channels = {}

    @staticmethod
    def make_key_for_channels(
            item: object
            ) -> str:
        if inspect.isclass(item):
            return item
        else:
            return type(item).__bases__[0]

    @staticmethod
    def make_key_for_messages(
            item: object
            ) -> str:
        if inspect.isclass(item):
            return type(item).__name__
        elif inspect.isfunction(item):
            return item.__name__
        else:
            if isinstance(item, object):
                return type(item).__name__

    def set_channels(
            self,
            channels: typing.Dict[str, Channel]
            ) -> None:
        if not self._channels:
            self._channels.update(channels)

    def set_handlers(
            self,
            handlers: typing.Dict[str, typing.Any]
            ) -> None:
        if not self._handlers:
            self._handlers.update(handlers)

    def select(self, event: typing.Any) -> typing.Tuple[Channel, list]:
        """Return pair: channel, [handlers] for event/cmd."""
        event_parent = self.make_key_for_channels(event)
        event_name = self.make_key_for_messages(event)
        channel = self._select_channel(event_parent)
        handlers = self._select_handlers(event_name)
        if all([channel, handlers]):
            return channel, handlers
        raise SelectorError(f'No such key: <{event_name}> registered.')

    def _select_channel(self, event_name: str) -> typing.Optional[Channel]:
        if self._key_in(event_name, self._channels):
            return self._channels[event_name]

    def _select_handlers(self, event_name: str) -> typing.Optional[list]:
        if self._key_in(event_name, self._handlers):
            return self._handlers[event_name]

    @staticmethod
    def _key_in(key: str, collection: dict) -> bool:
        return key in collection


class Exchange:

    _queue = collections.deque

    def __init__(self, *, max_size: typing.Optional[int] = None) -> None:
        self._to_read = self._queue([], max_size)
        self._to_write = self._queue([], max_size)
        self._qs = None

    def put_message(self, msg: typing.Any) -> None:
        element_count = 1
        if not self.queue_have_free_space(self._to_read, element_count):
            raise ExchangeError('Requests queue overflow.')
        self._to_read.append(msg)

    def put_result(self, msg: typing.Any) -> None:
        element_count = 1
        if not self.queue_have_free_space(self._to_write, element_count):
            raise ExchangeError('Results queue overflow.')
        self._to_write.append(msg)

    @staticmethod
    def queue_have_free_space(queue: collections.deque, _add: int) -> bool:
        if queue.maxlen is not None:
            return queue.maxlen >= len(queue) + _add
        return True

    def fetch_by_round(self) -> typing.NamedTuple:
        if self._qs is None:
            self._build_order_for_round_robin()
        first = 0
        last = -1
        while True:
            source = self._qs[first]
            self._qs[first], self._qs[last] = self._qs[last], self._qs[first]
            if source:
                yield source.popleft()
            else:
                yield None

    def _build_order_for_round_robin(self) -> None:
        self._qs = [
            q for k, q in self.__dict__.items()
            if k.startswith('_to')
            ]


class Scheduler:

    _queue = collections.deque

    def __init__(self,
                 selector: Selector,
                 exchange: Exchange,
                 *,
                 max_operations: typing.Optional[int] = None) -> None:
        self._operations = self._queue([], max_operations)
        self._selector = selector
        self._exchange = exchange
        self._exchange_collection = self._generate_queues_order()
        self._stopped = False

    def _shutdown(self) -> None:
        self._stopped = True

    def _restart(self) -> None:
        self._stopped = False

    def _generate_queues_order(self) -> typing.Generator:
        return self._exchange.fetch_by_round()

    def check_events(self) -> None:
        repeats = 0
        repack = []
        while not self._stopped:
            event = next(self._exchange_collection)
            if event is None:
                if repeats > 0:
                    self._shutdown()
                else:
                    repeats += 1
            else:
                repeats = 0
                self._add_to_plan(event)

            while self._operations:
                results = next(self._operations.popleft())
                for result in results:
                    try:
                        self._exchange.put_result(result)
                    except ExchangeError:
                        pos = results.index(result)
                        repack.extend(results[pos:])
                        break
            if repack:
                self._schedule_canceled(repack)
            self._handle_errors()

        else:
            repeats = 0
            self._restart()

    def _add_to_plan(self, event: typing.Any) -> None:

        def create_operation(event: typing.Any,
                             channel: Channel) -> typing.Generator:
            try:
                channel.handle(event)
                channel.clear()
                yield channel.events
            except Exception:
                channel.clear()

        channel = None
        try:
            channel, handlers = self._selector.select(event)
            channel.set_handlers(handlers)
            self._operations.append(create_operation(event, channel))
        except SelectorError as e:
            print(e.__class__.__name__, e, 'SELECTOR ERROR')

    def _handle_errors(self) -> None:
        ...

    def _schedule_canceled(self, events: list) -> None:
        if len(self._operations) + 1 <= self._operations.maxlen:
            repacked = self._repack_results(events.copy())
            self._operations.append(repacked)
            events.clear()

    def _repack_results(self, results: typing.List) -> typing.Generator:
        yield results


class Receiver:

    def __init__(self,
                 scheduler: Scheduler,
                 exchange: Exchange) -> None:
        self._scheduler = scheduler
        self._exchange = exchange
        self._buffer = collections.deque()

    def receive(self, msg: typing.Any) -> None:
        self._buffer.append(msg)
        from_buffer = None
        while self._buffer:
            len_buffer = len(self._buffer)
            for _ in range(len_buffer):
                from_buffer = self._buffer.popleft()
                try:
                    self._exchange.put_message(from_buffer)
                except ExchangeError as e:
                    print(e.__class__.__name__, e)
                    self._buffer.append(from_buffer)
            self._scheduler.check_events()
