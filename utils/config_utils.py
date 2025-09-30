import sys
from typing import Any, Dict

import yaml


def simple_load_config() -> Dict[str, Any]:
    """简单加载配置文件"""
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


def simple_save_config(config: Dict[str, Any]) -> None:
    """简单保存配置文件"""
    config_path = "config/settings.yaml"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(
                config, f, default_flow_style=False, allow_unicode=True, sort_keys=False
            )
        print(f"✅ 配置已保存到: {config_path}")
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")


def load_config(flag: int = 1) -> Dict[str, Any]:
    """加载配置文件"""
    config_path = "config/settings.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            owner = f"{config['github']['owner']}".strip()
            if owner:
                config["github"]["owner"] = owner

            repo = f"{config['github']['repository']}".strip()
            if repo:
                config["github"]["repository"] = repo

            fconfs_r_yaml = f"{config['github']['fconfs_remote_yaml']}".strip()

            fconf_dirs = f"{config['github'][f'fconfs_directories_{flag}']}".strip()
            if fconf_dirs and fconfs_r_yaml:
                config["github"][f"fconfs_directories_{flag}"] = ",".join(
                    list(dict.fromkeys(fconfs_r_yaml.split(",") + fconf_dirs.split(",")))
                )
            elif fconf_dirs and not fconfs_r_yaml:
                config["github"][f"fconfs_directories_{flag}"] = fconf_dirs

            proxies_dir = f"{config['github']['proxies_directory']}".strip()
            if proxies_dir:
                config["github"]["proxies_directory"] = proxies_dir

            rules_dir = f"{config['github']['rules_directory']}".strip()
            if rules_dir:
                config["github"]["rules_directory"] = rules_dir

            return config
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)

# 远程YAML文件正则表达式
REMOTE_YAML_PATTERN = r"^https:\/\/.+\.yaml$"

# YAML文件正则表达式
YAML_PATTERN = r".+\.yaml$"