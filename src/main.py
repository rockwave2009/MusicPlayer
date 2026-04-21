#!/usr/bin/env python3
"""
专业音乐播放器 - 主入口文件
支持macOS的专业音乐播放器
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from core.theme import ThemeManager


def setup_environment():
    """设置应用程序环境"""
    QApplication.setApplicationName("专业音乐播放器")
    QApplication.setApplicationVersion("1.0.0")
    QApplication.setOrganizationName("MusicPlayer")
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def main():
    """主函数"""
    setup_environment()
    
    app = QApplication(sys.argv)
    
    # 初始化主题管理器
    theme_manager = ThemeManager()
    
    # 应用主题
    theme_manager.apply_theme(app)
    
    # 创建并显示主窗口
    window = MainWindow(theme_manager)
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()