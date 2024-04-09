FastAPI
---
运行本地的服务器：
```shell
uvicorn <project directory>.main:app --reload
```
加入`--reload`参数可以让每次修改保存后，都会重新运行服务器。


---
PyTest
---

使用pytest指令：
```shell
# 显示每次执行测试方法时所用到的指令
pytest --fixtures-per-test
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
async是单核单线程跑多个任务，因此一定会有些许的延迟，花费多工任务的时间比单任务的时间还长。但不会使单线程停滞在一个任务上。
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
import asyncio
import time

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
# def ...
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

