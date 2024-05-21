FastAPI
---
运行本地的服务器：
```shell
uvicorn <project directory>.main:app --reload
# deploy
cd <project directory>
uvicorn <project directory>.main:app --host 0.0.0.0 --port $PORT > /dev/null &
# 查找占用PORT的PID
lsof -i :$PORT
kill -9 PID
```
加入`--reload`参数可以让每次修改保存后，都会重新运行服务器。
* ##### Remote by ssh
用ssh传输档案可以用`rsync`和`spc`指令：
```shell
# push to remote
rsync <file_name> <user_name>@<ip_address>:/path/to/remote
rsync -r <directory> <user_name>@<ip_address>:/path/to/remote
# pull from remote
rsync <user_name>@<ip_address>:/path/to/remote/file <source_path>
rsync -r <user_name>@<ip_address>:/path/to/remote/directory <source_path>
```
ref. https://linuxhandbook.com/transfer-files-ssh/


FastAPI会自动解析JSON的field给Model，但要注意model的field只能多不能少，多的field会自动被忽略，千万注意在API声明的Model类型有没有满足返回的JSON能够被解析：
```py
class UserPost(UserPostIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int

class UserPostWithLikes(UserPost):
    model_config = ConfigDict(from_attributes=True)
    likes: int

class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"

@router.get("/post", response_model=list[UserPostWithLikes])
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    logger.info("Getting all posts")
    query = None
    # only support above python 3.10 with switch statement
    match sorting:
        case PostSorting.new:
            query = select_post_and_likes.order_by(post_table.c.id.desc())
        case PostSorting.old:
            query = select_post_and_likes.order_by(post_table.c.id.asc())
        case PostSorting.most_likes:
            query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    logger.debug(query)

    return await database.fetch_all(query)
```
例如上述代码块，在`response_model`可以用`[UserPost]`和`[UserPostWithLikes]`在JSON字串里有"like" field，但`UserPost`少了仍然可以被解析。\
传入Enum参数可以让fastAPI自动辨识为request的query，解义为Url就是http://localhost:8000/post?sorting=new


DataBase
---
SQLite is a great database if you application is doing mostly reads, but it's maybe not so good for an async application if you're doing a lot of writes.\
So for a REST API, SQLite is probably not the right choice in most scenarios, but PostgreSQL could be the right choice.

