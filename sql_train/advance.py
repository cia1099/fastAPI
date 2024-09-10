import time
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
    stmt = sql.select("*").select_from(User).order_by(sql.desc(User.name))
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
        sql.select(Post.id, Post.create_at, sql.func.count(Like.id).label("like"))
        .select_from(Post)
        .outerjoin(Like, Post.id == Like.post_id)
        .group_by(Post.id)
        # .having(sql.func.count(Like.id) > 0)
        # .order_by(sql.desc("like"))
        .order_by(sql.desc(Post.create_at))
    )
    """
    SELECT posts.id, count(likes.id) AS "like" 
    FROM posts LEFT OUTER JOIN likes ON posts.id = likes.post_id GROUP BY posts.id ORDER BY "like" DESC
    """
    print(stmt)
    # sql.engine.ResultProxy().
    tic = time.time()
    res = cursor.execute(stmt)
    print("execution time = %.3f ms" % ((time.time() - tic) * 1e3))
    print("=" * 20)
    print(res.fetchmany(10))
    # first = res.fetchone()
    # print("post %d has %d likes" % (first.id, first.like))
    # print(res.fetchmany(10))


@bind_engine
def length_of_table(cursor: sql.engine.Connection):
    stmt = sql.select(
        sql.select(sql.func.count("*")).select_from(User).label("n_user"),
        sql.select(sql.func.count(Post.id)).label("n_post"),
        sql.select(sql.func.count(Like.id)).label("n_like"),
    )
    print(stmt)
    res = cursor.execute(stmt)
    print("%s" % res.first())


@bind_engine
def find_who_not_post(cursor: sql.engine.Connection):
    stmt = (
        sql.select(User, Post.id)
        .select_from(User)
        .outerjoin(Post, Post.user_id == User.id, full=True)
        .where(Post.id == None)
    )
    # stmt = sql.union_all(sql.select(User.id), sql.select(Post.user_id))
    print(stmt)
    res = cursor.execute(stmt)
    users = res.fetchall()
    print("How many users who not post: %d" % len(users))
    if len(users) < 20:
        print(users)


@bind_engine
def most_like_post(cursor: sql.engine.Connection):
    post_like_cte = (
        sql.select(Post.id, sql.func.count(Like.id).label("like"))
        .select_from(Post)
        .outerjoin(Like, Like.post_id == Post.id)
        .group_by(Post.id)
        .cte("post_likes")
    )
    subq = sql.select(sql.func.max(post_like_cte.c.like) - 1).scalar_subquery()
    stmt = (
        sql.select(post_like_cte.c.like, Post.id)
        .join(Post, Post.id == post_like_cte.c.id)
        .where(post_like_cte.c.like >= subq)
        # .having(sql.func.max(post_like_cte.c.like) >= subq)
        # .group_by(post_like_cte.c.id)
    )
    avg_qu = sql.select(sql.func.avg(stmt.subquery().c.like))
    print(stmt)
    res = cursor.execute(stmt)
    print(res.fetchall())
    # print(len(res.fetchall()))


if __name__ == "__main__":
    search_User_id()
    # order_user_name()
    # find_user_likes()
    # count_post_like()
    # length_of_table()
    # find_who_not_post()
    # most_like_post()
