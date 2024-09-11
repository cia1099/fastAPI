# Sqlalchemy

## Introduction
Sqlalchemy是一个非常强大的工具，可以用Pythonic的写法，来生成SQL表达语句。只要定义好Sqlalchemy的schema，就能够依照这个schema里table的field，来生成SQL语句，可以依据现有的database来写schema，这样就能对这个database做SQL CRUD各种操作。\
此外，Sqlalchemy还有自定义的`relationship`方法，可以让table之间的filed有关联性，但只有在`Session`的获取下才能补货这关联，不会影响database内table存储的内容。\
我们还可以用[sqlacodegen_v2](https://github.com/maacck/sqlacodegen_v2)来对现有的database来自动生成schema。

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

* Generate SQL expression\
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
* Execute SQL\
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
* Handle exception\
注意在对database写入操作的时候，要做异常捕获，如果发生异常可以将database回溯：
```py
with engine.connect() as cursor:
    stmt = sqlalchemy.insert(User).values(name="Fuck Man")
    try:
        cursor.execute(stmt)
        cursor.commit()
    except Exception as e:
        print("error incurred:", e)
        cursor.rollback()
```
做写入都要`commit()`之后才会写入disk。Sqlalchemy在第一次执行`execute()`的时候就会预设SQL`BEGIN TRANSACTION`\
https://docs.sqlalchemy.org/en/20/core/connections.html#using-transactions

## Advance Expression
#### 1. Regex Search & IN operator
```py
stmt = sql.select("*").select_from(User).where(User.name.like("%man"))
# [(19, 'James Roman'), (27, 'Shit Man'), (88, 'Denise Goodman')]
stmt = sql.select("*").select_from(User).where(User.name.like("% man"))
stmt = sql.select("*").select_from(User).where(User.name.in_(["Shit Man"]))
# [(27, 'Shit Man')]
stmt = sql.select("*").select_from(User).where(User.name.like("man%"))
# [(5, 'Manuel Benson')]
```
```sql
SELECT * 
FROM users 
WHERE users.name LIKE :name_1
```
* __%__: This represents zero, one, or multiple characters. For example, if you are looking for any words that contain the letters "cat" in a column, you can use the pattern %cat%. This will return any records that have "cat" anywhere in the column.
* **_**: This represents a single character. For example, if you are looking for any words that have "at" as their second and third letters in a column, you can use the pattern _%at%. This will return any records that have any character as their first letter, followed by "at" as their second and third letters.

* ##### AND, OR operator
```py
stmt = (
        sql.select("*")
        .select_from(User)
        .where((sql.func.length(User.name) == 8) | (User.id == 1))
    )
# [(1, 'Melissa Hebert'), (27, 'Shit Man'), (34, 'Roy Wall'), (81, 'Ryan Orr')]
stmt = (
        sql.select("*")
        .select_from(User)
        .where((sql.func.length(User.name) == 8) & (User.id == 27))
    )
# [(27, 'Shit Man')]
```
注意想用pythonic的样式，记得要将每个条件用()包裹起来。\
https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.or_
#### 2. JOIN操作
JOIN操作，就是将两张table的column做选择，这两张table之间最好要有关联的field，这样join的column才不会合并成所有的column组合。选定的两张table都是以左表的row数据量来做返回。\
JOIN又分为inner和outer，预设都是inner。
#### [Example](https://github.com/cia1099/fastAPI/blob/main/sql_train/example.py)

<table>
  <tr>
    <td>

#### Customer
<table border="1">
  <thead>
    <tr>
      <th>ID</th>
      <th>Name</th>
      <th>Country</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>Alex</td>
      <td>USA</td>
    </tr>
    <tr>
      <td>2</td>
      <td>Bob</td>
      <td>UK</td>
    </tr>
    <tr>
      <td>3</td>
      <td>Chris</td>
      <td>France</td>
    </tr>
    <tr>
      <td>4</td>
      <td>Dave</td>
      <td>Canada</td>
    </tr>
  </tbody>
</table>
</td>
<td>

#### Order
<table border="1">
  <thead>
    <tr>
      <th>ID</th>
      <th>CustomerID</th>
      <th>Amount</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>1</td>
      <td>100</td>
    </tr>
    <tr>
      <td>2</td>
      <td>2</td>
      <td>200</td>
    </tr>
    <tr>
      <td>3</td>
      <td>5</td>
      <td>300</td>
    </tr>
    <tr>
      <td>4</td>
      <td>3</td>
      <td>400</td>
    </tr>
  </tbody>
</table>

</td>
</tr>
</table>

* ##### INNER JOIN
只有满足左右两表的条件才做返回，数据量可能会少于左表，实际数量就是两张表的交集。
```sql
SELECT orders.id, customers.name, orders.amount 
FROM orders JOIN customers ON orders.customer_id = customers.id
```
Result:
<table border="1">
    <th>OrderID</th>
    <th>CustomerName</th>
    <th>Amount</th>
    <tr>
      <td>1</td>
      <td>Alex</td>
      <td>100</td>
    </tr>
    <tr>
      <td>2</td>
      <td>Bob</td>
      <td>200</td>
    </tr>
    <tr>
      <td>4</td>
      <td>Chris</td>
      <td>400</td>
    </tr>
</table>

* #### OUTER JOIN
outer是一定要返回左表的数据量，当满足右表条件就返回，但不满足右表条件的数据会补充为NULL。
```sql
SELECT customers.id, customers.name, orders.amount 
FROM customers LEFT OUTER JOIN orders ON customers.id = orders.customer_id
```
Result:
<table border="1">
    <th>CustomerID</th>
    <th>CustomerName</th>
    <th>Amount</th>
    <tr>
      <td>1</td>
      <td>Alex</td>
      <td>100</td>
    </tr>
    <tr>
      <td>2</td>
      <td>Bob</td>
      <td>200</td>
    </tr>
    <tr>
      <td>3</td>
      <td>Chris</td>
      <td>400</td>
    </tr>
    <tr>
      <td>4</td>
      <td>Dave</td>
      <td>NULL</td>
    </tr>
</table>

```sql
SELECT orders.id, customers.name, orders.amount 
FROM customers LEFT OUTER JOIN orders ON orders.customer_id = customers.id
```
Result:
<table border="1">
    <th>OrderID</th>
    <th>CustomerName</th>
    <th>Amount</th>
    <tr>
      <td>1</td>
      <td>Alex</td>
      <td>100</td>
    </tr>
    <tr>
      <td>2</td>
      <td>Bob</td>
      <td>200</td>
    </tr>
    <tr>
      <td>4</td>
      <td>Chris</td>
      <td>400</td>
    </tr>
    <tr>
      <td>NULL</td>
      <td>Dave</td>
      <td>NULL</td>
    </tr>
</table>

* #### FULL JOIN
full join是只要满足左右两表其中一个，就会返回，返回数据量是两张表的联集。
```sql
SELECT customers.id, orders.id AS id_1, customers.name, orders.amount 
FROM customers FULL OUTER JOIN orders ON orders.customer_id = customers.id
```
Result:
<table border="1">
    <th>CustomerID</th>
    <th>OrderID</th>
    <th>CustomerName</th>
    <th>Amount</th>
    <tr>
      <td>1</td>
      <td>1</td>
      <td>Alex</td>
      <td>100</td>
    </tr>
    <tr>
      <td>2</td>
      <td>2</td>
      <td>Bob</td>
      <td>200</td>
    </tr>
    <tr>
      <td>3</td>
      <td>4</td>
      <td>Chris</td>
      <td>400</td>
    </tr>
    <tr>
      <td>4</td>
      <td>NULL</td>
      <td>Dave</td>
      <td>NULL</td>
    </tr>
    <tr>
      <td>NULL</td>
      <td>3</td>
      <td>NULL</td>
      <td>300</td>
    </tr>
</table>

#### 3. Aggregate Function
用来计算返回资料row数量的统计数据
```py
stmt = (
        sql.select(Post.id, Post.create_at, sql.func.count(Like.id).label("like"))
        .select_from(Post)
        .outerjoin(Like, Post.id == Like.post_id)
        .group_by(Post.id)
        .having(sql.func.count(Like.id) > 0)
        .order_by(sql.asc("like"))
        # .order_by(sql.desc(Post.create_at))
    )
```
这里计算了某个Post.id总共有多少个Like，新增的column可以用label来方便后面调用。在SQL语句里，只有`HAVING`里面才能用aggregate function，`WHERE`只能调用field或是只对field运算的function(e.g. LENGTH)，反之`HAVING`里不能调用field；想要在`WHERE`里面使用aggregate function，可以利用subquery来完成。
#### 4. Subquery
Subquery是一个独立的请求，可以结合多个subquery到一个query做取样
```py
stmt = sql.select(
        sql.select(sql.func.count("*")).select_from(User).label("n_user"),
        sql.select(sql.func.count(Post.id)).scalar_subquery().label("n_post"),
        sql.select(sql.func.count(Like.id)).label("n_like"),
    )
```
这个请求计算了资料库里的table分别有多少个row数据。\
https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#subqueries-and-ctes
#### 5. Common Table Expression
CTE是将subquery的数据暂存起来，为一个暂时的table，方便后面在用这个数据来join操作
```py
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
```
```sql
WITH post_likes AS 
(SELECT posts.id AS id, count(likes.id) AS "like" 
FROM posts LEFT OUTER JOIN likes ON likes.post_id = posts.id GROUP BY posts.id)
 SELECT post_likes."like", posts.id 
FROM post_likes JOIN posts ON posts.id = post_likes.id 
WHERE post_likes."like" >= (SELECT max(post_likes."like") - :max_1 AS anon_1 
FROM post_likes)
```
这个操作就暂存了`post_likes_cte`这个表格，而要想用表格的field可以加上`.c`这个调用在Sqlalchemy。在做function的请求最好加上`scalar_subquery()`可以防止警告，在`sql.select()`套嵌内的`sql.select()`加上`subquery()`可以变成table来呼叫field。\
https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#common-table-expressions-ctes

[advance.py](https://github.com/cia1099/fastAPI/blob/main/sql_train/advance.py)

#### 6. UNION & UNION_ALL
这两个方法是将两个`subquery`合并row的数量成一个新table，前提是这两个`subquery`要有相同的column才可以合并，`union_all`会包含重复的row,`union`则是联集。\
https://docs.sqlalchemy.org/en/20/tutorial/data_select.html#union-union-all-and-other-set-operations

#### 7. Stored Procedure and Trigger
Sqlalchemy并没有实现这些SQL特性，需要自己用SQL语句来加入到资料库里。\
https://docs.sqlalchemy.org/en/20/core/connections.html#working-with-the-dbapi-cursor-directly
