from pathlib import Path
import sys, random

from schemas import *
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import sqlalchemy
from faker import Faker


DB_URL = "sqlite:///database.db"


def create_mock(engine: sqlalchemy.engine.Engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    faker = Faker(["en_US"])
    faker.seed_instance(55123)
    with Session(bind=engine, future=True) as session:
        n_user = 100
        n_post = 250
        n_like = 1000
        users = [User(name="Shit Man")] + [
            User(name=faker.name()) for _ in range(n_user - 1)
        ]
        session.add_all(random.sample(users, len(users)))
        session.add_all(
            Post(body=faker.text(), user_id=faker.random_int(1, n_user))
            for _ in range(n_post)
        )
        likes = [set() for _ in range(n_post)]
        for _ in range(n_like):
            post_idx = faker.random_int(0, n_post - 1)
            # print("post %d has like: %s" % (post_idx+1, likes[post_idx]))
            while user_id := faker.random_int(1, n_user):
                if user_id in likes[post_idx]:
                    continue
                else:
                    likes[post_idx].add(user_id)
                    break

        session.add_all(
            Like(user_id=user_id, post_id=post + 1)
            for post, user_ids in enumerate(likes)
            for user_id in user_ids
        )

        session.commit()


if __name__ == "__main__":
    # https://www.reddit.com/r/learnpython/comments/vupzfa/importerror_attempted_relative_import_with_no/
    # sys.path.append(str(Path(__file__).parent.parent))
    # from storeapi.routers.posts import select_post_and_likes
    # print(select_post_and_likes)

    engine = create_engine(DB_URL, echo=False)
    Base.metadata.create_all(engine)
    # create_mock(engine)
    stmt = sqlalchemy.select(User).where(User.name == "Shit Man")
    print("What type is %s\n%s" % (type("%s" % stmt), stmt))
    with engine.connect() as cursor:
        user = cursor.execute(stmt).one()
        print(type(user))
        print(f"'{user.name}' whose id is {user.id}")
        posts = cursor.execute(sqlalchemy.select(Post).where(Post.user_id == user.id))
        print(f"He posted: {[post.id for post in posts]}")
    with Session(bind=engine, future=True) as session:
        # user = session.query(User).filter(User.name == "Shit Man").one()
        user = session.scalars(stmt).one()
        print(user)
        print("Session query: %s" % [post.id for post in user.posts])
