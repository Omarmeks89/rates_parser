import typing
import pytest

from template import models


@pytest.fixture
def name_and_count() -> typing.Tuple[str, int]:
    return 'table', 10


@pytest.fixture(scope='module')
def only_name_for_model() -> str:
    return 'test_table'


@pytest.fixture(scope='module')
def model(only_name_for_model: str) -> models.SheetTemplate:
    name = only_name_for_model
    return models.SheetTemplate(name)


@pytest.fixture
def dropper() -> models._StringArrayDropper:
    return models._StringArrayDropper()


def test_can_add_headers(model: models.SheetTemplate) -> None:
    headers = ['pol', 'pod', '20ft', '40ft', 'DTHC']
    model.add_headers(headers)
    assert not model.empty, 'model is empty'


def test_model_preview_with_headers_only(model: models.SheetTemplate) -> None:
    struct = model.get_sheet_struct
    assert struct.values == (), f'Fail, values = {struct.values}'


def test_model_can_validate_values(model: models.SheetTemplate) -> None:
    values = ['a', 'b']
    assert not model.validate(values), 'invalid values passed test'


def test_model_validate_and_add_values(model: models.SheetTemplate) -> None:
    values = ['start', 'end/new end', 1000, 3000, 0]
    assert model.validate(values), 'correct values didn`t pass.'


def test_array_dropper_for_model(dropper: models._StringArrayDropper) -> None:
    values = ['start', 'end/new end', 1000, 3000, 0]
    dropper.find_array_positions(values) == (1), 'invalid positions'


def test_make_rows_for_model(dropper: models._StringArrayDropper) -> None:
    values = ['start', 'end/new end', 1000, 3000, 0]
    compiler = dropper.collect_array_items(values)
    gen = compiler.rows()
    f_row = next(gen)
    assert f_row == ['end'], f'Fail: {f_row}'
    assert next(gen) == ['new end'], 'second failed'


def test_make_rows_what_collect(dropper: models._StringArrayDropper) -> None:
    values = ['start', 'end/new end', 1000, 3000, 0]
    result = []
    compiler = dropper.collect_array_items(values)
    for i in compiler.rows():
        result.extend(i)
    assert compiler.count == 2, f'Count in comp {compiler.count} != 2'
    assert result == ['end', 'new end'], f'Failed, res is = {result}'


def test_model_can_add_values_correct(model: models.SheetTemplate) -> None:
    values = ['start', 'end/new end', 1000, 3000, 0]
    model.add_values(values)
    assert model.rows_count == 2, f'rows count {model.rows_count} != 2'


def test_model_return_rows(model: models.SheetTemplate) -> None:
    rows = model.rows
    result = []
    for r in rows:
        result.append(r)
    assert result == [
            ['pol', 'pod', 'ft20', 'ft40', 'DTHC'],
            ['start', 'end', 1000, 3000, 0],
            ['start', 'new end', 1000, 3000, 0]
            ], f'Failed, res = {result}'
