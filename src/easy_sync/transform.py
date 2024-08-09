import inspect
import ast
import sys
from typing import Any, Awaitable, Callable, TypeVar, ParamSpec
import textwrap

P = ParamSpec("P")
R = TypeVar("R")

def _is_sync_compatible_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name) and decorator.id == 'sync_compatible':
        return True
    return False

class FunctionTransformer(ast.NodeTransformer):
    def __init__(self):
        self.is_toplevel = True
        self.need_time_import = False
        self.parents : list[ast.AST] = []
        self.new_nodes : set[ast.AST] = set()
        self.visited_nodes : set[ast.AST] = set()

    def visit(self, node: ast.AST):
        if node in self.visited_nodes:
            return node
        if node in self.new_nodes:
            return node

        is_nesting = isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
        if is_nesting:
            self.parents.append(node)
        result = super().visit(node)
        if is_nesting:
            self.parents.pop()
        return result

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):

        #print(self.is_toplevel)
        #print(node.name)

        self.visited_nodes.add(node)

        # 将 async def 转换为 def，并修改函数名
        if sys.version_info >= (3, 12): #pragma: no cover
            _new_sync_node = ast.FunctionDef(
                name=node.name + '__sync__',
                args=node.args,
                body=node.body,
                decorator_list=[], #移除所有装饰器，因为它们是为异步函数设计的，很可能不适用于同步函数
                returns=node.returns,
                type_comment=node.type_comment,
                lineno=node.lineno,
                col_offset=node.col_offset,
                type_params = node.type_params
            )
        else:
            _new_sync_node = ast.FunctionDef(
                name=node.name + '__sync__',
                args=node.args,
                body=node.body,
                decorator_list=[], #移除所有装饰器，因为它们是为异步函数设计的，很可能不适用于同步函数
                returns=node.returns,
                type_comment=node.type_comment,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

        if self.is_toplevel:
            self.is_toplevel = False
            new_sync_node = self.visit(_new_sync_node)
            return new_sync_node
        else: # nested inner function

            # 将 async def 的装饰器转换为 @sync_compatible(sync_fn=xxx__sync__)
            new_decorator = ast.Call(ast.Name(id='sync_compatible', ctx=ast.Load()), [], [ast.keyword(arg='sync_fn', value=ast.Name(id=node.name + '__sync__', ctx=ast.Load()))])
            new_decorator_list = [new_decorator if _is_sync_compatible_decorator(d) else d for d in node.decorator_list]

            if sys.version_info >= (3, 12): #pragma: no cover
                new_async_node = ast.AsyncFunctionDef(
                    name=node.name,
                    args=node.args,
                    body=node.body, #[self.visit(x) for x in node.body],
                    decorator_list=new_decorator_list, #替换装饰器
                    returns=node.returns,
                    type_comment=node.type_comment,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    type_params = node.type_params
                )
            else:
                new_async_node = ast.AsyncFunctionDef(
                    name=node.name,
                    args=node.args,
                    body=node.body, #[self.visit(x) for x in node.body],
                    decorator_list=new_decorator_list, #替换装饰器
                    returns=node.returns,
                    type_comment=node.type_comment,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )

            self.new_nodes.add(new_async_node) #避免重复处理

            # 将 同步函数的定义 和 异步函数的定义都 插入到父函数的body中
            # 这里返回的 会替换当前位置，所以插入的位置要在当前位置之后

            #print(f"parents: {[parent.name for parent in self.parents]}")
            #print(f"current: {node.name}")

            parent : ast.AsyncFunctionDef = self.parents[-2] #type: ignore
            print(f"current: {node.name}, parent: {parent.name}")
            index = parent.body.index(node)

            #print(f"inserted node: {new_async_node.name} at index: {index}")
            parent.body.insert(index + 1, new_async_node)

            new_sync_node = self.visit(_new_sync_node)
            self.new_nodes.add(new_sync_node) #避免重复处理

            return self.visit(new_sync_node)

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

    #print("[NEW_SOURCE_CODE]:")
    #print(new_source_code)

    # 编译修改后的AST为代码对象
    try:
        code = compile(new_source_code, filename="<ast>", mode="exec")
    except Exception as e: #pragma: no cover
        print("[Transformed Code]:")
        print(new_source_code)
        raise Exception("[transform_function_to_sync()]: failed to compile code", {"code": new_source_code}) from e

    # 创建一个新的函数对象
    local_vars : dict[str, Any] = {}

    globals : dict[str, Any]

    if transformer.need_time_import:
        import time
        globals = {"time": time} | func.__globals__
    else:
        globals = func.__globals__

    try:
        exec(code, globals, local_vars)
    except Exception as e: #pragma: no cover
        print("[Transformed Code]:")
        print(new_source_code)
        raise Exception("[transform_function_to_sync()]: failed to exec code", {"code": new_source_code}) from e

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
