# 专业音乐播放器

一款功能强大的跨平台音乐播放器，支持多种音频格式、歌词同步显示、在线搜索下载等功能。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey.svg)

## 功能特性

- 🎵 支持多种音频格式：MP3, FLAC, WAV, AAC, M4A, OGG等
- 📝 LRC歌词同步显示
- 🎚️ 10频段均衡器
- 🔍 在线音乐搜索和下载（基于jzmp3.com）
- 🌙 明/暗主题切换
- 📚 音乐库管理
- 📋 播放列表功能

## 下载安装

### macOS
1. 从 [Releases](https://github.com/rockwave2009/MusicPlayer/releases) 下载最新版本的 `.dmg` 文件
2. 双击打开，将应用拖入 Applications 文件夹
3. 首次运行可能需要在"系统偏好设置 > 安全性与隐私"中允许

### Windows
1. 从 [Releases](https://github.com/rockwave2009/MusicPlayer/releases) 下载最新版本的 `.zip` 文件
2. 解压到任意目录
3. 双击 `MusicPlayer.exe` 运行

## 在线搜索功能

首次使用在线搜索功能时，会自动下载浏览器组件（约150MB，一次性操作）。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开音乐文件 |
| Ctrl+Shift+O | 打开音乐文件夹 |
| Ctrl+L | 加载歌词文件 |
| Ctrl+D | 切换深色/浅色模式 |
| Space | 播放/暂停 |
| Ctrl+S | 停止 |
| Ctrl+Left | 上一曲 |
| Ctrl+Right | 下一曲 |
| Ctrl+Q | 退出 |

## 从源码运行

```bash
# 克隆仓库
git clone https://github.com/rockwave2009/MusicPlayer.git
cd MusicPlayer

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装ffmpeg（用于播放AAC等格式）
# macOS: brew install ffmpeg
# Windows: 下载ffmpeg并添加到PATH

# 可选：安装playwright（用于在线搜索）
pip install playwright
playwright install chromium

# 运行
python src/main.py
```

## 构建

```bash
# 安装构建依赖
pip install pyinstaller

# 下载ffmpeg
bash scripts/download_ffmpeg.sh  # macOS/Linux
# 或运行 scripts/download_ffmpeg.ps1  # Windows

# 打包
pyinstaller music_player.spec
```

## 许可证

MIT License