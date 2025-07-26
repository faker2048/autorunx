# Autostartx - 命令行程序服务化工具

一行命令将任何命令行程序转换为可自动重启的后台服务。简单、快速、零配置。

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

[中文文档](README_zh.md) | [English](README.md)

## 快速开始

**方式1: 使用 uvx 直接运行（推荐）**

将长期运行的命令转为服务

```
uvx autostartx add "python -m http.server 8000" --name web
```

**方式2: 安装到系统**

一次安装，随处使用

```pip install autostartx```

或

```uvx autostartx install```

**基本用法**
```bash
autostartx add "python -m http.server 8000" --name web
autostartx add "tailscale up --ssh" --name vpn

# 或使用简化别名 'asx'（功能完全相同）
asx add "python -m http.server 8000" --name web
asx list
```

**查看服务状态**
```bash
autostartx list        # 显示所有服务
autostartx logs web -f # 查看日志

# 简化版本
asx list
asx logs web -f
```

**方式3: 传统安装**
```bash
git clone https://github.com/faker2048/autostartx.git && cd autostartx && pip install .
```

## 常用命令

```bash
autostartx add "命令"              # 添加服务（或: asx add "命令"）
autostartx list                   # 查看服务（或: asx list）
autostartx start/stop/restart     # 控制服务
autostartx logs <名称> -f         # 查看日志
autostartx daemon --action start  # 启动自动重启守护进程
```

## 为什么选择 Autostartx？

- **简单**: 一行命令就能将任何长期运行的程序变成服务
- **可靠**: 程序崩溃时自动重启
- **跨平台**: 支持 Windows、Linux、macOS
- **零配置**: 无需设置文件

适用于开发服务器、后台守护进程、监控工具、代理服务等场景。

## 许可证

MIT License