* #### Sqlalchemey
FastAPI使用ORM的方式，需要个别定义Sqlalchemy的model和http响应的schemas；http响应用的schema用`pydanic-setting`模块来定义，例如:
```py
#--- <project_name>/database/models.py
import sqlalchemy

metadata = sqlalchemy.MetaData()
user_table = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String, unique=True),
    sqlalchemy.Column("password", sqlalchemy.String),
    sqlalchemy.Column("confirmed", sqlalchemy.Boolean, default=False),
)
#--- <project_name>/schemas/user.py
from pydantic import BaseModel, ConfigDict

class UserIn(BaseModel):
    email: str
    password: str

class User(UserIn):
    model_config = ConfigDict(from_attributes=True)

    id: int

```
上面是用async的写法，Sqlalchemy搭配`databases`套件实现对资料库async的query，可以参考[ Async SQL (Relational) Databases](https://fastapi.tiangolo.com/how-to/async-sql-encode-databases/)。\
如果是对资料库同步的query，参考[SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)。\
可以发现Sqlalchemy需要另外写一个model和http响应的schema是相互独立的ORM。\
如果是现有的资料库已经存在，可以使用[sqlacodegen](https://github.com/agronholm/sqlacodegen?tab=readme-ov-file)来对现有的资料库生成Sqlalchemy的models。

---
Pipenv
---
`pip freeze`可以查看module的版本\
Module pipenv是一个套件管理包，可以取代requirement.txt\
Pipfile可以编辑里面的套件，有这个文件以后用`pipenv install`就能全部安装好到venv，连python的版本都能在这文件指定。要启动pipenv建立的venv，只需输入`pipenv shell`就能进入该venv；离开就打`exit`，操作更直观。
要安装dev-package只要输入`pipenv install -—dev <package_name>`，就能将套件安装在dev-package。以后在别的设备开发，只要输入pipenv install —dev就会将Pipfile的dev-package安装到venv环境。
使用`pipenv uninstall <package_name>`可以卸载，并将Pipfile的package除去。\
最好在venv的环境下安装pipenv，这样pipenv安装的套件都能在这个venv的文件夹安装套件：

```shell
cd project
python -m venv venv
source venv/bin/activate
pip install pipenv
pipenv install || pipenv install --dev
# VIRTUAL_ENV=path/to/your/venv pipenv install
```
Refs
https://stackoverflow.com/questions/50598220/pipenv-how-to-force-virtualenv-directory \
https://stackoverflow.com/questions/52540121/make-pipenv-create-the-virtualenv-in-the-same-folder

发布上线前，可以使用指令生成`requirements.txt`。来方便在线上安装Python套件。以github的测试Action为例：
```shell
# 生成Pipfile.lock
pipenv lock && pipenv lock --dev
pipenv requirements > requirements.txt && pipenv requirements --dev > requirements-dev.txt
# 线上安装
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```
refs: https://stackoverflow.com/questions/51845562/how-to-freeze-a-requirement-with-pipenv

PyTest
---

使用pytest指令：
```shell
# 显示每次执行测试方法时所用到的指令
pytest --fixtures-per-test
# 单独测试一个脚本
pytest <file_path>
# 单独测试一个pytest.mark.anyio
pytest -k <method name>
#e.g. pytest -k test_generate_and_add_to_post_success
```
执行pytest的文件目录结构如下：
```shell
<project directory>
├── __init__.py
├── main.py
└── test
    ├── __init__.py
    ├── conftest.py
    └── test_post.py
```
在专案目录下创建一个目录test，该目录下要而外一个`__init__.py`；设定档`conftest.py`,想要测试的脚本命名一定要包含test，例如：`test_XXX.py`或`XXX_test.py`。

* ##### @pytest.fixture()
表示pytest的作用域，在声明的方法上加入，可以让pytest自己根据参数的名字找到对应的对象，使开发者不需要在传入对象或创建对象。例如在执行一个测试方法时，所有对象都要重建，pytest会帮我们把所有对象重建，再执行测试逻辑；因此对象生成最好写一个方法来返回产生。

有时候pytest会失败，将执行目录切换到test资料夹的父目录`storeapi`就可以运行成功。

* ##### @pytest.mark.anyio
要测试的方法，前面要加上的签名。然后定义的方法能传入前面有`@pytest.fixture()`的声明方法参数。

* ##### @pytest.mark.parametrize()
想重复跑一个方法不同的参数，可以用这个声明，在parentheses里用字符串逗号来区分参数名，用bracket来区分每次的呼叫，用tuple来区分呼叫传入的参数：
```py
@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order",
    [
        (PostSorting.new.value, [2, 1]),
        (PostSorting.old.value, [1, 2])
    ],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
): #....
```

* #### pytest-coverage
想要知道测试漏掉了哪些方法，可以安装`pytest-cov`模块。
```shell
# 待测试，大陆不能安转
# pytest --cov=storeapi -k test_generate_and_add_to_post_success
```

Logging
---
最基础的log设定方式，能够日志console和file，在专案目录下创建一个[loggin_conf.py](https://github.com/cia1099/fastAPI/blob/main/storeapi/logging_conf.py?plain=1#L31-L98)的设定档案：
```py
import logging
from logging.config import dictConfig

handlers = ["default", "rotating_file"]
def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "logging.Formatter",  # "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    # For JsonFormatter, the format string just defines what keys are included in the log record
                    # It's a bit clunky, but it's the way to do it for now
                    "format": "%(asctime)s %(msecs)03d %(levelname)-s %(name)s %(lineno)d %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler", #"rich.logging.RichHandler"
                    "level": "DEBUG",
                    "formatter": "console",
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "storeapi.log",
                    "maxBytes": 1024 * 1024,  # 1 MB
                    "backupCount": 2,
                    "encoding": "utf8",
                },
            },
            "loggers": {
                # if you would like to cosistent with uvicorn formate
                # "uvicorn": {"handlers": handlers, "level": "INFO"},
                "storeapi": {
                    "handlers": handlers,
                    "level": "DEBUG", #if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,
                },
                # "databases": {"handlers": ["default"], "level": "WARNING"},
                # "aiosqlite": {"handlers": ["default"], "level": "WARNING"},
            },
        }
    )
```
想要使用"rich.logging.RichHandler"就要安装`rich`套件。\
"pythonjsonlogger.jsonlogger.JsonFormatter"要安装`python-json-logger`，让输出的日志可以给NoSQL的资料库系统来归档。

Python Basic
---
* ##### Decorator
用来绑定方法的方法，在方法宣告上头加上@func就可以让呼叫自动被@func呼叫为套嵌。e.g.
```py
def response_to_approacher(name):
    def inner_response(func):
        def wrapper(*arg, **kwargs):
            print(f"A {name} is comming")
            response = func(*arg, **kwargs)
            return response
        return wrapper
    return inner_response

@response_to_approacher("mailman")
def conjure_sound(sound):
    return sound*2

# 绑定了inner_response的参数
ret = conjure_sound("woof")
print("return value:", ret)
'''
A mailman is comming
return value: woofwoof
'''

def foo(func: callable):
    def wrapper(x: int):
        return 1 + func(x)
    return wrapper

@foo
def square(x: int):
    return x**2

print(square(3))
'''10'''
```
* ##### Generator
节省内存空间，不要一次读取资料存放；而是读取部份资料，并只占用少量内存。通常用在io或串流。e.g.
```py
def read_line(filename):
    with open(filename, 'r') as ifile:
        for line in ifile:
            yield line
file_contents = read_line('file.txt') #generator
for line in file_contents
    print(line)
file_contents = read_line('file.txt')
while file_contents:
    print(next(file_contents))

all_stream = [j for j in (i for i in range(5))]
print(all_stream)
'''[0, 1, 2, 3, 4]'''
quick_generator = (i for i in range(5))
while True:
    try:
        print(next(quick_generator), end=", ")
    except StopIteration:
        break
'''0, 1, 2, 3, 4, '''
```
* ##### Typing
python的容器可以用[T]，来声明容器内的类型e.g. `list[int]`, `dict[str, int]`。
```py
def list2dict(p: list[int]) -> dict[str, int]:
    return {str(i): x for i, x in enumerate(p)}

print(list2dict([i for i in range(5, 10)]))
'''{'0': 5, '1': 6, '2': 7, '3': 8, '4': 9}'''
```
用typing模组套件可以更简洁清楚声明类型。但实际上我们有声明类型，实际运行还是可以随便放任意形态，声明类型只是帮助IDE能够发出警告：
```py
from typing import Optional, Union

def division(a: [int, float], b: Union[int]) -> Optional[float]:
    if b != 0:
        return a / b
    # return None

print(division(1, 2))
print(division(1, 0))
print(division(1.0, 2.0)) #第二个参数会报警
'''
0.5
None
0.5
'''
```

* ##### async Function
async是单核单线程跑多个任务，因此一定会有些许的延迟，花费多工任务的时间比单任务的时间还长。但不会使单线程停滞在等待任务上。
```py
import asyncio
import time


async def async_hello(n):
    print("Before sleep %d" % n)
    await asyncio.sleep(1)
    print(f"async({n}) hello")


async def say_hi():
    print("Hi")

# 同时启动每个async方法
async def process_async_funcs():
    t = asyncio.create_task(async_hello(1))
    await async_hello(2)
    await say_hi()
    await t
    '''注意Hi的位置
    Before sleep 2
    Before sleep 1
    async(2) hello
    Hi
    async(1) hello
    '''
    await asyncio.gather(async_hello(1), async_hello(2), say_hi())
    '''
    Before sleep 1
    Before sleep 2
    Hi
    async(1) hello
    async(2) hello
    '''


tic = time.time()
asyncio.run(process_async_funcs())
print(f"elapsed time = {time.time() - tic}")
print("sync hello")
'''
elapsed time = 2.003916025161743
sync hello
'''
```
在python里，只有声明了async的方法能够同时启动，在线程里asyncio.run()后面的程序仍在等待。在`async process_async_funcs()`才能await task或await asyncio.gather来一次启动。\
在asyncio.gather()里面能用`asyncio.wait_for()`来限制等待时间
```py
    try:
        await asyncio.gather(
            asyncio.wait_for(async_hello(1), 0.5), async_hello(2), say_hi()
        )
    except asyncio.TimeoutError:
        print("timeout")
    '''
    Before sleep 2
    Hi
    Before sleep 1
    timeout
    elapsed time = 1.5035719871520996
    '''
```
* ##### wait statement
使用asyncio.wait()不会抛异常，而会让异步中断，进程继续运行，并且还能保留被中断的异步任务对象。
```py
import asyncio, time

async def async_sleep(n):
    await asyncio.sleep(n)
    print("task %d has done" % n)
    return n

async def process_async_funcs():
    pending = {asyncio.create_task(async_sleep(t)) for t in range(1, 11)}
    done, pending = await asyncio.wait(pending, return_when="FIRST_COMPLETED")
    #---equivalent to below code here
    # done, pending = await asyncio.wait(pending, timeout=1)
    
    print(f"done tasks = {len(done)}, penddings = {len(pending)}")
    print("Task results =", {d.result() for d in done})
    

tic = time.time()
asyncio.run(process_async_funcs())
print(f"elapsed time = {time.time() - tic}")
'''
task 1 has done
done tasks = 1, penddings = 9
Task results = {1}
elapsed time = 1.0031888484954834
'''
```
其中done是完成的任务，而pendding是未完成的任务，可以再用`asyncio.wait(pendding)`将剩余的任务完成。

* ##### Combining Async and Multiprocessing
可以定义一个方法用来执行`asyncio.run`来给`Process`。注意使用`multiprocessing`要声明`if __name__=='__main__:'`的作用域下运行：
```py
import asyncio, time
from multiprocessing import Process
# def ...same as above block
def arun():
    asyncio.run(process_async_funcs())

if __name__ == "__main__":
    tic = time.time()
    ps = [Process(target=arun) for _ in range(4)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
    print(f"elapsed time = {time.time() - tic}")
''' Four Tasks done only at one second
    ...
elapsed time = 1.0695140361785889
'''
```

* ##### Multiprocessing

可以用`multiprocessing.Queue`将每个Process所运行的结果存放到这个共享记忆体，再由FIFO来取结果。
```py
from multiprocessing import Process, Queue
import time


def check_value_in_list(x, i, number_of_process, queue):
    lower = int(i * 10**8 / number_of_process)
    upper = int((i + 1) * 10**8)
    number_of_hit = []
    for i in range(lower, upper):
        if i in x:
            number_of_hit += [i]
    queue.put((lower, upper, number_of_hit))

if __name__ == "__main__":
    num_process = 4
    queue = Queue(num_process)
    tic = time.time()
    ps = [
        Process(target=check_value_in_list, args=([1, 2, 3], i, num_process, queue))
        for i in range(0, num_process)
    ]
    for p in ps:
        p.start()
    # check_value_in_list([1, 2, 3], 0, num_process, queue)
    while num_process > 0:
        if queue.empty():
            time.sleep(0.5)
        else:
            num_process -= 1
            lower, upper, number_of_hit = queue.get()
            print(
                "Between",
                lower,
                "and",
                upper,
                f"we have {len(number_of_hit)}{number_of_hit}",
                "value in the range",
            )
    print("elapsed time =", time.time() - tic, "second")
'''
Between 0 and 100000000 we have 3[1, 2, 3] value in the range
Between 25000000 and 200000000 we have 0[] value in the range
Between 50000000 and 300000000 we have 0[] value in the range
Between 75000000 and 400000000 we have 0[] value in the range
elapsed time = 9.07421326637268 second
'''
```
`multiprocessing.cpu_count()`方法可以帮助我们知道设备的核心数量；可以使用`multiprocessing.Pool`来自动分配一个池帮我们管理，其中有很奇葩的方法`Pool.starmap()`，可以用tuple集合来传多参数：
```py
from multiprocessing import Pool, cpu_count
import time


def square(x, y, z):
    return x**y + z

if __name__ == "__main__":
    num_cpu_to_use = max(1, cpu_count() - 1)
    print("Number of cpus being used:", num_cpu_to_use)
    tic = time.time()
    star_args = [(x, 3 - i, 1) for i, x in enumerate([1, 2, 3])]
    with Pool(num_cpu_to_use) as mp_pool:
        result = mp_pool.starmap(square, star_args)
    print(result, "Pool elapsed time =", time.time() - tic)
    tic = time.time()
    result = map(lambda x, y, z: x**y + z, [1, 2, 3], [3, 2, 1], [1] * 3)
    print(list(result), "Main Thread elapsed time =", time.time() - tic)

'''
Number of cpus being used: 7
[2, 5, 4] Pool elapsed time = 0.05268287658691406
[2, 5, 4] Main Thread elapsed time = 3.0994415283203125e-06
'''
```
因此当我们想要一次获得所有结果时，可以利用`Pool.starmap()`，上面例子可以改写成：
```py
from multiprocessing import Pool, cpu_count
import time


def check_value_in_list(x, i, number_of_process):
    lower = int(i * 10**8 / number_of_process)
    upper = int((i + 1) * 10**8)
    number_of_hit = []
    for i in range(lower, upper):
        if i in x:
            number_of_hit += [i]
    return lower, upper, number_of_hit

if __name__ == "__main__":
    num_cpu_to_use = max(1, cpu_count() - 1)
    star_args = [([1, 2, 3], i, 4) for i in range(4)]
    tic = time.time()
    with Pool(num_cpu_to_use) as mp_pool:
        results = mp_pool.starmap(check_value_in_list, star_args) #main thread will be block here
    for result in results:
        lower, upper, number_of_hit = result
        print(
            "Between",
            lower,
            "and",
            upper,
            f"we have {len(number_of_hit)}{number_of_hit}",
            "value in the range",
        )
    print("Pool elapsed time =", time.time() - tic)
'''
Between 0 and 100000000 we have 3[1, 2, 3] value in the range
Between 25000000 and 200000000 we have 0[] value in the range
Between 50000000 and 300000000 we have 0[] value in the range
Between 75000000 and 400000000 we have 0[] value in the range
Pool elapsed time = 8.973009824752808
'''
```
其实和`Queue`的效率一样，但是用Queue的话，主线程不会被堵死在`starmap()`


### Pylyzer 
https://github.com/mtshiba/pylyzer \
是一个很好的lsp，可惜目前只支援vscode。
使用pylyzer server需要主动开启服务器：
```shell
source venv/bin/activate
ERG_PATH=venv/lib/python3.10/site-packages/.erg pylyzer --server
```
在2023/05/08的时候无法辨识venv安装的package，import会报错；因此不值得使用。