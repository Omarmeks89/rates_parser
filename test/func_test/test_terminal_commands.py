import pytest


from core import command_filters as cf


@pytest.fixture
def invalid_cmd() -> str:
    return 'ab'


@pytest.fixture
def valid_cmd() -> str:
    return 'loadfile /home/egor_usual/rates/vvo_promo.xlsx testfile'


def test_invalid_command_failed(invalid_cmd: str) -> None:
    inv_cmd = cf.PreProcessor.make_cmd_template(invalid_cmd)
    assert inv_cmd is None, f'Not None, cmd is {inv_cmd}'


@pytest.mark.xfail(raises=cf.PostprocessorError)
def test_postprocessor_failed_to_parse(invalid_cmd: str) -> None:
    inv_cmd = cf.PreProcessor.make_cmd_template(invalid_cmd)
    cf.PostProcessor.make_command_from(inv_cmd)


def test_postprocessor_set_none_without_filters(valid_cmd) -> None:
    val_cmd = cf.PreProcessor.make_cmd_template(valid_cmd)
    cmd = cf.PostProcessor.make_command_from(val_cmd)
    assert cf.PostProcessor.filters() == [], f'{cf.PostProcessor.filters()}'
    assert cmd is None, f'Cmd is not None -> {cmd}'


@pytest.mark.xfail(raises=cf.SystemValidationError)
def test_cmd_check_raised_error(valid_cmd: str) -> None:
    val_cmd = cf.PreProcessor.make_cmd_template(valid_cmd)
    cmd = cf.PostProcessor.make_command_from(val_cmd)
    cf.check_command_subscribed(cmd, {})
