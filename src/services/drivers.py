import typing
import inspect
import abc

import openpyxl as opxl


NEED_COMMENTS = True


class CompilerError(Exception):
    pass


class DriverError(Exception):
    pass


class LoaderConfigError(Exception):
    pass


class _Compiler(abc.ABC):

    @abc.abstractmethod
    def compile_values(self, line: typing.Any) -> typing.NoReturn:
        pass

    @abc.abstractmethod
    def compile_headers(self, line: typing.Any) -> typing.NoReturn:
        pass


class Driver:

    @abc.abstractmethod
    def fetch_values(self, item: typing.Any) -> typing.NoReturn:
        pass

    @abc.abstractmethod
    def fetch_headers(self, item: typing.Any) -> typing.NoReturn:
        pass


class Loader:

    @abc.abstractmethod
    def setup(self, settings: typing.Any) -> typing.NoReturn:
        pass


class BaseLoader(Loader):

    def __init__(self,
                 readers: typing.Callable,
                 flags: typing.Callable) -> None:
        self._readers = readers
        self._flags = flags
        self._settings = None
        self._driver = None
        self._reader = None

    def setup(self, settings: typing.Any) -> None:
        """
        readers.get_pattern -> (driver, reader)
        flags.get_pattern -> func.build() -> types.MappingProxyType.
        Very strange int.
        Have to correct.
        """
        pattern_builder = self._flags.get_pattern(settings.flag)
        if pattern_builder is not None:
            driver, reader = self._readers.get_pattern(settings.suffix)
            self._reader = reader
            self._driver = driver
            self._driver.headers_preset = pattern_builder
            self._settings = settings

    def get_load_sources(self) -> typing.Tuple[
                                    Driver, typing.Callable
                                    ]:
        """Return Driver and func, that read data from reader."""

        reader = self._reader.read(self._settings)

        is_gen = inspect.isgenerator
        is_gen_func = inspect.isgeneratorfunction

        if is_gen(reader) or is_gen_func(reader):
            pass
        else:
            raise LoaderConfigError('Reader isn`t a generator.')

        def load():
            nonlocal reader
            try:
                return next(reader)
            except StopIteration:
                pass

        def stop_loading() -> None:
            nonlocal reader
            try:
                reader.throw(StopIteration)
            except StopIteration:
                pass

        def dummy() -> None:
            """dummy for closure."""
            pass

        dummy.load = load
        dummy.stop_loading = stop_loading
        return self._driver, dummy


class BaseSaver:
    ...


class BaseDriver(Driver):
    """
    TODO make fetch abstract.
    move impl into TxtDriver class.
    """

    def __init__(self,
                 logger: typing.Any,
                 compiler: _Compiler) -> None:
        self._compiler = compiler
        self._logger = logger
        self._headers_preset = None
        self._errors = []

    @property
    def headers_preset(self) -> typing.List[str]:
        """List of headers is a preset."""
        return self._headers_preset

    @headers_preset.setter
    def headers_preset(self, preset: typing.List[str]) -> None:
        # validate
        self._headers_preset = preset

    def fetch_values(self, item: str) -> typing.List[str]:
        """Fetch parts of data using compilers .txt.
           Try to clean code, delete flag from args."""

        self.validate(item)

        values = []
        for idx, header in enumerate(self._headers_preset):
            self._compiler.pattern = self._headers_preset[header]
            fetched_value = None
            try:
                fetched_value = self._compiler.compile_values(item)
            except CompilerError as e:
                err_msg = f'Expected error: {e} on pos {idx}, item: {header} '\
                          f'line:\n\t{item}.\n'
                self._errors.append(err_msg)

            self._logger.warning(fetched_value)
            if fetched_value is None:
                msg = f'[-] Value for header <{header}> not found. '\
                      f'Check with exact file. Header pos: {idx}.'
                fetched_value = msg

            values.append(fetched_value)

        self._handle_errors()
        return values

    def fetch_headers(
            self,
            item: str
            ) -> typing.List[str]:

        self.validate(item)

        headers = []
        for idx, header in enumerate(self._headers_preset):
            self._compiler.pattern = self._headers_preset[header]
            fetched_header = None
            try:
                fetched_header = self._compiler.compile_headers(item)
            except CompilerError as e:
                self._errors.append(e)

            if fetched_header is None:
                fetched_header = header

            headers.append(fetched_header.upper())

        self._handle_errors()
        return headers

    def validate(self, item: str) -> None:
        if not isinstance(item, str):
            err_msg = f'Unsupportable item type: {type(item)}, expected <str>.'
            self._logger.warning(err_msg)
            raise DriverError(err_msg)

    def _handle_errors(self) -> None:
        if self._errors:
            for e in self._errors:
                self._logger.warning(e)


