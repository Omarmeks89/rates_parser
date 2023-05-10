import enum
import dataclasses


class SystemErrorType(enum.Enum):
    INVALID_CMD: str = 'INVALID COMMAND'
    INVALID_FILE_TYPE: str = 'INVALID FILE TYPE'


@dataclasses.dataclass
class SystemMessage:
    pass


@dataclasses.dataclass
class Event:
    pass


@dataclasses.dataclass
class Command:
    pass
