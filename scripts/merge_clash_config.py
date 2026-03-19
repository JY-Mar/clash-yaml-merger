#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash配置文件整合工具
从GitHub私有仓库读取多个订阅YAML文件，整合代理节点和规则，生成统一的Clash配置
"""

import os
import re
import sys
import yaml
import requests
import base64
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import logging
from functools import reduce

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
sys.path.insert(0, root_dir)

from utils import files_utils
from utils.files_utils import load_yaml_content
from utils.patterns import (
    BASE64_PATTERN,
    RELATIVE_YAML_PATTERN,
    REMOTE_FILE_PATTERN,
    REMOTE_YAML_PATTERN,
    FCONFS_DIR_PATTERN,
)
from utils.config_utils import load_config
from utils.merge_utils import deep_merge
from utils.string_utils import (
    cut_fonfs_name,
    desensitize_url,
    split_str_to_1d_array,
    split_str_to_2d_array,
)
from utils.array_utils import (
    extract_valid_array,
    unshift_to_array,
    filter_valid_strings,
)
from utils.object_utils import extract_valid_object, get_property, pick_properties

# 设置默认编码
import codecs

# 强制设置UTF-8编码
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

# 确保UTF-8编码
try:
    if hasattr(sys.stdout, "buffer") and sys.stdout.encoding != "utf-8":
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    if hasattr(sys.stderr, "buffer") and sys.stderr.encoding != "utf-8":
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")
except:
    pass  # 在某些环境下可能会失败，忽略错误

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# settings.yaml 配置
settings_config = load_config()


class ClashConfigMerger:
    def __init__(
        self,
        github_token: str = "",
        repo_owner: str = "",
        repo_name: str = "",
        local_mode: bool = False,
    ):
        """
        初始化Clash配置合并器

        Args:
            github_token: GitHub访问令牌
            repo_owner: 仓库所有者
            repo_name: 仓库名称
            local_mode: 是否使用本地模式
        """
        self.local_mode = local_mode
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name

        if not local_mode:
            self.headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            self.base_url = (
                f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents"
            )

    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        获取文件内容（支持本地和GitHub模式）

        Args:
            file_path: 文件路径

        Returns:
            文件内容字符串，失败返回None
        """
        if self.local_mode:
            # 本地模式：直接读取文件
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    logger.info(f"成功读取本地文件: {file_path}")
                    return content
            except FileNotFoundError:
                logger.error(f"本地文件不存在: {file_path}")
                return None
            except Exception as e:
                logger.error(f"读取本地文件失败 {file_path}: {e}")
                return None
        else:
            # GitHub模式：通过API获取
            try:
                if re.fullmatch(REMOTE_YAML_PATTERN, file_path) is not None:
                    # 是yaml文件路径直接读取
                    url = file_path
                    response = requests.get(url)
                    try:
                        yaml_raw_content = response.text
                    except json.JSONDecodeError as e:
                        yaml_raw_content = None
                        logger.error(f"解析失败：不是合法的 JSON 格式: {e}")

                    if yaml_raw_content:
                        logger.info(f"成功获取文件: {desensitize_url(file_path)}")

                    return yaml_raw_content
                else:
                    url = f"{self.base_url}/{file_path}"
                    response = requests.get(url, headers=self.headers)
                    response.raise_for_status()
                    file_data = response.json()

                if file_data["encoding"] == "base64":
                    content = base64.b64decode(file_data["content"]).decode("utf-8")
                    logger.info(f"成功获取文件: {desensitize_url(file_path)}")
                    return content
                else:
                    logger.error(f"不支持的编码格式: {file_data['encoding']}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"获取文件失败 {file_path}: {e}")
                return None
            except Exception as e:
                logger.error(f"解析文件失败 {file_path}: {e}")
                return None

    def get_directory_file(self, file_path: str) -> str | None:
        """
        获取指定文件路径（支持本地和GitHub模式）

        Args:
            file_path: 文件路径

        Returns:
            文件路径
        """
        if self.local_mode:
            # 本地模式：扫描本地目录
            try:
                if not os.path.exists(file_path):
                    logger.warning(f"本地文件不存在: {file_path}")
                    return None

                if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    logger.info(f"发现YAML本地文件: {file_path}")
                    return file_path
                else:
                    logger.warning(f"未发现YAML本地文件: {file_path}")
                    return None

            except Exception as e:
                logger.error(f"识别本地文件失败 {file_path}: {e}")
                return None
        else:
            # GitHub模式：通过API获取
            try:
                url = f"{self.base_url}/{file_path}"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                file_info = response.json()
                if file_info["type"] == "file" and file_info["name"].endswith(".yaml"):
                    logger.info(f"发现YAML文件: {file_info['path']}")
                    return file_info["path"]
                else:
                    logger.warning(f"未发现YAML文件: {file_info['path']}")
                    return None

            except requests.exceptions.RequestException as e:
                logger.error(f"识别文件失败 {file_path}: {e}")
                return None

    def get_directory_files(self, directory_path: str) -> List[str]:
        """
        获取目录下的所有文件列表（支持本地和GitHub模式）

        Args:
            directory_path: 目录路径

        Returns:
            文件路径列表
        """
        if self.local_mode:
            # 本地模式：扫描本地目录
            try:
                if not os.path.exists(directory_path):
                    logger.warning(f"本地目录不存在: {directory_path}")
                    return []

                file_paths = []
                for filename in os.listdir(directory_path):
                    if filename.endswith(".yaml") or filename.endswith(".yml"):
                        file_path = os.path.join(directory_path, filename)
                        file_paths.append(file_path)

                logger.info(
                    f"发现 {len(file_paths)} 个YAML文件在本地目录: {directory_path}"
                )
                return file_paths

            except Exception as e:
                logger.error(f"扫描本地目录失败 {directory_path}: {e}")
                return []
        else:
            # GitHub模式：通过API获取
            try:
                url = f"{self.base_url}/{directory_path}"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                files = response.json()
                file_paths = []

                for file_info in files:
                    if file_info["type"] == "file" and file_info["name"].endswith(
                        ".yaml"
                    ):
                        file_paths.append(file_info["path"])

                if len(file_paths) == 0:
                    logger.warning(
                        f"发现 {len(file_paths)} 个YAML文件在目录: {directory_path}"
                    )
                else:
                    logger.info(
                        f"发现 {len(file_paths)} 个YAML文件在目录: {directory_path}"
                    )
                return file_paths

            except requests.exceptions.RequestException as e:
                logger.error(f"获取目录文件列表失败 {directory_path}: {e}")
                return []

    def merge_proxies(self, configs_with_sources: List[tuple]) -> List[Dict[str, Any]]:
        """
        合并多个配置文件的代理节点

        Args:
            configs_with_sources: 配置文件和来源信息的元组列表 [(config, source_file), ...]

        Returns:
            合并后的代理节点列表（包含来源信息）
        """
        merged_proxies = []
        seen_names = set()

        for config, source_file in configs_with_sources:
            if "proxies" in config and isinstance(config["proxies"], list):
                source_name = os.path.basename(source_file).replace(".yaml", "")
                for proxy in config["proxies"]:
                    if isinstance(proxy, dict) and "name" in proxy:
                        # 避免重复的代理节点名称
                        original_name = proxy["name"]
                        name = original_name
                        counter = 1

                        while name in seen_names:
                            name = f"{original_name}_{counter}"
                            counter += 1

                        proxy["name"] = name
                        proxy["_source_file"] = source_name  # 添加来源标识
                        seen_names.add(name)
                        merged_proxies.append(proxy)

        logger.info(f"合并了 {len(merged_proxies)} 个代理节点")
        return merged_proxies

    def merge_rules(self, rules_files: List[str]) -> List[str]:
        """
        合并规则列表（只使用rule目录下的规则文件）

        Args:
            rules_files: 规则文件路径列表

        Returns:
            合并后的规则列表
        """
        merged_rules = []
        seen_rules = set()

        # 只从规则文件中加载规则，忽略 proxies 文件中的规则
        for rule_file_path in rules_files:
            content = self.get_file_content(rule_file_path)
            if content:
                rule_data = load_yaml_content(content)
                logger.info(f"规则文件 {rule_file_path}")
                if rule_data and "payload" in rule_data:
                    rule_file_name = os.path.basename(rule_file_path).replace(
                        ".yaml", ""
                    )
                    logger.info(f"处理规则文件: {rule_file_name}")

                    for rule in rule_data["payload"]:
                        if isinstance(rule, str) and rule not in seen_rules:
                            # 确保规则格式正确，所有规则都指向"网络代理"
                            rule = rule.strip()
                            if rule:
                                # 所有规则都指向"网络代理"组
                                formatted_rule = f"{rule},网络代理"
                                merged_rules.append(formatted_rule)
                                seen_rules.add(formatted_rule)

        logger.info(f"合并了 {len(merged_rules)} 条规则")
        return merged_rules

    def create_proxy_groups(
        self, proxies: List[Dict[str, Any]], proxies_files: List[str]
    ) -> List[Dict[str, Any]]:
        """
        创建策略组结构

        Args:
            proxies: 代理节点列表
            proxies_files: 订阅文件路径列表

        Returns:
            策略组配置列表
        """
        proxy_names = [proxy["name"] for proxy in proxies if "name" in proxy]

        # 按订阅文件分组代理节点 - 基于来源信息进行精确分组
        temp_groups = {}
        for file_path in proxies_files:
            # 从文件路径提取文件名作为分组名
            file_name = os.path.basename(file_path).replace(".yaml", "")
            temp_groups[file_name] = []

        # 根据代理的来源信息进行精确分组
        for proxy in proxies:
            if isinstance(proxy, dict) and "_source_file" in proxy:
                source_name = proxy["_source_file"]
                proxy_name = proxy.get("name", "")
                if source_name in temp_groups and proxy_name:
                    temp_groups[source_name].append(proxy_name)

        # 创建策略组列表
        proxy_groups = []

        # 1. 创建主网络策略组（只包含 proxies 分组，不包含 rules 分组）
        temp_group_names = list(temp_groups.keys())

        network_proxy_options = ["自动选择", "故障转移"] + temp_group_names
        proxy_groups.append(
            {"name": "网络代理", "type": "select", "proxies": network_proxy_options}
        )

        # 2. 创建自动选择和故障转移组
        proxy_groups.extend(
            [
                {
                    "name": "自动选择",
                    "type": "url-test",
                    "proxies": proxy_names,
                    "url": "http://www.gstatic.com/generate_204",
                    "interval": 300,
                },
                {
                    "name": "故障转移",
                    "type": "fallback",
                    "proxies": proxy_names,
                    "url": "http://www.gstatic.com/generate_204",
                    "interval": 300,
                },
            ]
        )

        # 3. 为每个订阅文件创建策略组（只为 proxies 文件创建，不为 rules 文件创建）
        for temp_item_name, temp_item_proxies in temp_groups.items():
            if temp_item_proxies:
                proxy_groups.append(
                    {
                        "name": temp_item_name,
                        "type": "select",
                        "proxies": ["自动选择", "故障转移"] + temp_item_proxies,
                    }
                )

        logger.info(f"创建了 {len(proxy_groups)} 个策略组")
        return proxy_groups

    def create_base_config(self) -> Dict[str, Any]:
        """
        创建基础配置

        Returns:
            基础配置字典
        """
        return {
            # HTTP 代理端口
            "port": 7890,
            # SOCKS5 代理端口
            "socks-port": 7891,
            # HTTP(S) and SOCKS5 共用端口
            "mixed-port": 7892,
            # Linux 和 macOS 的 redir 透明代理端口 (重定向 TCP 和 TProxy UDP 流量)
            "redir-port": 7893,
            # Linux 的透明代理端口（适用于 TProxy TCP 和 TProxy UDP 流量)
            "tproxy-port": 7894,
            "unified-delay": True,
            "tcp-concurrent": True,
            "find-process-mode": "strict",
            # 允许局域网的连接（可用来共享代理）
            "allow-lan": True,
            # Clash 路由工作模式
            # 规则模式：rule（规则） / global（全局代理）/ direct（全局直连）
            "mode": "rule",
            # Clash 默认将日志输出至 STDOUT
            # 设置日志输出级别 (默认级别：silent，即不输出任何内容，以避免因日志内容过大而导致程序内存溢出）。
            # 5 个级别：silent / info / warning / error / debug。级别越高日志输出量越大，越倾向于调试，若需要请自行开启。
            "log-level": "silent",
            "ipv6": True,
            "udp": True,
            "bind-address": "*",
            # clash 的 RESTful API 监听地址
            "external-controller": "0.0.0.0:9090",
            "external-controller-tls": "0.0.0.0:9443",
            "external-controller-unix": "mihomo.sock",
            "external-controller-pipe": "\\.\\pipe\\mihomo",
            # 存放配置文件的相对路径，或存放网页静态资源的绝对路径
            # Clash core 将会将其部署在 http://{{external-controller}}/ui
            "external-ui": "ui",
            "external-ui-name": "zashboard",
            "external-ui-url": "https://github.com/Zephyruso/zashboard/archive/refs/heads/gh-pages.zip",
            "external-doh-server": "/dns-query",
            "global-client-fingerprint": "chrome",
            "dns": {
                "enable": True,
                "ipv6": False,
                "default-nameserver": ["223.5.5.5", "119.29.29.29", "114.114.114.114"],
                "enhanced-mode": "fake-ip",
                "fake-ip-range": "198.18.0.1/16",
                "use-hosts": True,
                "nameserver": ["223.5.5.5", "119.29.29.29", "114.114.114.114"],
                "fallback": ["1.1.1.1", "8.8.8.8"],
                "fallback-filter": {
                    "geoip": True,
                    "geoip-code": "CN",
                    "ipcidr": ["240.0.0.0/4"],
                },
            },
        }

    def generate_merged_config(
        self,
        fconfs_directories: List[str] = ["fconfs"],
        proxy_providers_directory: str = "proxy-providers",
        proxies_directory: str = "proxies",
        rule_providers_directory: str = "rule-providers",
        rules_directory: str = "rules",
    ) -> Dict[str, Any]:
        """
        生成合并后的配置文件

        Args:
            fconfs_directories: 全量配置文件目录，支持私有仓库目录、单独指定的yaml文件
            proxy_providers_directory: 代理集文件目录
            proxies_directory: 代理节点文件目录
            rule_providers_directory: 规则集文件目录
            rules_directory: 规则文件目录

        Returns:
            合并后的基础配置
        """

        # 1. 创建基础配置
        merged_config = self.create_base_config()

        # MARK: 2.1 全量配置
        # 2.1.1 获取全量配置文件列表
        fconfs_files: List[str] = []
        if fconfs_directories:
            for fconf_directory in fconfs_directories:
                if re.fullmatch(REMOTE_YAML_PATTERN, fconf_directory) is not None:
                    fconfs_files.extend([fconf_directory])
                elif re.fullmatch(RELATIVE_YAML_PATTERN, fconf_directory) is not None:
                    _res = self.get_directory_file(fconf_directory)
                    if _res is not None:
                        fconfs_files.extend([_res])
                else:
                    fconfs_files.extend(self.get_directory_files(fconf_directory))
        if not fconfs_files:
            logger.warning(f"未找到全量配置文件在目录: {fconfs_directories}")

        # 2.1.2 从全量配置文件列表加载所有全量配置
        configs_from_fconf_files: List[Dict[str, Any]] = []
        for file_path in fconfs_files:
            content = self.get_file_content(file_path)
            if content:
                config = load_yaml_content(content)
                if config:
                    configs_from_fconf_files.append((config))

        if not configs_from_fconf_files:
            logger.error(f"未能加载任何有效的全量配置文件")
            return {}

        # 2.1.3 合并全量配置
        if configs_from_fconf_files:
            merged_config = reduce(deep_merge, configs_from_fconf_files)

        # MARK: 2.2 代理集
        # 2.2.1 获取代理集文件列表
        proxy_providers_files = self.get_directory_files(proxy_providers_directory)
        if not proxy_providers_files:
            logger.warning(f"未找到代理集文件在目录: {proxy_providers_directory}")

        # 2.2.2 加载所有代理集配置
        configs_from_proxy_providers_files = []
        for file_path in proxy_providers_files:
            content = self.get_file_content(file_path)
            if content:
                config = pick_properties(
                    load_yaml_content(content), ["proxy-providers"]
                )
                if config:
                    configs_from_proxy_providers_files.append((config))

        if not configs_from_proxy_providers_files:
            logger.error(f"未能加载任何有效的代理节点配置文件")
            # return {}

        # 2.2.3 合并代理集
        if configs_from_proxy_providers_files:
            merged_proxy_providers = reduce(
                deep_merge, configs_from_proxy_providers_files
            )
            # 将已有 proxy-providers 与 外部 proxy-providers 合并
            merged_config["proxy-providers"] = deep_merge(
                extract_valid_object(
                    get_property(merged_config, "proxy-providers", {})
                ),
                extract_valid_object(
                    get_property(merged_proxy_providers, "proxy-providers", {})
                ),
            )

        # MARK: 2.3 代理节点
        # 2.3.1 获取代理节点文件列表
        proxies_files = self.get_directory_files(proxies_directory)
        if not proxies_files:
            logger.warning(f"未找到代理节点文件在目录: {proxies_directory}")

        # 2.3.2 加载所有代理节点配置
        configs_from_proxies_files = []
        for file_path in proxies_files:
            content = self.get_file_content(file_path)
            if content:
                config = pick_properties(load_yaml_content(content), ["proxies"])
                if config:
                    configs_from_proxies_files.append((config))

        if not configs_from_proxies_files:
            logger.error(f"未能加载任何有效的代理节点配置文件")
            # return {}

        # 2.3.3 合并代理节点
        if configs_from_proxies_files:
            merged_proxies = reduce(deep_merge, configs_from_proxies_files)
            # 将已有 proxies 与 外部 proxies 合并
            merged_config["proxies"] = deep_merge(
                extract_valid_array(get_property(merged_config, "proxies", [])),
                extract_valid_array(get_property(merged_proxies, "proxies", [])),
            )

        # MARK: 2.4 规则集
        # 2.4.1 获取规则集文件列表
        rule_providers_files = self.get_directory_files(rule_providers_directory)
        if not rule_providers_files:
            logger.warning(f"未找到规则集文件在目录: {rule_providers_directory}")

        # 2.4.2 加载所有规则集配置
        configs_from_rule_providers_files = []
        for file_path in rule_providers_files:
            content = self.get_file_content(file_path)
            if content:
                config = pick_properties(load_yaml_content(content), ["rule-providers"])
                if config:
                    configs_from_rule_providers_files.append((config))

        if not configs_from_rule_providers_files:
            logger.error(f"未能加载任何有效的规则集配置文件")
            # return {}

        # 2.4.3 合并规则集
        if configs_from_rule_providers_files:
            merged_rule_providers = reduce(
                deep_merge, configs_from_rule_providers_files
            )
            # 将已有 rule-providers 与 外部 rule-providers 合并
            merged_config["rule-providers"] = deep_merge(
                extract_valid_object(get_property(merged_config, "rule-providers", {})),
                extract_valid_object(
                    get_property(merged_rule_providers, "rule-providers", {})
                ),
            )

        # MARK: 2.5 规则
        # 2.5.1 获取规则文件列表
        rules_files = self.get_directory_files(rules_directory)
        if not rules_files:
            logger.warning(f"未找到规则文件在目录: {rules_directory}")

        # 2.5.2 加载所有规则配置
        configs_from_rules_files = []
        for file_path in rules_files:
            content = self.get_file_content(file_path)
            if content:
                config = pick_properties(
                    load_yaml_content(content), ["rule-providers", "rules"]
                )
                if config:
                    configs_from_rules_files.append((config))

        if not configs_from_rules_files:
            logger.error(f"未能加载任何有效的规则配置文件")
            # return {}

        # 2.5.3 合并规则
        if configs_from_rules_files:
            merged_rules = reduce(deep_merge, configs_from_rules_files)
            # 将已有 rule-providers 与 外部 rule-providers 合并
            merged_config["rule-providers"] = deep_merge(
                extract_valid_object(get_property(merged_config, "rule-providers", {})),
                extract_valid_object(get_property(merged_rules, "rule-providers", {})),
            )
            # 将已有 rules 与 外部 rules 合并，rules 优先级高于 fconfs 中的 rules
            merged_config["rules"] = deep_merge(
                extract_valid_array(get_property(merged_rules, "rules", [])),
                extract_valid_array(get_property(merged_config, "rules", [])),
            )

        # 3. 清理代理节点中的临时字段
        try:
            for proxy in merged_config.get("proxies", []):
                if isinstance(proxy, dict) and "_source_file" in proxy:
                    del proxy["_source_file"]
        except Exception as e:
            logger.error(f"清理代理节点中的临时字段失败: {e}")

        return merged_config

    def save_config_to_file(
        self, config: Dict[str, Any], output_path: str, alias_name: str = "Clash"
    ) -> bool:
        """
        保存配置到文件

        Args:
            config: 配置字典
            output_path: 输出文件路径
            alias_name: 文件别名

        Returns:
            保存是否成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 使用UTF-8 BOM编码写入文件，确保GitHub Pages正确识别
            with open(output_path, "w", encoding="utf-8-sig", newline="\n") as f:
                # 使用自定义的YAML输出格式，确保中文正确显示
                yaml_content = yaml.dump(
                    config,
                    Dumper=YamlIndentDumper,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    encoding=None,  # 返回字符串而不是字节
                    width=1000,  # 避免长行被折断
                    indent=2,
                )

                # 插入头部内容
                header = [
                    f"# Automatically generated `{alias_name}` yaml file",
                    "# Do not modify manually",
                    f"# Last Update: {datetime.now(timezone.utc).isoformat()}",
                ]
                # 合并为最终文本
                final_yaml_content = "\n".join(header) + "\n\n" + yaml_content

                # 确保写入UTF-8编码的内容
                f.write(final_yaml_content)

            logger.info(f"配置文件已保存到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False


class ClashConfigInitParams:
    def __init__(
        self,
        local_mode: bool = False,
        merger: ClashConfigMerger | None = None,
        auth_token: str = "",
        output_dir: str = "",
        fconfs_dirs: List[List[str]] = [],
        fconfs_filenames: List[str] = [],
        proxy_providers_dir: str = "",
        proxies_dir: str = "",
        rule_providers_dir: str = "",
        rules_dir: str = "",
    ):
        """
        初始化Clash配置初始化参数

        Args:
            local_mode: 是否使用本地模式
            merger: Clash配置合并对象
            auth_token: 用户鉴权令牌
            output_dir: 输出目录
            fconfs_dirs: 全量配置目录列表
            fconfs_filenames: 生成配置文件名列表
            proxy_providers_dir: 代理集目录
            proxies_dir: 代理节点目录
            rule_providers_dir: 规则集目录
            rules_dir: 规则目录
        """
        self.local_mode = local_mode
        self.merger = merger
        self.output_dir = output_dir
        self.fconfs_dirs = fconfs_dirs
        self.fconfs_filenames = fconfs_filenames
        self.proxy_providers_dir = proxy_providers_dir
        self.proxies_dir = proxies_dir
        self.rule_providers_dir = rule_providers_dir
        self.rules_dir = rules_dir
        self.auth_token = auth_token

        self.rules_dir = rules_dir
        self.auth_token = auth_token


class YamlIndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(YamlIndentDumper, self).increase_indent(flow, False)


def merger_init() -> ClashConfigInitParams:
    """
    初始化merger、output_dir、fconfs_dirs、fconfs_filenames、proxy_providers_dir、proxies_dir、rule_providers_dir、rules_dir、auth_token等重要参数

    Returns:
        初始化参数对象
    """

    # 检查是否为本地测试模式
    local_mode = len(sys.argv) > 1 and sys.argv[1] == "--local"

    fconfs_dirs = [["fconfs"]]
    fconfs_filenames = ["filename"]
    proxy_providers_dir = "proxy-providers"
    proxies_dir = "proxies"
    rule_providers_dir = "rules-providers"
    rules_dir = "rules"

    if local_mode:
        logger.info(f"🧪 本地测试模式")
        # 本地模式配置
        merger = ClashConfigMerger(local_mode=True)
        output_dir = "output"
        auth_token = "local-test"
    else:
        logger.info(f"☁️ GitHub模式")
        # 从环境变量获取配置
        github_token = os.getenv("GITHUB_TOKEN")
        repo_owner = os.getenv("REPO_OWNER", "your-username")
        repo_name = os.getenv("REPO_NAME", "clash-config")
        output_dir = os.getenv("OUTPUT_DIR", "docs")
        auth_token = os.getenv("AUTH_TOKEN", "default-token")
        _fconfs_remote_yamls = filter_valid_strings(
            [
                os.getenv("REMOTE_YAMLS", ""),
                settings_config["github"]["fconfs_remote_yamls"],
            ]
        )
        fconfs_remote_yamls = (
            ",".join(_fconfs_remote_yamls) if _fconfs_remote_yamls else ""
        )
        _fconfs_directories = filter_valid_strings(
            [
                os.getenv("FCONFS_DIRECTORIES", ""),
                settings_config["github"]["fconfs_directories"],
            ]
        )
        fconfs_directories = (
            ";".join(_fconfs_directories) if _fconfs_directories else ""
        )
        proxy_providers_directory = settings_config["github"][
            "proxy_providers_directory"
        ]
        proxies_directory = settings_config["github"]["proxies_directory"]
        rule_providers_directory = settings_config["github"]["rule_providers_directory"]
        rules_directory = settings_config["github"]["rules_directory"]

        fconfs_remote_yamls_1d_list: List[str] = []
        if fconfs_remote_yamls and isinstance(fconfs_remote_yamls, str):
            fconfs_remote_yamls_1d_list = split_str_to_1d_array(
                fconfs_remote_yamls.strip()
            )

        if fconfs_directories and isinstance(fconfs_directories, str):
            # 获取文件名，默认取“name|。。。”的name值，否则取第一个目录名
            fconfs_filenames = list(
                map(
                    lambda f_d: cut_fonfs_name(f_d),
                    # 这里需要groupName，不能去除，否则文件名取值可能出错
                    split_str_to_2d_array(fconfs_directories),
                )
            )
            fconfs_dirs = unshift_to_array(
                # 通过正则去除groupName，将处理后的字符串转化为二维数组
                split_str_to_2d_array(
                    re.sub(FCONFS_DIR_PATTERN, r"\2", fconfs_directories)
                ),
                fconfs_remote_yamls_1d_list,
            )

        if proxy_providers_directory and isinstance(proxy_providers_directory, str):
            proxy_providers_dir = proxy_providers_directory.strip()

        if proxies_directory and isinstance(proxies_directory, str):
            proxies_dir = proxies_directory.strip()

        if rule_providers_directory and isinstance(rule_providers_directory, str):
            rule_providers_dir = rule_providers_directory.strip()

        if rules_directory and isinstance(rules_directory, str):
            rules_dir = rules_directory.strip()

        if not github_token:
            logger.error(f"未设置GITHUB_TOKEN环境变量")
            sys.exit(1)

        # 创建合并器实例
        merger = ClashConfigMerger(
            github_token, repo_owner, repo_name, local_mode=False
        )

    return ClashConfigInitParams(
        local_mode=local_mode,
        merger=merger,
        output_dir=output_dir,
        fconfs_dirs=fconfs_dirs,
        fconfs_filenames=fconfs_filenames,
        proxy_providers_dir=proxy_providers_dir,
        proxies_dir=proxies_dir,
        rule_providers_dir=rule_providers_dir,
        rules_dir=rules_dir,
        auth_token=auth_token,
    )


def merger_gen_config():
    """
    生成合并后的配置
    """

    ida = merger_init()
    merged_configs: Dict[str, Dict[str, Any]] = {}
    if (
        ida.merger is not None
        and ida.fconfs_dirs
        and isinstance(ida.fconfs_dirs, list)
        and ida.fconfs_filenames
        and isinstance(ida.fconfs_filenames, list)
        and len(ida.fconfs_dirs) == len(ida.fconfs_filenames)
    ):
        _merger = ida.merger
        logger.info(f"=== ↓↓↓ 开始生成合并配置 ↓↓↓ ===")
        for i, dirs in enumerate(ida.fconfs_dirs):
            attr = ida.fconfs_filenames[i]
            dirs_desensitize = list(map(lambda dir: desensitize_url(dir), dirs))
            logger.info(
                f"=== [{i + 1} / {len(ida.fconfs_dirs)}] 开始合并 {attr} <== {dirs_desensitize} ==="
            )
            merged_configs[attr] = _merger.generate_merged_config(
                dirs,
                ida.proxy_providers_dir,
                ida.proxies_dir,
                ida.rule_providers_dir,
                ida.rules_dir,
            )
            logger.info(f"=== [{i + 1} / {len(ida.fconfs_dirs)}] 合并完成 {attr}  ===")
        logger.info(f"=== ↑↑↑ 配置合并完成 ↑↑↑ ===")
    else:
        merged_configs = {}

    if not merged_configs:
        logger.error(f"生成配置失败")
        sys.exit(1)

    for filename, merged_config in merged_configs.items():
        if filename and merged_config:
            final_filename = f"-{filename}"
            # 使用token作为文件名的一部分进行认证
            config_filename = f"{settings_config['output']['config_filename']}{final_filename}-{ida.auth_token}.yaml"
            # 配置文件保存路径
            output_path = os.path.join(ida.output_dir, config_filename)
            # 统计文件保存路径
            stats_path = os.path.join(
                ida.output_dir,
                f"{settings_config['output']['stats_filename']}{final_filename}.json",
            )

            # 生成统计信息
            # 1. 定义东八区时区 (UTC+8)
            tz_utc_8 = timezone(timedelta(hours=8))
            # 2. 获取当前东八区时间
            now_tz_utc_8 = datetime.now(tz_utc_8)
            # 3. 格式化输出
            now_tz_utc_8_formatted_time = now_tz_utc_8.strftime('%Y-%m-%d %H:%M:%S TZ=UTC+8:00')
            stats = {
                "generated_timestamp": now_tz_utc_8_formatted_time,
                # proxy-providers 个数
                "proxy_providers_count": 0,
                # proxies 总个数 = sum(item["count"] for item in proxy_providers__proxies__count.values()) + indep_proxies_count
                "total_proxies_count": 0,
                # 独立的 proxies 个数
                "indep_proxies_count": 0,
                # 单 proxy-providers 中所包含的 proxies 个数
                "proxy_providers__proxies__count": {},
                # proxy-groups 个数
                "proxy_groups_count": 0,
                # rule-providers 个数
                "rule_providers_count": 0,
                # rules 总个数
                "total_rules_count": 0,
                # rules.RULE-SET 个数
                "rules__rule_set__count": 0,
                # 独立的 rules 个数
                "indep_rules_count": 0,
            }
            try:
                # proxy-providers
                _proxy_providers = merged_config.get("proxy-providers", {})
                proxy_providers_count = len(_proxy_providers)
                proxy_providers__proxies__count = {}

                # 暂时移除订阅用量/剩余统计代码
                for proxyProviderKey, proxyProviderValue in _proxy_providers.items():
                    #     proxyProviderUrl = proxyProviderValue.get("url", "")
                    _count = 0
                    userinfo_used = ""
                    userinfo_total = ""
                    userinfo_expire = ""
                    userinfo_overview = ""
                    #     if (
                    #         proxyProviderUrl
                    #         and isinstance(proxyProviderUrl, str)
                    #         and re.fullmatch(REMOTE_FILE_PATTERN, proxyProviderUrl)
                    #         is not None
                    #     ):
                    #         url_content = files_utils.request_url_content(proxyProviderUrl)
                    #         if url_content and isinstance(url_content, dict):
                    #             text = url_content["content"]
                    #             if text and isinstance(text, str):
                    #                 if re.fullmatch(BASE64_PATTERN, text) is not None:
                    #                     # base64
                    #                     # 解码为字节
                    #                     decoded_bytes = base64.b64decode(text)
                    #                     # 如果你知道是 UTF-8 编码的文本，可以转为字符串
                    #                     decoded_str = decoded_bytes.decode("utf-8")
                    #                     _count = decoded_str.count("ss://")
                    #                     _count += decoded_str.count("ssr://")
                    #                     _count += decoded_str.count("vmess://")
                    #                 else:
                    #                     yaml_content = load_yaml_content(text)
                    #                     if yaml_content and isinstance(yaml_content, dict):
                    #                         _proxies = yaml_content.get("proxies", [])
                    #                         _count = len(_proxies)

                    #             userinfo_used = url_content.get("used", "")
                    #             userinfo_total = url_content.get("total", "")
                    #             userinfo_expire = url_content.get("expire", "")
                    #             userinfo_overview = url_content.get("overview", "")
                    #             logger.info(
                    #                 f"[{filename}] 🧾 {proxyProviderKey} 订阅信息：{userinfo_used}/{userinfo_total} {userinfo_expire}"
                    #             )
                    #             if userinfo_used and userinfo_total and userinfo_expire:
                    #                 if "proxies" not in merged_config or (
                    #                     "proxies" in merged_config
                    #                     and merged_config["proxies"] is None
                    #                 ):
                    #                     merged_config["proxies"] = []

                    #                 merged_config["proxies"].extend(
                    #                     [
                    #                         {
                    #                             "name": f"{proxyProviderKey} 流量使用：{userinfo_used}/{userinfo_total}",
                    #                             "type": "trojan",
                    #                             "server": "127.0.0.1",
                    #                             "port": 8080,
                    #                             "password": "",
                    #                             "uuid": f"scat-proxy-{proxyProviderKey}-userinfo-used",
                    #                             "tls": False,
                    #                             "skip-cert-verify": True,
                    #                             "udp": True,
                    #                         },
                    #                         {
                    #                             "name": f"{proxyProviderKey} 套餐到期：{userinfo_expire}",
                    #                             "type": "trojan",
                    #                             "server": "127.0.0.1",
                    #                             "port": 8080,
                    #                             "password": "",
                    #                             "uuid": f"scat-proxy-{proxyProviderKey}-userinfo-expire",
                    #                             "tls": False,
                    #                             "skip-cert-verify": True,
                    #                             "udp": True,
                    #                         },
                    #                     ]
                    #                 )

                    proxy_providers__proxies__count.update(
                        {
                            proxyProviderKey: {
                                "count": _count,
                            }
                        }
                    )

                # proxies
                _proxies = list(
                    filter(
                        lambda o: not (
                            "uuid" in o
                            and isinstance(o["uuid"], str)
                            and o["uuid"].startswith("scat-proxy-")
                        ),
                        merged_config.get("proxies", []),
                    )
                )
                indep_proxies_count = len(_proxies)
                total_proxies_count = indep_proxies_count + sum(
                    item["count"] for item in proxy_providers__proxies__count.values()
                )
                # proxy-groups
                _proxy_groups = merged_config.get("proxy-groups", [])
                proxy_groups_count = len(_proxy_groups)
                # rule-providers
                _rule_providers = merged_config.get("rule-providers", {})
                rule_providers_count = len(_rule_providers)
                # rules
                _rules = merged_config.get("rules", [])
                total_rules_count = len(_rules)
                # rules startsWith "RULE-SET,"
                _rule_set_keys = []
                PREFIX = "RULE-SET,"
                for s in _rules:
                    if isinstance(s, str) and s.strip().startswith(PREFIX):
                        rest = s[len(PREFIX) :]
                        parts = rest.split(",", 1)  # 只分割一次
                        _rule_set_keys.append(parts[0])
                rules__rule_set__count = len(
                    list(
                        set(
                            _rule_providers.keys()
                            if isinstance(_rule_providers, dict)
                            else []
                        )
                        & set(_rule_set_keys)
                    )
                )
                indep_rules_count = total_rules_count - rules__rule_set__count

                stats.update(
                    {
                        "proxy_providers_count": proxy_providers_count,
                        "total_proxies_count": total_proxies_count,
                        "indep_proxies_count": indep_proxies_count,
                        "proxy_providers__proxies__count": proxy_providers__proxies__count,
                        "proxy_groups_count": proxy_groups_count,
                        "rule_providers_count": rule_providers_count,
                        "total_rules_count": total_rules_count,
                        "rules__rule_set__count": rules__rule_set__count,
                        "indep_rules_count": indep_rules_count,
                    }
                )
            except Exception as e:
                logger.error(f"[{filename}] ❌ 生成统计信息失败: {e}")

            # region 配置写入到文件“*.yaml”
            if not ida.merger or (
                ida.merger
                and not ida.merger.save_config_to_file(
                    merged_config, output_path, filename
                )
            ):
                sys.exit(1)
            # endregion

            try:
                os.makedirs(ida.output_dir, exist_ok=True)
                with open(stats_path, "w", encoding="utf-8") as f:
                    json.dump(stats, f, indent=2, ensure_ascii=False)

                logger.info(f"[{filename}] ℹ️ 统计信息已保存到: {stats_path}")
            except Exception as e:
                logger.warning(f"[{filename}] ❌ 保存统计信息失败: {e}")

            logger.info(f"[{filename}] ✅ 任务完成! ")
            logger.info(
                f"[{filename}] 📁 配置文件: {settings_config['output']['config_filename']}{final_filename}-{{your-token}}.yaml"
            )
            if ida.local_mode:
                logger.info(f"[{filename}] 📁 输出路径: {output_path}")


def main():
    """主函数"""
    merger_gen_config()


if __name__ == "__main__":
    main()
