import typing
import collections


class SettingsFactoryError(Exception):
    pass


class PreviewFactoryError(Exception):
    pass


class ExcelSheetStruct(typing.NamedTuple):
    name: str
    headers: typing.Tuple[str]
    values: typing.Optional[typing.Tuple[typing.Tuple[str]]] = tuple()


class SheetPreviewSettings(typing.NamedTuple):
    headers_cnt: int
    cols_width: typing.List[int]
    table_width: int
    sourse_hash: int


class PreviewFactory:

    _empty: typing.Final[str] = ''
    _border_symb: typing.Final[str] = '|'
    _separator: typing.Final[str] = '+'
    _horiz_border_symb: typing.Final[str] = '-'

    def __init__(self) -> None:
        self._interm_border = None
        self._main_border = None
        self._title = None
        self._strings = []
        self._chops = []

    @property
    def preview(self) -> typing.Generator:
        return (r for r in self._strings)

    @staticmethod
    def pair_is_valid(data_struct: ExcelSheetStruct,
                      settings: SheetPreviewSettings) -> bool:
        return hash(data_struct) == settings.sourse_hash

    def create_preview(self,
                       data_struct: ExcelSheetStruct,
                       settings: SheetPreviewSettings) -> None:
        if self._chops and self._strings:
            self._delete_previous_settings()

        cols_width, new_table_width = settings.cols_width, settings.table_width
        self._create_empty_queues_for_chops(settings.headers_cnt)
        self._build_intermediate_border(cols_width)
        self._build_main_border(new_table_width)

        if data_struct.name:
            self._build_title(data_struct.name, new_table_width)
        else:
            default_name = 'Default name'
            self._build_title(default_name, new_table_width)

        rows = (data_struct.headers, *data_struct.values)
        try:
            self._build_columns_from(rows, cols_width)
        except IndexError as error:
            raise PreviewFactoryError(error)

    def _delete_previous_settings(self) -> None:
        for arg in self.__dict__:
            if issubclass(arg, typing.Iterable):
                arg.clear()
            else:
                arg = None

    def _create_empty_queues_for_chops(self, count: int) -> None:
        for _ in range(count):
            queue = collections.deque()
            self._chops.append(queue)

    def _build_main_border(self, width: int) -> None:
        _sp = self._separator
        string = f'{_sp}{self._horiz_border_symb * width}{_sp}'
        self._main_border = string

    def _build_title(self, name: str, width: int) -> None:
        self._create_title_line(name, width)
        self._strings.append(self._main_border)
        self._strings.append(self._title)

    def _create_title_line(self, name: str, width: int) -> None:
        _brd = self._border_symb
        self._title = f'{_brd}{name.center(width)}{_brd}'

    def _build_columns_from(self,
                            rows: typing.Tuple[tuple],
                            rows_width: typing.Tuple[int]) -> typing.Any:
        self._strings.append(self._interm_border)
        for row in rows:
            self._generate_row_strings(row, rows_width)
            self._strings.append(self._interm_border)

    def _build_intermediate_border(self, cols_width: tuple) -> None:
        line = []
        for width in cols_width:
            string = f'{self._separator}{self._horiz_border_symb * width}'
            line.append(string)
        line.append(self._separator)
        self._interm_border = self._empty.join(line)

    def _generate_row_strings(self,
                              row: typing.Tuple[str],
                              cells_width: typing.Tuple[int]) -> None:
        for idx, value in enumerate(row):
            width = cells_width[idx]
            self._separate_to_chops_recursively(idx, value, width)
        while any(self._chops):
            line = []
            for idx, queue in enumerate(self._chops):
                cell_width = cells_width[idx]
                if queue:
                    chop = queue.popleft()
                else:
                    chop = self._make_string_from(cell_width, self._empty)
                line.append(chop)
            else:
                line.append(self._border_symb)
                line = self._empty.join(line)
                self._strings.append(line)

    def _separate_to_chops_recursively(self,
                                       pos: int,
                                       value: str,
                                       cell_width: int) -> None:
        fill, chop = self._separate_line_to_chops(cell_width, value)
        string = self._make_string_from(cell_width, fill)
        self._chops[pos].append(string)
        if len(chop) <= cell_width:
            if not chop:
                return
            chop_str = self._make_string_from(cell_width, chop)
            self._chops[pos].append(chop_str)
        else:
            self._separate_to_chops_recursively(pos, chop, cell_width)

    def _separate_line_to_chops(self, max_pos: int, line: str) -> tuple:
        return line[:max_pos], line[max_pos:]

    def _make_string_from(self, cell_width: int, string: str) -> str:
        if len(string) == cell_width:
            return f'{self._border_symb}{string.center(cell_width)}'
        return f'{self._border_symb}{string.ljust(cell_width)}'


