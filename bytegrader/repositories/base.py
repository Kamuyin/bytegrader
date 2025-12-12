from typing import TypeVar, Generic, Optional, List, Type
from sqlalchemy.exc import SQLAlchemyError

from ..core.database.connection import DatabaseManager
from ..core.exceptions import DatabaseError
from ..core.models import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db_manager: DatabaseManager):
        self.model = model
        self.db_manager = db_manager

    def create(self, **kwargs) -> T:
        with self.db_manager.get_session() as session:
            try:
                instance = self.model(**kwargs)
                session.add(instance)
                session.flush()
                session.refresh(instance)
                return instance
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to create {self.model.__name__}: {str(e)}") from e

    def create_from_instance(self, instance: T) -> T:
        with self.db_manager.get_session() as session:
            try:
                session.add(instance)
                session.flush()
                session.refresh(instance)
                return instance
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to persist instance of {self.model.__name__}: {str(e)}") from e

    def get(self, id: str) -> Optional[T]:
        with self.db_manager.get_session() as session:
            try:
                instance = session.query(self.model).get(id)
                return instance
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve {self.model.__name__} with id {id}: {str(e)}") from e

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        with self.db_manager.get_session() as session:
            try:
                instances = session.query(self.model).offset(skip).limit(limit).all()
                return instances
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to retrieve {self.model.__name__} records: {str(e)}") from e

    def update(self, id: str, **kwargs) -> Optional[T]:
        with self.db_manager.get_session() as session:
            try:
                instance = session.query(self.model).get(id)
                if not instance:
                    return None
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                session.flush()
                session.refresh(instance)
                return instance
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to update {self.model.__name__} with id {id}: {str(e)}") from e

    def delete(self, id: str) -> None:
        with self.db_manager.get_session() as session:
            try:
                instance = session.query(self.model).get(id)
                if not instance:
                    return None
                session.delete(instance)
                return None
            except SQLAlchemyError as e:
                raise DatabaseError(f"Failed to delete {self.model.__name__} with id {id}: {str(e)}") from e
