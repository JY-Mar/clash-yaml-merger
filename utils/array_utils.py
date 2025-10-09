from typing import List


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

    valid_strings = list(filter(lambda s: isinstance(s, str) and s.strip(), s_list))

    return valid_strings
