import inspect
import ast
import sys
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, ParamSpec
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

        # turn `async def some_func` into `def some_func__sync__`
        if sys.version_info >= (3, 12): #pragma: no cover
            _new_sync_node = ast.FunctionDef(
                name=node.name + '__sync__',
                args=node.args,
                body=node.body,
                decorator_list=[], #NOTE: remove decorators, as they are designed for async functions and may not be applicable to sync functions
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
                decorator_list=[], #NOTE: remove decorators, as they are designed for async functions and may not be applicable to sync functions
                returns=node.returns,
                type_comment=node.type_comment,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

        if self.is_toplevel:
            self.is_toplevel = False
            new_sync_node = self.visit(_new_sync_node)
            return new_sync_node
        else:
            #NOTE: this is for nested inner function

            # turn `@sync_compatible` decorator into `@sync_compatible(sync_fn=xxx__sync__)`
            new_decorator = ast.Call(ast.Name(id='sync_compatible', ctx=ast.Load()), [], [ast.keyword(arg='sync_fn', value=ast.Name(id=node.name + '__sync__', ctx=ast.Load()))])
            new_decorator_list = [new_decorator if _is_sync_compatible_decorator(d) else d for d in node.decorator_list]

            if sys.version_info >= (3, 12): #pragma: no cover
                new_async_node = ast.AsyncFunctionDef(
                    name=node.name,
                    args=node.args,
                    body=node.body,
                    decorator_list=new_decorator_list,
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
                    decorator_list=new_decorator_list,
                    returns=node.returns,
                    type_comment=node.type_comment,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )

            self.new_nodes.add(new_async_node) #avoid duplicate processing

            # NOTE: insert the new async & sync function's definition into the parent function's body
            # the return value will replace the current position, so the insertion position should be after the current position

            #print(f"parents: {[parent.name for parent in self.parents]}")
            #print(f"current: {node.name}")

            parent : ast.AsyncFunctionDef = self.parents[-2] #type: ignore
            print(f"current: {node.name}, parent: {parent.name}")
            index = parent.body.index(node)

            #print(f"inserted node: {new_async_node.name} at index: {index}")
            parent.body.insert(index + 1, new_async_node)

            new_sync_node = self.visit(_new_sync_node)
            self.new_nodes.add(new_sync_node) #avoid duplicate processing

            return self.visit(new_sync_node)

    def visit_Await(self, node: ast.Await):
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == 'sleep' and isinstance(call.func.value, ast.Name) and call.func.value.id == 'asyncio':
            # replace `await asyncio.sleep(1)` into `time.sleep(1)`
            self.need_time_import = True
            new_call = ast.Call(func=ast.Attribute(value=ast.Name(id='time', ctx=ast.Load()), attr='sleep', ctx=ast.Load()), args=call.args, keywords=call.keywords)
            return new_call
        else:
            # replace `await f(x)` into `f(x).wait()`
            new_call = ast.Call(func=ast.Attribute(value=call, attr='wait', ctx=ast.Load()), args=[], keywords=[])
            return new_call


def transform_function_to_sync(func: Callable[P, Awaitable[R]]) -> Callable[P, R]:
    source_code = inspect.getsource(func)

    # remove leading whitespace to ensure consistent indentation
    source_code = textwrap.dedent(source_code)

    tree = ast.parse(source_code)

    #print("tree", ast.dump(tree, indent=2))

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

    try:
        # compile the new source code
        code = compile(new_source_code, filename="<ast>", mode="exec")
    except Exception as e: #pragma: no cover
        print("[Transformed Code]:")
        print(new_source_code)
        raise Exception("[transform_function_to_sync()]: failed to compile code", {"code": new_source_code}) from e

    # prepare for exec
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
