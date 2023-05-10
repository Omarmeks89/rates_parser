import typing
import dotenv
import types
import collections
import copy
import re
import os


ENV_FILE: typing.Final[str] = 'env.env'

MULTY_HEADERS_KEY: typing.Final[str] = 'MULTY_HEADERS'
RAIL_HEADERS_KEY: typing.Final[str] = 'RAIL_HEADERS'
_RE_PATTERN_PREF: typing.Final[str] = 'RE'
_DEF_STR_SEP: typing.Final[str] = ', '

_HEADER_NAME_PATTERN: re.Pattern = re.compile(
        '^.+<([a-zA-Z]{2,})>.+$'
        )
_MULTIVALUE_STR_PATTERN: re.Pattern = re.compile(
        '([a-zA-Z0-9]{1,})'
        )


path_exists = os.path.exists


def make_config(*, path=None) -> collections.OrderedDict:
    """
    Make config dict() from .env file.
    Raise Exception if not .env file found.
    """
    path = ENV_FILE if not path else path
    return _generate_config(path)


def _make_dotenv_path() -> str:
    path = dotenv.find_dotenv(
            raise_error_if_not_found=True
            )
    if path_exists(path):
        return path


def _generate_config(path: str) -> typing.Dict[str, str]:
    config = dotenv.dotenv_values(
            dotenv_path=path
            )
    if config:
        return config
    else:
        res = dotenv.load_dotenv(path)
        return res


def build_patterns_map(
        headers_key: str,
        config: typing.Dict[str, str]
        ) -> types.MappingProxyType:
    """
    Build patterns map for txt driver.
    If config wasn`t created or headers not found
    raised Exception.
    """
    headers = _fetch_env_value(headers_key, config)
    if headers:
        pattern_builder = pattern()
        keys = [key for key in config if key.startswith(_RE_PATTERN_PREF)]
        pattern_builder.build_from(headers_key, keys, headers, config)
        if len(headers) == pattern_builder.count(headers_key):
            return pattern_builder.get(headers_key)
    raise Exception('Patterns map wasn`t created')


def _fetch_env_value(
        key: str,
        environ: typing.Dict[str, str]
        ) -> typing.Union[str, list]:
    """tested succ."""
    value = environ.get(key)
    if value:
        if _is_multivalue_str(value):
            return _split_multiple(value)
        return value


def _is_multivalue_str(
        string: str
        ) -> bool:
    """tested succ."""
    return string.count(_DEF_STR_SEP) != 0


def _split_multiple(
        in_line: str
        ) -> typing.List[str]:
    return _MULTIVALUE_STR_PATTERN.findall(in_line)


class pattern:
    """
    Generate pattern map from config and headers.
    Used closures now.
    Return MappingProxyType for using with drivers.
    """
    def __init__(self) -> None:
        self._patterns = {}

    def build_from(
            self,
            header_key: str,
            keys: typing.List[str],
            headers: typing.List[str],
            config: typing.Dict[str, str]
            ) -> None:
        pattern = {}
        pattern_name = None
        for key in keys:
            patt_line = config[key]
            matches = _HEADER_NAME_PATTERN.search(patt_line)
            if matches:
                res = matches.groups()
                pattern_name = ''.join(res).upper()
            if pattern_name in headers:
                if pattern_name in pattern:
                    pattern[pattern_name].append(re.compile(patt_line))
                else:
                    pattern.update(
                            {pattern_name: [re.compile(patt_line)]}
                            )
        if pattern:
            self._patterns[header_key] = copy.deepcopy(pattern)
            pattern.clear()

    def get(self, key: str) -> types.MappingProxyType:
        return types.MappingProxyType(self._patterns[key])

    def count(self, key: str) -> int:
        if self._patterns.get(key) is None:
            return 0
        else:
            return len(self._patterns.get(key))
