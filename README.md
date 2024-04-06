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