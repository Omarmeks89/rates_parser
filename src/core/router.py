import typing
import functools


class ApiRouter:
    """
    Class that set api routing
    by terminal commands names.
    """

    def __init__(self) -> None:
        self._map = {}
        self._logger = None

    def set_logger(self, logger: typing.Any) -> None:
        if hasattr(logger, 'debug'):
            self._logger = logger

    @property
    def configured(self) -> bool:
        return self._map != {}

    @property
    def controllers(self) -> typing.List[str]:
        return list(self._map.keys())

    def route(
            self,
            key: str,
            ) -> typing.Callable[..., typing.Any]:

        if key not in self._map:
            self._map[key] = self._map.get(key, None)
            if self._logger:
                self._logger.warning(f'REGISTERED API HANDLER: {key}.')
            else:
                pass
        _registered_key = key

        def wrapper(
                func: typing.Callable[..., typing.Any]
                ) -> typing.Callable[..., typing.Any]:

            nonlocal _registered_key
            functools.wraps(func)
            if self._map[_registered_key] is None:
                self._map[_registered_key] = func

            def _executor(*args, **kwargs) -> typing.Any:
                nonlocal _registered_key
                executor = self._map[_registered_key]
                return executor(*args, **kwargs)

            return _executor

        return wrapper

    def dispatch(self, key: str, arg: typing.Any) -> None:
        if key in self._map:
            func = self._map[key]
            try:
                func(arg)
            except Exception as e:
                if self._logger:
                    self._logger.critical(e)
                else:
                    print('ERROR: ', e)
