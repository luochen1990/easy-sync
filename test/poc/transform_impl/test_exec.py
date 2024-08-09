from typing import Any, TypeVar, ParamSpec

P = ParamSpec("P")
R = TypeVar("R")

y = 100

source_code = '''
import time

def some_sync_function(x: int) -> int:
    time.sleep(1)
    return x + y
'''

code = compile(source_code, filename="<ast>", mode="exec")

import time

local_vars : dict[str, Any] = {}

# 看起来必须在这里的globals中加入time，否则exec中的time.sleep会找不到time (即使在 source_code 中已经import time)
exec(code, {"y": y, "time": time}, local_vars)

new_func = local_vars['some_sync_function']

print(new_func(2))