class ExcelDriver(BaseDriver):

    def __init__(self,
                 logger: typing.Any,
                 compiler: _Compiler) -> None:
        super().__init__(logger, compiler)
        self._positions_preset = None

    def validate(self, item: tuple) -> None:
        if not isinstance(item, tuple):
            err_msg = f'Unsupportable type: {type(item)}, expected <tuple>.'
            self._logger.warning(err_msg)
            raise DriverError(err_msg)

    def fetch_values(self, item: tuple) -> typing.List[str]:

        self.validate(item)

        value = []
        self._compiler.set_pattern((NEED_COMMENTS, self._positions_preset))
        try:
            value = self._compiler.compile_values(item)
        except CompilerError as e:
            self._errors.append(e)
            self._logger.warning(e)

        self._handle_errors()
        return value

    def fetch_headers(self, item: tuple) -> typing.List[str]:

        self.validate(item)
        headers_preset = list(self._headers_preset)

        header = []
        self._compiler.set_pattern((NEED_COMMENTS, headers_preset))
        self._logger.debug(f'compiler pattern = {self._compiler.pattern}')
        try:
            positions, header = self._compiler.compile_headers(item)
            if len(positions) == len(headers_preset):
                if not self._positions_preset:
                    self._positions_preset = positions
            self._logger.warning(f'position {positions} != {header}')
        except CompilerError as e:
            msg = f'Location {self.__class__.__name__}, err: {e}'
            self._errors.append(e)
            self._logger.warning(msg)
        self._handle_errors()
        if self._have_all_required_headers(
                headers_preset,
                header,
                ):
            return header
        err_msg = f'Fetched: {header} don`t '\
                  f'match to required: {headers_preset}'
        raise DriverError(err_msg)

    def _have_all_required_headers(
            self,
            required: typing.List[str],
            fetched: typing.List[str]
            ) -> bool:
        matched = []
        for idx, i in enumerate(required):
            try:
                matched.append(fetched[idx] == i)
            except IndexError:
                matched.append(False)
        return True if all(matched) else False


class BaseTxtCompiler(_Compiler):

    def __init__(self) -> None:
        self._pattern = None

    @property
    @abc.abstractmethod
    def pattern(self) -> typing.NoReturn:
        pass

    @pattern.setter
    @abc.abstractmethod
    def pattern(self, value) -> typing.NoReturn:
        pass

    def compile_values(self, item: str) -> str:
        """Fetch data from string using re.Pettern in self.patten."""

        compiled_success = False
        for pattern in self.pattern:
            compiled = pattern.match(item)
            if compiled:
                compiled_success = True
                compiled = compiled.groupdict()
                value = (_v for _, _v in compiled.items())
                return next(value)
        if not compiled_success:
            err_msg = f'Unknown item format: {item} '\
                      f'{self.__class__.__name__} can`t parse it.'\
                      f'\nCurrent pattern: {pattern}.'
            raise CompilerError(err_msg)

    def compile_headers(
            self,
            item: str
            ) -> str:
        """Fetch data from string using re.Pettern in self.patten."""

        for pattern in self.pattern:
            compiled = pattern.match(item)
            if compiled:
                compiled = compiled.groupdict()
                header = (_h.upper() for _h in compiled)
                return next(header)
            else:
                err_msg = f'Unknown item format: {item} '\
                          f'{self.__class__.__name__} can`t parse it.'\
                          f'\nCurrent pattern: {self.pattern}.'
                raise CompilerError(err_msg)


class BaseExcelCompiler(_Compiler):
    """
    Base class for Excel like files compilers.
    Pattern here - bool value (for fetching comments)
    and int value (headers idx / pos).
    """
    def __init__(self) -> None:
        self._pattern = None

    @property
    @abc.abstractmethod
    def pattern(self) -> typing.NoReturn:
        """
        Bool value - need_comment;
        int value - headers row position (1st by default)
        """
        pass

    def set_pattern(self, pattern: typing.Any) -> None:
        self._pattern = pattern

    def compile_values(self, item: tuple) -> typing.List[str]:
        need_comment, headers_pos = self.pattern
        if headers_pos is None:
            msg = 'No headers positions found.'
            raise CompilerError(msg)
        values = []
        comments = []
        separator = ' '

        for idx in headers_pos:
            cell = item[idx]
            value = self._convert_value(cell)
            values.append(value)
            if need_comment:
                comment = self._fetch_comment(cell)
                if comment:
                    comments.append(comment)

        if need_comment:
            comment = separator.join(comments)
            values.append(comment)

        return values

    def compile_headers(self, item: tuple) -> typing.List[str]:
        need_comment, headers_names = self.pattern
        headers = []
        positions = []

        for idx, cell in enumerate(item):
            header = cell.value
            if header:
                header = header.upper()
                if header in headers_names:
                    positions.append(idx)
                    headers.append(header)
            else:
                err_msg = f'Invalid header on pos: {idx}.'
                raise CompilerError(err_msg)

        if need_comment:
            headers.append('comments'.upper())

        return positions, headers

    def _fetch_comment(
            self,
            cell: opxl.cell
            ) -> typing.Optional[str]:

        if hasattr(cell, 'comment'):
            comment = cell.comment
            if comment:
                text, author = comment.text, comment.author
                comm_body = f'[+] {text.strip()}'\
                            f'[Author: {author.strip()}]'
                return comm_body
        return ''

    def _convert_value(self, cell: opxl.cell) -> str:
        value = cell.value
        return value


class ExcelCompiler(BaseExcelCompiler):

    @property
    def pattern(self) -> typing.Tuple[bool, int]:
        return self._pattern


class TxtCompiler(BaseTxtCompiler):

    @property
    def pattern(self) -> typing.Any:
        return self._pattern

    @pattern.setter
    def pattern(self, value: typing.Any) -> None:
        self._pattern = value
