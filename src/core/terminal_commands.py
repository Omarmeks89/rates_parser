import functools
import typing
import enum
import os

from .io_adapters import (
                FileReaderInterface,
                FileWriterInterface,
                )
from .sys_constants import SysCommandType


ExtFileDriver: typing.TypeAlias = object


_PASS: bool = True
_VALID: bool = True

# cmd descr: ~$ loadfile [ path ] [ --flag ] [ name ]
# ~$ loadfile /home/my_dir/data.xlsx --m [ --r ] tempname
LOADFILE: typing.Final[str] = 'loadfile'
SAVEFILE: typing.Final[str] = 'savefile'
SHOWPREV: typing.Final[str] = 'showprev'

ExtFileDriver: typing.TypeAlias = object
ExtFileReader: typing.TypeAlias = object
ExtFileWriter: typing.TypeAlias = object


class ValidationError(BaseException):
    pass


class CommandParams(str, enum.Enum):
    PATH: str = 'path'
    FLAG: str = 'flag'
    FNAME: str = 'fname'
    SUFFIX: str = 'suffix'


class CommandFlag(str, enum.Enum):
    MULTY: str = '--m'
    RAIL: str = '--r'


class CmdKey(str, enum.Enum):
    LOADFILE: str = LOADFILE
    SAVEFILE: str = SAVEFILE
    SHOWPREV: str = SHOWPREV


_FLAGS: typing.Dict[str, typing.Callable] = {}
_SUBCRIBED_READERS: typing.Dict[str, typing.Any] = {}
_SUBCRIBED_WRITERS: typing.Dict[
                        str,
                        typing.Tuple[
                            ExtFileDriver,
                            ExtFileWriter,
                            ]
                        ] = {}
_REQUIRED_CMD_ARGS = {
        LOADFILE: (
            CommandParams.PATH,
            CommandParams.FLAG,
            CommandParams.FNAME,
            CommandParams.SUFFIX
            ),
        SAVEFILE: (
            CommandParams.FNAME,
            CommandParams.SUFFIX
            ),
        SHOWPREV: (
            CommandParams.FNAME
            )
        }


def _path_exists(path: str, checkable: bool) -> bool:
    return os.path.exists(path) if checkable else _PASS


def _check_fname(fname: list, checkable: bool) -> bool:
    valid = isinstance(fname, list) and fname
    return valid if checkable else _PASS


def _get_io_handlers(f_suff: str, _t: SysCommandType) -> typing.Callable:
    if _t == SysCommandType.IO_READ:
        return lambda x, y: get_readers_repo().get(x) if y else _PASS
    return lambda x, y: get_writers_repo().get(x) if y else _PASS


_VALIDATORS: typing.Dict[typing.Tuple[str, str], typing.Callable] = {
        CommandParams.PATH: _path_exists,
        CommandParams.FLAG: lambda x, y: flags().get(x) if y else _PASS,
        CommandParams.FNAME: _check_fname,
        CommandParams.SUFFIX: _get_io_handlers,
        }


def get_validator(arg: str, _t: SysCommandType) -> typing.Callable[..., bool]:
    valid_hnd = _VALIDATORS.get(arg)
    if _t in (SysCommandType.IO_READ, SysCommandType.IO_WRITE):
        if valid_hnd is not None:
            return valid_hnd(arg, _t)
    return valid_hnd


def flags() -> typing.Callable:

    def _add_flag(flag: str, item: typing.Any) -> None:
        if flag not in _FLAGS:
            _FLAGS[flag] = item

    def _get(flag: str) -> bool:
        return flag in _FLAGS

    def _get_pattern(flag: str) -> typing.Callable:
        return _FLAGS.get(flag)

    flags.add = _add_flag
    flags.get = _get
    flags.get_pattern = _get_pattern
    return flags


def get_readers_repo() -> typing.Callable:

    def _add_suff(
            suffix: str,
            item: typing.Tuple[
                        ExtFileDriver,
                        FileReaderInterface,
                        ],
            ) -> None:
        if suffix not in _SUBCRIBED_READERS:
            _SUBCRIBED_READERS[suffix] = item

    def _get(suffix: str) -> bool:
        return suffix in _SUBCRIBED_READERS

    def _get_item(suffix: str) -> typing.Tuple[
                                    ExtFileDriver,
                                    FileReaderInterface,
                                    ]:
        """return Driver, Reader for file operations."""
        return _SUBCRIBED_READERS.get(suffix)

    get_readers_repo.add = _add_suff
    get_readers_repo.get = _get
    get_readers_repo.get_pattern = _get_item
    return get_readers_repo


