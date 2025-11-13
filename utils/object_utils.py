from typing import Any, Dict, List


def pick_properties(
    d: Dict[str, Any] | None, keys: List[str] | None = None
) -> Dict[str, Any]:
    """
    获取字典中指定的属性，合成并返回新的字典

    Args:
        d: 原始字典
        keys: 需要提取的属性

    Returns:
        新的字典
    """

    if not isinstance(d, dict) or (isinstance(d, dict) and len(d) == 0):
      return {}

    if not isinstance(keys, list) or (isinstance(keys, list) and len(keys) == 0):
      return d if isinstance(d, dict) else {}

    return {k: d[k] for k in keys if k in d} if isinstance(d, dict) else {}

def extract_valid_object(object: Any = None) -> Dict[str, Any]:
    """
    萃取有效对象

    Args:
        object: 原始对象

    Returns:
        返回的必为对象
    """
    return object if isinstance(object, dict) and len(object) > 0 else {}