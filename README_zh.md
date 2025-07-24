# Autostartx - 命令行程序服务化工具

一行命令将任何命令行程序转换为可自动重启的后台服务。简单、快速、零配置。

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[中文文档](README_zh.md) | [English](README.md)

## 安装和快速开始

```bash
# 从 GitHub 安装
git clone https://github.com/faker2048/autostartx.git
cd autostartx
pip install -e .

# 添加服务
autostartx add "python -m http.server 8000" --name web

# 查看状态
autostartx list

# 查看日志
autostartx logs web -f
```

## 常用命令

```bash
autostartx add "命令"              # 添加服务
autostartx list                   # 查看服务
autostartx start/stop/restart     # 控制服务
autostartx logs <名称> -f         # 查看日志
autostartx daemon --action start  # 启动自动重启守护进程
```

## 为什么选择 Autostartx？

- **简单**: 一行命令就能将任何程序变成服务
- **可靠**: 程序崩溃时自动重启
- **跨平台**: 支持 Windows、Linux、macOS
- **零配置**: 无需设置文件

适用于开发服务器、后台任务、代理服务等场景。

## 许可证

MIT License