import abc
import logging
import typing

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class BaseRepo(abc.ABC):
    def __init__(self, s) -> None:
        self._s: Session = s

    @abc.abstractmethod
    def get(self, **kwargs) -> typing.Optional[Base]:
        pass

    @abc.abstractmethod
    def add(self, obj: Base) -> bool:
        pass