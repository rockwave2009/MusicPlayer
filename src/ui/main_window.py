"""
主窗口模块（带歌词显示和主题切换）
音乐播放器的主要用户界面
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QLabel, QPushButton,
    QSlider, QMenu, QToolBar, QStatusBar, QMenuBar,
    QFileDialog, QMessageBox, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QProgressBar, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence

from pathlib import Path
from typing import List

from core.player import AudioPlayer, AudioTrack, RepeatMode
from core.library import MusicLibrary
from core.playlist import PlaylistManager
from core.theme import ThemeManager, Theme
from ui.widgets.lyrics_widget import LyricsDisplayWidget
from ui.widgets.online_search_widget import OnlineSearchWidget


class TrackListWidget(QListWidget):
    """曲目列表组件"""
    
    track_double_clicked = pyqtSignal(int)
    track_right_clicked = pyqtSignal(object, object)  # track, global_position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.doubleClicked.connect(self._on_double_click)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
    
    def _on_context_menu(self, position):
        """右键菜单"""
        item = self.itemAt(position)
        if item:
            track = item.data(Qt.ItemDataRole.UserRole)
            if track:
                self.track_right_clicked.emit(track, self.mapToGlobal(position))
    
    def _on_double_click(self, index):
        if index.isValid():
            self.track_double_clicked.emit(index.row())
    
    def add_track(self, track: AudioTrack):
        item = QListWidgetItem()
        display_text = f"{track.title} - {track.artist}"
        if track.album:
            display_text += f" ({track.album})"
        item.setText(display_text)
        item.setData(Qt.ItemDataRole.UserRole, track)
        self.addItem(item)
    
    def clear_tracks(self):
        self.clear()


class PlaybackControlWidget(QWidget):
    """播放控制组件"""
    
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    previous_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    volume_changed = pyqtSignal(int)
    position_changed = pyqtSignal(float)
    favorite_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 播放控制按钮
        button_layout = QHBoxLayout()
        
        self.previous_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.pause_btn = QPushButton("⏸")
        self.stop_btn = QPushButton("⏹")
        self.next_btn = QPushButton("⏭")
        self.favorite_btn = QPushButton("♥")
        self.favorite_btn.setFixedSize(40, 40)
        self.favorite_btn.setStyleSheet("QPushButton { color: #999; } QPushButton:checked { color: #FF6B6B; }")
        self.favorite_btn.setCheckable(True)
        
        for btn in [self.previous_btn, self.play_btn, self.pause_btn, self.stop_btn, self.next_btn]:
            btn.setFixedSize(40, 40)
            button_layout.addWidget(btn)
        
        button_layout.addSpacing(20)
        button_layout.addWidget(self.favorite_btn)
        
        layout.addLayout(button_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.total_time_label = QLabel("00:00")
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)
        
        layout.addLayout(progress_layout)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        volume_label = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_label = QLabel("80%")
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        layout.addLayout(volume_layout)
    
    def _connect_signals(self):
        self.play_btn.clicked.connect(self.play_clicked)
        self.pause_btn.clicked.connect(self.pause_clicked)
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.previous_btn.clicked.connect(self.previous_clicked)
        self.next_btn.clicked.connect(self.next_clicked)
        self.favorite_btn.clicked.connect(self.favorite_clicked)
        
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.progress_slider.sliderMoved.connect(self._on_position_changed)
    
    def _on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")
        self.volume_changed.emit(value)
    
    def _on_position_changed(self, value):
        self.position_changed.emit(float(value))
    
    def update_position(self, current: float, total: float):
        if total > 0:
            self.progress_slider.setMaximum(int(total))
            self.progress_slider.setValue(int(current))
            self.current_time_label.setText(self._format_time(current))
            self.total_time_label.setText(self._format_time(total))
    
    def _format_time(self, seconds: float) -> str:
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def set_playing_state(self, is_playing: bool):
        self.play_btn.setEnabled(not is_playing)
        self.pause_btn.setEnabled(is_playing)


class LibraryWidget(QWidget):
    """音乐库组件"""
    
    def __init__(self, library: MusicLibrary, parent=None):
        super().__init__(parent)
        self.library = library
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 搜索框
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索歌曲、歌手、专辑...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_input)
        
        self.clear_search_btn = QPushButton("清空")
        self.clear_search_btn.setFixedWidth(50)
        self.clear_search_btn.clicked.connect(lambda: self.search_input.clear())
        search_layout.addWidget(self.clear_search_btn)
        
        layout.addLayout(search_layout)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 刷新音乐库")
        self.refresh_btn.clicked.connect(self._on_refresh)
        btn_layout.addWidget(self.refresh_btn)
        
        self.cleanup_btn = QPushButton("🧹 清理无效文件")
        self.cleanup_btn.clicked.connect(self._on_cleanup)
        btn_layout.addWidget(self.cleanup_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 分类标签
        self.tab_widget = QTabWidget()
        
        # 所有曲目
        self.all_tracks_list = TrackListWidget()
        self.tab_widget.addTab(self.all_tracks_list, "所有曲目")
        
        # 艺术家
        self.artists_tree = QTreeWidget()
        self.artists_tree.setHeaderLabels(["艺术家"])
        self.artists_tree.itemClicked.connect(self._on_artist_clicked)
        self.tab_widget.addTab(self.artists_tree, "艺术家")
        
        # 专辑
        self.albums_tree = QTreeWidget()
        self.albums_tree.setHeaderLabels(["专辑"])
        self.albums_tree.itemClicked.connect(self._on_album_clicked)
        self.tab_widget.addTab(self.albums_tree, "专辑")
        
        layout.addWidget(self.tab_widget)
        
        # 统计信息
        self.stats_label = QLabel("音乐库统计: 0 首歌曲")
        layout.addWidget(self.stats_label)
    
    def _on_refresh(self):
        """刷新按钮点击"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "提示", "音乐库已刷新，无效文件已清理")
        self.refresh_library()
    
    def _on_cleanup(self):
        """清理按钮点击"""
        from PyQt6.QtWidgets import QMessageBox
        removed = self.library.refresh_library()
        self.refresh_library()
        QMessageBox.information(self, "清理完成", f"已清理 {removed} 个不存在的文件")
    
    def _on_search_text_changed(self, text: str):
        """搜索框文本变化时实时过滤"""
        query = text.strip()
        self.all_tracks_list.clear_tracks()
        
        if not query:
            # 空搜索显示全部
            tracks = self.library.get_all_tracks()
        else:
            # 模糊搜索
            tracks = self.library.search_tracks(query)
        
        for track in tracks:
            self.all_tracks_list.add_track(track)
        
        # 切换到所有曲目tab
        self.tab_widget.setCurrentIndex(0)
    
    def refresh_library(self):
        try:
            self.all_tracks_list.clear_tracks()
            tracks = self.library.get_all_tracks()
            for track in tracks:
                self.all_tracks_list.add_track(track)
            
            # 刷新艺术家
            self.artists_tree.clear()
            for artist in self.library.get_all_artists():
                self.artists_tree.addTopLevelItem(QTreeWidgetItem([artist]))
            
            # 刷新专辑
            self.albums_tree.clear()
            for album in self.library.get_all_albums():
                self.albums_tree.addTopLevelItem(QTreeWidgetItem([album]))
            
            # 更新统计信息
            stats = self.library.get_library_stats()
            self.stats_label.setText(f"音乐库统计: {stats.total_tracks} 首歌曲")
            
        except Exception as e:
            print(f"刷新音乐库失败: {e}")
    
    def _on_artist_clicked(self, item, column):
        artist = item.text(0)
        tracks = self.library.get_tracks_by_artist(artist)
        self.all_tracks_list.clear_tracks()
        for track in tracks:
            self.all_tracks_list.add_track(track)
        # 切换到"全部歌曲"tab 让用户看到结果
        self.tab_widget.setCurrentIndex(0)
    
    def _on_album_clicked(self, item, column):
        album = item.text(0)
        tracks = self.library.get_tracks_by_album(album)
        self.all_tracks_list.clear_tracks()
        for track in tracks:
            self.all_tracks_list.add_track(track)
        # 切换到"全部歌曲"tab 让用户看到结果
        self.tab_widget.setCurrentIndex(0)


