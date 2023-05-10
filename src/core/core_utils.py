import typing
import logging
import abc
import functools


class InvalidLogLevel(Exception):
    pass


class BaseLogFactory(abc.ABC):

    def __init__(self, settings: typing.NamedTuple) -> None:
        self._settings = settings

    def get_logger(self) -> typing.Any:
        logger = self._create_logger()
        return logger

    @abc.abstractmethod
    def _create_logger(self) -> typing.NoReturn:
        """Have to override this method."""
        pass


class ProxyLogger:

    _base_log_level: typing.Final[str] = 'debug'
    _exp_proxy_cls: BaseException = BaseException
    _exp_proxy_msg: str = 'Reraised Exception: {}'

    def __init__(self, _log: logging.Logger) -> None:
        self._log = _log
        self._log_method = None

    def __repr__(self) -> str:
        name = self.__class__.__name__
        _m = self._log_method
        return f'LogProxy {name}, logger: {self._log}, method: {_m}'

    def log(self, *, level: typing.Optional[str] = None) -> typing.Callable:
        if level is not None:
            self._set_wrapper_loglevel(level)
            self._log.debug(f'Registered {self._log_method} as exp logmethod')

        def wrapper(func: typing.Callable[..., typing.Any]) -> typing.Callable:
            @functools.wraps(func)
            def inner(*args, **kwargs) -> typing.Any:
                try:
                    return func(*args, **kwargs)
                except (Exception, BaseException) as exp:
                    if self._log_method is not None:
                        self._log_method(exp)
                    else:
                        self._log.warning(exp)
                    log_message = self._build_log_message(exp, args, kwargs)
                    exp_proxy = self._generate_exception_proxy(exp)
                    raise exp_proxy(log_message) from exp
            self._log.debug(f'Registered method: {func.__name__}.')
            return inner
        return wrapper

    def _build_log_message(self, _exp: typing.Any, /, *args, **kwargs) -> str:
        msg = 'Expected {}, payload: args={}, kwargs={}'
        return msg.format(_exp, args, kwargs)

    def _set_wrapper_loglevel(self, level: str) -> None:
        try:
            self._is_loglevel_valid(level)
            self._log_method = self._get_loglevel_method(level)
        except InvalidLogLevel as error:
            self._log.warning(error)
            msg = self._exp_proxy_msg.format(error)
            exp_proxy = self._generate_exception_proxy(error)
            raise exp_proxy(msg) from error

    def _get_loglevel_method(self, level: str) -> typing.Callable:
        return getattr(self._log, level)

    def _is_loglevel_valid(self, level: str) -> None:
        if not isinstance(level, str) or not hasattr(self._log, level):
            raise InvalidLogLevel(f'Type {type(level)} not allowed.')

    def _generate_exception_proxy(self, _err: typing.Any) -> BaseException:
        err_name = f'{type(_err).__name__}'
        return type(err_name, (self._exp_proxy_cls,), {'value': _err})


class BaseLogger:

    def __init__(self, settings: typing.Any) -> None:
        logging.basicConfig(level=settings.log_level,
                            format=settings.fmt)
        self._name = settings.name

    @property
    def get_logger(self) -> logging.Logger:
        return logging.getLogger(self._name)
