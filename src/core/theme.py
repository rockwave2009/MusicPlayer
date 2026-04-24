"""
主题管理模块
支持明/暗主题切换
"""

from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication


class Theme(Enum):
    """主题枚举"""
    LIGHT = "light"
    DARK = "dark"


# 浅色主题样式
LIGHT_THEME = """
    QMainWindow, QWidget {
        background-color: #FFFFFF;
        color: #333333;
    }
    
    QLabel {
        color: #333333;
        background: transparent;
    }
    
    QPushButton {
        background-color: #F0F0F0;
        color: #333333;
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 6px 12px;
    }
    
    QPushButton:hover {
        background-color: #E0E0E0;
        border-color: #00AAFF;
    }
    
    QPushButton:pressed {
        background-color: #D0D0D0;
    }
    
    QPushButton:checked {
        background-color: #00AAFF;
        color: white;
        border-color: #00AAFF;
    }
    
    QPushButton[role="primary"] {
        background-color: #00AAFF;
        color: white;
        border: none;
    }
    
    QPushButton[role="primary"]:hover {
        background-color: #0088CC;
    }
    
    QListWidget, QTreeWidget {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        alternate-background-color: #F5F5F5;
    }
    
    QListWidget::item, QTreeWidget::item {
        padding: 6px;
    }
    
    QListWidget::item:hover, QTreeWidget::item:hover {
        background-color: #E0E0E0;
    }
    
    QListWidget::item:selected, QTreeWidget::item:selected {
        background-color: #D0E8FF;
        color: #333333;
    }
    
    QTabWidget::pane {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        background-color: #FFFFFF;
    }
    
    QTabBar::tab {
        background-color: #F5F5F5;
        color: #666666;
        border: 1px solid #E0E0E0;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #FFFFFF;
        color: #333333;
        border-bottom-color: #FFFFFF;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #E0E0E0;
    }
    
    QSlider::groove:horizontal {
        height: 6px;
        background-color: #E0E0E0;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        width: 14px;
        height: 14px;
        margin: -4px 0;
        background-color: #00AAFF;
        border-radius: 7px;
    }
    
    QSlider::sub-page:horizontal {
        background-color: #00AAFF;
        border-radius: 3px;
    }
    
    QProgressBar {
        height: 6px;
        background-color: #E0E0E0;
        border-radius: 3px;
    }
    
    QProgressBar::chunk {
        background-color: #00AAFF;
        border-radius: 3px;
    }
    
    QScrollBar:vertical {
        width: 10px;
        background-color: #F0F0F0;
        border-radius: 5px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #CCCCCC;
        border-radius: 5px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #AAAAAA;
    }
    
    QScrollBar:horizontal {
        height: 10px;
        background-color: #F0F0F0;
        border-radius: 5px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #CCCCCC;
        border-radius: 5px;
        min-width: 30px;
    }
    
    QMenuBar {
        background-color: #F5F5F5;
        color: #333333;
        border-bottom: 1px solid #E0E0E0;
    }
    
    QMenuBar::item:selected {
        background-color: #E0E0E0;
    }
    
    QMenu {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #E0E0E0;
    }
    
    QToolBar {
        background-color: #F5F5F5;
        border-bottom: 1px solid #E0E0E0;
    }
    
    QStatusBar {
        background-color: #F0F0F0;
        color: #666666;
        border-top: 1px solid #E0E0E0;
    }
    
    QLineEdit {
        background-color: #FFFFFF;
        color: #333333;
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        padding: 6px;
    }
    
    QLineEdit:focus {
        border-color: #00AAFF;
    }
    
    QFrame[frameShape="4"] {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        background-color: #F5F5F5;
    }
    
    /* 歌词行样式 */
    QLabel[lyricLine="true"] {
        color: #888888;
        padding: 8px 16px;
        background: transparent;
    }
    
    QLabel[lyricLine="true"][current="true"] {
        color: #00AAFF;
        padding: 12px 16px;
        background: rgba(0, 170, 255, 0.1);
        border-radius: 8px;
    }
    
    /* 辅助文字样式 */
    QLabel[role="hint"] {
        color: #aaaaaa;
    }
    
    QLabel[role="subtitle"] {
        font-size: 14px;
        font-weight: bold;
        color: #333333;
        background: #f0f0f0;
    }
"""

