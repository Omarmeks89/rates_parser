from abc import ABC, abstractmethod
from typing import NoReturn


class FileReaderInterface(ABC):

    @abstractmethod
    def read(self) -> NoReturn:
        pass


class FileWriterInterface(ABC):

    @abstractmethod
    def write(self) -> NoReturn:
        pass


class FileDriverInterface(ABC):
    """header for driver-type description."""
    pass
