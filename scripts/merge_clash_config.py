#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clash配置文件整合工具
从GitHub私有仓库读取多个订阅YAML文件，整合代理节点和规则，生成统一的Clash配置
"""

import os
import sys
import yaml
import requests
import base64
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 设置默认编码
import locale
import codecs

# 强制设置UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# 确保UTF-8编码
try:
    if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer') and sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
except:
    pass  # 在某些环境下可能会失败，忽略错误

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClashConfigMerger:
    def __init__(self, github_token: str = None, repo_owner: str = None, repo_name: str = None, local_mode: bool = False):
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
                'Authorization': f'token {github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            self.base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents'
        
    def load_config() -> Dict[str, Any]:
        """加载配置文件"""
        config_path = "config/settings.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ 配置文件格式错误: {e}")
            sys.exit(1)

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
                with open(file_path, 'r', encoding='utf-8') as f:
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
                url = f'{self.base_url}/{file_path}'
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                file_data = response.json()
                if file_data['encoding'] == 'base64':
                    content = base64.b64decode(file_data['content']).decode('utf-8')
                    logger.info(f"成功获取文件: {file_path}")
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
    
    def load_yaml_content(self, content: str) -> Optional[Dict[str, Any]]:
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
                    if filename.endswith('.yaml') or filename.endswith('.yml'):
                        file_path = os.path.join(directory_path, filename)
                        file_paths.append(file_path)

                logger.info(f"发现 {len(file_paths)} 个YAML文件在本地目录: {directory_path}")
                return file_paths

            except Exception as e:
                logger.error(f"扫描本地目录失败 {directory_path}: {e}")
                return []
        else:
            # GitHub模式：通过API获取
            try:
                url = f'{self.base_url}/{directory_path}'
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                files = response.json()
                file_paths = []

                for file_info in files:
                    if file_info['type'] == 'file' and file_info['name'].endswith('.yaml'):
                        file_paths.append(file_info['path'])

                logger.info(f"发现 {len(file_paths)} 个YAML文件在目录: {directory_path}")
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
            if 'proxies' in config and isinstance(config['proxies'], list):
                source_name = os.path.basename(source_file).replace('.yaml', '')
                for proxy in config['proxies']:
                    if isinstance(proxy, dict) and 'name' in proxy:
                        # 避免重复的代理节点名称
                        original_name = proxy['name']
                        name = original_name
                        counter = 1

                        while name in seen_names:
                            name = f"{original_name}_{counter}"
                            counter += 1

                        proxy['name'] = name
                        proxy['_source_file'] = source_name  # 添加来源标识
                        seen_names.add(name)
                        merged_proxies.append(proxy)

        logger.info(f"合并了 {len(merged_proxies)} 个代理节点")
        return merged_proxies
    
    def merge_rules(self, rule_files: List[str]) -> List[str]:
        """
        合并规则列表（只使用rule目录下的规则文件）

        Args:
            rule_files: 规则文件路径列表

        Returns:
            合并后的规则列表
        """
        merged_rules = []
        seen_rules = set()

        # 只从规则文件中加载规则，忽略sub文件中的规则
        for rule_file_path in rule_files:
            content = self.get_file_content(rule_file_path)
            if content:
                rule_data = self.load_yaml_content(content)
                if rule_data and 'payload' in rule_data:
                    rule_file_name = os.path.basename(rule_file_path).replace('.yaml', '')
                    logger.info(f"处理规则文件: {rule_file_name}")

                    for rule in rule_data['payload']:
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
    
    def create_proxy_groups(self, proxies: List[Dict[str, Any]], sub_files: List[str], rule_files: List[str]) -> List[Dict[str, Any]]:
        """
        创建代理组结构

        Args:
            proxies: 代理节点列表
            sub_files: 订阅文件路径列表
            rule_files: 规则文件路径列表

        Returns:
            代理组配置列表
        """
        proxy_names = [proxy['name'] for proxy in proxies if 'name' in proxy]

        # 按订阅文件分组代理节点 - 基于来源信息进行精确分组
        sub_groups = {}
        for file_path in sub_files:
            # 从文件路径提取文件名作为分组名
            file_name = os.path.basename(file_path).replace('.yaml', '')
            sub_groups[file_name] = []

        # 根据代理的来源信息进行精确分组
        for proxy in proxies:
            if isinstance(proxy, dict) and '_source_file' in proxy:
                source_name = proxy['_source_file']
                proxy_name = proxy.get('name', '')
                if source_name in sub_groups and proxy_name:
                    sub_groups[source_name].append(proxy_name)

        # 创建代理组列表
        proxy_groups = []

        # 1. 创建主网络代理组（只包含sub分组，不包含rule分组）
        sub_group_names = list(sub_groups.keys())

        network_proxy_options = ['自动选择', '故障转移'] + sub_group_names
        proxy_groups.append({
            'name': '网络代理',
            'type': 'select',
            'proxies': network_proxy_options
        })

        # 2. 创建自动选择和故障转移组
        proxy_groups.extend([
            {
                'name': '自动选择',
                'type': 'url-test',
                'proxies': proxy_names,
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300
            },
            {
                'name': '故障转移',
                'type': 'fallback',
                'proxies': proxy_names,
                'url': 'http://www.gstatic.com/generate_204',
                'interval': 300
            }
        ])

        # 3. 为每个订阅文件创建代理组（只为sub文件创建，不为rule文件创建）
        for sub_name, sub_proxies in sub_groups.items():
            if sub_proxies:
                proxy_groups.append({
                    'name': sub_name,
                    'type': 'select',
                    'proxies': ['自动选择', '故障转移'] + sub_proxies
                })

        logger.info(f"创建了 {len(proxy_groups)} 个代理组")
        return proxy_groups

    def create_base_config(self) -> Dict[str, Any]:
        """
        创建基础配置

        Returns:
            基础配置字典
        """
        return {
            'mixed-port': 7890,
            'allow-lan': True,
            'bind-address': '*',
            'mode': 'rule',
            'log-level': 'info',
            'external-controller': '127.0.0.1:9090',
            'dns': {
                'enable': True,
                'ipv6': False,
                'default-nameserver': ['223.5.5.5', '119.29.29.29', '114.114.114.114'],
                'enhanced-mode': 'fake-ip',
                'fake-ip-range': '198.18.0.1/16',
                'use-hosts': True,
                'nameserver': ['223.5.5.5', '119.29.29.29', '114.114.114.114'],
                'fallback': ['1.1.1.1', '8.8.8.8'],
                'fallback-filter': {
                    'geoip': True,
                    'geoip-code': 'CN',
                    'ipcidr': ['240.0.0.0/4']
                }
            }
        }

    def generate_merged_config(self, sub_directory: str = 'sub', rule_directory: str = 'rule') -> Dict[str, Any]:
        """
        生成合并后的配置文件

        Args:
            sub_directory: 订阅文件目录
            rule_directory: 规则文件目录

        Returns:
            合并后的完整配置
        """
        logger.info("开始生成合并配置...")

        # 获取订阅文件列表
        sub_files = self.get_directory_files(sub_directory)
        if not sub_files:
            logger.warning(f"未找到订阅文件在目录: {sub_directory}")

        # 获取规则文件列表
        rule_files = self.get_directory_files(rule_directory)
        if not rule_files:
            logger.warning(f"未找到规则文件在目录: {rule_directory}")

        # 加载所有订阅配置
        configs_with_sources = []
        for file_path in sub_files:
            content = self.get_file_content(file_path)
            if content:
                config = self.load_yaml_content(content)
                if config:
                    configs_with_sources.append((config, file_path))

        if not configs_with_sources:
            logger.error("未能加载任何有效的订阅配置文件")
            return {}

        # 创建基础配置
        merged_config = self.create_base_config()

        # 合并代理节点
        merged_proxies = self.merge_proxies(configs_with_sources)
        merged_config['proxies'] = merged_proxies

        # 创建代理组（传入文件列表用于创建对应的分组）
        proxy_groups = self.create_proxy_groups(merged_proxies, sub_files, rule_files)
        merged_config['proxy-groups'] = proxy_groups

        # 合并规则（只使用rule目录下的规则）
        merged_rules = self.merge_rules(rule_files)

        # 只添加最基本的默认规则
        default_rules = [
            'MATCH,DIRECT'  # 默认流量走网络代理组
        ]

        merged_config['rules'] = merged_rules + default_rules

        # 清理代理节点中的临时字段
        for proxy in merged_config.get('proxies', []):
            if isinstance(proxy, dict) and '_source_file' in proxy:
                del proxy['_source_file']

        logger.info("配置合并完成")
        return merged_config

    def save_config_to_file(self, config: Dict[str, Any], output_path: str) -> bool:
        """
        保存配置到文件

        Args:
            config: 配置字典
            output_path: 输出文件路径

        Returns:
            保存是否成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 使用UTF-8 BOM编码写入文件，确保GitHub Pages正确识别
            with open(output_path, 'w', encoding='utf-8-sig', newline='\n') as f:
                # 使用自定义的YAML输出格式，确保中文正确显示
                yaml_content = yaml.dump(config,
                                        default_flow_style=False,
                                        allow_unicode=True,
                                        sort_keys=False,
                                        encoding=None,  # 返回字符串而不是字节
                                        width=1000,     # 避免长行被折断
                                        indent=2)
                # 确保写入UTF-8编码的内容
                f.write(yaml_content)

            logger.info(f"配置文件已保存到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False


def main():
    """主函数"""
    # 检查是否为本地测试模式
    local_mode = len(sys.argv) > 1 and sys.argv[1] == '--local'

    if local_mode:
        logger.info("🧪 本地测试模式")
        # 本地模式配置
        merger = ClashConfigMerger(local_mode=True)
        output_dir = 'output'
        sub_dir = 'sub'
        rule_dir = 'rule'
        auth_token = 'local-test'
    else:
        logger.info("☁️ GitHub模式")
        # 从环境变量获取配置
        github_token = os.getenv('GITHUB_TOKEN')
        repo_owner = os.getenv('REPO_OWNER', 'your-username')
        repo_name = os.getenv('REPO_NAME', 'clash-config')
        output_dir = os.getenv('OUTPUT_DIR', 'docs')
        auth_token = os.getenv('AUTH_TOKEN', 'default-token')
        
        loadedConfig = load_config()
        subscription_directory = loadedConfig['github']['subscription_directory']
        rules_directory = loadedConfig['github']['rules_directory']
        
        sub_dir = 'sub'
        if not subscription_directory
            sub_dir = subscription_directory
        
        rule_dir = 'rule'
        if not rules_directory
            rule_dir = rules_directory

        if not github_token:
            logger.error("未设置GITHUB_TOKEN环境变量")
            sys.exit(1)

        # 创建合并器实例
        merger = ClashConfigMerger(github_token, repo_owner, repo_name, local_mode=False)

    # 生成合并配置
    merged_config = merger.generate_merged_config(sub_dir, rule_dir)

    if not merged_config:
        logger.error("生成配置失败")
        sys.exit(1)

    # 使用token作为文件名的一部分进行认证
    config_filename = f'clash-{auth_token}.yaml'
    config_filename_dot = f'clash-xxxxxx.yaml'
    output_path = os.path.join(output_dir, config_filename)
    output_path_dot = os.path.join(output_dir, config_filename_dot)
    if not merger.save_config_to_file(merged_config, output_path):
        sys.exit(1)

    # 生成统计信息
    stats = {
        'generated_at': datetime.now().isoformat(),
        'proxy_count': len(merged_config.get('proxies', [])),
        'proxy_group_count': len(merged_config.get('proxy-groups', [])),
        'rule_count': len(merged_config.get('rules', [])),
        'config_filename': config_filename  # 添加配置文件名信息
    }

    stats_path = os.path.join(output_dir, 'stats.json')
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.info(f"统计信息已保存到: {stats_path}")
    except Exception as e:
        logger.warning(f"保存统计信息失败: {e}")

    logger.info(f"✅ 任务完成! 代理节点: {stats['proxy_count']}, 规则: {stats['rule_count']}")
    logger.info(f"📁 配置文件: {config_filename_dot}")
    if local_mode:
        logger.info(f"📁 输出路径: {output_path_dot}")


if __name__ == '__main__':
    main()
