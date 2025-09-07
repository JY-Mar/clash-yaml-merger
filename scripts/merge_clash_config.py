#!/usr/bin/env python3
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

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClashConfigMerger:
    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        """
        初始化Clash配置合并器
        
        Args:
            github_token: GitHub访问令牌
            repo_owner: 仓库所有者
            repo_name: 仓库名称
        """
        self.github_token = github_token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents'
        
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        从GitHub仓库获取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串，失败返回None
        """
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
        获取目录下的所有文件列表
        
        Args:
            directory_path: 目录路径
            
        Returns:
            文件路径列表
        """
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
    
    def merge_proxies(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并多个配置文件的代理节点
        
        Args:
            configs: 配置文件列表
            
        Returns:
            合并后的代理节点列表
        """
        merged_proxies = []
        seen_names = set()
        
        for config in configs:
            if 'proxies' in config and isinstance(config['proxies'], list):
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
                        seen_names.add(name)
                        merged_proxies.append(proxy)
        
        logger.info(f"合并了 {len(merged_proxies)} 个代理节点")
        return merged_proxies
    
    def merge_rules(self, configs: List[Dict[str, Any]], rule_files: List[str]) -> List[str]:
        """
        合并规则列表
        
        Args:
            configs: 配置文件列表
            rule_files: 规则文件路径列表
            
        Returns:
            合并后的规则列表
        """
        merged_rules = []
        seen_rules = set()
        
        # 从规则文件中加载规则
        for rule_file_path in rule_files:
            content = self.get_file_content(rule_file_path)
            if content:
                rule_data = self.load_yaml_content(content)
                if rule_data and 'payload' in rule_data:
                    for rule in rule_data['payload']:
                        if isinstance(rule, str) and rule not in seen_rules:
                            # 将规则格式化为Clash格式
                            if not rule.endswith(',PROXY') and not rule.endswith(',DIRECT'):
                                rule = f"{rule},PROXY"
                            merged_rules.append(rule)
                            seen_rules.add(rule)
        
        # 从配置文件中加载规则
        for config in configs:
            if 'rules' in config and isinstance(config['rules'], list):
                for rule in config['rules']:
                    if isinstance(rule, str) and rule not in seen_rules:
                        merged_rules.append(rule)
                        seen_rules.add(rule)
        
        logger.info(f"合并了 {len(merged_rules)} 条规则")
        return merged_rules
    
    def create_proxy_groups(self, proxies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        创建代理组
        
        Args:
            proxies: 代理节点列表
            
        Returns:
            代理组配置列表
        """
        proxy_names = [proxy['name'] for proxy in proxies if 'name' in proxy]
        
        proxy_groups = [
            {
                'name': 'PROXY',
                'type': 'select',
                'proxies': ['自动选择', '故障转移'] + proxy_names
            },
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
        ]
        
        # 按地区分组
        regions = {}
        for proxy in proxies:
            name = proxy.get('name', '')
            if '🇭🇰' in name or '香港' in name:
                regions.setdefault('香港', []).append(name)
            elif '🇨🇳' in name or '台湾' in name:
                regions.setdefault('台湾', []).append(name)
            elif '🇸🇬' in name or '新加坡' in name:
                regions.setdefault('新加坡', []).append(name)
            elif '🇯🇵' in name or '日本' in name:
                regions.setdefault('日本', []).append(name)
            elif '🇺🇸' in name or '美国' in name:
                regions.setdefault('美国', []).append(name)
        
        # 为每个地区创建代理组
        for region, region_proxies in regions.items():
            if region_proxies:
                proxy_groups.append({
                    'name': f'{region}节点',
                    'type': 'select',
                    'proxies': region_proxies
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
        configs = []
        for file_path in sub_files:
            content = self.get_file_content(file_path)
            if content:
                config = self.load_yaml_content(content)
                if config:
                    configs.append(config)

        if not configs:
            logger.error("未能加载任何有效的订阅配置文件")
            return {}

        # 创建基础配置
        merged_config = self.create_base_config()

        # 合并代理节点
        merged_proxies = self.merge_proxies(configs)
        merged_config['proxies'] = merged_proxies

        # 创建代理组
        proxy_groups = self.create_proxy_groups(merged_proxies)
        merged_config['proxy-groups'] = proxy_groups

        # 合并规则
        merged_rules = self.merge_rules(configs, rule_files)

        # 添加默认规则
        default_rules = [
            'DOMAIN-SUFFIX,local,DIRECT',
            'IP-CIDR,127.0.0.0/8,DIRECT',
            'IP-CIDR,172.16.0.0/12,DIRECT',
            'IP-CIDR,192.168.0.0/16,DIRECT',
            'IP-CIDR,10.0.0.0/8,DIRECT',
            'IP-CIDR,17.0.0.0/8,DIRECT',
            'IP-CIDR,100.64.0.0/10,DIRECT',
            'GEOIP,CN,DIRECT',
            'MATCH,PROXY'
        ]

        merged_config['rules'] = merged_rules + default_rules

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

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            logger.info(f"配置文件已保存到: {output_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False


def main():
    """主函数"""
    # 从环境变量获取配置
    github_token = os.getenv('GITHUB_TOKEN')
    repo_owner = os.getenv('REPO_OWNER', 'your-username')
    repo_name = os.getenv('REPO_NAME', 'clash-config')
    output_dir = os.getenv('OUTPUT_DIR', 'docs')

    if not github_token:
        logger.error("未设置GITHUB_TOKEN环境变量")
        sys.exit(1)

    # 创建合并器实例
    merger = ClashConfigMerger(github_token, repo_owner, repo_name)

    # 生成合并配置
    merged_config = merger.generate_merged_config()

    if not merged_config:
        logger.error("生成配置失败")
        sys.exit(1)

    # 保存配置文件
    output_path = os.path.join(output_dir, 'clash.yaml')
    if not merger.save_config_to_file(merged_config, output_path):
        sys.exit(1)

    # 生成统计信息
    stats = {
        'generated_at': datetime.now().isoformat(),
        'proxy_count': len(merged_config.get('proxies', [])),
        'proxy_group_count': len(merged_config.get('proxy-groups', [])),
        'rule_count': len(merged_config.get('rules', []))
    }

    stats_path = os.path.join(output_dir, 'stats.json')
    try:
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        logger.info(f"统计信息已保存到: {stats_path}")
    except Exception as e:
        logger.warning(f"保存统计信息失败: {e}")

    logger.info(f"任务完成! 代理节点: {stats['proxy_count']}, 规则: {stats['rule_count']}")


if __name__ == '__main__':
    main()
