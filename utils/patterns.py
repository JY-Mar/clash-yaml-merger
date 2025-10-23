'''
Author       : Scientificat
Date         : 2025-10-09 01:32:33
LastEditTime : 2025-10-23 07:58:44
LastEditors  : Scientificat
Description  : Regular expression
'''

# 远程YAML文件正则表达式
REMOTE_YAML_PATTERN = r"^https:\/\/.+\.yaml$"

# 远程文件正则表达式
REMOTE_FILE_PATTERN = r"^http(s)?:\/\/.+$"

# YAML文件正则表达式
YAML_PATTERN = r".+\.yaml$"

# settings.yaml fconfs目录配置正则表达式
FCONFS_DIR_PATTERN = r"([a-zA-Z][a-zA-Z0-9_-]*)\|([^;]+;?)"

# base64正则表达式
BASE64_PATTERN = r'^[A-Za-z0-9+/]+={0,2}$'
