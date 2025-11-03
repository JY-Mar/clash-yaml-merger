import re
import time
from typing import Any, Dict, Optional
import yaml
import logging
import requests
from utils.patterns import SUB_HEADERS_PATTERN

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
        logger.error(f"YAML解析失败: {e}")
        return None


def trans_b_to_upper(b: int) -> Dict[str, Any]:
    """
    将字符串中的B转为KB、MB、GB

    Args:
        b: 字节

    Returns:
        转换后的数值 + 单位
    """
    unit = "B"
    value = b
    if isinstance(value, int) and value > 1024:
        value = value / 1024
        unit = "KB"
        if value > 1024:
            value = value / 1024
            unit = "MB"
            if value > 1024:
                value = value / 1024
                unit = "GB"

    return {"value": value, "unit": unit}


def request_url_content(
    url: str,
    headers: Dict[str, Any] = {
        "User-Agent": "Clash.Meta Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115.0 Safari/537.36"
    },
) -> Optional[Dict[str, Any]]:
    """
    从URL请求文件内容

    Args:
        url: 文件URL
        headers: 请求头

    Returns:
        请求到的文件内容，失败返回None
    """
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return_info: Dict[str, Any] = {"content": response.text}
            userinfo = response.headers.get("subscription-userinfo", "")
            match = re.search(SUB_HEADERS_PATTERN, userinfo)
            if match:
                upload_int = int(match.group(1))
                download_int = int(match.group(2))
                used = trans_b_to_upper(upload_int + download_int)
                total = trans_b_to_upper(int(match.group(3)))
                expire = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(int(match.group(4)))
                )
                return_info["overview"] = (
                    f"{used['value']:.2f}{used['unit']} / {total['value']:.2f}{total['unit']} · {expire}"
                )
                return_info["used"] = f"{used['value']:.2f}{used['unit']}"
                return_info["total"] = f"{total['value']:.2f}{total['unit']}"
                return_info["expire"] = expire
            else:
                return_info["overview"] = None
                return_info["used"] = None
                return_info["total"] = None
                return_info["expire"] = None

            return return_info
        else:
            return None
    except requests.RequestException as e:
        return None
