# AutoRunX 使用指南

[English](USAGE.md) | [中文](USAGE_zh.md)

## 快速开始

### 安装

```bash
# 使用 uvx 直接运行（无需安装）
uvx autorunx add "python -m http.server 8000" --name my-web

# 或安装后使用
pip install autorunx
```

### 基本操作

```bash
# 添加服务
autorunx add "python -m http.server 8000" --name web-server

# 查看服务列表
autorunx list

# 启动服务
autorunx start --name web-server

# 查看服务状态
autorunx status --name web-server

# 查看实时日志
autorunx logs --name web-server --follow

# 停止服务
autorunx stop --name web-server

# 删除服务
autorunx remove --name web-server
```

## 详细功能

### 服务管理

#### 添加服务
```bash
# 基本添加
autorunx add "command to run" --name service-name

# 高级选项
autorunx add "uvicorn main:app" \
  --name api-server \
  --working-dir /path/to/project

# 禁用自动重启（适用于一次性任务）
autorunx add "backup.sh" --name backup --no-auto-restart
```

#### 服务控制
```bash
# 启动/停止/重启
autorunx start --name service-name
autorunx stop --name service-name
autorunx restart --name service-name

# 暂停/恢复（发送 SIGSTOP/SIGCONT 信号）
autorunx pause --name service-name
autorunx resume --name service-name

# 强制操作
autorunx stop --name service-name --force
autorunx restart --name service-name --force
```

#### 查看状态
```bash
# 简单列表
autorunx list

# 详细状态
autorunx list --status

# 单个服务详细信息
autorunx status --name service-name
```

### 日志管理

```bash
# 查看最近100行日志
autorunx logs --name service-name

# 查看最近50行日志
autorunx logs --name service-name --tail 50

# 实时跟踪日志
autorunx logs --name service-name --follow

# 清空日志
autorunx logs --name service-name --clear
```

### 后台监控

```bash
# 启动守护进程（后台运行，自动重启服务）
autorunx daemon --action start

# 查看守护进程状态
autorunx daemon --action status

# 停止守护进程
autorunx daemon --action stop

# 前台监控模式（用于调试）
autorunx monitor
```

## 交互式模式

当命令缺少必需参数时，工具会进入交互式模式：

```bash
# 没有指定服务时，会显示服务列表供选择
autorunx start
autorunx logs
autorunx remove
```

## 配置文件

默认配置文件位置：`~/.config/autorunx/config.toml`

```toml
[general]
log_level = "INFO"
max_log_size = "10MB"
log_retention_days = 7

[services]
auto_restart = true
restart_delay = 5
max_restart_attempts = 3

[ui]
interactive_mode = true
color_output = true
```

可以通过 `--config` 参数指定自定义配置文件。

## 使用场景

### Web 服务

```bash
# Flask 应用
autorunx add "flask run --host 0.0.0.0 --port 5000" --name flask-app

# FastAPI 应用
autorunx add "uvicorn main:app --host 0.0.0.0 --port 8000" --name fastapi-app

# 静态文件服务
autorunx add "python -m http.server 8080" --name static-server
```

### 代理服务

```bash
# sing-box
autorunx add "sing-box run -c config.json" --name proxy

# v2ray
autorunx add "v2ray run -c config.json" --name v2ray
```

### 后台任务

```bash
# 数据处理脚本
autorunx add "python process_data.py" --name data-processor

# 定时任务
autorunx add "python cron_job.py" --name scheduler

# 监控脚本
autorunx add "python monitor.py" --name monitor
```

### 开发工具

```bash
# 文件监控
autorunx add "watchmedo auto-restart --patterns '*.py' python main.py" --name dev-server

# 前端开发服务器
autorunx add "npm run dev" --name frontend-dev

# 数据库
autorunx add "redis-server" --name redis
```

## 最佳实践

### 1. 服务命名
- 使用有意义的名称，如 `web-api`、`background-worker`
- 避免特殊字符，使用短横线分隔单词

### 2. 工作目录
- 为需要特定工作目录的服务指定 `--working-dir`
- 确保相对路径的正确性

### 3. 日志管理
- 定期查看和清理日志
- 重要服务启用实时日志监控
- 调整日志保留天数和大小限制

### 4. 监控和维护
- 启用守护进程进行自动监控
- 设置合适的重启次数限制
- 定期检查服务状态

### 5. 安全考虑
- 不要在命令中包含敏感信息
- 使用环境变量传递配置
- 限制服务运行权限

## 故障排除

### 服务启动失败
1. 检查命令是否正确
2. 验证工作目录和权限
3. 查看服务日志了解错误信息

### 自动重启不工作
1. 确认 `auto_restart` 已启用
2. 检查是否达到最大重启次数
3. 查看守护进程是否运行

### 日志文件过大
1. 调整 `max_log_size` 配置
2. 使用 `logs --clear` 清空日志
3. 减少日志保留天数

### 性能问题
1. 监控进程资源使用
2. 调整重启延迟时间
3. 检查系统资源限制

## API 使用

可以在 Python 代码中直接使用 AutoRunX：

```python
from autorunx.service_manager import ServiceManager

# 创建管理器
manager = ServiceManager()

# 添加服务
service = manager.add_service(
    name="my-service",
    command="python app.py",
    auto_restart=True
)

# 启动服务
if manager.start_service(service.id):
    print("服务启动成功")

# 获取服务状态
status = manager.get_service_status(service.id)
print(f"服务状态: {status['service'].status.value}")
```

更多示例请查看 `examples/` 目录。