class PreviewSettingsFactory:

    _cell_min_width_symbols: typing.Final[int] = 6
    _min_header_indent: typing.Final[int] = 2

    def __init__(self) -> None:
        self._columns_width = []
        self._table_width = 0
        self._headers_cnt = 0
        self._sourse_hash = None

    def __repr__(self) -> str:
        return f'w:{self._table_width}, '\
               f'hc:{self._headers_cnt}, '\
               f'cw:{self._columns_width}, '\
               f'hash:{self._sourse_hash}.'

    @property
    def preview_settings(self) -> SheetPreviewSettings:
        if not all((self._columns_width, self._table_width,
                    self._headers_cnt, self._sourse_hash)):
            raise SettingsFactoryError('Settings don`t created.')

        return SheetPreviewSettings(headers_cnt=self._headers_cnt,
                                    cols_width=self._columns_width,
                                    table_width=self._table_width,
                                    sourse_hash=self._sourse_hash)

    def calculate_preview_settings(self, sheet: ExcelSheetStruct) -> None:
        try:
            self._calculate_preview_dimentions(sheet)
            self._sourse_hash = hash(sheet)
        except (Exception, BaseException) as err:
            msg = f'Invalid format {sheet},\nraised {err}'
            raise SettingsFactoryError(msg)

    def sheet_is_valid(self, sheet: ExcelSheetStruct) -> bool:
        headers_count = len(sheet.headers)
        if sheet.values:
            return all(
                    (self._validate_headers(sheet.headers),
                     self._validate_row_lenght(headers_count, sheet.values),
                     sheet.name)
                    )
        else:
            return all((self._validate_headers(sheet.headers), sheet.name))

    def _validate_headers(self, _h: typing.Tuple[str]) -> bool:
        return all(_h)

    def _validate_row_lenght(self, cnt: int, rows: typing.Tuple[str]) -> bool:
        rows_are_valid = tuple(len(row) == cnt for row in rows)
        return all(rows_are_valid)

    def _calculate_preview_dimentions(self, sheet: ExcelSheetStruct) -> None:
        self._calculate_table_width(sheet.headers)
        header_width = len(sheet.name)

        if self._table_width < header_width:
            width_difference = (header_width - self._table_width) // 2
            diff = self._calculate_prime_difference(width_difference)
            if diff < self._min_header_indent:
                self._table_width += self._min_header_indent * 2
            else:
                self._table_width += diff * 2
        else:
            diff = self._table_width - header_width
            if diff < self._min_header_indent:
                self._table_width += self._min_header_indent * 2
            else:
                diff = (diff // 2) * 2
                self._table_width += diff

        self._headers_cnt = len(sheet.headers)
        self._rows_cnt = len(sheet.values)
        self._recalculate_row_width()

    def _calculate_prime_difference(self, _wd: int) -> int:
        return _wd if _wd % 2 else _wd + 1

    def _recalculate_row_width(self) -> None:
        pointer, max_col_index = 0, len(self._columns_width) - 1
        row_width = self._table_width - (self._headers_cnt - 1)

        diff = row_width - sum(self._columns_width)
        add_align = diff // self._headers_cnt

        while pointer <= max_col_index:
            if pointer == max_col_index:
                self._columns_width[pointer] += diff - (add_align * pointer)
            else:
                self._columns_width[pointer] += add_align
            pointer += 1

    def _calculate_table_width(self, headers: typing.Tuple[str]) -> None:
        for header in headers:
            header_width = self._set_correct_column_width(len(header))
            self._columns_width.append(header_width)
            self._table_width += header_width
        self._table_width += len(headers) - 1

    def _set_correct_column_width(self, col_width: int) -> int:
        if col_width >= self._cell_min_width_symbols:
            return col_width
        return self._cell_min_width_symbols
