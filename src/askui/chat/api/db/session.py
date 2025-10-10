from typing import Annotated, Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from askui.chat.api.db.engine import engine


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
