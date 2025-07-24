# 安装指南

[English](INSTALL.md) | [中文](INSTALL_zh.md)

AutoRunX 目前还在开发中，尚未发布到 PyPI。以下是可用的安装方法：

## 方法1: 使用 uvx 直接运行（推荐）

最简单的方式，无需安装即可试用 AutoRunX：

```bash
# 从 GitHub 直接运行
uvx --from git+https://github.com/faker2048/autorunx autorunx --help

# 添加服务
uvx --from git+https://github.com/faker2048/autorunx autorunx add "python -m http.server 8000" --name web-server

# 查看服务列表
uvx --from git+https://github.com/faker2048/autorunx autorunx list
```

**优点：**
- 无需安装
- 总是获取最新版本
- 干净，不污染系统

## 方法2: 从 GitHub 用 pip 安装

将 AutoRunX 安装到你的 Python 环境：

```bash
# 从 GitHub main 分支安装
pip install git+https://github.com/faker2048/autorunx.git

# 或从特定分支安装
pip install git+https://github.com/faker2048/autorunx.git@develop

# 或从特定标签安装
pip install git+https://github.com/faker2048/autorunx.git@v0.1.0
```

安装后可以直接使用 `autorunx` 命令：

```bash
autorunx --help
autorunx add "python -m http.server 8000" --name web-server
```

## 方法3: 克隆本地安装

用于开发或想要修改代码时：

```bash
# 克隆仓库
git clone https://github.com/faker2048/autorunx.git
cd autorunx

# 以开发模式安装
pip install -e .

# 或使用 make 方便安装
make install-local
```

## 方法4: 开发环境设置

如果你想贡献代码或开发 AutoRunX：

```bash
# 克隆仓库
git clone https://github.com/faker2048/autorunx.git
cd autorunx

# 安装开发依赖
make install

# 运行测试
make test

# 开发模式运行
make dev
```

## 系统要求

- Python 3.8 或更高版本
- pip 或 uv 包管理器

### 依赖项

AutoRunX 依赖项很少：
- `click` - 命令行界面
- `psutil` - 进程和系统监控
- `rich` - 丰富文本和美观格式化
- `toml` - 配置文件解析

## 故障排除

### Git 安装问题

如果从 Git 安装遇到问题：

```bash
# 确保已安装 Git
git --version

# 尝试使用明确的 Git URL
pip install git+https://github.com/faker2048/autorunx.git@main

# 或如果你有访问权限，使用 SSH
pip install git+ssh://git@github.com/faker2048/autorunx.git
```

### 权限问题

如果遇到权限错误：

```bash
# 安装到用户目录
pip install --user git+https://github.com/faker2048/autorunx.git

# 或使用虚拟环境
python -m venv autorunx-env
source autorunx-env/bin/activate  # Windows: autorunx-env\Scripts\activate
pip install git+https://github.com/faker2048/autorunx.git
```

### Python 版本问题

AutoRunX 需要 Python 3.8+：

```bash
# 检查 Python 版本
python --version

# 如果你有多个 Python 版本
python3.8 -m pip install git+https://github.com/faker2048/autorunx.git
```

## 升级

升级到最新版本：

```bash
# 使用 pip
pip install --upgrade git+https://github.com/faker2048/autorunx.git

# 使用 uvx（总是获取最新版本）
uvx --from git+https://github.com/faker2048/autorunx autorunx --version
```

## 卸载

移除 AutoRunX：

```bash
pip uninstall autorunx
```

注意：这不会删除配置文件和服务数据。要完全清理：

```bash
# 删除配置目录
rm -rf ~/.config/autorunx

# 删除数据目录
rm -rf ~/.local/share/autorunx
```

## 未来的 PyPI 发布

一旦 AutoRunX 发布到 PyPI，安装将更简单：

```bash
# 未来的安装方式（目前尚不可用）
pip install autorunx
uvx autorunx
```

## 获取帮助

如果遇到任何安装问题：

1. 查看 [GitHub Issues](https://github.com/faker2048/autorunx/issues)
2. 确保满足系统要求
3. 尝试上述故障排除步骤
4. 创建新 issue 并提供错误详情