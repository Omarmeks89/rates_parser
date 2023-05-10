import pytest


from core.terminal_commands import check_load_path_exists


@pytest.fixture
def path() -> str:
    return "/home/egor_usual/rates/vvo_promo.xlsx"


def test_path_exists(path: str) -> None:
    assert check_load_path_exists(path), f'Path {path} not exists.'