def get_writers_repo() -> typing.Callable:

    def _reg_suff(
            suffix: str,
            item: typing.Tuple[
                        ExtFileDriver,
                        FileWriterInterface,
                        ],
            ) -> None:
        if suffix not in _SUBCRIBED_WRITERS:
            _SUBCRIBED_WRITERS[suffix] = item

    def _get(suffix: str) -> bool:
        return suffix in _SUBCRIBED_WRITERS

    def _get_item(suffix: str) -> typing.Tuple[
                                    ExtFileDriver,
                                    FileWriterInterface,
                                    ]:
        return _SUBCRIBED_WRITERS.get(suffix)

    get_writers_repo.add = _reg_suff
    get_writers_repo.get = _get
    get_writers_repo.get_pattern = _get_item
    return get_writers_repo


def check_load_path_exists(
        path: str
        ) -> bool:
    return os.path.exists(path)


def get_required_args(
        cmd_name: str
        ) -> typing.List[str]:
    return _REQUIRED_CMD_ARGS.get(cmd_name)


class command_validator:

    fail_message: str = 'Arg <{}> have invalid value: <{}>. '\
                        'Check required command parameters.'

    def __init__(
            self,
            sys_task_type: SysCommandType,
            /,
            check_mode: bool = False,
            check_path: bool = False,
            check_flag: bool = False,
            check_args: bool = False,
            check_suffix: bool = False
            ) -> None:
        self._t_type = sys_task_type
        self.mode = check_mode
        self.path = check_path
        self.flag = check_flag
        self.args = check_args
        self.suffix = check_suffix

    def __call__(self, command: type) -> typing.Callable:
        functools.wraps(command)

        def _wrapper(*args, **kwargs) -> object:
            all_valid = []
            invalid = []
            empty_str = ''
            if args:
                self._validate_cmd_args_types(command, args)
            elif kwargs:
                self._validate_cmd_kwargs_types(command, kwargs)

            cmd = command(*args, **kwargs)
            checked_args = self._find_required_args_for_check(cmd.name)
            if isinstance(checked_args, tuple) and not checked_args:
                all_valid.append(_PASS)
            for arg in checked_args:
                value = getattr(cmd, arg)
                validator = get_validator(arg, self._t_type)
                contr = self.__dict__.get(arg)
                is_valid = validator(value, contr) if validator else True

                if is_valid:
                    all_valid.append(is_valid)
                else:
                    not_valid = is_valid
                    msg = self.fail_message.format(arg, value)
                    invalid.append(msg)
                    all_valid.append(not_valid)

            if all(all_valid):
                return cmd
            del cmd
            msg = empty_str.join(invalid)
            raise ValidationError(msg)

        _wrapper.__name__ = command.__name__
        return _wrapper

    def _validate_cmd_args_types(
            self,
            cmd: type,
            args: typing.Tuple[typing.Any]
            ) -> None:
        msg = None
        cmd_value = None
        arg_type = None
        args_max_index = len(args) - 1
        for idx, arg in enumerate(cmd.__annotations__):
            if idx <= args_max_index:
                cmd_value = args[idx]
            arg_type = cmd.__annotations__[arg]
            if not isinstance(cmd_value, arg_type):
                if cmd_value is None:
                    msg = f'AttributeError. Wished arg <{arg}> not found. '\
                          f'Item: <class "{cmd.__name__}".'
                else:
                    msg = f'TypeError. Type {type(cmd_value)} '\
                          f'of arg <{arg}>, expected {arg_type}.'\
                          f'Creation command <class "{cmd.__name__}"> failed.'
                raise ValidationError(msg)

    def _validate_cmd_kwargs_types(
            self,
            cmd: type,
            kwargs: typing.Dict[typing.Any, typing.Any]
            ) -> None:
        msg = None
        for arg, arg_type in cmd.__annotations__.items():
            cmd_value = kwargs.get(arg)
            if not isinstance(cmd_value, arg_type):
                if cmd_value is None:
                    msg = f'AttributeError. Wished arg <{arg}> not found. '\
                          f'Item: <class "{cmd.__name__}".'
                else:
                    msg = f'TypeError. Type {type(cmd_value)} '\
                          f'of arg <{arg}>, expected {arg_type}.'\
                          f'Creation command <class "{cmd.__name__}"> failed.'
                raise ValidationError(msg)

    def _find_required_args_for_check(
            self,
            cmd_name: str
            ) -> None:
        required = get_required_args(cmd_name)
        if required is not None:
            if isinstance(required, tuple):
                return required
            elif isinstance(required, str):
                return (required,)
        msg = f'Expected command name <{cmd_name}> not registered. '\
              f'Use "HELP" to find registered commands.'
        raise ValidationError(msg)


__all__ = [
        'ValidationError',
        'flags',
        'get_readers_repo',
        'command_validator',
        'CmdKey'
        ]
