# Clash 配置整合工具

🚀 自动从 GitHub 私有仓库整合多个 Clash 订阅配置文件，生成统一的订阅链接。

## ✨ 功能特性

- 🔄 **自动整合**：从私有仓库读取多个订阅 YAML 文件并智能合并
- 🛡️ **规则优化**：整合多个规则列表，自动去重和优化
- 🌍 **地区分组**：自动按地区对代理节点进行分组
- 🔐 **安全认证**：支持 token 认证，保护配置文件访问
- ⚡ **自动更新**：GitHub Actions 定时更新，确保配置始终最新
- 📊 **统计信息**：提供详细的配置统计和更新时间

## 🏗️ 项目结构

```
├── .github/workflows/
│   └── update-config.yml      # GitHub Actions工作流
├── scripts/
│   └── merge_clash_config.py  # 核心合并脚本
├── config/
│   └── settings.yaml          # 配置文件
├── docs/                      # GitHub Pages输出目录
│   ├── index.html            # 主页面
│   ├── <your_clash_config_filename>.yaml            # 生成的配置文件
│   └── stats.json            # 统计信息
└── README.md
```

## 🚀 快速开始

### 1. 准备工作

1. **Fork 此仓库**到您的 GitHub 账户
2. **创建私有仓库**存放您的 Clash 订阅文件，目录结构如下：
   ```
   your-private-repo/
   ├── Clash/                       # Clash文件
   │   ├── proxies/                    # 订阅文件目录
   │   │   ├── provider1.yaml
   │   │   ├── provider2.yaml
   │   │   └── provider3.yaml
   │   ├── rules/                   # 规则文件目录
   │   │   ├── rules_proxy_basic.yaml
   │   │   └── rules_proxy_custom.yaml
   │   └── fconfs/                  # 完整规则文件目录
   │       ├── conf1.yaml
   │       └── conf2.yaml
   │  ...
   ```

### 2. 配置 GitHub Secrets

在您的仓库设置中添加以下 Secrets：

| Secret 名称          | 说明                              | 示例值              |
| -------------------- | --------------------------------- | ------------------- |
| `CLASH_GITHUB_TOKEN` | GitHub 访问令牌（需要 repo 权限） | `ghp_xxxxxxxxxxxx`  |
| `CLASH_REPO_OWNER`   | 私有仓库所有者用户名              | `your-username`     |
| `CLASH_REPO_NAME`    | 私有仓库名称                      | `clash-config`      |
| `CLASH_AUTH_TOKEN`   | 访问配置文件的认证 token          | `your-secret-token` |

### 3. 启用 GitHub Pages

1. 进入仓库设置 → Pages
2. Source 选择 "GitHub Actions"
3. 保存设置

### 4. 运行工作流

1. 进入 Actions 标签页
2. 选择 "Update Clash Config" 工作流
3. 点击 "Run workflow" 手动触发

## 📖 使用方法

### 订阅链接

配置完成后，您的 Clash 订阅链接为：

```
https://your-username.github.io/your-repo/<your_clash_config_filename>.yaml
```

### 直接下载

访问主页查看配置统计和下载链接：

```
https://your-username.github.io/your-repo/
```

## ⚙️ 配置说明

### 订阅文件格式

支持标准的 Clash 配置文件格式，脚本会自动提取以下部分：

- `proxies`: 代理节点列表
- `proxy-groups`: 策略组配置
- `rules`: 规则列表

### 规则文件格式

支持两种格式：

1. **Clash 规则格式**（直接在 rules 中）：

```yaml
rules:
  - DOMAIN-SUFFIX,google.com,PROXY
  - DOMAIN-SUFFIX,github.com,PROXY
```

2. **Payload 格式**（用于规则集）：

```yaml
payload:
  - DOMAIN-SUFFIX,google.com
  - DOMAIN-SUFFIX,github.com
```

### 自定义配置

编辑 `config/settings.yaml` 文件可以自定义：

- 代理分组规则
- DNS 配置
- 默认规则
- 更新频率等

## 🔧 高级功能

### 自动更新

- **定时更新**：每小时自动检查并更新配置
- **推送触发**：当脚本或配置文件更新时自动重新生成
- **手动触发**：支持在 Actions 页面手动运行

### 代理优化

- **智能去重**：自动处理重复的代理节点名称
- **地区分组**：根据节点名称自动分组
- **负载均衡**：自动创建自动选择和故障转移组

### 规则整合

- **多源合并**：整合来自多个文件的规则
- **自动去重**：移除重复的规则条目
- **优先级排序**：确保规则的正确优先级

## 🛡️ 安全特性

- **Token 认证**：防止未授权访问
- **私有仓库**：源配置文件存储在私有仓库中
- **GitHub Secrets**：敏感信息通过 Secrets 管理
- **访问控制**：可配置 IP 白名单（可选）

## 📊 监控和日志

- **实时统计**：显示代理数量、规则数量等信息
- **更新时间**：记录最后更新时间
- **错误日志**：详细的错误信息和调试日志
- **状态监控**：通过 GitHub Actions 查看运行状态

## 🔍 故障排除

### 常见问题

1. **配置文件生成失败**

   - 检查 GitHub Token 权限
   - 确认私有仓库路径正确
   - 查看 Actions 日志获取详细错误信息

2. **访问被拒绝**

   - 确认认证 token 正确
   - 检查 URL 参数格式

3. **代理节点缺失**
   - 检查源文件 YAML 格式
   - 确认文件路径和权限

### 调试方法

1. 查看 GitHub Actions 运行日志
2. 检查生成的 stats.json 文件
3. 验证源文件的 YAML 格式

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⚠️ 免责声明

- 本工具仅供学习和个人使用
- 请遵守相关法律法规和服务条款
- 使用者需对自己的行为负责
