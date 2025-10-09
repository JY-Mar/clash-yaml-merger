import re
from typing import List
from utils.patterns import FCONFS_DIR_PATTERN


def split_str_to_2d_array(s: str) -> List[List[str]]:
    """
    将字符串按 ';' 分割为第一维，再按 ',' 分割为第二维。
    自动过滤空字符串和空子数组。

    Args:
        s: 待分割的字符串

    Returns:
        二维数组
    """

    result: List[List[str]] = []
    for group in s.split(";"):
        items = [item.strip() for item in group.split(",") if item.strip()]
        if items:
            result.append(items)

    return result


def split_str_to_1d_array(s: str) -> List[str]:
    """
    将字符串按 ';' 分割为第一维，再按 ',' 分割为第二维。
    自动过滤空字符串和空子数组。
    平铺为一维数组。

    Args:
        s: 待分割的字符串

    Returns:
        一维数组
    """

    result: List[List[str]] = split_str_to_2d_array(s)

    flatten_result: List[str] = [item for sublist in result for item in sublist]

    return flatten_result


def cut_fonfs_name(s_list: List[str]) -> str:
    """
    从字符串列表中提取文件名

    Args:
        s_list: 待分割的字符串的数组

    Returns:
        文件名
    """

    res: str = ""
    for s in s_list:
        if re.fullmatch(FCONFS_DIR_PATTERN, s) is not None:
            res = s.split("|")[0]
            break
        elif "/" in s:
            res = s.rsplit("/", 1)[-1]
    if not res:
        res = s_list[0]

    return res

def filter_valid_strings(s_list: List[str] | None) -> List[str]:
    """
    过滤掉无效的字符串（空、None、仅空格）

    Args:
        s_list: 待过滤的字符串列表

    Returns:
        过滤后的字符串列表
    """

    if not isinstance(s_list, list):
        return []

    valid_strings = list(filter(lambda s: isinstance(s, str) and s.strip(), s_list))

    return valid_strings