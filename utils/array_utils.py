import re
from typing import Any, List
from utils.patterns import MULTI_DIR_PATTERN

def unshift_to_array(data: List[List[str]], prefix: str | List[str]) -> List[List[str]]:
    """
    向二维数组的每个一维数组头部插入一个字符串或拼接一个字符串数组。
    - 如果 prefix 是字符串且非空，则插入该字符串
    - 如果 prefix 是字符串数组，则拼接所有非空字符串
    - 空字符串或空数组不会插入

    Args:
        data: 待处理的二维数组
        prefix: 待插入值，字符串或字符串数组

    Returns:
        处理后的二维数组
    """
    # 处理字符串情况
    if isinstance(prefix, str):
        cleaned = prefix.strip()
        if not cleaned:
            return data  # 空字符串不插入
        return [[cleaned] + row for row in data if isinstance(row, list)]

    # 处理字符串数组情况
    elif isinstance(prefix, list):
        cleaned_list = [
            item.strip() for item in prefix if isinstance(item, str) and item.strip()
        ]
        if not cleaned_list:
            return data  # 空数组或全为空字符串不插入
        return [cleaned_list + row for row in data if isinstance(row, list)]

    # 其他类型不处理
    return data


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

    valid_strings = [
        "".join(s.split()) for s in s_list if isinstance(s, str) and s.strip()
    ]

    return valid_strings


def extract_valid_array(array: Any = None) -> List[Any]:
    """
    萃取有效列表

    Args:
        object: 原始列表

    Returns:
        返回的必为列表
    """
    return array if isinstance(array, list) and len(array) > 0 else []


def break_down_multi_dirs(s_list: List[List[str]]) -> List[List[str]]:
    """
    将包含多个文件名的字符串列表拆分成多个字符串列表

    Args:
        s_list: 包含多个文件名的字符串列表

    Returns:
        拆分成后的字符串列表
    """

    result: List[List[str]] = []

    if isinstance(s_list, list):
        for dim1 in s_list:
            if isinstance(dim1, list):
                res: List[str] = []
                for dim1item in dim1:
                    if isinstance(dim1item, str):
                        regx = re.compile(MULTI_DIR_PATTERN)
                        _dim1item = re.sub(r"\s", "", dim1item.strip())
                        regxResult = regx.search(_dim1item)
                        if regxResult is not None:
                            # regxResult => {*.yaml,*.yaml}
                            matched = re.sub(r"\{|\}", "", regxResult.group(0))
                            splitted_list = [item.strip() for item in matched.split(',') if item.strip()]
                            if isinstance(splitted_list, list) and len(splitted_list) > 0:
                                res.extend(splitted_list)
                        else:
                            res.append(dim1item.strip())
                    else:
                        continue

                result.append(res)
            else:
                result.append(dim1)

    return result
