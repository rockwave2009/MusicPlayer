"""
在线音乐搜索组件
提供在线搜索和下载界面
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QProgressBar,
    QSplitter, QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from typing import List
from core.downloader import OnlineMusicDownloader, SearchResult, DownloadResult


class OnlineSearchWidget(QWidget):
    """
    在线音乐搜索组件
    """
    
    # 信号定义
    download_completed = pyqtSignal(str, str)  # 文件路径, 文件名
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化下载器
        self.downloader = OnlineMusicDownloader()
        
        # 状态变量
        self.current_query = ""
        self.current_page = 1
        self.total_pages = 1
        self.search_results: List[SearchResult] = []
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_label = QLabel("在线音乐搜索")
        title_label.setProperty("role", "title")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(title_label)
        
        # 搜索区域
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_frame)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入歌曲名、歌手或专辑...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.setProperty("role", "primary")
        self.search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_btn)
        
        layout.addWidget(search_frame)
        
        # 搜索结果区域
        results_frame = QFrame()
        results_frame.setFrameShape(QFrame.Shape.StyledPanel)
        results_layout = QVBoxLayout(results_frame)
        
        # 结果标题
        results_header = QHBoxLayout()
        self.results_label = QLabel("搜索结果")
        self.results_label.setProperty("role", "subtitle")
        results_header.addWidget(self.results_label)
        
        results_header.addStretch()
        
        # 分页按钮
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self._on_prev_page)
        results_header.addWidget(self.prev_btn)
        
        self.page_label = QLabel("第 1/1 页")
        results_header.addWidget(self.page_label)
        
        self.next_btn = QPushButton("下一页")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self._on_next_page)
        results_header.addWidget(self.next_btn)
        
        results_layout.addLayout(results_header)
        
        # 搜索结果列表
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_result_double_click)
        results_layout.addWidget(self.results_list)
        
        # 下载按钮
        download_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("下载选中")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._on_download_selected)
        download_layout.addWidget(self.download_btn)
        
        download_layout.addStretch()
        
        # 下载目录
        self.dir_label = QLabel(f"下载目录: {self.downloader.get_download_dir()}")
        self.dir_label.setProperty("role", "hint")
        download_layout.addWidget(self.dir_label)
        
        self.change_dir_btn = QPushButton("更改目录")
        self.change_dir_btn.clicked.connect(self._on_change_dir)
        download_layout.addWidget(self.change_dir_btn)
        
        results_layout.addLayout(download_layout)
        
        layout.addWidget(results_frame)
        
        # 进度区域
        progress_frame = QFrame()
        progress_frame.setFrameShape(QFrame.Shape.StyledPanel)
        progress_layout = QVBoxLayout(progress_frame)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
        
        # 提示信息
        if not self.downloader.is_playwright_available():
            hint_label = QLabel("⚠️ 需要安装 Playwright 才能使用在线搜索功能\n请运行: pip install playwright && playwright install chromium")
            hint_label.setStyleSheet("color: #FF6B6B; padding: 8px; background: rgba(255, 107, 107, 0.1); border-radius: 4px;")
            hint_label.setWordWrap(True)
            layout.addWidget(hint_label)
    
    def _connect_signals(self):
        """连接信号"""
        self.downloader.search_finished.connect(self._on_search_finished)
        self.downloader.search_error.connect(self._on_search_error)
        self.downloader.download_progress.connect(self._on_download_progress)
        self.downloader.download_finished.connect(self._on_download_finished)
        
        self.results_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _on_search(self):
        """搜索按钮点击"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        if not self.downloader.is_playwright_available():
            QMessageBox.warning(self, "提示", "请先安装 Playwright:\npip install playwright\nplaywright install chromium")
            return
        
        self.current_query = query
        self.current_page = 1
        
        self.search_btn.setEnabled(False)
        self.search_btn.setText("搜索中...")
        self.results_list.clear()
        self.results_list.addItem("正在搜索...")
        self.progress_label.setText(f"正在搜索: {query}...")
        
        self.downloader.search(query, 1)
    
    def _on_search_finished(self, songs: List[SearchResult], query: str, total_pages: int):
        """搜索完成"""
        self.search_results = songs
        self.total_pages = total_pages
        
        self.results_list.clear()
        
        if not songs:
            self.results_list.addItem("未找到歌曲")
            self.results_label.setText("搜索结果")
        else:
            for song in songs:
                display_text = f"♪ {song.title}"
                if song.artist:
                    display_text += f" - {song.artist}"
                if song.album:
                    display_text += f" ({song.album})"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, song)
                self.results_list.addItem(item)
            
            self.results_label.setText(f"搜索结果 (共 {len(songs)} 首)")
        
        self._update_page_buttons()
        self.search_btn.setEnabled(True)
        self.search_btn.setText("搜索")
        self.progress_label.setText(f"找到 {len(songs)} 首歌曲")
    
    def _on_search_error(self, error: str):
        """搜索错误"""
        self.results_list.clear()
        self.results_list.addItem(f"搜索失败: {error}")
        
        self.search_btn.setEnabled(True)
        self.search_btn.setText("搜索")
        self.progress_label.setText(f"搜索失败: {error}")
    
    def _update_page_buttons(self):
        """更新分页按钮状态"""
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        self.page_label.setText(f"第 {self.current_page}/{self.total_pages} 页")
    
    def _on_prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.search_btn.setEnabled(False)
            self.results_list.clear()
            self.results_list.addItem("加载中...")
            
            self.downloader.search(self.current_query, self.current_page)
    
    def _on_next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.search_btn.setEnabled(False)
            self.results_list.clear()
            self.results_list.addItem("加载中...")
            
            self.downloader.search(self.current_query, self.current_page)
    
    def _on_selection_changed(self):
        """选择改变"""
        has_selection = len(self.results_list.selectedItems()) > 0
        self.download_btn.setEnabled(has_selection and not self.downloader.is_downloading())
    
    def _on_result_double_click(self, item: QListWidgetItem):
        """双击搜索结果"""
        song = item.data(Qt.ItemDataRole.UserRole)
        if song:
            self._download_song(song)
    
    def _on_download_selected(self):
        """下载选中项"""
        items = self.results_list.selectedItems()
        if not items:
            return
        
        song = items[0].data(Qt.ItemDataRole.UserRole)
        if song:
            self._download_song(song)
    
    def _download_song(self, song: SearchResult):
        """下载歌曲"""
        if self.downloader.is_downloading():
            QMessageBox.information(self, "提示", "正在下载中，请等待完成")
            return
        
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"准备下载: {song.title}...")
        
        self.downloader.download(song)
    
    def _on_download_progress(self, message: str):
        """下载进度"""
        self.progress_label.setText(message)
    
    def _on_download_finished(self, result: DownloadResult):
        """下载完成"""
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        
        if result.success:
            self.progress_label.setText(f"✓ 下载成功: {result.filename}")
            
            # 显示成功消息
            msg = f"下载完成!\n\n文件: {result.filename}\n大小: {result.file_size / 1024 / 1024:.2f} MB"
            if result.lyrics_file:
                msg += f"\n歌词: {result.lyrics_file}"
            
            QMessageBox.information(self, "下载成功", msg)
            
            # 发送下载完成信号
            self.download_completed.emit(result.filepath, result.filename)
        else:
            self.progress_label.setText(f"✗ 下载失败: {result.error}")
            QMessageBox.warning(self, "下载失败", result.error)
    
    def _on_change_dir(self):
        """更改下载目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择下载目录",
            self.downloader.get_download_dir()
        )
        
        if dir_path:
            self.downloader.set_download_dir(dir_path)
            self.dir_label.setText(f"下载目录: {dir_path}")