# 🌳 MRPACK TUI Inspector

> A Textual terminal interface for reading and browsing Modrinth `.mrpack` modpacks.

> **[📖 English](README.en-us.md)**
> **[📖 简体中文(大陆)](README.md)**
> **[📖 繁體中文(台灣)](README.zh-tw.md)**

## ✨ Features

- 📦 View pack metadata, dependencies, Modrinth indexed files, and archive root statistics.
- 🌳 Browse the complete ZIP file tree, with directories collapsed by default for large modpacks.
- 🔍 Filter indexed files by path, environment side, or download URL.
- 🌐 Support Simplified Chinese, Traditional Chinese, and English.

## 🖼️ Preview

### 📦 Overview

![Overview](docs/images/preview/概览-overview.png)

### 🗂️ Indexed Files

![Indexed files](docs/images/preview/索引文件-indexed-files.png)

### 🔢 File Count

![File count](docs/images/preview/文件数-file-count.png)

### 🗃️ Archive Contents

![Archive contents](docs/images/preview/归档内容-archive.png)

## 🚀 Usage

💡 Requirement: Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```powershell
uvx read-mrpack-tui
```

📂 Pass an absolute modpack path directly:

```powershell
uvx read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```

🌐 Select a display language:

```powershell
uvx read-mrpack-tui --lang en-us "D:\Minecraft\modpacks\example.mrpack"
```

## 🛠️ Development

```powershell
uv sync
uv run read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```
