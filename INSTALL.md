# Installation Guide

[English](INSTALL.md) | [中文](INSTALL_zh.md)

AutoRunX is currently in development and not yet published to PyPI. Here are the available installation methods:

## Method 1: Direct Run with uvx (Recommended)

The easiest way to try AutoRunX without installation:

```bash
# Run directly from GitHub
uvx --from git+https://github.com/faker2048/autorunx autorunx --help

# Add a service
uvx --from git+https://github.com/faker2048/autorunx autorunx add "python -m http.server 8000" --name web-server

# List services
uvx --from git+https://github.com/faker2048/autorunx autorunx list
```

**Advantages:**
- No installation required
- Always gets the latest version
- Clean, no system pollution

## Method 2: Install with pip from GitHub

Install AutoRunX to your Python environment:

```bash
# Install from GitHub main branch
pip install git+https://github.com/faker2048/autorunx.git

# Or install from a specific branch
pip install git+https://github.com/faker2048/autorunx.git@develop

# Or install from a specific tag
pip install git+https://github.com/faker2048/autorunx.git@v0.1.0
```

After installation, you can use the `autorunx` command directly:

```bash
autorunx --help
autorunx add "python -m http.server 8000" --name web-server
```

## Method 3: Clone and Install Locally

For development or when you want to modify the code:

```bash
# Clone the repository
git clone https://github.com/faker2048/autorunx.git
cd autorunx

# Install in development mode
pip install -e .

# Or use make for convenience
make install-local
```

## Method 4: Development Setup

If you want to contribute or develop AutoRunX:

```bash
# Clone the repository
git clone https://github.com/faker2048/autorunx.git
cd autorunx

# Install development dependencies
make install

# Run tests
make test

# Run in development mode
make dev
```

## Requirements

- Python 3.8 or higher
- pip or uv package manager

### Dependencies

AutoRunX has minimal dependencies:
- `click` - Command line interface
- `psutil` - Process and system monitoring
- `rich` - Rich text and beautiful formatting
- `toml` - Configuration file parsing

## Troubleshooting

### Git Installation Issues

If you encounter issues installing from Git:

```bash
# Make sure Git is installed
git --version

# Try with explicit Git URL
pip install git+https://github.com/faker2048/autorunx.git@main

# Or use SSH if you have access
pip install git+ssh://git@github.com/faker2048/autorunx.git
```

### Permission Issues

If you get permission errors:

```bash
# Install to user directory
pip install --user git+https://github.com/faker2048/autorunx.git

# Or use virtual environment
python -m venv autorunx-env
source autorunx-env/bin/activate  # On Windows: autorunx-env\Scripts\activate
pip install git+https://github.com/faker2048/autorunx.git
```

### Python Version Issues

AutoRunX requires Python 3.8+:

```bash
# Check Python version
python --version

# If you have multiple Python versions
python3.8 -m pip install git+https://github.com/faker2048/autorunx.git
```

## Upgrading

To upgrade to the latest version:

```bash
# With pip
pip install --upgrade git+https://github.com/faker2048/autorunx.git

# With uvx (always gets latest)
uvx --from git+https://github.com/faker2048/autorunx autorunx --version
```

## Uninstalling

To remove AutoRunX:

```bash
pip uninstall autorunx
```

Note: This won't remove configuration files and service data. To completely clean up:

```bash
# Remove configuration directory
rm -rf ~/.config/autorunx

# Remove data directory
rm -rf ~/.local/share/autorunx
```

## Future PyPI Release

Once AutoRunX is published to PyPI, installation will be simpler:

```bash
# Future installation (not available yet)
pip install autorunx
uvx autorunx
```

## Getting Help

If you encounter any installation issues:

1. Check the [GitHub Issues](https://github.com/faker2048/autorunx/issues)
2. Make sure you meet the requirements
3. Try the troubleshooting steps above
4. Create a new issue with your error details