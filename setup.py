#!/usr/bin/env python3
"""
Clash配置整合工具设置脚本
帮助用户快速配置GitHub Secrets和验证设置
"""

import os
import sys
import getpass
from typing import Dict, Any

from utils.config_utils import simple_load_config, simple_save_config


def setup_github_config():
    """设置GitHub相关配置"""
    print("\n🔧 GitHub配置设置")
    print("=" * 50)

    config = simple_load_config()

    # GitHub仓库配置
    print("\n📁 私有仓库信息:")
    owner = input(f"仓库所有者用户名 [{config['github']['owner']}]: ").strip()
    if owner:
        config["github"]["owner"] = owner

    repo = input(f"仓库名称 [{config['github']['repository']}]: ").strip()
    if repo:
        config["github"]["repository"] = repo

    fconfs_r_yaml = input(
        f"远程订阅文件 [{config['github']['fconfs_remote_yaml']}]: "
    ).strip()

    fconfs_dirs_1 = input(
        f"订阅文件目录 [{config['github']['fconfs_directories_1']}]: "
    ).strip()
    if fconfs_dirs_1 and fconfs_r_yaml:
        config["github"]["fconfs_directories_1"] = ",".join(
            list(dict.fromkeys(fconfs_r_yaml.split(",") + fconfs_dirs_1.split(",")))
        )
    elif fconfs_dirs_1 and not fconfs_r_yaml:
        config["github"]["fconfs_directories_1"] = fconfs_dirs_1

    fconfs_dirs_2 = input(
        f"订阅文件目录 [{config['github']['fconfs_directories_2']}]: "
    ).strip()
    if fconfs_dirs_2 and fconfs_r_yaml:
        config["github"]["fconfs_directories_2"] = ",".join(
            list(dict.fromkeys(fconfs_r_yaml.split(",") + fconfs_dirs_2.split(",")))
        )
    elif fconfs_dirs_2 and not fconfs_r_yaml:
        config["github"]["fconfs_directories_2"] = fconfs_dirs_2

    fconfs_dirs_3 = input(
        f"订阅文件目录 [{config['github']['fconfs_directories_3']}]: "
    ).strip()
    if fconfs_dirs_3 and fconfs_r_yaml:
        config["github"]["fconfs_directories_3"] = ",".join(
            list(dict.fromkeys(fconfs_r_yaml.split(",") + fconfs_dirs_3.split(",")))
        )
    elif fconfs_dirs_3 and not fconfs_r_yaml:
        config["github"]["fconfs_directories_3"] = fconfs_dirs_3

    proxies_dir = input(f"订阅文件目录 [{config['github']['proxies_directory']}]: ").strip()
    if proxies_dir:
        config["github"]["proxies_directory"] = proxies_dir

    rules_dir = input(f"规则文件目录 [{config['github']['rules_directory']}]: ").strip()
    if rules_dir:
        config["github"]["rules_directory"] = rules_dir

    # 认证配置
    print("\n🔐 认证配置:")
    auth_token = getpass.getpass("访问认证Token (输入时不显示): ").strip()
    if auth_token:
        config["authentication"]["token"] = auth_token

    simple_save_config(config)

    return config


def generate_secrets_info(config: Dict[str, Any]):
    """生成GitHub Secrets配置信息"""
    print("\n🔑 GitHub Secrets配置")
    print("=" * 50)
    print("请在您的GitHub仓库设置中添加以下Secrets:")
    print()

    secrets = [
        ("CLASH_GITHUB_TOKEN", "GitHub访问令牌（需要repo权限）", "ghp_xxxxxxxxxxxx"),
        ("CLASH_REPO_OWNER", "私有仓库所有者", config["github"]["owner"]),
        ("CLASH_REPO_NAME", "私有仓库名称", config["github"]["repository"]),
        ("CLASH_AUTH_TOKEN", "访问认证Token", config["authentication"]["token"]),
    ]

    for name, desc, value in secrets:
        print(f"📌 {name}")
        print(f"   描述: {desc}")
        print(f"   值: {value}")
        print()


def validate_setup():
    """验证设置"""
    print("\n✅ 设置验证")
    print("=" * 50)

    # 检查必要文件
    required_files = [
        "scripts/merge_clash_config.py",
        ".github/workflows/update-config.yml",
        "config/settings.yaml",
        "requirements.txt",
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("❌ 缺少必要文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print("✅ 所有必要文件都存在")

    # 检查配置文件
    try:
        config = simple_load_config()
        print("✅ 配置文件格式正确")

        # 检查关键配置
        if config["github"]["owner"] == "your-username":
            print("⚠️  请更新GitHub仓库所有者配置")

        if config["github"]["repository"] == "clash-config":
            print("⚠️  请更新GitHub仓库名称配置")

        if config["authentication"]["token"] == "your-secret-auth-token":
            print("⚠️  请更新认证Token配置")

        return True

    except Exception as e:
        print(f"❌ 配置文件验证失败: {e}")
        return False


def show_next_steps():
    """显示后续步骤"""
    print("\n🚀 后续步骤")
    print("=" * 50)

    steps = [
        "1. 创建GitHub私有仓库存放您的Clash配置文件",
        "2. 在私有仓库中创建 proxies/ 和 rules/ 目录",
        "3. 将您的订阅文件放入 proxies/ 目录",
        "4. 将您的规则文件放入 rules/ 目录",
        "5. 获取GitHub Personal Access Token（需要repo权限）",
        "6. 在当前仓库设置中添加上述GitHub Secrets",
        "7. 启用GitHub Pages（Source选择GitHub Actions）",
        "8. 运行GitHub Actions工作流生成配置",
        "9. 使用生成的订阅链接",
    ]

    for step in steps:
        print(f"   {step}")

    print("\n📖 详细说明请参考 README.md 文件")


def main():
    """主函数"""
    print("🎯 Clash配置整合工具设置向导")
    print("=" * 50)

    # 设置GitHub配置
    config = setup_github_config()

    # 生成Secrets信息
    generate_secrets_info(config)

    # 验证设置
    if validate_setup():
        print("\n🎉 设置完成！")
        show_next_steps()
    else:
        print("\n❌ 设置验证失败，请检查配置")
        sys.exit(1)


if __name__ == "__main__":
    main()
