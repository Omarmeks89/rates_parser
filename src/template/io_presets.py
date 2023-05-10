import typing


class ReadSettings(typing.NamedTuple):
    name: str
    path: str
    mode: bool
    flag: str
    suffix: str


class WriteSettings(typing.NamedTuple):
    name: str
    path: str
    mode: bool
    suffix: str


class TxtReadSettings(typing.NamedTuple):
    name: str
    path: str
    mode: str
    encoding: str
