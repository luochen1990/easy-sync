import inspect
import ast
import sys
from typing import Any, Awaitable, Callable, TypeVar, ParamSpec
import textwrap

P = ParamSpec("P")
R = TypeVar("R")

# def _is_sync_compatible_decorator(decorator: ast.expr) -> bool:
#     if isinstance(decorator, ast.Name) and decorator.id == 'sync_compatible':
#         return True
#     #elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == 'sync_compatible':
#     #    return True
#     return False

class FunctionTransformer(ast.NodeTransformer):
    def __init__(self):
        self.need_time_import = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # 移除 @sync_compatible 装饰器
        #new_decorator_list = [decorator for decorator in node.decorator_list if not _is_sync_compatible_decorator(decorator)]

        # 将 async def 转换为 def，并修改函数名
        new_node = ast.FunctionDef(
            name=node.name + '__sync__',
            args=node.args,
            body=node.body,
            decorator_list=[], #移除所有装饰器，因为它们是为异步函数设计的，很可能不适用于同步函数
            returns=node.returns,
            type_comment=node.type_comment,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        if sys.version_info >= (3, 12):
            new_node.type_params = node.type_params

        # 继续遍历新的函数定义节点
        return self.visit(new_node)

    def visit_Await(self, node: ast.Await):
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'sleep' and isinstance(call.func.value, ast.Name) and call.func.value.id == 'asyncio':
            # 将 await asyncio.sleep(1) 替换为 time.sleep(1)
            self.need_time_import = True
            new_call = ast.Call(func=ast.Attribute(value=ast.Name(id='time', ctx=ast.Load()), attr='sleep', ctx=ast.Load()), args=call.args, keywords=call.keywords)
            return new_call
        else:
            # 将 await f(x) 替换为 f(x).wait()
            new_call = ast.Call(func=ast.Attribute(value=call, attr='wait', ctx=ast.Load()), args=[], keywords=[])
            return new_call


def transform_function_to_sync(func: Callable[P, Awaitable[R]]) -> Callable[P, R]:
    # 获取函数源代码
    source_code = inspect.getsource(func)

    # 去除前导空白，确保缩进一致
    source_code = textwrap.dedent(source_code)

    # 解析源代码为AST
    tree = ast.parse(source_code)

    #print("tree", ast.dump(tree, indent=2))

    # 创建转换器并应用到AST
    transformer = FunctionTransformer()

    new_tree = transformer.visit(tree)

    # NOTE: not working
    # if transformer.need_time_import:
    #     import_time_stmt = ast.Import(names=[ast.alias(name='time', asname=None)])
    #     new_tree.body.insert(0, import_time_stmt)

    new_source_code = ast.unparse(new_tree)

    #print("new_tree", ast.dump(new_tree, indent=2))

    #print("new_source_code:")
    #print(new_source_code)

    # 编译修改后的AST为代码对象
    code = compile(new_source_code, filename="<ast>", mode="exec")

    # 创建一个新的函数对象
    local_vars : dict[str, Any] = {}

    globals : dict[str, Any]

    if transformer.need_time_import:
        import time
        globals = {"time": time} | func.__globals__
    else:
        globals = func.__globals__

    exec(code, globals, local_vars)

    new_func = local_vars[func.__name__ + '__sync__']

    return new_func


if __name__ == '__main__': # pragma: no cover
    import asyncio

    y = 100

    async def some_async_function(x: int) -> int:
        await asyncio.sleep(1)
        return x + y

    new_func = transform_function_to_sync(some_async_function)

    print(new_func(3))
