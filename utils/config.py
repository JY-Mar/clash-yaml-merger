"""
Author       : Scientificat 51430248+JY-Mar@users.noreply.github.com
Date         : 2025-09-16 06:27:21
LastEditTime : 2025-09-16 06:27:23
LastEditors  : Scientificat 51430248+JY-Mar@users.noreply.github.com
Description  : 加载文件
"""

import sys
from typing import Any, Dict
import yaml


def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = "config/settings.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)


def save_config(config: Dict[str, Any]) -> None:
    """保存配置文件"""
    config_path = "config/settings.yaml"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
        print(f"✅ 配置已保存到: {config_path}")
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
