from typing import Any, Dict, Optional
import yaml
import logging

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
