# 🌳 MRPACK 终端检查器

[![PyPI 包版本 / Package Version](https://img.shields.io/pypi/v/read-mrpack-tui?style=for-the-badge&logo=pypi&logoColor=white&label=Package%20Version&labelColor=3775A9&color=FFD43B)](https://pypi.org/project/read-mrpack-tui/)
[![支持的 Python 版本 / Supported Python Versions](https://img.shields.io/pypi/pyversions/read-mrpack-tui?style=for-the-badge&logo=python&logoColor=white&labelColor=3775A9&color=FFD43B)](https://pypi.org/project/read-mrpack-tui/)

> 一个基于 Textual 的终端界面，用于读取和浏览 Modrinth `.mrpack` 整合包。

> **[📖 English](README.en-us.md)**
> **[📖 简体中文(大陆)](README.md)**
> **[📖 繁體中文(台灣)](README.zh-tw.md)**

## ✨ 功能

- 📦 查看整合包元数据、依赖、Modrinth 索引文件与归档根目录统计。
- 🌳 浏览完整 ZIP 文件树，目录默认折叠以适应大型整合包。
- 🔎 在文件树中搜索文件名、文件夹名或受限 UTF-8 文本内容，并用上/下按钮、方向键或 W/S 切换匹配项。
- 🔍 按路径、环境侧别或下载地址筛选索引文件。
- 🌐 支持简体中文、繁体中文和英文。

## 🚀 使用

💡 环境要求：Python 3.11 或更高版本，以及 [uv](https://docs.astral.sh/uv/)。

```powershell
uvx --refresh read-mrpack-tui
```

📂 直接传入整合包绝对路径：

```powershell
uvx --refresh read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```

🌐 指定界面语言：

```powershell
uvx --refresh read-mrpack-tui --lang zh-cn "D:\Minecraft\modpacks\example.mrpack"
```

## 🛠️ 开发

```powershell
uv sync
uv run read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```

## 🖼️ 界面预览

### 📦 概览

![概览](docs/images/preview/概览-overview.png)

### 🗂️ 索引文件

![索引文件](docs/images/preview/索引文件-indexed-files.png)

### 🌳 文件树

![文件树](docs/images/preview/文件树-file-tree.png)

### 🗃️ 归档内容

![归档内容](docs/images/preview/归档内容-archive.png)

## 📄 许可证

本项目采用 [MIT License](LICENSE)。