class PlaylistWidget(QWidget):
    """播放列表组件"""
    
    def __init__(self, playlist_manager: PlaylistManager, parent=None):
        super().__init__(parent)
        self.playlist_manager = playlist_manager
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 播放列表操作按钮
        button_layout = QHBoxLayout()
        self.create_btn = QPushButton("新建播放列表")
        self.delete_btn = QPushButton("删除播放列表")
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.delete_btn)
        layout.addLayout(button_layout)
        
        # 播放列表分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 播放列表树
        self.playlists_tree = QTreeWidget()
        self.playlists_tree.setHeaderLabels(["播放列表"])
        self.playlists_tree.itemClicked.connect(self._on_playlist_clicked)
        splitter.addWidget(self.playlists_tree)
        
        # 播放列表曲目
        self.playlist_tracks = TrackListWidget()
        splitter.addWidget(self.playlist_tracks)
        
        splitter.setSizes([200, 400])
        layout.addWidget(splitter)
        
        self.create_btn.clicked.connect(self._create_playlist)
        self.delete_btn.clicked.connect(self._delete_playlist)
    
    def refresh_playlists(self):
        self.playlists_tree.clear()
        for playlist in self.playlist_manager.get_all_playlists():
            item = QTreeWidgetItem([playlist.name])
            item.setData(0, Qt.ItemDataRole.UserRole, playlist.id)
            self.playlists_tree.addTopLevelItem(item)
    
    def _on_playlist_clicked(self, item, column):
        playlist_id = item.data(0, Qt.ItemDataRole.UserRole)
        if playlist_id:
            self.playlist_tracks.clear_tracks()
            for track in self.playlist_manager.get_playlist_tracks(playlist_id):
                self.playlist_tracks.add_track(track)
    
    def _create_playlist(self):
        self.playlist_manager.create_playlist("新播放列表")
        self.refresh_playlists()
    
    def _delete_playlist(self):
        current_item = self.playlists_tree.currentItem()
        if current_item:
            playlist_id = current_item.data(0, Qt.ItemDataRole.UserRole)
            if playlist_id:
                self.playlist_manager.delete_playlist(playlist_id)
                self.refresh_playlists()


