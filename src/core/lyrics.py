"""
歌词模块
支持LRC格式歌词的解析、加载和同步显示
"""

import re
import os
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class LyricLine:
    """歌词行数据类"""
    time: float      # 时间点（秒）
    text: str        # 歌词文本


class LyricParser:
    """
    LRC歌词解析器
    支持标准LRC格式和扩展格式
    """
    
    # 时间标签正则表达式 [mm:ss.xx] 或 [mm:ss.xxx]
    TIME_PATTERN = re.compile(r'\[(\d{1,3}):(\d{1,2})\.(\d{1,3})\]')
    
    # 元数据标签正则表达式 [key:value]
    META_PATTERN = re.compile(r'\[([a-zA-Z]+):([^\]]*)\]')
    
    def __init__(self):
        self.metadata = {}
    
    def parse_file(self, file_path: str) -> List[LyricLine]:
        """
        解析LRC歌词文件
        
        Args:
            file_path: LRC文件路径
            
        Returns:
            List[LyricLine]: 歌词行列表
        """
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_string(content)
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                return self.parse_string(content)
            except Exception:
                return []
        except Exception:
            return []
    
    def parse_string(self, content: str) -> List[LyricLine]:
        """
        解析LRC格式字符串
        
        Args:
            content: LRC格式的歌词内容
            
        Returns:
            List[LyricLine]: 歌词行列表
        """
        lines = []
        self.metadata = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # 尝试解析元数据标签
            meta_match = self.META_PATTERN.match(line)
            if meta_match:
                key, value = meta_match.groups()
                self.metadata[key.lower()] = value
                continue
            
            # 解析时间标签和歌词内容
            lyric_lines = self._parse_lyric_line(line)
            lines.extend(lyric_lines)
        
        # 按时间排序
        lines.sort(key=lambda x: x.time)
        
        return lines
    
    def _parse_lyric_line(self, line: str) -> List[LyricLine]:
        """
        解析单行歌词（可能包含多个时间标签）
        
        Args:
            line: 歌词行
            
        Returns:
            List[LyricLine]: 解析后的歌词行列表
        """
        # 找出所有时间标签
        time_matches = list(self.TIME_PATTERN.finditer(line))
        
        if not time_matches:
            return []
        
        # 提取歌词文本（最后一个时间标签之后的内容）
        last_match_end = time_matches[-1].end()
        text = line[last_match_end:].strip()
        
        # 为每个时间标签创建歌词行
        lines = []
        for match in time_matches:
            minutes, seconds, milliseconds = match.groups()
            
            # 转换为秒
            time_seconds = int(minutes) * 60 + int(seconds)
            
            # 处理毫秒（可能是2位或3位）
            ms = milliseconds
            if len(ms) == 2:
                time_seconds += int(ms) / 100
            elif len(ms) == 3:
                time_seconds += int(ms) / 1000
            else:
                time_seconds += int(ms) / 100
            
            lines.append(LyricLine(time=time_seconds, text=text))
        
        return lines
    
    def get_metadata(self) -> dict:
        """获取解析到的元数据"""
        return self.metadata


class LyricsManager(QObject):
    """
    歌词管理器
    负责加载、查找和同步歌词
    """
    
    # 信号定义
    lyrics_loaded = pyqtSignal(str)  # 歌词加载完成信号
    current_line_changed = pyqtSignal(int, str)  # 当前行改变信号（索引，文本）
    error_occurred = pyqtSignal(str)  # 错误信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.parser = LyricParser()
        self.lyrics: List[LyricLine] = []
        self.current_index = -1
        self.current_file = ""
    
    def load_lyrics(self, file_path: str) -> bool:
        """
        加载LRC歌词文件
        
        Args:
            file_path: 歌词文件路径
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.lyrics = self.parser.parse_file(file_path)
            self.current_index = -1
            self.current_file = file_path
            
            if self.lyrics:
                self.lyrics_loaded.emit(f"已加载 {len(self.lyrics)} 行歌词")
                return True
            else:
                self.error_occurred.emit("歌词文件为空或格式错误")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"加载歌词失败: {str(e)}")
            return False
    
    def load_from_string(self, content: str) -> bool:
        """
        从字符串加载歌词
        
        Args:
            content: LRC格式的歌词内容
            
        Returns:
            bool: 是否成功加载
        """
        try:
            self.lyrics = self.parser.parse_string(content)
            self.current_index = -1
            
            if self.lyrics:
                self.lyrics_loaded.emit(f"已加载 {len(self.lyrics)} 行歌词")
                return True
            else:
                self.error_occurred.emit("歌词内容为空或格式错误")
                return False
                
        except Exception as e:
            self.error_occurred.emit(f"加载歌词失败: {str(e)}")
            return False
    
    def auto_find_lyrics(self, audio_file_path: str) -> bool:
        """
        自动查找与音频文件同名的歌词文件
        
        Args:
            audio_file_path: 音频文件路径
            
        Returns:
            bool: 是否找到并加载歌词
        """
        audio_path = Path(audio_file_path)
        
        # 尝试同目录下的同名.lrc文件
        lrc_path = audio_path.with_suffix('.lrc')
        if lrc_path.exists():
            return self.load_lyrics(str(lrc_path))
        
        # 尝试lyrics子目录
        lyrics_dir = audio_path.parent / "lyrics"
        if lyrics_dir.exists():
            lrc_path = lyrics_dir / f"{audio_path.stem}.lrc"
            if lrc_path.exists():
                return self.load_lyrics(str(lrc_path))
        
        return False
    
    def update_position(self, position: float):
        """
        更新播放位置，同步歌词显示
        
        Args:
            position: 当前播放位置（秒）
        """
        if not self.lyrics:
            return
        
        # 查找当前应该显示的歌词行
        new_index = -1
        
        for i, line in enumerate(self.lyrics):
            if line.time <= position:
                new_index = i
            else:
                break
        
        # 如果行改变，发出信号
        if new_index != self.current_index and new_index >= 0:
            self.current_index = new_index
            self.current_line_changed.emit(new_index, self.lyrics[new_index].text)
    
    def get_current_line(self) -> Optional[LyricLine]:
        """获取当前歌词行"""
        if 0 <= self.current_index < len(self.lyrics):
            return self.lyrics[self.current_index]
        return None
    
    def get_all_lyrics(self) -> List[LyricLine]:
        """获取所有歌词"""
        return self.lyrics
    
    def get_lyrics_with_index(self) -> List[Tuple[int, LyricLine]]:
        """获取带索引的歌词列表"""
        return [(i, line) for i, line in enumerate(self.lyrics)]
    
    def clear(self):
        """清空歌词"""
        self.lyrics = []
        self.current_index = -1
        self.current_file = ""
    
    def has_lyrics(self) -> bool:
        """是否有歌词"""
        return len(self.lyrics) > 0
    
    def get_duration(self) -> float:
        """获取歌词总时长（最后一个时间点）"""
        if self.lyrics:
            return self.lyrics[-1].time
        return 0.0
    
    def get_line_time(self, index: int) -> float:
        """获取指定索引歌词行的时间点（秒）"""
        if 0 <= index < len(self.lyrics):
            return self.lyrics[index].time
        return 0.0