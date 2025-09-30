from typing import List


def split_str_to_array(s: str, flatten: bool = False) -> List[str] | List[List[str]]:
    """
    将字符串按 ';' 分割为第一维，再按 ',' 分割为第二维。
    自动过滤空字符串和空子数组。

    Args:
        s: 待分割的字符串
        flatten: 是否展平为一维数组（默认 False）

    Returns:
        二维数组或一维数组
    """
    result = []
    for group in s.split(";"):
        items = [item.strip() for item in group.split(",") if item.strip()]
        if items:
            result.append(items)

    return [item for sublist in result for item in sublist] if flatten else result
