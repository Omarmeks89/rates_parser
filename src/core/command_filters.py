import re
import typing
import abc
import dataclasses


DEFAULT_INVOKE_SYMB: str = '~$ '
PASS_SYMB: str = ''

PATH_FILTER_KEY: str = 'path'
ARGS_FILTER_KEY: str = 'args'

POSTPROCESSOR_FILTERS_KEYS: typing.Tuple[str] = (
    PATH_FILTER_KEY,
    ARGS_FILTER_KEY
    )


_CMD_PATTERN: re.Pattern = re.compile(
    '''(?x)(?P<cmd>[a-z]{3,})\s(?P<mode>(?:-[a-z]{1,3})?)
    (\s)?(?P<path>(?:(.+)\.[a-z]{2,6})?)(\s)?
    (?P<flag>(?:--[a-z]{1,3})?)(\s)?(?P<args>(?:.+)?)$''' # noqa
    )
_ARGS: re.Pattern = re.compile(
    '\w+' # noqa
    )
_SUFFIX: re.Pattern = re.compile(
    '^.+(?P<suffix>[\.][a-z]{2,6})$' # noqa
    )


_PostProcessor = typing.NewType('_PostProcessor', type)


class FilterError(Exception):
    pass


class SystemValidationError(Exception):
    pass


class PostprocessorError(BaseException):
    pass


@dataclasses.dataclass
class CommandTemplate:
    cmd: str
    mode: str
    path: str
    flag: str
    args: str


@dataclasses.dataclass
class TerminalCommand:
    cmd: str
    mode: str = dataclasses.field(default_factory=str)
    path: str = dataclasses.field(default_factory=str)
    flag: str = dataclasses.field(default_factory=str)
    args: list = dataclasses.field(default_factory=list)
    suffix: str = dataclasses.field(default_factory=str)


class Filter(abc.ABC):

    _pattern: re.Pattern

    @classmethod
    @abc.abstractmethod
    def prepare(
            cls,
            item: str
            ) -> typing.NoReturn:
        pass


class ArgsToListFilter(Filter):
    """Fetch args from command."""

    _pattern: re.Pattern = _ARGS

    @classmethod
    def prepare(
            cls,
            item: str
            ) -> typing.List[str]:

        try:
            return cls._pattern.findall(item)
        except (
                Exception,
                BaseException
                ) as err:
            msg = f'No matches with line: <{item}>, error: {err}'
            raise FilterError(msg)


class FetchSuffixFilter(Filter):
    """Fetch file suffix (.txt) from command."""

    _pattern: re.Pattern = _SUFFIX

    @classmethod
    def prepare(
            cls,
            item: str
            ) -> str:

        match_suffix = cls._pattern.match(item)
        if match_suffix:
            return match_suffix.groupdict()
        else:
            err = f'<{item}> not match. Len item = {len(item)}'
            raise FilterError(err)


def set_postprocessor_filters(
        postprocessor: _PostProcessor,
        filters: typing.Dict[str, Filter]
        ) -> None:
    """
    Set filters to PostProcessor class.
    """
    if hasattr(postprocessor, 'add_filter'):
        for k, f in filters.items():
            postprocessor.add_filter(k, f)
    else:
        raise Exception(
            f'Instance {postprocessor} isn`t a subclass of PostProcessor'
            )


class PreProcessor:
    """
    Parse raw_cmd from terminal input
    into dataclass CommandTemplate.
    """

    _pattern: re.Pattern = _CMD_PATTERN

    @classmethod
    def make_cmd_template(
            cls,
            cmd: str
            ) -> typing.Optional[CommandTemplate]:

        template = cls._pattern.match(cmd)
        try:
            return CommandTemplate(**template.groupdict())
        except AttributeError:
            return template


class PostProcessor:
    """Make TerminalCommand from CommandTemplate.
       Fetch all needed parameters using Filters().
       Return TerminalCommand.
       """

    _keys: str = POSTPROCESSOR_FILTERS_KEYS
    _filters_map: typing.Optional[
        typing.Dict[str, Filter]
        ] = {}

    @classmethod
    def filters(cls) -> typing.List[Filter]:
        return [*cls._filters_map.values()]

    @classmethod
    def add_filter(
            cls,
            key: str,
            new_filter: Filter
            ) -> None:

        if cls._is_filter(new_filter) and cls._has_such_filter_key(key):
            cls._filters_map[key] = cls._filters_map.get(key, new_filter)
        else:
            raise Exception('PostProcessorError')

    @classmethod
    def _has_such_filter_key(cls, key: str) -> bool:
        return key in cls._keys

    @classmethod
    def _is_filter(cls, new_filter: Filter) -> bool:
        return issubclass(new_filter, Filter)

    @classmethod
    def make_command_from(
            cls,
            cmd_template: CommandTemplate
            ) -> TerminalCommand:

        cmd_chops = {}
        if cls.filters():
            cmd_chops = cls._template_to_dict(cmd_template)

        new_chops = {}
        for key, val in cmd_chops.items():
            _filter = cls._filters_map.get(key)
            if _filter:
                try:
                    prepared = _filter.prepare(val)
                    if isinstance(prepared, list):
                        cmd_chops[key] = prepared
                    elif isinstance(prepared, dict):
                        k, v = cls._parse_dict(prepared)
                        new_chops[k] = new_chops.get(k, v)
                    else:
                        pass
                except FilterError:
                    pass
            else:
                pass

        cmd_chops.update(new_chops)
        if cmd_chops:
            return TerminalCommand(**cmd_chops)

    @staticmethod
    def _parse_dict(
            item: typing.Dict[str, str]
            ) -> typing.Tuple[str, str]:

        parsed = ((k, v) for k, v in item.items())
        return next(parsed)

    @staticmethod
    def _template_to_dict(
            template: CommandTemplate
            ) -> typing.Dict[str, str]:
        try:
            return dataclasses.asdict(template)
        except TypeError as e:
            raise PostprocessorError from e


def read_terminal_cmd(
        *,
        invoke_symb: str = DEFAULT_INVOKE_SYMB,
        pass_symb: str = PASS_SYMB
        ) -> str:
    """Read raw command (str) from terminal.
       Enter -> go to new line.
       """

    min_symb_cnt = 1

    if not invoke_symb:
        raise Exception('No invoke symbol.')

    raw_cmd = input(invoke_symb)
    if len(raw_cmd) > min_symb_cnt:
        return raw_cmd.strip()
    else:
        return raw_cmd


def check_command_subscribed(
        cmd: TerminalCommand,
        controllers: typing.Dict[str, typing.Callable[..., None]]
        ) -> None:
    """validate current cmd
       or raise SystemValidationError().
       """
    correct_cmd_type = isinstance(cmd, TerminalCommand)
    if correct_cmd_type:
        cmd_registered = cmd.cmd in controllers
        if not all((correct_cmd_type, cmd_registered)):
            msg = 'Cmd validation failed. Correct type: {}, registered: {}.'
            raise SystemValidationError(
                    msg.format(correct_cmd_type, cmd_registered)
                    )
