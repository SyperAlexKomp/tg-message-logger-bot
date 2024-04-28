import logging
import typing

from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import Session

from repo.modules.base import Base, BaseRepo


class UserData(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    connection_id = Column(String(1028), unique=True)
    channel_id = Column(BigInteger)
    language = Column(String(4))


class UsersRepo(BaseRepo):
    def __init__(self, s) -> None:
        super().__init__(s)

    def add(self, user: UserData) -> bool:
        s = self.get(user.id)
        if s is not None:
            return False

        try:
            self._s.add(user)
            self._s.commit()
            return True
        except Exception as e:
            logging.error(e)
            return False

    def get(self, id: int) -> typing.Optional[UserData]:
        return self._s.query(UserData).get({"id": id})

    def get_by_connection(self, connection_id: str) -> typing.Optional[UserData]:
        return self._s.query(UserData).filter_by(connection_id=connection_id).first()

    def update_connection_id(self, user: UserData, connection_id: str) -> bool:
        user.connection_id = connection_id

        self._s.commit()

    def delete(self, user: UserData) -> bool:
        self._s.delete(user)
        self._s.commit()