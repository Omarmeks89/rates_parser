import collections
import pytest
import os

from core.settings import settings


@pytest.fixture
def multivalue_str() -> str:
    return 'a, b, c'


@pytest.fixture
def single_str() -> str:
    return 'bcbf'


@pytest.fixture(scope='module')
def get_conf() -> collections.OrderedDict:
    return settings.make_config()


def test_make_path_to_env() -> None:
    path = settings._make_dotenv_path()
    assert path is not None, f'Fail, path = <{path}>'
    assert path != '', 'Fail, path is empty line'
    assert os.path.exists(path), 'Path is not exists.'


def test_path_to_env_exists(get_conf: collections.OrderedDict) -> None:
    assert get_conf['MULTY_HEADERS'] != '', 'Fail'


def test_fetch_env_value(get_conf: collections.OrderedDict) -> None:
    res = settings._fetch_env_value('MULTY_HEADERS', get_conf)
    assert isinstance(res, list) and res != [], f'FAIL, res={res}'


def test_patterns_map_building(get_conf: collections.OrderedDict) -> None:
    """
    Marked like xfail in reason of empty .env
    """
    p_map = settings.build_patterns_map(
            settings.MULTY_HEADERS_KEY,
            get_conf
            )
    assert p_map["POL"] != ''


def test_fetch_any_env_value(get_conf: collections.OrderedDict) -> None:
    item = settings._fetch_env_value('MULTY_HEADERS', get_conf)
    assert not isinstance(item, str), f'Item is {type(item)}, {item}'
    assert item != [], 'Invalid value, not empty in config'


def test_find_multivalue_string(multivalue_str: str) -> None:
    assert settings._is_multivalue_str(multivalue_str), 'fail'


def test_find_singlevalue_str(single_str: str) -> None:
    assert not settings._is_multivalue_str(single_str), 'single test fail'
