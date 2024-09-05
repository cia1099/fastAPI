from schemas import *
import sqlalchemy as sql
from main import DB_URL


def bind_engine(func: callable):
    engine = sql.create_engine(DB_URL)

    def wrapper(*args):
        with engine.connect() as cursor:
            func(cursor, *args)

    return wrapper


@bind_engine
def search_User_id(cursor: sql.engine.Connection):
    stmt = sql.select(User.id).where(User.name == "Shit Man")
    print(stmt)
    res = cursor.execute(stmt)
    print(type(res))
    print("Shit Man is at id %d" % res.first().id)


@bind_engine
def order_user_name(cursor: sql.engine.Connection):
    stmt = sql.select(User).order_by(sql.desc(User.name))
    print(stmt)
    res = cursor.execute(stmt)
    print(type(res))
    names = [f"{user.name}(uid:{user.id})" for user in res.fetchall()]
    print("User's name in descend order = %s ..." % names[:10])


@bind_engine
def find_user_likes(cursor: sql.engine.Connection):
    stmt = (
        sql.select(Like.post_id, User.name)
        .select_from(Like)
        .join(User, Like.user_id == User.id)
        .where(User.name == "Shit Man")
        # .group_by(Like.post_id)
    )
    print(stmt)
    res = cursor.execute(stmt).fetchall()
    res2 = cursor.execute(sql.select(Like).where(Like.user_id == 23)).fetchall()
    print(res)
    print("join like %d, no join %d" % (len(res), len(res2)))
    print(res2)


@bind_engine
def count_post_like(cursor: sql.engine.Connection):
    stmt = (
        sql.select(Post.id, sql.func.count(Like.post_id).label("like"))
        .select_from(Post)
        .outerjoin(Like, Post.id == Like.post_id)
        .group_by(Post.id)
        .order_by(sql.desc("like"))
    )
    """
    SELECT posts.id, count(likes.id) AS "like" 
    FROM posts LEFT OUTER JOIN likes ON posts.id = likes.post_id GROUP BY posts.id ORDER BY "like" DESC
    """
    print(stmt)
    # sql.engine.ResultProxy().
    res = cursor.execute(stmt)
    print(res.fetchmany(10))
    first = res.fetchone()
    print("post %d has %d likes" % (first.id, first.like))
    # print(res.fetchmany(10))


if __name__ == "__main__":
    # search_User_id()
    # order_user_name()
    # find_user_likes()
    count_post_like()
