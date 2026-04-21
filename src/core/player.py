"""
音频播放器核心模块
使用 ffplay 或 afplay 作为音频引擎
"""

import subprocess
import signal
import os
import sys
import time
import shutil
from typing import Optional, List
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持PyInstaller打包"""
    if getattr(sys, 'frozen', False):
        # 运行在PyInstaller打包后的环境中
        base_path = sys._MEIPASS
    else:
        # 运行在开发环境中
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def get_ffplay_path():
    """获取ffplay的路径，优先使用打包的版本"""
    # 首先检查打包的ffmpeg目录
    bundled_ffplay = get_resource_path('resources/ffmpeg/ffplay')
    if sys.platform == 'win32':
        bundled_ffplay += '.exe'
    
    if os.path.exists(bundled_ffplay):
        return bundled_ffplay
    
    # 回退到系统PATH中的ffplay
    system_ffplay = shutil.which('ffplay')
    if system_ffplay:
        return system_ffplay
    
    # 回退到系统PATH中的afplay (macOS)
    if sys.platform == 'darwin':
        system_afplay = shutil.which('afplay')
        if system_afplay:
            return system_afplay
    
    return None


class PlayerState(Enum):
    """播放器状态枚举"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class RepeatMode(Enum):
    """重复模式枚举"""
    NONE = "none"
    ONE = "one"
    ALL = "all"


@dataclass
class AudioTrack:
    """音频轨道数据类"""
    file_path: str
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    track_number: int = 0
    year: int = 0
    genre: str = ""
    cover_art: Optional[bytes] = None


