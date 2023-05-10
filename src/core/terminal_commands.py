import functools
import typing
import enum
import os


_PASS: bool = True
_VALID: bool = True


LOADFILE: typing.Final[str] = 'loadfile'
SAVEFILE: typing.Final[str] = 'savefile'
SHOWPREV: typing.Final[str] = 'showprev'


class ValidationError(BaseException):
    pass


class CommandParams(enum.Enum):
    PATH: str = 'path'
    FLAG: str = 'flag'
    FNAME: str = 'fname'
    SUFFIX: str = 'suffix'


class CommandFlag(enum.Enum):
    MULTY: str = '--m'
    RAIL: str = '--r'


class CmdKey(enum.Enum):
    LOADFILE: str = LOADFILE
    SAVEFILE: str = SAVEFILE
    SHOWPREV: str = SHOWPREV


_FLAGS: typing.Dict[str, typing.Callable] = {}
_SUFFIXES: typing.Dict[str, typing.Any] = {}
_REQUIRED_CMD_ARGS = {
        LOADFILE: (
            CommandParams.PATH.value,
            CommandParams.FLAG.value,
            CommandParams.FNAME.value,
            CommandParams.SUFFIX.value
            ),
        SAVEFILE: (
            CommandParams.FNAME.value,
            CommandParams.SUFFIX.value
            ),
        SHOWPREV: (
            CommandParams.FNAME.value
            )
        }


def _path_exists(path: str, checkable: bool) -> bool:
    return os.path.exists(path) if checkable else _PASS


def _check_fname(fname: list, checkable: bool) -> bool:
    valid = isinstance(fname, list) and fname
    return valid if checkable else _PASS


_VALIDATORS: typing.Dict[typing.Tuple[str, str], typing.Callable] = {
        CommandParams.PATH.value: _path_exists,
        CommandParams.FLAG.value: lambda x, y: flags().get(x) if y else _PASS,
        CommandParams.FNAME.value: _check_fname,
        CommandParams.SUFFIX.value: lambda x, y: suffixes().get(x) if y else _PASS
        }


def get_validator(arg: str) -> typing.Callable[..., bool]:
    return _VALIDATORS.get(arg)


def flags() -> typing.Callable:

    def _add_flag(flag: str, item: typing.Any) -> None:
        if flag not in _FLAGS:
            _FLAGS[flag] = item

    def _get(flag: str) -> bool:
        return flag in _FLAGS

    def _get_pattern(flag: str) -> typing.Any:
        return _FLAGS.get(flag)

    flags.add = _add_flag
    flags.get = _get
    flags.get_pattern = _get_pattern
    return flags


def suffixes() -> typing.Callable:

    def _add_suff(suffix: str, item: typing.Any) -> None:
        if suffix not in _SUFFIXES:
            _SUFFIXES[suffix] = item

    def _get(suffix: str) -> bool:
        return suffix in _SUFFIXES

    def _get_item(suffix: str) -> typing.Any:
        return _SUFFIXES.get(suffix)

    suffixes.add = _add_suff
    suffixes.get = _get
    suffixes.get_pattern = _get_item
    return suffixes


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
            *,
            check_mode: bool = False,
            check_path: bool = False,
            check_flag: bool = False,
            check_args: bool = False,
            check_suffix: bool = False
            ) -> None:
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
                validator, contr = get_validator(arg), self.__dict__.get(arg)
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
        'suffixes',
        'command_validator',
        'CmdKey'
        ]
