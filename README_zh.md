# AutoRunX - 命令行程序服务化工具

一行命令将任何命令行程序转换为可自动重启的后台服务。专为开发者设计，提供简单直观的进程管理和监控功能。零配置开箱即用，无需复杂设置。

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org) [![UV](https://img.shields.io/badge/built_with-uv-green.svg)](https://github.com/astral-sh/uv) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[中文文档](README_zh.md) | [English](README.md)

## 快速上手

### 安装

```bash
# 通过 uvx 从 GitHub 直接运行（推荐）
uvx --from git+https://github.com/faker2048/autorunx autorunx add "python -m http.server 8000" --name my-web

# 或者用 pip 从 GitHub 安装
pip install git+https://github.com/faker2048/autorunx.git

# 或者克隆到本地安装
git clone https://github.com/faker2048/autorunx.git
cd autorunx
pip install -e .
```

> **注意**: AutoRunX 还未发布到 PyPI，请使用上述 GitHub 安装方式。
> 
> 📋 **详细安装说明和故障排除请查看 [INSTALL_zh.md](INSTALL_zh.md)**

### 基本使用
```bash
# 添加服务
autorunx add "python -m http.server 8000" --name web-server

# 查看服务状态
autorunx list

# 查看日志
autorunx logs -f

# 控制服务
autorunx pause
autorunx resume
```

### 使用场景
```bash
# Web 应用服务
autorunx add "uvicorn main:app --host 0.0.0.0 --port 8000"

# 代理服务
autorunx add "sing-box run -c config.json"

# 后台处理脚本
autorunx add "python process_data.py"

# 一次性任务（禁用自动重启）
autorunx add "backup.sh" --no-auto-restart
```

## 工具对比

| 特性 | AutoRunX | systemd | PM2 | supervisor |
|------|----------|---------|-----|------------|
| **学习成本** | 低 | 高 | 中等 | 高 |
| **平台支持** | 跨平台 | Linux 限定 | 跨平台 | 跨平台 |
| **配置复杂度** | 零配置 | 需要配置文件 | 中等配置 | 复杂配置 |
| **目标用户** | 开发者 | 系统管理员 | Node.js 开发者 | 运维工程师 |


## 贡献

欢迎通过以下方式参与项目：
- 提交 Issue 报告问题或建议功能
- 发送 Pull Request 改进代码
- 为项目点 Star 支持开发

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。