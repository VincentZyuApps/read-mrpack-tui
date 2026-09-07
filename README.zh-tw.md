# 🌳 MRPACK 終端檢查器

[![PyPI 包版本 / Package Version](https://img.shields.io/pypi/v/read-mrpack-tui?style=for-the-badge&logo=pypi&logoColor=white&label=Package%20Version&labelColor=3775A9&color=FFD43B)](https://pypi.org/project/read-mrpack-tui/)
[![支援的 Python 版本 / Supported Python Versions](https://img.shields.io/pypi/pyversions/read-mrpack-tui?style=for-the-badge&logo=python&logoColor=white&labelColor=3775A9&color=FFD43B)](https://pypi.org/project/read-mrpack-tui/)

> 一個基於 Textual 的終端介面，用於讀取及瀏覽 Modrinth `.mrpack` 整合包。

> **[📖 English](README.en-us.md)**
> **[📖 简体中文(大陆)](README.md)**
> **[📖 繁體中文(台灣)](README.zh-tw.md)**

## ✨ 功能

- 📦 檢視整合包中繼資料、相依項目、Modrinth 索引檔案及封存根目錄統計。
- 🌳 瀏覽完整 ZIP 檔案樹，目錄預設摺疊以適應大型整合包。
- 🔎 在檔案樹中搜尋檔案名稱、資料夾名稱或受限 UTF-8 文字內容，並用方向鍵或 W/S 切換相符項目。
- 🔍 依路徑、環境側別或下載網址篩選索引檔案。
- 🌐 支援簡體中文、繁體中文及英文。

## 🚀 使用方式

💡 環境需求：Python 3.11 或更新版本，以及 [uv](https://docs.astral.sh/uv/)。

```powershell
uvx --refresh read-mrpack-tui
```

📂 直接傳入整合包絕對路徑：

```powershell
uvx --refresh read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```

🌐 指定介面語言：

```powershell
uvx --refresh read-mrpack-tui --lang zh-tw "D:\Minecraft\modpacks\example.mrpack"
```

## 🛠️ 開發

```powershell
uv sync
uv run read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```

## 🖼️ 介面預覽

### 📦 概覽

![概覽](docs/images/preview/概览-overview.png)

### 🗂️ 索引檔案

![索引檔案](docs/images/preview/索引文件-indexed-files.png)

### 🌳 檔案樹

![檔案樹](docs/images/preview/文件树-file-tree.png)

### 🗃️ 封存內容

![封存內容](docs/images/preview/归档内容-archive.png)

## 📄 授權條款

本專案採用 [MIT License](LICENSE)。
