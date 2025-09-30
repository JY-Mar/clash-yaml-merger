from copy import deepcopy
from typing import Any


def deep_merge(a: Any, b: Any) -> Any:
    """
    深合并，将b合并到a中

    Args:
        a: 合并对象1
        b: 合并对象2

    Returns:
        文件内容字符串，失败返回None
    """
    # 类型一致才合并
    if type(a) != type(b):
        return deepcopy(b)

    # 合并 dict（Map）
    if isinstance(a, dict):
        result = deepcopy(a)
        for key, value in b.items():
            if key in result:
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = deepcopy(value)
        return result

    # 合并 list
    elif isinstance(a, list):
        return deepcopy(a) + deepcopy(b)

    # 合并 set
    elif isinstance(a, set):
        return deepcopy(a) | deepcopy(b)

    # 合并对象（自定义类）
    elif hasattr(a, "__dict__") and hasattr(b, "__dict__"):
        result = deepcopy(a)
        for attr in b.__dict__:
            if hasattr(result, attr):
                merged_value = deep_merge(getattr(result, attr), getattr(b, attr))
                setattr(result, attr, merged_value)
            else:
                setattr(result, attr, deepcopy(getattr(b, attr)))
        return result

    # 基础类型直接替换
    else:
        return deepcopy(b)