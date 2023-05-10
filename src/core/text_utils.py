import typing
import types
import re


DEFAULT_ARRAY_SEPARATOR: typing.Final[str] = '/'


DEFAULT_NUMERICS_ORDER: re.Pattern = re.compile(
        '^(\d+)(.+)$'
        )
DEFAULT_CLEAN_PATTERN: re.Pattern = re.compile(
        '(?:[a-zA-Z\s]{3,}){1,}'
        )


class TextOperationError(Exception):
    pass


class SymbolsGroupOrder:

    _re_group_symb: typing.Final[str] = r'\{}'

    @classmethod
    def create_new_order(
            cls,
            ord_template: typing.Tuple[int]
            ) -> 'SymbolsGroupOrder':
        if ord_template and isinstance(ord_template, tuple):
            return cls(ord_template)
        raise Exception(f'Invalid template: {ord_template}.')

    def __init__(
            self,
            ord_template: typing.Tuple[str]
            ) -> None:
        self._templ = ord_template

    def reorder(
            self,
            subs: re.Pattern,
            string: str
            ) -> str:
        """
        Return reordered string if it matches with template.
        Else return string without changes.
        """
        order = self.generate_order(self._templ)
        matches = subs.match(string)
        if matches:
            reordered = matches.expand(order)
            return reordered
        else:
            return string

    @classmethod
    def generate_order(
            cls,
            indexes: typing.Tuple[int]
            ) -> str:
        """
        Return order like r'\1\2' from (1, 2).
        """
        if not indexes:
            raise Exception('text_utils.generate_order No indexes found.')
        repeats_cnt = len(indexes)
        template = cls._re_group_symb * repeats_cnt
        return template.format(*indexes)


def detect_array_in_str(
        string: str,
        *,
        arr_sep: typing.Optional[str] = None
        ) -> bool:
    """
    return True if wished separator registered
    in string.
    """
    sep = arr_sep or DEFAULT_ARRAY_SEPARATOR
    if isinstance(string, str) and len(string) > 1:
        return sep in string
    return False


def convert_str_array_to_list(
        string: str,
        pattern: re.Pattern
        ) -> typing.List[str]:
    return [i for i in pattern.findall(string) if i]


def replace_control_sequences(
        subs_map: types.MappingProxyType,
        string: str,
        ) -> str:

    separator = '|'
    if not subs_map:
        raise TextOperationError(f'No map: {subs_map}.')

    def _replace(_mth: re.Match) -> str:
        return str(subs_map[_mth.group()])

    pattern = re.compile(separator.join(subs_map.keys()))
    return pattern.sub(_replace, string)


def create_replace_map(
        subs: typing.List[str],
        repl: typing.List[str]
        ) -> types.MappingProxyType:

    if len(subs) != len(repl):
        raise TextOperationError(f'Non equal sequences: {subs} != {repl}')
    replace_map = dict(zip(subs, repl))
    return types.MappingProxyType(replace_map)