class AudioPlayer(QObject):
    """
    音频播放器核心类
    优先使用 ffplay 支持更多格式，回退到 afplay
    """
    
    # 信号定义
    state_changed = pyqtSignal(str)
    position_changed = pyqtSignal(float)
    duration_changed = pyqtSignal(float)
    volume_changed = pyqtSignal(int)
    track_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    track_ended = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 播放器状态
        self.state = PlayerState.STOPPED
        self.current_track: Optional[AudioTrack] = None
        self.playlist: List[AudioTrack] = []
        self.current_index = -1
        
        # 播放设置
        self._volume = 80  # 0-100
        self.repeat_mode = RepeatMode.NONE
        self.shuffle_mode = False
        
        # 播放进程
        self._process: Optional[subprocess.Popen] = None
        self._start_time = 0.0
        self._paused_position = 0.0
        
        # 检测可用的播放器
        self._player_type = self._detect_player()
        
        # 定时器用于更新位置和检测播放结束
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._check_playing)
        self.position_timer.setInterval(500)
    
    def _detect_player(self) -> str:
        """检测可用的音频播放器"""
        player_path = get_ffplay_path()
        if player_path:
            # 保存路径供后续使用
            self._player_path = player_path
            if 'ffplay' in player_path:
                return 'ffplay'
            else:
                return 'afplay'
        else:
            self._player_path = None
            return 'none'
    
    def _check_playing(self):
        """检查播放状态"""
        if self._process:
            # 检查进程是否还在运行
            if self._process.poll() is not None:
                # 进程已结束
                self._process = None
                self.position_timer.stop()
                self.state = PlayerState.STOPPED
                self.state_changed.emit(PlayerState.STOPPED.value)
                
                # 自动播放下一曲
                if self.current_track:
                    self._play_next()
            else:
                # 更新位置
                if self.state == PlayerState.PLAYING:
                    position = self._paused_position + (time.time() - self._start_time)
                    self.position_changed.emit(position)
    
    def load_track(self, track: AudioTrack) -> bool:
        """加载音频轨道"""
        try:
            file_path = Path(track.file_path)
            if not file_path.exists():
                self.error_occurred.emit(f"文件不存在: {track.file_path}")
                return False
            
            # 使用mutagen获取时长
            if track.duration <= 0:
                try:
                    from mutagen import File
                    audio = File(track.file_path, easy=True)
                    if audio and hasattr(audio, 'info'):
                        track.duration = audio.info.length
                except Exception:
                    track.duration = 0
            
            # 更新当前轨道
            self.current_track = track
            self._paused_position = 0.0
            self.track_changed.emit(track.title or file_path.name)
            self.duration_changed.emit(track.duration)
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"加载轨道失败: {str(e)}")
            return False
    
    def play(self) -> bool:
        """开始播放"""
        if not self.current_track:
            self.error_occurred.emit("没有加载曲目")
            return False
        
        if self._player_type == 'none' or not hasattr(self, '_player_path') or not self._player_path:
            self.error_occurred.emit("未找到可用的音频播放器（需要 ffplay 或 afplay）")
            return False
        
        try:
            # 停止当前播放
            if self._process:
                self._process.terminate()
                self._process.wait()
            
            # 根据播放器类型构建命令
            file_path = self.current_track.file_path
            
            if self._player_type == 'ffplay':
                # ffplay 支持更多格式包括 AAC
                cmd = [
                    self._player_path, '-nodisp', '-autoexit', 
                    '-loglevel', 'quiet',
                    '-volume', str(self._volume),
                    file_path
                ]
            else:
                # afplay (不支持AAC)
                cmd = [self._player_path, file_path]
            
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self._start_time = time.time()
            self.state = PlayerState.PLAYING
            self.state_changed.emit(PlayerState.PLAYING.value)
            self.position_timer.start()
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"播放错误: {str(e)}")
            return False
    
    def pause(self):
        """暂停播放"""
        if self._process and self.state == PlayerState.PLAYING:
            try:
                if self._player_type == 'ffplay':
                    # ffplay 不支持 SIGSTOP，直接停止
                    self._paused_position += time.time() - self._start_time
                    self._process.terminate()
                    self._process = None
                else:
                    os.kill(self._process.pid, signal.SIGSTOP)
                    self._paused_position += time.time() - self._start_time
                
                self.state = PlayerState.PAUSED
                self.state_changed.emit(PlayerState.PAUSED.value)
                self.position_timer.stop()
            except (ProcessLookupError, OSError):
                pass
    
    def resume(self):
        """恢复播放"""
        if self.state == PlayerState.PAUSED and self.current_track:
            if self._player_type == 'ffplay':
                # ffplay 需要重新播放
                self.play()
            elif self._process:
                try:
                    os.kill(self._process.pid, signal.SIGCONT)
                    self._start_time = time.time()
                    self.state = PlayerState.PLAYING
                    self.state_changed.emit(PlayerState.PLAYING.value)
                    self.position_timer.start()
                except ProcessLookupError:
                    pass
    
    def stop(self):
        """停止播放"""
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=1)
            except:
                try:
                    self._process.kill()
                except:
                    pass
            self._process = None
        
        self.state = PlayerState.STOPPED
        self._paused_position = 0.0
        self.state_changed.emit(PlayerState.STOPPED.value)
        self.position_timer.stop()
    
    def seek(self, position: float):
        """跳转到指定位置（简化实现）"""
        if self.current_track:
            was_playing = self.state == PlayerState.PLAYING
            self.stop()
            self._paused_position = position
            
            if was_playing:
                self.play()
    
    def set_volume(self, volume: int):
        """设置音量（0-100）"""
        self._volume = max(0, min(100, volume))
        self.volume_changed.emit(self._volume)
        
        # ffplay 需要重启才能改变音量
        if self._player_type == 'ffplay' and self.state == PlayerState.PLAYING:
            current_pos = self.get_position()
            self.stop()
            self._paused_position = current_pos
            self.play()
    
    def get_volume(self) -> int:
        """获取当前音量"""
        return self._volume
    
    def get_position(self) -> float:
        """获取当前播放位置（秒）"""
        if self.state == PlayerState.PLAYING:
            return self._paused_position + (time.time() - self._start_time)
        elif self.state == PlayerState.PAUSED:
            return self._paused_position
        return 0.0
    
    def get_duration(self) -> float:
        """获取音频时长（秒）"""
        if self.current_track:
            return self.current_track.duration
        return 0.0
    
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.state == PlayerState.PLAYING
    
    def is_paused(self) -> bool:
        """是否暂停"""
        return self.state == PlayerState.PAUSED
    
    def set_repeat_mode(self, mode: RepeatMode):
        """设置重复模式"""
        self.repeat_mode = mode
    
    def set_shuffle_mode(self, enabled: bool):
        """设置随机播放模式"""
        self.shuffle_mode = enabled
    
    def load_playlist(self, tracks: List[AudioTrack]):
        """加载播放列表"""
        self.playlist = tracks
        self.current_index = 0 if tracks else -1
    
    def play_track_at(self, index: int) -> bool:
        """播放指定索引的曲目"""
        if 0 <= index < len(self.playlist):
            self.current_index = index
            track = self.playlist[index]
            if self.load_track(track):
                return self.play()
        return False
    
    def next_track(self):
        """播放下一曲目"""
        self._play_next()
    
    def previous_track(self):
        """播放上一曲目"""
        if len(self.playlist) == 0:
            return
        
        if self.shuffle_mode:
            import random
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)
        
        self.play_track_at(self.current_index)
    
    def _play_next(self):
        """内部方法：播放下一曲目"""
        if len(self.playlist) == 0:
            return
        
        if self.repeat_mode == RepeatMode.ONE:
            self.play_track_at(self.current_index)
        elif self.shuffle_mode:
            import random
            self.current_index = random.randint(0, len(self.playlist) - 1)
            self.play_track_at(self.current_index)
        else:
            next_index = (self.current_index + 1) % len(self.playlist)
            
            if next_index == 0 and self.repeat_mode != RepeatMode.ALL:
                self.stop()
            else:
                self.play_track_at(next_index)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的音频格式"""
        if self._player_type == 'ffplay':
            return ["*.mp3", "*.m4a", "*.aac", "*.wav", "*.flac", "*.ogg", "*.wma", "*.opus"]
        else:
            return ["*.mp3", "*.m4a", "*.wav", "*.aiff", "*.flac"]
    
    def get_player_info(self) -> str:
        """获取播放器信息"""
        return f"使用 {self._player_type} 播放音频"
    
    def cleanup(self):
        """清理资源"""
        self.position_timer.stop()
        self.stop()