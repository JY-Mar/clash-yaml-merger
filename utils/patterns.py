'''
Date         : 2025-10-09 01:32:33
LastEditTime : 2026-03-24 14:23:44
Description  : Regular expression
'''

# 远程YAML文件正则表达式
REMOTE_YAML_PATTERN = r"^https:\/\/.+\.yaml$"

# 远程文件正则表达式
REMOTE_FILE_PATTERN = r"^http(s)?:\/\/.+$"

# 相对位置的 YAML 文件正则表达式
RELATIVE_YAML_PATTERN = r"^(?!(https?://|ftp://|file:///)).+\.yaml$"

# 相对位置的 TXT 文件正则表达式
RELATIVE_TXT_PATTERN = r"^(?!(https?://|ftp://|file:///)).+\.txt$"

# settings.yaml fconfs目录配置正则表达式
FCONFS_DIR_PATTERN = r"([a-zA-Z][a-zA-Z0-9_-]*)\|([^;]+;?)"

# settings.yaml 同父目录的多个文件正则表达式
MULTI_DIR_PATTERN = r"\{([a-zA-Z0-9-_]+\.(yaml|yml|txt),?)+\}$"

# base64正则表达式
BASE64_PATTERN = r'^[A-Za-z0-9+/]+={0,2}$'

# 订阅报文头正则表达式
SUB_HEADERS_PATTERN = r"upload=(\d+); download=(\d+); total=(\d+); expire=(\d+)"
