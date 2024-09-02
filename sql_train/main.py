from pathlib import Path
import sys

from schemas import *
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import sqlalchemy


DB_URL = "sqlite:///database.db"

if __name__ == "__main__":
    # https://www.reddit.com/r/learnpython/comments/vupzfa/importerror_attempted_relative_import_with_no/
    sys.path.append(str(Path(__file__).parent.parent))
    # from storeapi.routers.posts import select_post_and_likes
    # print(select_post_and_likes)

    # engine = create_engine(DB_URL, echo=True)
    # Base.metadata.drop_all(engine)
    # Base.metadata.create_all(engine)
    # with Session(bind=engine, future=True) as session:
    #     new_user = User(name="Shit Man")
    #     session.add(new_user)
    #     session.commit()
    stmt = sqlalchemy.select(User).where(User.name == "Shit Man")
    print(stmt)
