import logging
import typing

from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import sessionmaker

from repo.modules.base import Base, BaseRepo


class MessageData(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger)
    message_id = Column(BigInteger)
    message = Column(String(4112))


class MessagesRepo(BaseRepo):
    def __init__(self, s):
        super().__init__(s)

    def add(self, message: MessageData) -> bool:
        try:
            self._s.add(message)
            self._s.commit()
            return True
        except Exception as e:
            logging.error(e)
            return False

    def get(self, message_id: int, chat_id: int) -> typing.Optional[MessageData]:
        return self._s.query(MessageData).filter_by(message_id=message_id, chat_id=chat_id).first()

    def delete(self, message: MessageData) -> bool:
        self._s.delete(message)