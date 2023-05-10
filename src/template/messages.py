import dataclasses

from .core_presets import messages as c_msg
from .core_presets import command_validator


@command_validator(
    check_path=True,
    check_flag=True,
    check_args=True,
    check_suffix=True
    )
@dataclasses.dataclass
class LoadExcelFile(c_msg.Command):
    name: str
    path: str
    flag: str
    mode: bool  # read_only -> bool
    fname: str
    suffix: str


@command_validator(
        check_path=True,
        check_flag=True,
        check_args=True,
        check_suffix=True
        )
@dataclasses.dataclass
class LoadTxtFile(c_msg.Command):
    name: str
    path: str
    flag: str
    mode: str
    fname: str
    suffix: str


@command_validator(
        check_args=True,
        check_suffix=True
        )
@dataclasses.dataclass
class SaveExcelFile(c_msg.Command):
    name: str
    path: str
    flag: str
    mode: bool  # write_only -> bool
    fname: str
    suffix: str
