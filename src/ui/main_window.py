"""
主窗口模块（带歌词显示和主题切换）
音乐播放器的主要用户界面
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QLabel, QPushButton,
    QSlider, QMenu, QToolBar, QStatusBar, QMenuBar,
    QFileDialog, QMessageBox, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QProgressBar, QFrame
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.doubleClicked.connect(self._on_double_click)
    
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
        
        for btn in [self.previous_btn, self.play_btn, self.pause_btn, self.stop_btn, self.next_btn]:
            btn.setFixedSize(40, 40)
            button_layout.addWidget(btn)
        
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
    
    def _on_album_clicked(self, item, column):
        album = item.text(0)
        tracks = self.library.get_tracks_by_album(album)
        self.all_tracks_list.clear_tracks()
        for track in tracks:
            self.all_tracks_list.add_track(track)


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
        
        # 音乐库信号
        self.library_widget.all_tracks_list.track_double_clicked.connect(self._play_track_from_library)
        
        # 播放列表信号
        self.playlist_widget.playlist_tracks.track_double_clicked.connect(self._play_track_from_playlist)
        
        # 在线搜索信号
        self.online_search_widget.download_completed.connect(self._on_download_completed)
        
        # 主题改变信号
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
    
    def _on_download_completed(self, filepath: str, filename: str):
        """下载完成处理"""
        # 刷新音乐库
        self.library_widget.refresh_library()
        
        # 尝试加载并播放下载的歌曲
        track = AudioTrack(
            file_path=filepath,
            title=Path(filepath).stem
        )
        self.player.load_track(track)
        self.player.play()
        self._update_current_track_display(track)
        
        # 尝试加载歌词
        self.lyrics_widget.set_audio_file(filepath)
        self.lyrics_widget._auto_find_lyrics()
        
        self.status_label.setText(f"已下载并播放: {filename}")
    
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
                
                # 尝试自动加载歌词
                self.lyrics_widget.set_audio_file(file_paths[0])
                self.lyrics_widget._auto_find_lyrics()
    
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
            self.library_widget.refresh_library()
            
            stats = self.library.get_library_stats()
            self.library_info_label.setText(f"音乐库: {stats.total_tracks} 首歌曲")
            self.status_label.setText("扫描完成")
            
        except Exception as e:
            self.status_label.setText(f"扫描失败: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def _play_track_from_library(self, index: int):
        """从音乐库播放曲目"""
        item = self.library_widget.all_tracks_list.item(index)
        if item:
            track = item.data(Qt.ItemDataRole.UserRole)
            if track:
                self.player.load_track(track)
                self.player.play()
                self._update_current_track_display(track)
                
                # 尝试加载歌词
                self.lyrics_widget.set_audio_file(track.file_path)
                self.lyrics_widget._auto_find_lyrics()
    
    def _play_track_from_playlist(self, index: int):
        """从播放列表播放曲目"""
        item = self.playlist_widget.playlist_tracks.item(index)
        if item:
            track = item.data(Qt.ItemDataRole.UserRole)
            if track:
                self.player.load_track(track)
                self.player.play()
                self._update_current_track_display(track)
                
                # 尝试加载歌词
                self.lyrics_widget.set_audio_file(track.file_path)
                self.lyrics_widget._auto_find_lyrics()
    
    def _update_current_track_display(self, track: AudioTrack):
        """更新当前曲目显示"""
        self.current_track_label.setText(track.title or "未知标题")
        self.current_artist_label.setText(track.artist or "未知艺术家")
        self.current_album_label.setText(track.album or "未知专辑")
    
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
        """曲目改变处理"""
        self.setWindowTitle(f"专业音乐播放器 - {track_name}")
    
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