# 深色主题样式
DARK_THEME = """
    QMainWindow, QWidget {
        background-color: #1E1E1E;
        color: #E0E0E0;
    }
    
    QLabel {
        color: #E0E0E0;
        background: transparent;
    }
    
    QPushButton {
        background-color: #383838;
        color: #E0E0E0;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 6px 12px;
    }
    
    QPushButton:hover {
        background-color: #454545;
        border-color: #00AAFF;
    }
    
    QPushButton:pressed {
        background-color: #505050;
    }
    
    QPushButton:checked {
        background-color: #00AAFF;
        color: white;
        border-color: #00AAFF;
    }
    
    QPushButton[role="primary"] {
        background-color: #00AAFF;
        color: white;
        border: none;
    }
    
    QPushButton[role="primary"]:hover {
        background-color: #33BBFF;
    }
    
    QListWidget, QTreeWidget {
        background-color: #2D2D2D;
        border: 1px solid #404040;
        border-radius: 4px;
        alternate-background-color: #383838;
    }
    
    QListWidget::item, QTreeWidget::item {
        padding: 6px;
        color: #E0E0E0;
    }
    
    QListWidget::item:hover, QTreeWidget::item:hover {
        background-color: #404040;
    }
    
    QListWidget::item:selected, QTreeWidget::item:selected {
        background-color: #1A3A4D;
        color: #E0E0E0;
    }
    
    QTabWidget::pane {
        border: 1px solid #404040;
        border-radius: 4px;
        background-color: #2D2D2D;
    }
    
    QTabBar::tab {
        background-color: #383838;
        color: #AAAAAA;
        border: 1px solid #404040;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    QTabBar::tab:selected {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border-bottom-color: #2D2D2D;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #404040;
    }
    
    QSlider::groove:horizontal {
        height: 6px;
        background-color: #404040;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        width: 14px;
        height: 14px;
        margin: -4px 0;
        background-color: #00AAFF;
        border-radius: 7px;
    }
    
    QSlider::sub-page:horizontal {
        background-color: #00AAFF;
        border-radius: 3px;
    }
    
    QProgressBar {
        height: 6px;
        background-color: #404040;
        border-radius: 3px;
    }
    
    QProgressBar::chunk {
        background-color: #00AAFF;
        border-radius: 3px;
    }
    
    QScrollBar:vertical {
        width: 10px;
        background-color: #2D2D2D;
        border-radius: 5px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #555555;
        border-radius: 5px;
        min-height: 30px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #777777;
    }
    
    QScrollBar:horizontal {
        height: 10px;
        background-color: #2D2D2D;
        border-radius: 5px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #555555;
        border-radius: 5px;
        min-width: 30px;
    }
    
    QMenuBar {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border-bottom: 1px solid #404040;
    }
    
    QMenuBar::item:selected {
        background-color: #404040;
    }
    
    QMenu {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #404040;
        border-radius: 4px;
    }
    
    QMenu::item:selected {
        background-color: #404040;
    }
    
    QToolBar {
        background-color: #2D2D2D;
        border-bottom: 1px solid #404040;
    }
    
    QStatusBar {
        background-color: #2D2D2D;
        color: #AAAAAA;
        border-top: 1px solid #404040;
    }
    
    QLineEdit {
        background-color: #2D2D2D;
        color: #E0E0E0;
        border: 1px solid #404040;
        border-radius: 4px;
        padding: 6px;
    }
    
    QLineEdit:focus {
        border-color: #00AAFF;
    }
    
    QFrame[frameShape="4"] {
        border: 1px solid #404040;
        border-radius: 4px;
        background-color: #383838;
    }
    
    /* 歌词行样式 */
    QLabel[lyricLine="true"] {
        color: #666666;
        padding: 8px 16px;
        background: transparent;
    }
    
    QLabel[lyricLine="true"][current="true"] {
        color: #33BBFF;
        padding: 12px 16px;
        background: rgba(0, 170, 255, 0.15);
        border-radius: 8px;
    }
    
    /* 辅助文字样式 */
    QLabel[role="hint"] {
        color: #888888;
    }
    
    QLabel[role="subtitle"] {
        font-size: 14px;
        font-weight: bold;
        color: #E0E0E0;
        background: #2D2D2D;
    }
"""


class ThemeManager(QObject):
    """
    主题管理器
    负责主题切换和样式应用
    """
    
    # 信号定义
    theme_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_theme = Theme.LIGHT
    
    def set_theme(self, theme: Theme):
        """设置主题"""
        if theme != self.current_theme:
            self.current_theme = theme
            self.theme_changed.emit(theme.value)
    
    def toggle_theme(self):
        """切换主题"""
        if self.current_theme == Theme.LIGHT:
            self.set_theme(Theme.DARK)
        else:
            self.set_theme(Theme.LIGHT)
    
    def get_theme(self) -> Theme:
        """获取当前主题"""
        return self.current_theme
    
    def is_dark(self) -> bool:
        """是否为深色主题"""
        return self.current_theme == Theme.DARK
    
    def get_stylesheet(self) -> str:
        """获取当前主题的样式表"""
        if self.current_theme == Theme.DARK:
            return DARK_THEME
        else:
            return LIGHT_THEME
    
    def apply_theme(self, app: QApplication):
        """应用主题到应用程序"""
        app.setStyleSheet(self.get_stylesheet())