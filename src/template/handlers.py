import typing

from .messages import LoadExcelFile
from .messages import LoadTxtFile
from .io_presets import ReadSettings
from .io_presets import TxtReadSettings

from .core_presets import handlers as h
from .core_presets import Cache


class LoadExcelFileCmdHandler(h.Handler):

    def __init__(
            self,
            uow: typing.Any,
            cache: Cache
            ) -> None:
        self._uow = uow
        self._cache = cache

    def fetch_events(self) -> typing.List[typing.Any]:
        return self._uow.events

    def handle(self, cmd: LoadExcelFile) -> None:
        with self._uow as operator:
            source = operator.port
            try:
                read_set = ReadSettings(
                        name=cmd.fname,
                        path=cmd.path,
                        mode=cmd.mode,
                        flag=cmd.flag,
                        suffix=cmd.suffix
                        )
                model = source.load(read_set)
                self._cache.add(model.name, model)
            except Exception as err:
                msg = f'Command handling failed with: {err}.'
                raise Exception(msg)


class LoadTxtFileCmdHandler(h.Handler):

    def __init__(
            self,
            uow: typing.Any,
            cache: Cache
            ) -> None:
        self._uow = uow
        self._cache = cache

    def fetch_events(self) -> typing.List[typing.Any]:
        return self._uow.events

    def handle(self, cmd: LoadTxtFile) -> None:
        with self._uow as operator:
            source = operator.port
            try:
                read_txt = TxtReadSettings(
                        name=cmd.fname,
                        path=cmd.path,
                        mode=cmd.mode,
                        flag=cmd.flag,
                        suffix=cmd.suffix
                        )
                model = source.load(read_txt)
                self._cache.add(model.name, model)
            except Exception as err:
                msg = f'{self.__class__.__name__} failed '\
                      f'with exception: {err}.'
                raise Exception(msg)