class MainWindow(QMainWindow):
    """
    主窗口类
    音乐播放器的主要用户界面（带歌词显示和主题切换）
    """
    
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        
        # 保存主题管理器引用
        self.theme_manager = theme_manager
        
        # 初始化核心组件
        self.player = AudioPlayer()
        self.library = MusicLibrary()
        self.playlist_manager = PlaylistManager()
        
        # 初始化UI
        self._init_ui()
        self._connect_signals()
        
        # 设置窗口属性
        self.setWindowTitle("专业音乐播放器")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)
        
        # 启动时自动刷新音乐库
        self._refresh_library_display()
    
    def _refresh_library_display(self):
        """刷新音乐库显示并更新状态栏计数"""
        self.library_widget.refresh_library()
        stats = self.library.get_library_stats()
        self.library_info_label.setText(f"音乐库: {stats.total_tracks} 首歌曲")
    
    def _init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 创建工具栏
        self._create_tool_bar()
        
        # 创建主内容区域
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板 - 音乐库、播放列表和在线搜索
        left_panel = QTabWidget()
        self.library_widget = LibraryWidget(self.library)
        self.playlist_widget = PlaylistWidget(self.playlist_manager)
        self.online_search_widget = OnlineSearchWidget()
        left_panel.addTab(self.library_widget, "音乐库")
        left_panel.addTab(self.playlist_widget, "播放列表")
        left_panel.addTab(self.online_search_widget, "在线搜索")
        content_splitter.addWidget(left_panel)
        
        # 右侧面板 - 播放控制和歌词
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分 - 播放控制
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # 当前播放信息
        current_track_frame = QFrame()
        current_track_frame.setFrameShape(QFrame.Shape.StyledPanel)
        current_track_layout = QVBoxLayout(current_track_frame)
        
        self.current_track_label = QLabel("未播放")
        self.current_track_label.setProperty("role", "title")
        self.current_track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.current_artist_label = QLabel("")
        self.current_artist_label.setProperty("role", "subtitle")
        self.current_artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.current_album_label = QLabel("")
        self.current_album_label.setProperty("role", "hint")
        self.current_album_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        current_track_layout.addWidget(self.current_track_label)
        current_track_layout.addWidget(self.current_artist_label)
        current_track_layout.addWidget(self.current_album_label)
        
        control_layout.addWidget(current_track_frame)
        
        # 播放控制
        self.playback_control = PlaybackControlWidget()
        control_layout.addWidget(self.playback_control)
        
        # 当前播放列表
        self.current_playlist_label = QLabel("当前播放列表")
        self.current_playlist_label.setProperty("role", "subtitle")
        control_layout.addWidget(self.current_playlist_label)
        
        self.current_playlist_tracks = TrackListWidget()
        control_layout.addWidget(self.current_playlist_tracks)
        
        right_splitter.addWidget(control_widget)
        
        # 下半部分 - 歌词显示
        self.lyrics_widget = LyricsDisplayWidget()
        right_splitter.addWidget(self.lyrics_widget)
        
        right_splitter.setSizes([300, 400])
        
        content_splitter.addWidget(right_splitter)
        content_splitter.setSizes([400, 600])
        
        main_layout.addWidget(content_splitter)
        
        # 创建状态栏
        self._create_status_bar()
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开音乐文件", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._open_music_files)
        file_menu.addAction(open_action)
        
        open_folder_action = QAction("打开音乐文件夹", self)
        open_folder_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_folder_action.triggered.connect(self._open_music_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        load_lyrics_action = QAction("加载歌词文件", self)
        load_lyrics_action.setShortcut(QKeySequence("Ctrl+L"))
        load_lyrics_action.triggered.connect(self._load_lyrics_file)
        file_menu.addAction(load_lyrics_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 播放菜单
        play_menu = menubar.addMenu("播放")
        
        play_action = QAction("播放", self)
        play_action.setShortcut(QKeySequence("Space"))
        play_action.triggered.connect(self.player.play)
        play_menu.addAction(play_action)
        
        pause_action = QAction("暂停", self)
        pause_action.triggered.connect(self.player.pause)
        play_menu.addAction(pause_action)
        
        stop_action = QAction("停止", self)
        stop_action.setShortcut(QKeySequence("Ctrl+S"))
        stop_action.triggered.connect(self.player.stop)
        play_menu.addAction(stop_action)
        
        play_menu.addSeparator()
        
        next_action = QAction("下一曲", self)
        next_action.setShortcut(QKeySequence("Ctrl+Right"))
        next_action.triggered.connect(self.player.next_track)
        play_menu.addAction(next_action)
        
        previous_action = QAction("上一曲", self)
        previous_action.setShortcut(QKeySequence("Ctrl+Left"))
        previous_action.triggered.connect(self.player.previous_track)
        play_menu.addAction(previous_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        self.dark_mode_action = QAction("深色模式", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(self.theme_manager.is_dark())
        self.dark_mode_action.setShortcut(QKeySequence("Ctrl+D"))
        self.dark_mode_action.triggered.connect(self._toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_tool_bar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        open_btn = QPushButton("打开")
        open_btn.clicked.connect(self._open_music_files)
        toolbar.addWidget(open_btn)
        
        scan_btn = QPushButton("扫描音乐库")
        scan_btn.clicked.connect(self._scan_music_library)
        toolbar.addWidget(scan_btn)
        
        toolbar.addSeparator()
        
        self.shuffle_btn = QPushButton("🔀 随机")
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.clicked.connect(self._toggle_shuffle)
        toolbar.addWidget(self.shuffle_btn)
        
        self.repeat_btn = QPushButton("🔁 重复")
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.clicked.connect(self._toggle_repeat)
        toolbar.addWidget(self.repeat_btn)
        
        toolbar.addSeparator()
        
        # 主题切换按钮
        self.theme_btn = QPushButton("🌙 深色" if not self.theme_manager.is_dark() else "☀️ 浅色")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.theme_btn)
    
    def _create_status_bar(self):
        """创建状态栏"""
        statusbar = self.statusBar()
        
        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        statusbar.addPermanentWidget(self.progress_bar)
        
        self.library_info_label = QLabel("音乐库: 0 首歌曲")
        statusbar.addPermanentWidget(self.library_info_label)
    
    def _connect_signals(self):
        """连接信号"""
        # 播放器信号
        self.player.state_changed.connect(self._on_player_state_changed)
        self.player.position_changed.connect(self._on_position_changed)
        self.player.track_changed.connect(self._on_track_changed)
        self.player.error_occurred.connect(self._on_error_occurred)
        
        # 播放控制信号
        self.playback_control.play_clicked.connect(self.player.play)
        self.playback_control.pause_clicked.connect(self.player.pause)
        self.playback_control.stop_clicked.connect(self.player.stop)
        self.playback_control.previous_clicked.connect(self.player.previous_track)
        self.playback_control.next_clicked.connect(self.player.next_track)
        self.playback_control.volume_changed.connect(self.player.set_volume)
        self.playback_control.position_changed.connect(self.player.seek)
        self.playback_control.favorite_clicked.connect(self._toggle_favorite_current_track)
        
        # 音乐库信号
        self.library_widget.all_tracks_list.track_double_clicked.connect(self._play_track_from_library)
        self.library_widget.all_tracks_list.track_right_clicked.connect(self._show_track_context_menu)
        
        # 播放列表信号
        self.playlist_widget.playlist_tracks.track_double_clicked.connect(self._play_track_from_playlist)
        self.playlist_widget.playlist_tracks.track_right_clicked.connect(self._show_playlist_track_context_menu)
        
        # 当前播放列表信号
        self.current_playlist_tracks.track_double_clicked.connect(self._play_track_from_current_playlist)
        
        # 在线搜索信号
        self.online_search_widget.download_completed.connect(self._on_download_completed)
        
        # 歌词信号
        self.lyrics_widget.line_clicked.connect(self._on_lyric_clicked)
        self.lyrics_widget.download_lyrics_requested.connect(self._on_download_lyrics_requested)
        
        # 主题改变信号
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_download_completed(self, filepath: str, filename: str):
        """下载完成处理"""
        # 将新下载的歌曲加入音乐库数据库
        try:
            self.library._process_music_file(filepath)
        except Exception as e:
            print(f"加入音乐库失败: {e}")
        
        # 刷新音乐库显示
        self.library_widget.refresh_library()
        
        # 获取完整曲目信息（从数据库读取，包含元数据）
        tracks = self.library.search_tracks(Path(filepath).stem)
        if tracks:
            track = tracks[0]
        else:
            track = AudioTrack(
                file_path=filepath,
                title=Path(filepath).stem
            )
        
        # 把当前音乐库列表设为播放列表，从这首新歌开始播
        all_tracks = self.library.get_all_tracks()
        self.player.load_playlist(all_tracks)
        # 找到这首新歌的索引
        start_index = 0
        for i, t in enumerate(all_tracks):
            if t.file_path == filepath:
                start_index = i
                break
        self.player.play_track_at(start_index)
        self._update_current_playlist_display(all_tracks)
        
        self.status_label.setText(f"已下载并播放: {filename}")
    
    def _on_lyric_clicked(self, index: int):
        """点击歌词行跳转到对应播放位置"""
        lyrics_manager = self.lyrics_widget.lyrics_manager
        time_seconds = lyrics_manager.get_line_time(index)
        if time_seconds > 0:
            self.player.seek(time_seconds)
            self.status_label.setText(f"已跳转到: {int(time_seconds // 60):02d}:{int(time_seconds % 60):02d}")
    
    def _on_download_lyrics_requested(self, query: str, audio_path: str):
        """处理歌词下载请求 - 使用在线搜索下载"""
        # 设置搜索关键词并执行搜索
        self.online_search_widget.search_input.setText(query)
        self.online_search_widget._on_search()
        self.status_label.setText(f"正在搜索歌词: {query}...")
    
    def _open_music_files(self):
        """打开音乐文件"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("音乐文件 (*.mp3 *.m4a *.wav *.flac *.aiff)")
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            tracks = []
            
            for file_path in file_paths:
                track = AudioTrack(
                    file_path=file_path,
                    title=Path(file_path).stem
                )
                tracks.append(track)
            
            if tracks:
                self.player.load_playlist(tracks)
                self.player.play_track_at(0)
                self._update_current_playlist_display(tracks)
    
    def _open_music_folder(self):
        """打开音乐文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择音乐文件夹")
        if folder:
            self._scan_folder(folder)
    
    def _scan_music_library(self):
        """扫描音乐库"""
        folder = QFileDialog.getExistingDirectory(self, "选择要扫描的音乐文件夹")
        if folder:
            self._scan_folder(folder)
    
    def _scan_folder(self, folder: str):
        """扫描文件夹"""
        self.status_label.setText(f"正在扫描: {folder}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        def progress_callback(current, total):
            progress = int((current / total) * 100) if total > 0 else 0
            self.progress_bar.setValue(progress)
            self.status_label.setText(f"扫描进度: {current}/{total}")
        
        try:
            self.library.scan_directory(folder, recursive=True, callback=progress_callback)
            self._refresh_library_display()
            self.status_label.setText("扫描完成")
            
        except Exception as e:
            self.status_label.setText(f"扫描失败: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def _play_track_from_library(self, index: int):
        """从音乐库播放曲目 - 将当前列表设为播放列表以支持自动下一首"""
        # 获取当前列表中的所有歌曲作为播放列表
        tracks = []
        for i in range(self.library_widget.all_tracks_list.count()):
            item = self.library_widget.all_tracks_list.item(i)
            if item:
                t = item.data(Qt.ItemDataRole.UserRole)
                if t:
                    tracks.append(t)
        
        if not tracks or index >= len(tracks):
            return
        
        self.player.load_playlist(tracks)
        self.player.play_track_at(index)
        self._update_current_playlist_display(tracks)
    
    def _play_track_from_playlist(self, index: int):
        """从播放列表播放曲目 - 将当前播放列表完整加载"""
        # 获取当前播放列表中的所有歌曲
        tracks = []
        for i in range(self.playlist_widget.playlist_tracks.count()):
            item = self.playlist_widget.playlist_tracks.item(i)
            if item:
                t = item.data(Qt.ItemDataRole.UserRole)
                if t:
                    tracks.append(t)
        
        if not tracks or index >= len(tracks):
            return
        
        self.player.load_playlist(tracks)
        self.player.play_track_at(index)
        self._update_current_playlist_display(tracks)
    
    def _play_track_from_current_playlist(self, index: int):
        """双击当前播放列表切歌"""
        self.player.play_track_at(index)
    
    def _show_track_context_menu(self, track, global_pos):
        """显示曲目右键菜单"""
        menu = QMenu(self)
        
        # 播放
        play_action = QAction("▶ 播放", self)
        play_action.triggered.connect(lambda: self._play_track_from_library(track))
        menu.addAction(play_action)
        
        menu.addSeparator()
        
        # 添加到播放列表子菜单
        add_to_menu = QMenu("添加到播放列表", self)
        playlists = self.playlist_manager.get_all_playlists()
        if playlists:
            for playlist in playlists:
                action = QAction(f"{playlist.name} ({playlist.track_count}首)", self)
                action.triggered.connect(
                    lambda checked, pid=playlist.id, fp=track.file_path: 
                    self._add_track_to_playlist(pid, fp)
                )
                add_to_menu.addAction(action)
        else:
            no_pl_action = QAction("(无播放列表)", self)
            no_pl_action.setEnabled(False)
            add_to_menu.addAction(no_pl_action)
        menu.addMenu(add_to_menu)
        
        # 收藏
        is_fav = self.playlist_manager.is_favorite(track.file_path)
        fav_action = QAction("♥ 取消收藏" if is_fav else "♥ 收藏", self)
        fav_action.triggered.connect(
            lambda: self._toggle_favorite(track.file_path, not is_fav)
        )
        menu.addAction(fav_action)
        
        menu.addSeparator()
        
        # 删除歌曲
        delete_action = QAction("🗑 删除歌曲文件", self)
        delete_action.triggered.connect(lambda: self._delete_track(track))
        menu.addAction(delete_action)
        
        menu.exec(global_pos)
    
    def _delete_track(self, track):
        """删除歌曲文件及相关文件"""
        from pathlib import Path
        import os
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除以下文件吗？\n\n{track.title} - {track.artist}\n\n"
            f"路径: {track.file_path}\n\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleted = []
                failed = []
                
                # 删除音频文件
                audio_path = Path(track.file_path)
                if audio_path.exists():
                    try:
                        audio_path.unlink()
                        deleted.append(audio_path.name)
                    except Exception as e:
                        failed.append(f"{audio_path.name}: {e}")
                
                # 删除同目录下的歌词文件
                lrc_path = audio_path.with_suffix('.lrc')
                if lrc_path.exists():
                    try:
                        lrc_path.unlink()
                        deleted.append(lrc_path.name)
                    except Exception as e:
                        failed.append(f"{lrc_path.name}: {e}")
                
                # 从音乐库中移除
                self.library.remove_track(track.file_path)
                
                # 从播放列表中移除（所有播放列表）
                for playlist in self.playlist_manager.get_all_playlists():
                    self.playlist_manager.remove_track_by_file_path(playlist.id, track.file_path)
                
                # 如果当前正在播放这首歌，停止播放
                if self.player.current_track and self.player.current_track.file_path == track.file_path:
                    self.player.stop()
                
                # 刷新音乐库显示
                self.library_widget.refresh_library()
                
                if deleted:
                    msg = f"已删除 {len(deleted)} 个文件:\n" + "\n".join(deleted)
                    if failed:
                        msg += f"\n\n删除失败:\n" + "\n".join(failed)
                    self.status_label.setText(f"已删除: {track.title}")
                else:
                    msg = "文件不存在或已被删除"
                
                QMessageBox.information(self, "删除结果", msg)
                
            except Exception as e:
                QMessageBox.warning(self, "删除失败", f"删除时发生错误:\n{str(e)}")
    
    def _show_playlist_track_context_menu(self, track, global_pos):
        """显示播放列表内曲目右键菜单"""
        menu = QMenu(self)
        
        # 从播放列表移除
        current_item = self.playlist_widget.playlists_tree.currentItem()
        if current_item:
            playlist_id = current_item.data(0, Qt.ItemDataRole.UserRole)
            remove_action = QAction("从播放列表移除", self)
            remove_action.triggered.connect(
                lambda: self._remove_track_from_playlist(playlist_id, track.file_path)
            )
            menu.addAction(remove_action)
        
        menu.addSeparator()
        
        # 收藏
        is_fav = self.playlist_manager.is_favorite(track.file_path)
        fav_action = QAction("♥ 取消收藏" if is_fav else "♥ 收藏", self)
        fav_action.triggered.connect(
            lambda: self._toggle_favorite(track.file_path, not is_fav)
        )
        menu.addAction(fav_action)
        
        menu.exec(global_pos)
    
    def _add_track_to_playlist(self, playlist_id, file_path):
        """添加曲目到播放列表"""
        if self.playlist_manager.add_track_by_file_path(playlist_id, file_path):
            self.status_label.setText("已添加到播放列表")
            self.playlist_widget.refresh_playlists()
        else:
            QMessageBox.warning(self, "添加失败", "歌曲不在音乐库中，请先扫描音乐库")
    
    def _remove_track_from_playlist(self, playlist_id, file_path):
        """从播放列表移除曲目"""
        if self.playlist_manager.remove_track_by_file_path(playlist_id, file_path):
            self.status_label.setText("已从播放列表移除")
            # 刷新当前播放列表曲目显示
            current_item = self.playlist_widget.playlists_tree.currentItem()
            if current_item:
                self.playlist_widget._on_playlist_clicked(current_item, 0)
            self.playlist_widget.refresh_playlists()
        else:
            self.status_label.setText("移除失败")
    
    def _toggle_favorite(self, file_path, add=True):
        """切换曲目收藏状态"""
        if add:
            if self.playlist_manager.add_to_favorites_by_path(file_path):
                self.status_label.setText("已收藏")
            else:
                self.status_label.setText("收藏失败")
        else:
            if self.playlist_manager.remove_from_favorites_by_path(file_path):
                self.status_label.setText("已取消收藏")
            else:
                self.status_label.setText("取消收藏失败")
        
        # 更新播放控制区的收藏按钮状态
        self._update_favorite_button()
    
    def _toggle_favorite_current_track(self):
        """切换当前播放曲目的收藏状态"""
        if self.player.current_track:
            file_path = self.player.current_track.file_path
            is_fav = self.playlist_manager.is_favorite(file_path)
            self._toggle_favorite(file_path, not is_fav)
    
    def _update_favorite_button(self):
        """更新收藏按钮状态"""
        if self.player.current_track:
            is_fav = self.playlist_manager.is_favorite(self.player.current_track.file_path)
            self.playback_control.favorite_btn.setChecked(is_fav)
        else:
            self.playback_control.favorite_btn.setChecked(False)
    
    def _update_current_track_display(self, track: AudioTrack):
        """更新当前曲目显示"""
        self.current_track_label.setText(track.title or "未知标题")
        self.current_artist_label.setText(track.artist or "未知艺术家")
        self.current_album_label.setText(track.album or "未知专辑")
        self._update_favorite_button()
    
    def _update_current_playlist_display(self, tracks: List[AudioTrack]):
        """更新当前播放列表显示"""
        self.current_playlist_tracks.clear_tracks()
        for track in tracks:
            self.current_playlist_tracks.add_track(track)
    
    def _on_player_state_changed(self, state: str):
        """播放器状态改变处理"""
        self.playback_control.set_playing_state(state == "playing")
        
        if state == "playing":
            self.status_label.setText("正在播放")
        elif state == "paused":
            self.status_label.setText("已暂停")
        elif state == "stopped":
            self.status_label.setText("已停止")
    
    def _on_position_changed(self, position: float):
        """播放位置改变处理"""
        duration = self.player.get_duration()
        self.playback_control.update_position(position, duration)
        
        # 同步歌词
        self.lyrics_widget.update_position(position)
    
    def _on_track_changed(self, track_name: str):
        """曲目改变处理 - 统一更新UI和加载歌词"""
        self.setWindowTitle(f"专业音乐播放器 - {track_name}")
        
        if self.player.current_track:
            # 更新歌曲信息显示（标题、艺术家、专辑）
            self._update_current_track_display(self.player.current_track)
            # 自动加载新歌曲的歌词
            self.lyrics_widget.set_audio_file(self.player.current_track.file_path)
            self.lyrics_widget._auto_find_lyrics()
            
            # 高亮当前播放列表中正在播放的歌曲
            if 0 <= self.player.current_index < self.current_playlist_tracks.count():
                self.current_playlist_tracks.setCurrentRow(self.player.current_index)
                item = self.current_playlist_tracks.item(self.player.current_index)
                if item:
                    self.current_playlist_tracks.scrollToItem(item)
            
            # 高亮音乐库"所有曲目"列表中对应的歌曲（通过文件路径匹配）
            current_path = self.player.current_track.file_path
            all_tracks_list = self.library_widget.all_tracks_list
            for i in range(all_tracks_list.count()):
                item = all_tracks_list.item(i)
                if item:
                    track = item.data(Qt.ItemDataRole.UserRole)
                    if track and track.file_path == current_path:
                        all_tracks_list.setCurrentRow(i)
                        all_tracks_list.scrollToItem(item)
                        break
    
    def _on_error_occurred(self, error_message: str):
        """错误处理"""
        QMessageBox.warning(self, "错误", error_message)
        self.status_label.setText(f"错误: {error_message}")
    
    def _toggle_shuffle(self):
        """切换随机播放模式"""
        is_shuffled = self.shuffle_btn.isChecked()
        self.player.set_shuffle_mode(is_shuffled)
        self.shuffle_btn.setText("🔀 随机✓" if is_shuffled else "🔀 随机")
    
    def _toggle_repeat(self):
        """切换重复播放模式"""
        is_repeated = self.repeat_btn.isChecked()
        if is_repeated:
            self.player.set_repeat_mode(RepeatMode.ALL)
            self.repeat_btn.setText("🔁 重复✓")
        else:
            self.player.set_repeat_mode(RepeatMode.NONE)
            self.repeat_btn.setText("🔁 重复")
    
    def _toggle_dark_mode(self):
        """切换深色模式（菜单触发）"""
        self.theme_manager.toggle_theme()
    
    def _toggle_theme(self):
        """切换主题（按钮触发）"""
        self.theme_manager.toggle_theme()
    
    def _on_theme_changed(self, theme_name: str):
        """主题改变处理"""
        from PyQt6.QtWidgets import QApplication
        
        is_dark = theme_name == "dark"
        
        # 更新菜单状态
        self.dark_mode_action.setChecked(is_dark)
        
        # 更新工具栏按钮
        self.theme_btn.setText("☀️ 浅色" if is_dark else "🌙 深色")
        
        # 应用主题样式
        app = QApplication.instance()
        if app:
            self.theme_manager.apply_theme(app)
        
        # 更新状态栏提示
        self.status_label.setText(f"已切换到{'深色' if is_dark else '浅色'}主题")
    
    def _load_lyrics_file(self):
        """加载歌词文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择歌词文件",
            "",
            "LRC歌词文件 (*.lrc);;所有文件 (*)"
        )
        
        if file_path:
            self.lyrics_widget.load_lyrics(file_path)
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于专业音乐播放器",
            "专业音乐播放器 v1.0.0\n\n"
            "一款功能强大的macOS音乐播放器\n"
            "支持多种音频格式，提供歌词同步显示\n\n"
            "功能特性:\n"
            "- 支持 MP3/M4A/WAV/FLAC 等格式\n"
            "- 音乐库管理和播放列表\n"
            "- LRC歌词同步显示\n"
            "- 10频段均衡器\n"
            "- 频谱分析和波形显示\n"
            "- 明/暗主题切换\n\n"
            "快捷键:\n"
            "Ctrl+O - 打开音乐文件\n"
            "Ctrl+L - 加载歌词文件\n"
            "Ctrl+D - 切换深色模式\n"
            "Space - 播放/暂停\n"
            "Ctrl+Left/Right - 上/下一曲"
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.player.cleanup()
        event.accept()