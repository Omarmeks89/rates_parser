import dataclasses

from .core_presets import messages as msg
from .core_presets import command_validator


@command_validator()
@dataclasses.dataclass
class ShowModelPreview(msg.Command):
    name: str
    fname: str
