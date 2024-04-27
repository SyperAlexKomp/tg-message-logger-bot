from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from repo.modules.base import Base
from repo.modules.messages import MessagesRepo
from repo.modules.users import UsersRepo


class Repo:
    def __init__(self, username: str, password: str, ip: str, port: int, db: str) -> None:
        self.engine = create_engine(f'mysql+pymysql://{username}:{password}@{ip}:{port}/{db}')

        self._Session = sessionmaker(bind=self.engine)
        self.session = self._Session()

        Base.metadata.create_all(self.engine)

    def save(self) -> None:
        self.session.commit()

    @property
    def users(self) -> UsersRepo:
        return UsersRepo(s=self.session)

    @property
    def messages(self) -> MessagesRepo:
        return MessagesRepo(s=self.session)
