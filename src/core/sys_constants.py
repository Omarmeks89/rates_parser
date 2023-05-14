from enum import Enum


class SysCommandType(str, Enum):
    IO_READ: str = "READ"
    IO_WRITE: str = "WRITE"
    INT_TASK: str = "INT_TASK"
