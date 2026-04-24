"""
播放列表管理模块
负责创建、编辑和管理播放列表
"""

import sqlite3
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from core.player import AudioTrack


@dataclass
class Playlist:
    """播放列表数据类"""
    id: int
    name: str
    description: str = ""
    date_created: Optional[datetime] = None
    track_count: int = 0


class PlaylistManager:
    """
    播放列表管理类
    负责创建、编辑和管理播放列表
    """
    
    def __init__(self, db_path: str = "music_library.db"):
        self.db_path = db_path
        self._init_playlists()
    
    def _init_playlists(self):
        """初始化播放列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建播放列表表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建播放列表曲目关联表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id INTEGER,
                track_id INTEGER,
                position INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                FOREIGN KEY (track_id) REFERENCES tracks (id),
                PRIMARY KEY (playlist_id, track_id)
            )
        ''')
        
        # 创建默认播放列表
        default_playlists = [
            ("我的收藏", "收藏的歌曲"),
            ("最近播放", "最近播放的歌曲"),
            ("最常播放", "播放次数最多的歌曲")
        ]
        
        for name, description in default_playlists:
            cursor.execute('''
                INSERT OR IGNORE INTO playlists (name, description) 
                VALUES (?, ?)
            ''', (name, description))
        
        conn.commit()
        conn.close()
    
    def create_playlist(self, name: str, description: str = "") -> int:
        """
        创建新播放列表
        
        Args:
            name: 播放列表名称
            description: 播放列表描述
            
        Returns:
            int: 新播放列表的ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查名称是否已存在，如果存在则添加数字后缀
        unique_name = name
        counter = 1
        while True:
            cursor.execute('SELECT id FROM playlists WHERE name = ?', (unique_name,))
            if cursor.fetchone() is None:
                break
            counter += 1
            unique_name = f"{name} ({counter})"
        
        cursor.execute('''
            INSERT INTO playlists (name, description) 
            VALUES (?, ?)
        ''', (unique_name, description))
        
        playlist_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return playlist_id
    
    def get_all_playlists(self) -> List[Playlist]:
        """获取所有播放列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.date_created,
                   COUNT(pt.track_id) as track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
            GROUP BY p.id, p.name, p.description, p.date_created
            ORDER BY p.date_created DESC
        ''')
        
        playlists = []
        for row in cursor.fetchall():
            playlist = Playlist(
                id=row[0],
                name=row[1],
                description=row[2] or "",
                date_created=datetime.fromisoformat(row[3]) if row[3] else None,
                track_count=row[4]
            )
            playlists.append(playlist)
        
        conn.close()
        return playlists
    
    def get_playlist(self, playlist_id: int) -> Optional[Playlist]:
        """获取指定播放列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.date_created,
                   COUNT(pt.track_id) as track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON p.id = pt.playlist_id
            WHERE p.id = ?
            GROUP BY p.id, p.name, p.description, p.date_created
        ''', (playlist_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        playlist = Playlist(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            date_created=datetime.fromisoformat(row[3]) if row[3] else None,
            track_count=row[4]
        )
        
        conn.close()
        return playlist
    
    def update_playlist(self, playlist_id: int, name: str = None, description: str = None):
        """更新播放列表信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if name:
            cursor.execute('UPDATE playlists SET name = ? WHERE id = ?', (name, playlist_id))
        if description:
            cursor.execute('UPDATE playlists SET description = ? WHERE id = ?', (description, playlist_id))
        
        conn.commit()
        conn.close()
    
    def delete_playlist(self, playlist_id: int):
        """删除播放列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 首先删除关联的曲目
        cursor.execute('DELETE FROM playlist_tracks WHERE playlist_id = ?', (playlist_id,))
        # 然后删除播放列表
        cursor.execute('DELETE FROM playlists WHERE id = ?', (playlist_id,))
        
        conn.commit()
        conn.close()
    
    def add_track_to_playlist(self, playlist_id: int, track_id: int):
        """
        添加曲目到播放列表
        
        Args:
            playlist_id: 播放列表ID
            track_id: 曲目ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前最大位置
        cursor.execute('''
            SELECT MAX(position) FROM playlist_tracks WHERE playlist_id = ?
        ''', (playlist_id,))
        max_position = cursor.fetchone()[0] or 0
        
        # 插入新曲目
        cursor.execute('''
            INSERT OR IGNORE INTO playlist_tracks (playlist_id, track_id, position)
            VALUES (?, ?, ?)
        ''', (playlist_id, track_id, max_position + 1))
        
        conn.commit()
        conn.close()
    
    def add_tracks_to_playlist(self, playlist_id: int, track_ids: List[int]):
        """批量添加曲目到播放列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前最大位置
        cursor.execute('''
            SELECT MAX(position) FROM playlist_tracks WHERE playlist_id = ?
        ''', (playlist_id,))
        max_position = cursor.fetchone()[0] or 0
        
        # 批量插入
        for i, track_id in enumerate(track_ids):
            cursor.execute('''
                INSERT OR IGNORE INTO playlist_tracks (playlist_id, track_id, position)
                VALUES (?, ?, ?)
            ''', (playlist_id, track_id, max_position + i + 1))
        
        conn.commit()
        conn.close()
    
    def remove_track_from_playlist(self, playlist_id: int, track_id: int):
        """从播放列表中移除曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM playlist_tracks 
            WHERE playlist_id = ? AND track_id = ?
        ''', (playlist_id, track_id))
        
        conn.commit()
        conn.close()
    
    def get_playlist_tracks(self, playlist_id: int) -> List[AudioTrack]:
        """获取播放列表中的曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.file_path, t.title, t.artist, t.album, t.duration, 
                   t.track_number, t.year, t.genre
            FROM tracks t
            JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ?
            ORDER BY pt.position
        ''', (playlist_id,))
        
        tracks = []
        for row in cursor.fetchall():
            track = AudioTrack(
                file_path=row[0],
                title=row[1] or "",
                artist=row[2] or "",
                album=row[3] or "",
                duration=row[4] or 0.0,
                track_number=row[5] or 0,
                year=row[6] or 0,
                genre=row[7] or ""
            )
            tracks.append(track)
        
        conn.close()
        return tracks
    
    def reorder_playlist(self, playlist_id: int, track_ids: List[int]):
        """重新排序播放列表中的曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for position, track_id in enumerate(track_ids):
            cursor.execute('''
                UPDATE playlist_tracks 
                SET position = ? 
                WHERE playlist_id = ? AND track_id = ?
            ''', (position, playlist_id, track_id))
        
        conn.commit()
        conn.close()
    
    def get_recently_played(self, limit: int = 50) -> List[AudioTrack]:
        """获取最近播放的曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, title, artist, album, duration, track_number, year, genre
            FROM tracks 
            WHERE last_played IS NOT NULL
            ORDER BY last_played DESC
            LIMIT ?
        ''', (limit,))
        
        tracks = []
        for row in cursor.fetchall():
            track = AudioTrack(
                file_path=row[0],
                title=row[1] or "",
                artist=row[2] or "",
                album=row[3] or "",
                duration=row[4] or 0.0,
                track_number=row[5] or 0,
                year=row[6] or 0,
                genre=row[7] or ""
            )
            tracks.append(track)
        
        conn.close()
        return tracks
    
    def get_most_played(self, limit: int = 50) -> List[AudioTrack]:
        """获取播放次数最多的曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, title, artist, album, duration, track_number, year, genre
            FROM tracks 
            WHERE play_count > 0
            ORDER BY play_count DESC
            LIMIT ?
        ''', (limit,))
        
        tracks = []
        for row in cursor.fetchall():
            track = AudioTrack(
                file_path=row[0],
                title=row[1] or "",
                artist=row[2] or "",
                album=row[3] or "",
                duration=row[4] or 0.0,
                track_number=row[5] or 0,
                year=row[6] or 0,
                genre=row[7] or ""
            )
            tracks.append(track)
        
        conn.close()
        return tracks
    
    def get_favorite_tracks(self) -> List[AudioTrack]:
        """获取收藏的曲目（评分5星）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, title, artist, album, duration, track_number, year, genre
            FROM tracks 
            WHERE rating = 5
            ORDER BY artist, album, track_number
        ''')
        
        tracks = []
        for row in cursor.fetchall():
            track = AudioTrack(
                file_path=row[0],
                title=row[1] or "",
                artist=row[2] or "",
                album=row[3] or "",
                duration=row[4] or 0.0,
                track_number=row[5] or 0,
                year=row[6] or 0,
                genre=row[7] or ""
            )
            tracks.append(track)
        
        conn.close()
        return tracks
    
    def add_to_favorites(self, track_id: int):
        """添加曲目到收藏（设置5星评分）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE tracks SET rating = 5 WHERE id = ?', (track_id,))
        
        conn.commit()
        conn.close()
    
    def remove_from_favorites(self, track_id: int):
        """从收藏中移除曲目（取消5星评分）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE tracks SET rating = 0 WHERE id = ?', (track_id,))
        
        conn.commit()
        conn.close()
    
    def get_playlist_stats(self, playlist_id: int) -> Dict[str, Any]:
        """获取播放列表统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取曲目数
        cursor.execute('''
            SELECT COUNT(*) FROM playlist_tracks WHERE playlist_id = ?
        ''', (playlist_id,))
        track_count = cursor.fetchone()[0]
        
        # 获取总时长
        cursor.execute('''
            SELECT SUM(t.duration) 
            FROM tracks t
            JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ?
        ''', (playlist_id,))
        total_duration = cursor.fetchone()[0] or 0.0
        
        # 获取总文件大小
        cursor.execute('''
            SELECT SUM(t.file_size) 
            FROM tracks t
            JOIN playlist_tracks pt ON t.id = pt.track_id
            WHERE pt.playlist_id = ?
        ''', (playlist_id,))
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "track_count": track_count,
            "total_duration": total_duration,
            "total_size": total_size
        }
    
    def _get_track_id_by_path(self, file_path: str) -> Optional[int]:
        """通过文件路径获取曲目ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM tracks WHERE file_path = ?', (file_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def add_track_by_file_path(self, playlist_id: int, file_path: str) -> bool:
        """通过文件路径添加曲目到播放列表"""
        track_id = self._get_track_id_by_path(file_path)
        if track_id is None:
            return False
        self.add_track_to_playlist(playlist_id, track_id)
        return True
    
    def remove_track_by_file_path(self, playlist_id: int, file_path: str) -> bool:
        """通过文件路径从播放列表移除曲目"""
        track_id = self._get_track_id_by_path(file_path)
        if track_id is None:
            return False
        self.remove_track_from_playlist(playlist_id, track_id)
        return True
    
    def is_track_in_playlist(self, playlist_id: int, file_path: str) -> bool:
        """检查曲目是否已在播放列表中"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 1 FROM playlist_tracks pt
            JOIN tracks t ON pt.track_id = t.id
            WHERE pt.playlist_id = ? AND t.file_path = ?
        ''', (playlist_id, file_path))
        result = cursor.fetchone() is not None
        conn.close()
        return result
    
    def add_to_favorites_by_path(self, file_path: str) -> bool:
        """通过文件路径添加曲目到收藏（设置5星评分）"""
        track_id = self._get_track_id_by_path(file_path)
        if track_id is None:
            return False
        self.add_to_favorites(track_id)
        return True
    
    def remove_from_favorites_by_path(self, file_path: str) -> bool:
        """通过文件路径从收藏中移除曲目"""
        track_id = self._get_track_id_by_path(file_path)
        if track_id is None:
            return False
        self.remove_from_favorites(track_id)
        return True
    
    def is_favorite(self, file_path: str) -> bool:
        """检查曲目是否已收藏"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT rating FROM tracks WHERE file_path = ?
        ''', (file_path,))
        result = cursor.fetchone()
        conn.close()
        return result is not None and result[0] == 5