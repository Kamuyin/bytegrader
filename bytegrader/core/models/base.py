from uuid import uuid4

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def new_uuid() -> str:
    return uuid4().hex
