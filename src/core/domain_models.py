import typing


class TableSheetModel:
    """
    Base model implementation.
    """

    @property
    def events(self) -> typing.NoReturn:
        pass

    @property
    def get_sheet_struct(self) -> typing.NoReturn:
        pass

    @property
    def empty(self) -> typing.NoReturn:
        pass

    @classmethod
    def validate(
            self,
            values: typing.List[str]
            ) -> typing.NoReturn:
        pass

    def add_headers(
            self,
            headers: typing.List[str]
            ) -> typing.NoReturn:
        pass

    def add_values(
            self,
            values: typing.List[str]
            ) -> typing.NoReturn:
        pass
