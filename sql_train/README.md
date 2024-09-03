# Sqlalchemy

## Introduction
Sqlalchemy是一个非常强大的工具，可以用Pythonic的写法，来生成SQL表达语句。只要定义好Sqlalchemy的schema，就能够依照这个schema里table的field，来生成SQL语句，可以依据现有的database来写schema，这样就能对这个database做SQL CRUD各种操作。\
此外，Sqlalchemy还有自定义的`relationship`方法，可以让table之间的filed有关联性，但只有在`Session`的获取下才能补货这关联，不会影响database内table存储的内容。\
我们还可以用[sqlacodegen](https://github.com/agronholm/sqlacodegen?tab=readme-ov-file)来对现有的database来自动生成schema。

## Example
[schema](https://github.com/cia1099/fastAPI/blob/main/sql_train/schemas.py) 我们有这样的资料结构，其中用`Column`的field才是database里存储的数据，`relationship("Class Name", back_populates="Table Name")`是Sqlalchemy为我们做的关联field，只有用`Session`才能有效，实际database并没有存这样的column在table里。


## Instructions

* Read database
```py
from sqlalchemy import create_engine

engine = create_engine(DB_URL, echo=False)
```
这个操作是读取`DB_URL`的路径位置，可以读取任意`.db`的档案，只要前面定义的schema符合这个`.db`的内容，都可以用Sqlalchemy来做SQL操作。要注意的是当路径还没有`.db`的档案存在时，需要建立这个`.db`：
* Create database
```py
Base.metadata.drop_all(engine) #清除.db内和schema中有宣告__tablename__一样名称的tables
Base.metadata.create_all(engine) #建立schema中有宣告__tablename__的名称写入.db内
```
基本上建立table都不会有问题，也就是说`create_all(engine)`方法不会有影响，建立和清除table都是根据是否有这个table名称在`.db`里来去执行。\
只要有继承[Base](https://github.com/cia1099/fastAPI/blob/main/sql_train/schemas.py?plain=1#L14-L15)的这个Class子类，都会被检查是否有这个table名称在`.db`。

* Generate SQL expression
本质上`sqlalchemy`提供的方法就是转化SQL语句，可以用打印的方式印出SQL的表达式：
```py
stmt = sqlalchemy.select(User).where(User.name == "Shit Man")
print("What type is %s\n%s" % (type("%s" % stmt), stmt))
''' print
What type is <class 'str'>
SELECT users.id, users.name 
FROM users 
WHERE users.name = :name_1
'''
```
sqlite3 使用 ? 作为占位符，但是 :name_1 是命名占位符，这在 SQLite 和许多其他 SQL 接口中也是支持的。
```py
import sqlite3
conn = sqlite3.connect(DB_URL)
cursor = conn.cursor()
# 定义 SQL 查询，使用命名参数 :name_1
sql_query = """
SELECT users.id, users.name 
FROM users 
WHERE users.name = :name_1
"""
# 定义参数字典，键为命名参数的名字，不带冒号
params = {'name_1': 'Shit Man'}
# 执行查询
user = cursor.execute(sql_query, params).one()
q_query = """
SELECT users.id, users.name 
FROM users 
WHERE users.name = ?
"""
user = cursor.execute(q_query, ('Shit Man',)).one()
cursor.close()
conn.close()
```
* Execute SQL
Sqlalchemy提供了两种执行方式，一种是原始的数据操作，另一种是借由`Session`来辅助补充Sqlalchemy自定义的field方法内容。
1. 原始Table操作
```py
with engine.connect() as cursor:
    user = cursor.execute(stmt).one()
    print(type(user))
    print(f"'{user.name}' whose id is {user.id}")
    posts = cursor.execute(sqlalchemy.select(Post).where(Post.user_id == user.id))
    print(f"He posted: {[post.id for post in posts]}")
```
2. Session操作
```py
with Session(bind=engine, future=True) as session:
    # user = session.query(User).filter(User.name == "Shit Man").one()
    user = session.scalars(stmt).one()
    print(user)
    print("Session query: %s" % [post.id for post in user.posts])
```
可以看到用原始Table操作返回的类型是`<class 'sqlalchemy.engine.row.Row'>`，而用Session操作返回`<schemas.User object at 0x10416ee00>`我们定义的schemas.User，是有关联的，field含有posts可以直接遍历。