import typing
import enum
import collections

import core.text_utils as t_ut
from core.domain_models import TableSheetModel
from services.preview_builders import ExcelSheetStruct  # TODO delete it


NEW_LINE_SYMB: typing.Final[str] = '\n'
TAB_SYMB: typing.Final[str] = '\t'

NEW_LINE_REPLACE: typing.Final[str] = '. '
TAB_REPLACE: typing.Final[str] = ' '

REPLACED_SYMBOLS: typing.List[str] = [
        NEW_LINE_SYMB,
        TAB_SYMB
        ]
NEW_SYMBOLS: typing.List[str] = [
        NEW_LINE_REPLACE,
        TAB_REPLACE
        ]


class TemplateError(Exception):
    pass


class InvalidRowValues(Exception):
    pass


class RowCompilerError(Exception):
    pass


class ValueCache:

    def __init__(self) -> None:
        self._items_map = {}

    def update(
            self,
            values: typing.List[str],
            *,
            fill_none: bool = False
            ) -> None:
        """If fill_none = True, it will replaced None
        in current values on previous values.
        """
        for idx, item in enumerate(values):
            if not self._items_map:
                self._items_map[idx] = self._items_map.get(idx, item)
            else:
                if fill_none:
                    if item is None:
                        # TODO None as str() is awful...
                        # TODO decide how to use None.
                        values[idx] = self._items_map[idx]
                    else:
                        self._items_map[idx] = item


class _CellValueCleaner:
    """
    Class, that replace control sequences like
    '\n' or '\t' to wished symbol.
    """

    def __init__(
            self,
            subs: typing.List[str],
            repl: typing.List[str]
            ) -> None:
        self._subs = subs
        self._repl = repl
        self._repl_map = t_ut.create_replace_map(
                self._subs,
                self._repl
                )

    def clean_values(
            self,
            values: typing.List[str],
            *,
            max_item: int = 10
            ) -> typing.Tuple[typing.Tuple[str]]:
        result = []
        # TODO how to set max_preview_lines from outside?
        max_item = max_item if isinstance(max_item, int) else 10
        for idx, val in enumerate(values):
            if idx <= max_item:
                cleaned = self._clean(val.values)
                result.append(cleaned)
            else:
                break
        return tuple(result)

    def _clean(self, values: typing.List[str]) -> typing.Tuple[str]:
        result = []
        for val in values:
            if val is not None:
                try:
                    cleaned = t_ut.replace_control_sequences(
                            self._repl_map,
                            val
                            )
                    result.append(cleaned)
                except (Exception, BaseException):
                    result.append(self._stringify(val))
            else:
                result.append(self._stringify(val))
        return tuple(result)

    def _stringify(self, value: typing.Any) -> str:
        return f'{value}'


