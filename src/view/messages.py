import dataclasses

from .core_presets import messages as msg
from .core_presets import command_validator
from .core_presets import constants as cst


@command_validator(cst.SysCommandType.INT_TASK)
@dataclasses.dataclass
class ShowModelPreview(msg.Command):
    name: str
    fname: str
