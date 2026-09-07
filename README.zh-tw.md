# 🌳 MRPACK 終端檢查器

> 一個基於 Textual 的終端介面，用於讀取及瀏覽 Modrinth `.mrpack` 整合包。

> **[📖 English](README.en-us.md)**
> **[📖 简体中文(大陆)](README.md)**
> **[📖 繁體中文(台灣)](README.zh-tw.md)**

## ✨ 功能

- 📦 檢視整合包中繼資料、相依項目、Modrinth 索引檔案及封存根目錄統計。
- 🌳 瀏覽完整 ZIP 檔案樹，目錄預設摺疊以適應大型整合包。
- 🔍 依路徑、環境側別或下載網址篩選索引檔案。
- 🌐 支援簡體中文、繁體中文及英文。

## 🖼️ 介面預覽

### 📦 概覽

![概覽](docs/images/preview/概览-overview.png)

### 🗂️ 索引檔案

![索引檔案](docs/images/preview/索引文件-indexed-files.png)

### 🔢 檔案數

![檔案數](docs/images/preview/文件数-file-count.png)

### 🗃️ 封存內容

![封存內容](docs/images/preview/归档内容-archive.png)

## 🚀 使用方式

💡 環境需求：Python 3.11 或更新版本，以及 [uv](https://docs.astral.sh/uv/)。

```powershell
uvx read-mrpack-tui
```

📂 直接傳入整合包絕對路徑：

```powershell
uvx read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```

🌐 指定介面語言：

```powershell
uvx read-mrpack-tui --lang zh-tw "D:\Minecraft\modpacks\example.mrpack"
```

## 🛠️ 開發

```powershell
uv sync
uv run read-mrpack-tui "D:\Minecraft\modpacks\example.mrpack"
```