class _RowCompiler:

    @classmethod
    def make_compiler(
            cls,
            columns: typing.List[typing.List[str]]
            ) -> '_RowCompiler':
        if not columns:
            raise RowCompilerError('No rows for compile.')
        return cls(columns)

    def __init__(
            self,
            columns: typing.List[str]
            ) -> None:
        self._columns = columns
        self._result = []

    @property
    def count(self) -> int:
        count = 1
        for i in self._columns:
            res = count * len(i)
            count = res
        return count

    def _generate_columns(self) -> typing.List[typing.List[str]]:
        arr = self._columns
        part = []
        y = None
        count = self.count
        delta = count
        arr_range = len(arr)
        max_idx = arr_range - 1
        for idx in range(arr_range):
            if idx == max_idx:
                column = arr[idx] * (count // len(arr[idx]))
                self._result.append(column)
            else:
                x = delta // len(arr[idx])
                if y is None:
                    y = x
                column_part = [[i] * x for i in arr[idx]]
                for i in column_part:
                    part.extend(i)
                column = []
                if len(part) * (y // x) != count:
                    column = part * (count // len(part))
                else:
                    column = part * (y // x)
                self._result.append(column)
                delta = x
                part.clear()

    def rows(self) -> typing.List[str]:
        self._generate_columns()
        pos = 0
        max_idx = len(self._result[pos]) - 1
        arr_range = len(self._result)
        while pos <= max_idx:
            line = [self._result[i][pos] for i in range(arr_range)]
            pos += 1
            yield line


class _StringArrayDropper:
    """
    Class, that convert array like a/b/c
    to ['a', 'b', 'c'].
    """
    def __init__(
            self,
            ) -> None:
        self._checked = []
        self._columns = []

    @property
    def array_slice(self) -> typing.Tuple[int]:
        if self._checked:
            return min(self._checked), max(self._checked) + 1

    @property
    def need_drop(self) -> bool:
        return self._checked != []

    def find_array_positions(
            self,
            array: typing.List[str]
            ) -> typing.Tuple[int]:
        indexes = []
        for idx, item in enumerate(array):
            if self.array_detected(item):
                distance = self.calculate_distance_between_positions(
                        idx,
                        indexes
                        )
                if distance is None or distance == 1:
                    indexes.append(idx)
        return tuple(indexes)

    def array_detected(self, line: str) -> bool:
        return t_ut.detect_array_in_str(line)

    def index_registered(self, idx: int) -> bool:
        return idx in self._checked

    def collect_array_items(
            self,
            line: typing.List[str]
            ) -> typing.Optional[_RowCompiler]:
        """If array like a/b/c founded,
        this element index will be append to
        self._checked.
        TODO rename.
        """
        for idx, item in enumerate(line):
            if idx > 2:
                # TODO how to decide with another values
                # that not match for pattern?
                break
            if self.array_detected(item):
                self._register_item_index(idx)
                if self.index_registered(idx):
                    dropped_array = self.drop_array(item)
                    self._add_column(dropped_array)
        if self.need_drop:
            return _RowCompiler.make_compiler(self._columns)

    def drop_array(self, line: str) -> None:
        return t_ut.convert_str_array_to_list(
                line,
                t_ut.DEFAULT_CLEAN_PATTERN
                )

    def _register_item_index(self, idx: int) -> None:
        if self._checked:
            diff = self._get_last_position_difference(idx)
            if diff != 1:
                return None
        self._checked.append(idx)

    def _get_last_position_difference(self, idx: int) -> int:
        if self._checked:
            return idx - max(self._checked)
        return 1

    def _add_column(self, dropped: typing.List[str]) -> None:
        self._columns.append(dropped)

    @staticmethod
    def calculate_distance_between_positions(
            idx: int,
            indexes: typing.List[int]
            ) -> typing.Optional[int]:
        if indexes:
            return idx - max(indexes)


class TableRow:

    __slots__ = [
            '_rate',
            '_columns',
            '_row'
            ]
    _name = 'Rate'

    def __init__(
            self,
            headers: typing.List[str]
            ) -> None:
        if not all(headers):
            err_msg = f'Some values in {headers} are empty.'
            raise InvalidRowValues(err_msg)
        try:
            self._rate = collections.namedtuple(
                    self._name,
                    headers
                    )
        except ValueError as e:
            inst_name = self.__class__.__name__
            err_msg = f'Namedtuple error: {e} inside {inst_name}'
            raise InvalidRowValues(err_msg)
        self._columns = 0
        self._row = 0

    @property
    def row(self) -> int:
        return self._row

    @property
    def values(self) -> typing.Generator:
        return (v for v in self._rate)

    @property
    def keys(self) -> typing.Generator:
        return (k for k in self._rate._fields)

    @property
    def columns(self) -> int:
        return self._columns

    def set_values(
            self,
            row: int,
            values: typing.List[str]
            ) -> None:
        """
        Set rate.
        Immutable type.
        """
        err_msg = None
        if self._rate is not None:
            try:
                self._rate = self._rate(*values)
                self._row = row
                self._columns = len(values)
            except TypeError as e:
                err_msg = e
        else:
            if err_msg is None:
                err_msg = 'Failed to set new value for immutable type.'
            raise InvalidRowValues(err_msg)


class SheetTemplate(TableSheetModel):

    class SymbolsGroupPosition(enum.Enum):
        NUMERIC: int = 1
        LITERAL: int = 2

        @classmethod
        def positions(cls) -> typing.Tuple[int]:
            return tuple(
                    sorted(
                        (cls.__dict__[i].value for i in cls._member_names_),
                        reverse=True
                       )
                    )

        @classmethod
        def make_order(cls) -> t_ut.SymbolsGroupOrder:
            positions = cls.positions()
            return t_ut.SymbolsGroupOrder(positions)

    _groups = SymbolsGroupPosition

    def __init__(
            self,
            name: str,
            ) -> None:
        self._name = name
        self._events = collections.deque()
        self._headers: typing.Optional[TableRow] = None
        self._values: typing.Optional[
                typing.List[TableRow]
                ] = []
        self._rows_count = 0
        self._cache = ValueCache()
        self._cleaner = _CellValueCleaner(
                REPLACED_SYMBOLS,
                NEW_SYMBOLS
                )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__} {self._rows_count}.'

    @property
    def name(self) -> str:
        return self._name

    @property
    def empty(self) -> bool:
        return self._headers is None

    @property
    def rows_count(self) -> int:
        return self._rows_count

    @property
    def events(self) -> typing.List:
        events_cnt = len(self._events)
        return [
                self._events.popleft()
                for _ in range(events_cnt)
                ]

    @property
    def get_sheet_struct(self) -> ExcelSheetStruct:
        headers = tuple(self._headers.values)
        if self._values is not None:
            cleaned_values = self._cleaner.clean_values(self._values)
            return ExcelSheetStruct(name=self._name,
                                    headers=headers,
                                    values=cleaned_values)
        else:
            return ExcelSheetStruct(name=self._name,
                                    headers=headers)

    @property
    def rows(self) -> typing.Generator:
        """
        Return generator that return list[str] at each iteration.
        """

        return (
                [*v.values] for v in (self._headers, *self._values)
                )

    def validate(
            self,
            values: typing.List[str]
            ) -> bool:
        """
        method for validating values, when headers created.
        If no headers registered - returned False.
        """
        if self.empty:
            return False
        return self._headers.columns == len(values)

    def add_headers(self, headers: typing.List[str]) -> None:
        self._reorder_headers(headers)
        try:
            table_row = TableRow(headers)
            table_row.set_values(
                    self._rows_count,
                    headers
                    )
            self._headers = table_row
        except InvalidRowValues as e:
            print(e)
        except (Exception, BaseException) as err:
            print(f'Unexpected Exception: {err}')

    def _reorder_headers(
            self,
            headers: typing.List[str]
            ) -> typing.List[str]:
        """Change srt "20ft" to "ft20"
        """
        order = self._groups.make_order()
        for idx, value in enumerate(headers):
            headers[idx] = order.reorder(
                    t_ut.DEFAULT_NUMERICS_ORDER,
                    value
                    )

    def add_values(
            self,
            values: typing.List[str]
            ) -> None:
        arrays_dropper = _StringArrayDropper()
        self._cache.update(values, fill_none=True)
        collected = arrays_dropper.collect_array_items(values)
        if collected:
            for row in collected.rows():
                start, end = arrays_dropper.array_slice
                values[start:end] = row
                self._make_row(values)
        else:
            self._make_row(values)

    def _make_row(self, values: typing.List[str]) -> None:
        rate_row = TableRow(tuple(self._headers.keys))
        self._rows_count += 1
        rate_row.set_values(
                self._rows_count,
                values
                )
        self._values.append(rate_row)
