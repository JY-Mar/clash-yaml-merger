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


def load_config() -> Dict[str, Any]:
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

            fconf_r_fs = f"{config['github']['fconf_remote_files']}".strip()

            fconf_dirs = f"{config['github'][f'fconf_directories']}".strip()
            if fconf_dirs and fconf_r_fs:
                config["github"][f"fconf_directories"] = ",".join(
                    list(dict.fromkeys(fconf_r_fs.split(",") + fconf_dirs.split(",")))
                )
            elif fconf_dirs and not fconf_r_fs:
                config["github"][f"fconf_directories"] = fconf_dirs

            sub_dir = f"{config['github']['sub_directory']}".strip()
            if sub_dir:
                config["github"]["sub_directory"] = sub_dir

            rule_dir = f"{config['github']['rule_directory']}".strip()
            if rule_dir:
                config["github"]["rule_directory"] = rule_dir

            return config
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ 配置文件格式错误: {e}")
        sys.exit(1)
