import typing
import abc


class Handler:

    @abc.abstractmethod
    def get_events(self) -> typing.NoReturn:
        pass

    @abc.abstractmethod
    def handle(self, cmd: typing.Any) -> typing.NoReturn:
        pass
