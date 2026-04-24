# Music Player

一款专业的音乐播放器软件，支持多种音频格式，具有现代化的界面和丰富的功能。

## 功能特点

- 🎵 支持多种音频格式（MP3、FLAC、AAC、WAV等）
- 🎨 现代化用户界面，支持主题颜色跟随
- 📝 歌词同步显示
- 🌐 在线音乐搜索和下载
- 🔊 高质量音频播放
- 🎵 多种播放模式（顺序、随机、单曲循环等）

## 系统要求

- Windows 10/11
- macOS 10.14 或更高版本
- Python 3.9 或更高版本

## 安装

### 从GitHub Releases下载

1. 访问 [GitHub Releases](https://github.com/rockwave2009/MusicPlayer/releases)
2. 下载适合您系统的版本
3. 解压并运行程序

### 从源码安装

```bash
git clone https://github.com/rockwave2009/MusicPlayer.git
cd MusicPlayer
pip install -r requirements.txt
python run.py
```

## 构建说明

本项目使用 PyInstaller 进行打包，支持跨平台构建：

- **macOS**: 生成 `.dmg` 安装包和 `.app` 应用程序
- **Windows**: 生成 `.exe` 可执行文件和 `.zip` 压缩包

构建过程通过 GitHub Actions 自动化完成，支持 Intel 和 AMD 架构。

## 开发

### 项目结构

```
src/
├── core/           # 核心功能模块
├── ui/             # 用户界面
├── plugins/        # 插件系统
└── utils/          # 工具函数
```

### 依赖项

主要依赖项：
- PyQt6: 用户界面框架
- mutagen: 音频文件处理
- numpy: 数值计算
- playwright: 网页自动化（用于在线搜索）

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 作者

Music Player Team - musicplayer@example.com