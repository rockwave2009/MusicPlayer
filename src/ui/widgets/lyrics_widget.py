"""
歌词显示组件
提供歌词的可视化显示和同步滚动
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette

from typing import List, Optional
from core.lyrics import LyricsManager, LyricLine


class LyricLineWidget(QLabel):
    """
    单行歌词组件
    支持高亮和动画效果
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.index = -1
        self.is_current = False
        self._setup_style()
    
    def _setup_style(self):
        """设置样式 - 使用属性让主题样式表控制颜色"""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.setFont(QFont("Microsoft YaHei", 12))
        self.setProperty("lyricLine", True)
        self.setProperty("current", False)
        self._apply_style()
    
    def _apply_style(self):
        """应用样式 - 只设置布局属性，颜色由主题样式表控制"""
        if self.is_current:
            self.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
            self.setProperty("current", True)
        else:
            self.setFont(QFont("Microsoft YaHei", 12))
            self.setProperty("current", False)
        # 强制刷新样式
        self.style().unpolish(self)
        self.style().polish(self)
    
    def set_current(self, is_current: bool):
        """设置是否为当前播放行"""
        self.is_current = is_current
        self._apply_style()


class LyricsDisplayWidget(QWidget):
    """
    歌词显示组件
    支持滚动显示和自动同步
    """
    
    # 信号定义
    line_clicked = pyqtSignal(int)  # 点击歌词行信号
    download_lyrics_requested = pyqtSignal(str, str)  # 请求下载歌词信号 (query, audio_path)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.lyrics_manager = LyricsManager()
        self.line_widgets: List[LyricLineWidget] = []
        self.current_index = -1
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化UI - 移除硬编码颜色，适配主题"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 歌词标题
        self.title_label = QLabel("歌词")
        self.title_label.setProperty("role", "subtitle")
        self.title_label.setStyleSheet("padding: 8px; border-bottom: 1px solid;")
        layout.addWidget(self.title_label)
        
        # 歌词滚动区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                width: 8px;
            }
            QScrollBar::handle:vertical {
                border-radius: 4px;
            }
        """)
        
        # 歌词容器
        self.lyrics_container = QWidget()
        self.lyrics_layout = QVBoxLayout(self.lyrics_container)
        self.lyrics_layout.setContentsMargins(16, 16, 16, 16)
        self.lyrics_layout.setSpacing(4)
        self.lyrics_layout.addStretch()
        
        self.scroll_area.setWidget(self.lyrics_container)
        layout.addWidget(self.scroll_area)
        
        # 底部工具栏
        toolbar = QFrame()
        toolbar.setFrameShape(QFrame.Shape.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar)
        
        # 加载歌词按钮
        self.load_btn = QPushButton("加载歌词")
        self.load_btn.setProperty("role", "primary")
        self.load_btn.clicked.connect(self._load_lyrics_file)
        toolbar_layout.addWidget(self.load_btn)
        
        # 自动查找按钮
        self.auto_find_btn = QPushButton("自动查找")
        self.auto_find_btn.clicked.connect(self._auto_find_lyrics)
        toolbar_layout.addWidget(self.auto_find_btn)
        
        # 下载歌词按钮
        self.download_lyrics_btn = QPushButton("下载歌词")
        self.download_lyrics_btn.clicked.connect(self._download_lyrics)
        toolbar_layout.addWidget(self.download_lyrics_btn)
        
        toolbar_layout.addStretch()
        
        # 歌词状态
        self.status_label = QLabel("未加载歌词")
        self.status_label.setProperty("role", "hint")
        toolbar_layout.addWidget(self.status_label)
        
        layout.addWidget(toolbar)
    
    def _connect_signals(self):
        """连接信号"""
        self.lyrics_manager.lyrics_loaded.connect(self._on_lyrics_loaded)
        self.lyrics_manager.current_line_changed.connect(self._on_line_changed)
        self.lyrics_manager.error_occurred.connect(self._on_error)
    
    def load_lyrics(self, file_path: str):
        """加载歌词文件"""
        self.lyrics_manager.load_lyrics(file_path)
    
    def load_from_string(self, content: str):
        """从字符串加载歌词"""
        self.lyrics_manager.load_from_string(content)
    
    def set_audio_file(self, audio_file_path: str):
        """设置音频文件路径（用于自动查找歌词）"""
        self.audio_file_path = audio_file_path
        # 切换歌曲时立即清空歌词，避免显示上一首的歌词
        self.lyrics_manager.clear()
        self._display_lyrics()
        self.status_label.setText("正在查找歌词...")
    
    def update_position(self, position: float):
        """更新播放位置"""
        self.lyrics_manager.update_position(position)
    
    def _on_lyrics_loaded(self, message: str):
        """歌词加载完成处理"""
        self.status_label.setText(message)
        self._display_lyrics()
    
    def _on_line_changed(self, index: int, text: str):
        """歌词行改变处理"""
        self._highlight_line(index)
    
    def _on_error(self, error_message: str):
        """错误处理"""
        self.status_label.setText(error_message)
        # 出错时也刷新显示为暂无歌词
        self._display_lyrics()
    
    def _display_lyrics(self):
        """显示歌词"""
        # 清空现有歌词
        self._clear_lyrics()
        
        lyrics = self.lyrics_manager.get_all_lyrics()
        if not lyrics:
            # 显示"暂无歌词"提示
            no_lyrics_label = QLabel("暂无歌词")
            no_lyrics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_lyrics_label.setProperty("role", "hint")
            no_lyrics_label.setStyleSheet("padding: 40px; font-size: 16px;")
            self.lyrics_layout.addWidget(no_lyrics_label)
            return
        
        # 添加空行（用于顶部间距）
        spacer_top = QLabel("")
        spacer_top.setFixedHeight(100)
        self.lyrics_layout.addWidget(spacer_top)
        
        # 创建歌词行
        for i, line in enumerate(lyrics):
            line_widget = LyricLineWidget(line.text)
            line_widget.index = i
            line_widget.mousePressEvent = lambda event, idx=i: self._on_line_click(idx)
            self.line_widgets.append(line_widget)
            self.lyrics_layout.addWidget(line_widget)
        
        # 添加空行（用于底部间距）
        spacer_bottom = QLabel("")
        spacer_bottom.setFixedHeight(200)
        self.lyrics_layout.addWidget(spacer_bottom)
        
        # 更新标题
        metadata = self.lyrics_manager.parser.get_metadata()
        title = metadata.get('ti', '')
        artist = metadata.get('ar', '')
        if title or artist:
            self.title_label.setText(f"{artist} - {title}" if artist and title else title or artist)
    
    def _clear_lyrics(self):
        """清空歌词显示"""
        # 清除所有歌词行组件
        for widget in self.line_widgets:
            widget.deleteLater()
        self.line_widgets.clear()
        
        # 清除布局中的所有项目
        while self.lyrics_layout.count():
            item = self.lyrics_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.current_index = -1
    
    def _highlight_line(self, index: int):
        """高亮指定行"""
        if index == self.current_index:
            return
        
        # 取消之前的高亮
        if 0 <= self.current_index < len(self.line_widgets):
            self.line_widgets[self.current_index].set_current(False)
        
        # 高亮新行
        if 0 <= index < len(self.line_widgets):
            self.line_widgets[index].set_current(True)
            self.current_index = index
            
            # 滚动到当前行
            self._scroll_to_line(index)
    
    def _scroll_to_line(self, index: int):
        """滚动到指定行"""
        if 0 <= index < len(self.line_widgets):
            widget = self.line_widgets[index]
            
            # 计算滚动位置（将当前行置于中央）
            scroll_bar = self.scroll_area.verticalScrollBar()
            widget_pos = widget.pos().y()
            widget_height = widget.height()
            area_height = self.scroll_area.height()
            
            target_pos = widget_pos - (area_height / 2) + (widget_height / 2)
            
            # 平滑滚动动画
            self.scroll_animation = QPropertyAnimation(scroll_bar, b"value")
            self.scroll_animation.setDuration(300)
            self.scroll_animation.setStartValue(scroll_bar.value())
            self.scroll_animation.setEndValue(int(target_pos))
            self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.scroll_animation.start()
    
    def _on_line_click(self, index: int):
        """歌词行点击处理"""
        self.line_clicked.emit(index)
    
    def _load_lyrics_file(self):
        """加载歌词文件对话框"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择歌词文件",
            "",
            "LRC歌词文件 (*.lrc);;所有文件 (*)"
        )
        
        if file_path:
            self.load_lyrics(file_path)
    
    def _auto_find_lyrics(self):
        """自动查找歌词"""
        if hasattr(self, 'audio_file_path') and self.audio_file_path:
            if self.lyrics_manager.auto_find_lyrics(self.audio_file_path):
                self.status_label.setText("已找到并加载歌词")
            else:
                self.status_label.setText("未找到匹配的歌词文件")
        else:
            self.status_label.setText("请先加载音频文件")
    
    def _download_lyrics(self):
        """为当前音频下载歌词（通过在线搜索）"""
        if not hasattr(self, 'audio_file_path') or not self.audio_file_path:
            self.status_label.setText("请先加载音频文件")
            return
        
        # 获取音频文件信息用于搜索
        from mutagen import File
        try:
            audio = File(self.audio_file_path, easy=True)
            title = audio.get('title', [''])[0] if audio else ''
            artist = audio.get('artist', [''])[0] if audio else ''
        except:
            title = ''
            artist = ''
        
        # 如果没有元数据，使用文件名
        if not title:
            title = Path(self.audio_file_path).stem
        
        query = f"{artist} {title}".strip()
        self.status_label.setText(f"正在搜索歌词: {query}...")
        
        # 发射信号让主窗口处理下载
        self.download_lyrics_requested.emit(query, self.audio_file_path)
    
    def on_lyrics_downloaded(self, success: bool, message: str):
        """歌词下载完成的回调"""
        self.status_label.setText(message)
        if success and hasattr(self, 'audio_file_path'):
            # 重新尝试自动查找
            self.lyrics_manager.auto_find_lyrics(self.audio_file_path)
            if self.lyrics_manager.has_lyrics():
                self._display_lyrics()
    
    def clear(self):
        """清空歌词"""
        self.lyrics_manager.clear()
        self._clear_lyrics()
        self.title_label.setText("歌词")
        self.status_label.setText("未加载歌词")


class MiniLyricsWidget(QWidget):
    """
    迷你歌词组件
    只显示当前播放的歌词行
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.lyrics_manager = LyricsManager()
        self.lyrics_manager.current_line_changed.connect(self._on_line_changed)
    
    def _init_ui(self):
        """初始化UI - 移除硬编码颜色"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.current_line_label = QLabel("暂无歌词")
        self.current_line_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_line_label.setWordWrap(True)
        self.current_line_label.setProperty("role", "hint")
        self.current_line_label.setStyleSheet("padding: 8px; border-radius: 8px;")
        layout.addWidget(self.current_line_label)
    
    def set_lyrics_manager(self, manager: LyricsManager):
        """设置歌词管理器"""
        self.lyrics_manager = manager
        self.lyrics_manager.current_line_changed.connect(self._on_line_changed)
    
    def update_position(self, position: float):
        """更新播放位置"""
        self.lyrics_manager.update_position(position)
    
    def _on_line_changed(self, index: int, text: str):
        """歌词行改变处理"""
        self.current_line_label.setText(text if text else "...")
    
    def clear(self):
        """清空"""
        self.current_line_label.setText("暂无歌词")