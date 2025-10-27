"""
Author       : Scientificat
Date         : 2025-10-23 07:54:42
LastEditTime : 2025-10-23 08:00:57
LastEditors  : Scientificat
Description  : 文件描述
"""

import base64
import re
from typing import Any, Dict, Optional
import requests
import yaml

def load_yaml_content(content: str) -> Optional[Dict[str, Any]]:
    """
    解析YAML内容

    Args:
        content: YAML字符串内容

    Returns:
        解析后的字典，失败返回None
    """
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"YAML解析失败: {e}")
        return None

BASE64_PATTERN = r"^[A-Za-z0-9+/]+={0,2}$"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36"
}
response = requests.get("", headers=headers)

if response.status_code == 200:
    file_content = response.text
    count = 0
    if re.fullmatch(BASE64_PATTERN, file_content) is not None:

        # 解码为字节
        decoded_bytes = base64.b64decode(file_content)
        # 如果你知道是 UTF-8 编码的文本，可以转为字符串
        decoded_str = decoded_bytes.decode("utf-8")
        print(decoded_str)

        count = decoded_str.count("ss://")
        count += decoded_str.count("ssr://")
        count += decoded_str.count("vmess://")

        print(count)
    else:
        yaml_content = load_yaml_content(file_content)
        if yaml_content and isinstance(yaml_content, dict):
            _proxies = yaml_content.get("proxies", [])
            count = len(_proxies)

        print(count)
else:
    print(f"Error: {response.status_code}")
