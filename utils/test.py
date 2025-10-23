"""
Author       : Scientificat
Date         : 2025-10-23 07:54:42
LastEditTime : 2025-10-23 08:00:57
LastEditors  : Scientificat
Description  : 文件描述
"""

import base64
import re
import requests

BASE64_PATTERN = r"^[A-Za-z0-9+/]+={0,2}$"

response = requests.get("https://jdddf.stc-spare2.com/link/pCWCI8auEY91py6z?sub=2")

if response.status_code == 200:
    file_content = response.text
    if re.fullmatch(BASE64_PATTERN, file_content) is not None:

        # 解码为字节
        decoded_bytes = base64.b64decode(file_content)

        # 如果你知道是 UTF-8 编码的文本，可以转为字符串
        decoded_str = decoded_bytes.decode("utf-8")

        count = decoded_str.count("ssr://")

        print(count)
else:
    print(f"Error: {response.status_code}")
