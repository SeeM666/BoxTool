# BoxTool v5.1 - 渗透测试工具箱

<div align="center">

![Version](https://img.shields.io/badge/version-5.1-red.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Kivy](https://img.shields.io/badge/kivy-2.3.0-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Android-lightgrey.svg)

**商业级渗透测试工具箱 - 纯 Python 实现，无需外部工具**

[下载 APK](../../releases) | [使用文档](#使用方法) | [功能模块](#功能模块)

</div>

---

## ✨ v5.1 核心特性

- ✅ **纯 Python 实现** - 无需安装 msfconsole/nmap/sqlmap
- ✅ **APK 100% 可用** - 所有功能打包后都能正常使用
- ✅ **商业级检测** - 真实 Payload 测试，非关键词匹配
- ✅ **快速启动** - 无外部工具依赖，秒级启动

---

## 📱 功能模块

### 🔍 核心模块（纯 Python 实现）
| 功能 | 描述 | 实现方式 |
|------|------|----------|
| 🔍 Whois 查询 | 域名注册信息查询 | python-whois 库 |
| 🔍 DNS 收集 | A/AAAA/MX/NS/TXT 记录 | dnspython 库 |
| 🔍 子域名枚举 | 暴力破解常见子域名 | socket 解析 |
| 🔍 端口扫描 | TCP 端口扫描 | socket 连接测试 |
| 📡 存活扫描 | 检测存活主机 | TCP 80/445 端口探测 |
| 📡 快速端口 | 常用端口扫描 | 14 个常用端口 |
| 📡 全端口扫描 | 1-10000 端口 | 多线程扫描 |
| 🌐 SQL 注入检测 | SQL 注入漏洞 | 6 种真实 Payload |
| 🌐 敏感文件检测 | .git/.env/备份文件 | HTTP 请求检测 |
| 🌐 WAF 检测 | 识别 Cloudflare 等 | HTTP 头分析 |
| 🔐 SSH/FTP 爆破 | 密码暴力破解 | paramiko/ftplib |
| 🔐 MySQL/Redis 爆破 | 数据库密码破解 | pymysql/redis 库 |

### 🚀 高级模块（纯 Python 实现）
| 功能 | 描述 | 实现方式 |
|------|------|----------|
| 🎯 漏洞扫描 | 端口 + 服务 + CVE 检测 | 纯 Python 实现 |
| 📶 WiFi 渗透 | 命令指导（需要 Linux） | 提供 aircrack-ng 命令 |
| 🛡️ Heartbleed | 心脏出血漏洞检测 | 纯 Python SSL 测试 |
| 📊 报告生成 | HTML/JSON/Markdown | 模板渲染 |

### 🌟 AI 渗透模块（商业级）
| 功能 | 描述 | 实现方式 |
|------|------|----------|
| 🌍 Shodan 侦察 | IoT 设备搜索 | Shodan API |
| 🤖 AI Web 渗透 | **技术栈识别/SQL/XSS/命令注入/文件包含** | 真实 Payload 测试 |
| 🧰 辅助工具 | 哈希/Base64/URL 编解码/IP 查询 | 标准库 + API |

#### AI Web 渗透详细说明
- ✅ **CMS 识别**: WordPress, Joomla, Drupal, DedeCMS 等 8 种
- ✅ **框架识别**: ThinkPHP, Laravel, Spring, Django 等 10 种
- ✅ **目录枚举**: 25+ 敏感路径 (后台/配置/备份/API)
- ✅ **SQL 注入**: Boolean/UNION/Time-Based 真实 Payload 测试
- ✅ **XSS 检测**: Script/Img/JS/SVG/Iframe 反射测试
- ✅ **命令注入**: Linux/Windows命令执行检测
- ✅ **文件包含**: LFI/RFI漏洞检测
- ✅ **API 发现**: REST/GraphQL/Swagger端点探测

---

## 🚀 快速开始

### Windows 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/boxtool.git
cd boxtool

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python main.py
```

### Android APK 安装

1. 前往 [Releases](../../releases) 下载最新 APK
2. 在 Android 设备上安装
3. 启动 BoxTool 开始使用

---

## 🔧 依赖安装

### 核心依赖（必须）
```bash
pip install -r requirements.txt
```

### 依赖说明
```bash
# 核心库 (必须)
kivy>=2.3.0              # GUI 框架
requests>=2.31.0         # HTTP 请求
beautifulsoup4>=4.12.0   # HTML 解析
urllib3>=2.0.0           # URL 处理

# 网络与安全 (推荐)
paramiko>=3.4.0          # SSH 爆破
pymysql>=1.1.0           # MySQL 爆破
dnspython>=2.4.0         # DNS 收集
python-whois>=0.8.0      # Whois 查询
redis>=5.0.0             # Redis 爆破

# 工具库
qrcode[pil]>=7.4.0       # 二维码生成
Pillow>=10.0.0           # 图像处理

# 可选 (高级功能)
# shodan>=2.3.0          # Shodan 侦察
# scapy>=2.5.0           # 高级网络扫描
```

---

## 📦 构建 APK

### 使用 GitHub Actions（推荐）

1. Fork 本仓库
2. 推送代码到你的仓库
3. 创建 tag: `git tag v5.1.0 && git push origin v5.1.0`
4. Actions 会自动构建 APK

### 本地构建

```bash
# 安装 buildozer
pip install buildozer cython

# 初始化（首次运行）
buildozer init

# 构建 debug 版本
buildozer android debug

# 构建 release 版本
buildozer android release
```

APK 文件将生成在 `bin/` 目录中。

---

## 📁 项目结构

```
apk/
├── main.py              # 主程序入口（GUI 界面）
├── engine.py            # 核心引擎模块（纯 Python 实现）
├── ai_module.py         # AI Web 渗透模块（商业级）
├── requirements.txt     # Python 依赖
├── buildozer.spec       # Buildozer 配置
├── fonts/
│   └── simhei.ttf       # 中文字体
├── wordlists/
│   ├── top_passwords.txt   # 常用密码表
│   └── top_usernames.txt   # 常用用户名表
├── .github/
│   └── workflows/
│       └── build-apk.yml  # GitHub Actions 工作流
└── README.md
```

---

## ✅ v5.1 升级内容

### 移除外部工具依赖
- ❌ 移除 msfconsole 依赖 → ✅ 纯 Python 漏洞检测
- ❌ 移除 nmap 依赖 → ✅ 纯 Python 端口扫描
- ❌ 移除 sqlmap 依赖 → ✅ 纯 Python SQL 注入检测

### 功能增强
- ✅ 所有模块纯 Python 实现
- ✅ APK 打包后 100% 可用
- ✅ AI Web 渗透商业级升级
- ✅ 报告生成功能完善

### 代码优化
- ✅ 重构 engine.py 核心引擎
- ✅ 独立 ai_module.py 模块
- ✅ 添加完整测试脚本
- ✅ 优化依赖管理

---

## ⚠️ 免责声明

本工具仅供**安全研究和教育目的**使用。

- ❌ 请勿用于非法用途
- ❌ 请勿未经授权对目标进行测试
- ✅ 仅在你拥有或获得授权的系统上使用
- ✅ 遵守当地法律法规

使用本工具进行未授权渗透测试可能导致法律责任。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📞 联系方式

- 📧 Email: your.email@example.com
- 💬 Issues: [GitHub Issues](../../issues)

---

<div align="center">

**Made with ❤️ by BoxTool Team**

⭐ 如果这个项目对你有帮助，请给个 Star！

</div>
