import typing
import types
import sys

from . import domain_models
from . import messages
from . import exchange
from . import cache
from . import channels
from . import handlers
from . import core_events
from . import text_utils
from . import core_utils
from . import command_filters
from . import router
from . import terminal_commands


class BrokenCore(BaseException):
    pass


Cache = cache.SystemCache()
api_router = router.ApiRouter()


exch = exchange.Exchange()
selector = exchange.Selector()
scheduler = exchange.Scheduler(
        selector,
        exch
        )
receiver = exchange.Receiver(
        scheduler,
        exch
        )


def setup_exchange(
        channels: typing.Dict[str, channels.Channel],
        handlers: typing.Dict[str, handlers.Handler]
        ) -> None:
    """Base ugly impl of exchange setup."""
    # nonlocal selector
    try:
        selector.set_channels(channels)
        selector.set_handlers(handlers)
    except (Exception, BaseException) as err:
        raise BrokenCore from err


def regkeys_maker() -> typing.Callable[[object], str]:
    key_maker = exchange.Selector

    def make_key_for_channel(
            item: object
            ) -> str:
        nonlocal key_maker
        return key_maker.make_key_for_channels(item)

    def make_key_for_message(
            item: object
            ) -> str:
        nonlocal key_maker
        return key_maker.make_key_for_messages(item)

    regkeys_maker.get_channel_key = make_key_for_channel
    regkeys_maker.get_message_key = make_key_for_message
    return regkeys_maker


class registrator:
    """class, that registered handlers
    and channels in event_system.
    """

    _channels: typing.Dict[str, channels.Channel] = {}
    _handlers: typing.Dict[str, handlers.Handler] = {}
    _keysmaker = regkeys_maker()

    @classmethod
    def can_setup(cls) -> bool:
        return all((cls._channels, cls._handlers))

    @classmethod
    def registered_channels(cls) -> types.MappingProxyType:
        return types.MappingProxyType(cls._channels)

    @classmethod
    def registered_handlers(cls) -> types.MappingProxyType:
        return types.MappingProxyType(cls._handlers)

    @classmethod
    def register_channel(
            cls,
            msg_item: object,
            channel: channels.Channel
            ) -> None:
        key = cls._keysmaker.get_channel_key(msg_item)
        cls._channels[key] = channel

    @classmethod
    def register_handler(
            cls,
            msg_item: object,
            handler: handlers.Handler
            ) -> None:
        key = cls._keysmaker.get_message_key(msg_item)
        cls._handlers[key] = handler

    @classmethod
    def setup_eventsystem(cls) -> None:
        if cls.can_setup():
            setup_exchange(
                    cls.registered_channels(),
                    cls.registered_handlers()
                    )
        else:
            msg = 'Eventsystem setup aborted.'\
                  ' Handlers: {} or '\
                  'Channels: {} don`t registered.'
            raise BrokenCore(
                msg.format(cls._handlers, cls._channels)
                )


__all__ = [
        'domain_models',
        'messages',
        'receiver',
        'Cache',
        'setup_exchange',
        'handlers',
        'channels',
        'core_events',
        'text_utils',
        'core_utils',
        'command_filters',
        'registrator',
        'api_router',
        'terminal_commands'
        ]
