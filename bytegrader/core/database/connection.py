from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Iterator, Dict, Any

from bytegrader.config.config import BYTEGraderConfig
from ..exceptions import DatabaseError
from ..models import BaseModel


class DatabaseManager:

    def __init__(self, uri: str, config: 'BYTEGraderConfig' = None):
        self.uri: str = uri
        self.engine = None
        self.SessionLocal = None

        self.config: 'BYTEGraderConfig' = config
        if not uri:
            raise ValueError("Database URI must be provided.")

    def _init_engine(self):
        try:
            echo_flag = False
            if self.config and hasattr(self.config, 'database'):
                echo_flag = getattr(self.config.database, 'echo', False)
            engine_kwargs: Dict[str, Any] = {
                "echo": echo_flag,
                "pool_pre_ping": True
            }

            if self.uri.startswith("sqlite://"):
                engine_kwargs.update({
                    'poolclass': StaticPool,
                    'connect_args': {'check_same_thread': False},
                })

            self.engine = create_engine(self.uri, **engine_kwargs)
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
                bind=self.engine
            )
            self.Session = scoped_session(self.SessionLocal)

            try:
                from bytegrader.core.observability import instrument_sqlalchemy

                instrument_sqlalchemy(self.engine)
            except Exception:
                pass

        except Exception as e:
            raise DatabaseError(f"Failed to initialize database engine: {e}") from e

    def create_tables(self):
        if not self.engine:
            self._init_engine()

        try:
            BaseModel.metadata.create_all(bind=self.engine)
        except Exception as e:
            raise DatabaseError(f"Failed to create tables: {e}") from e

    @contextmanager
    def get_session(self) -> Iterator[Session]:
        if not self.engine:
            self._init_engine()

        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"Database operation failed: {e}") from e
        finally:
            session.close()

    def close(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
        else:
            raise DatabaseError("Database engine is not initialized or already closed.")

    def remove_session(self):
        try:
            self.Session.remove()
        except Exception:
            pass
