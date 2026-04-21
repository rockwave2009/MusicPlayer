"""
音乐库管理模块
负责扫描、分类和管理本地音乐文件
"""

import os
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from mutagen import File

from core.player import AudioTrack


@dataclass
class MusicLibraryStats:
    """音乐库统计信息"""
    total_tracks: int = 0
    total_artists: int = 0
    total_albums: int = 0
    total_genres: int = 0
    total_duration: float = 0.0
    total_size: int = 0  # 字节


class MusicLibrary:
    """
    音乐库管理类
    负责扫描、索引和管理本地音乐文件
    """
    
    def __init__(self, db_path: str = "music_library.db"):
        self.db_path = db_path
        self.supported_extensions = {
            '.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a',
            '.wma', '.opus', '.aiff', '.ape', '.ac3', '.dts'
        }
        self._init_database()
        self._scan_lock = threading.Lock()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建曲目表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                title TEXT,
                artist TEXT,
                album TEXT,
                genre TEXT,
                year INTEGER,
                track_number INTEGER,
                duration REAL,
                file_size INTEGER,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_played TIMESTAMP,
                play_count INTEGER DEFAULT 0,
                rating INTEGER DEFAULT 0
            )
        ''')
        
        # 创建艺术家表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # 创建专辑表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT,
                year INTEGER,
                cover_art BLOB,
                UNIQUE(title, artist)
            )
        ''')
        
        # 创建播放列表表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建播放列表曲目关联表
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
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_artist ON tracks (artist)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_album ON tracks (album)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_genre ON tracks (genre)')
        
        conn.commit()
        conn.close()
    
    def scan_directory(self, directory: str, recursive: bool = True, callback=None):
        """
        扫描目录中的音乐文件
        
        Args:
            directory: 要扫描的目录
            recursive: 是否递归扫描子目录
            callback: 进度回调函数
        """
        with self._scan_lock:
            directory_path = Path(directory)
            if not directory_path.exists():
                raise ValueError(f"目录不存在: {directory}")
            
            # 获取所有音乐文件
            music_files = []
            if recursive:
                for ext in self.supported_extensions:
                    music_files.extend(directory_path.rglob(f"*{ext}"))
            else:
                for ext in self.supported_extensions:
                    music_files.extend(directory_path.glob(f"*{ext}"))
            
            total_files = len(music_files)
            processed_files = 0
            
            # 使用线程池处理文件
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for file_path in music_files:
                    future = executor.submit(self._process_music_file, str(file_path))
                    futures.append(future)
                
                # 等待所有任务完成
                for future in futures:
                    try:
                        future.result()
                        processed_files += 1
                        if callback:
                            callback(processed_files, total_files)
                    except Exception as e:
                        print(f"处理文件时出错: {e}")
    
    def _process_music_file(self, file_path: str):
        """处理单个音乐文件"""
        try:
            # 检查文件是否已存在
            if self._track_exists(file_path):
                return  # 跳过已存在的文件
            
            # 使用mutagen读取元数据
            audio = File(file_path, easy=True)
            if audio is None:
                return
            
            # 提取元数据
            title = audio.get('title', ['未知'])[0]
            artist = audio.get('artist', ['未知艺术家'])[0]
            album = audio.get('album', ['未知专辑'])[0]
            genre = audio.get('genre', ['未知流派'])[0]
            
            # 处理年份
            year = 0
            if 'date' in audio:
                date_str = audio['date'][0]
                if date_str and len(date_str) >= 4:
                    try:
                        year = int(date_str[:4])
                    except ValueError:
                        pass
            
            # 处理曲目号
            track_number = 0
            if 'tracknumber' in audio:
                track_str = audio['tracknumber'][0]
                if '/' in track_str:
                    track_str = track_str.split('/')[0]
                try:
                    track_number = int(track_str)
                except ValueError:
                    pass
            
            # 获取时长
            duration = 0.0
            if hasattr(audio, 'info'):
                duration = audio.info.length
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 保存到数据库
            self._save_track_to_db(
                file_path=file_path,
                title=title,
                artist=artist,
                album=album,
                genre=genre,
                year=year,
                track_number=track_number,
                duration=duration,
                file_size=file_size
            )
            
        except Exception as e:
            print(f"处理音乐文件失败 {file_path}: {e}")
    
    def _track_exists(self, file_path: str) -> bool:
        """检查曲目是否已存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM tracks WHERE file_path = ?', (file_path,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def _save_track_to_db(self, file_path: str, title: str, artist: str, album: str,
                          genre: str, year: int, track_number: int, duration: float,
                          file_size: int):
        """保存曲目到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 使用 INSERT OR IGNORE 避免重复
            cursor.execute('''
                INSERT OR IGNORE INTO tracks 
                (file_path, title, artist, album, genre, year, track_number, duration, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_path, title, artist, album, genre, year, track_number, duration, file_size))
            
            # 插入艺术家
            if artist and artist != '未知艺术家':
                cursor.execute('INSERT OR IGNORE INTO artists (name) VALUES (?)', (artist,))
            
            # 插入专辑
            if album and album != '未知专辑':
                cursor.execute('''
                    INSERT OR IGNORE INTO albums (title, artist, year) 
                    VALUES (?, ?, ?)
                ''', (album, artist, year))
            
            conn.commit()
        except Exception as e:
            print(f"保存到数据库失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_all_tracks(self) -> List[AudioTrack]:
        """获取所有曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, title, artist, album, duration, track_number, year, genre
            FROM tracks ORDER BY artist, album, track_number
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
    
    def search_tracks(self, query: str) -> List[AudioTrack]:
        """搜索曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_query = f"%{query}%"
        cursor.execute('''
            SELECT file_path, title, artist, album, duration, track_number, year, genre
            FROM tracks 
            WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? OR genre LIKE ?
            ORDER BY artist, album, track_number
        ''', (search_query, search_query, search_query, search_query))
        
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
    
    def get_tracks_by_artist(self, artist: str) -> List[AudioTrack]:
        """按艺术家获取曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, title, artist, album, duration, track_number, year, genre
            FROM tracks WHERE artist = ?
            ORDER BY album, track_number
        ''', (artist,))
        
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
    
    def get_tracks_by_album(self, album: str) -> List[AudioTrack]:
        """按专辑获取曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, title, artist, album, duration, track_number, year, genre
            FROM tracks WHERE album = ?
            ORDER BY track_number
        ''', (album,))
        
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
    
    def get_all_artists(self) -> List[str]:
        """获取所有艺术家"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT artist FROM tracks WHERE artist IS NOT NULL ORDER BY artist')
        artists = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return artists
    
    def get_all_albums(self) -> List[str]:
        """获取所有专辑"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT album FROM tracks WHERE album IS NOT NULL ORDER BY album')
        albums = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return albums
    
    def get_all_genres(self) -> List[str]:
        """获取所有流派"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT genre FROM tracks WHERE genre IS NOT NULL ORDER BY genre')
        genres = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return genres
    
    def get_library_stats(self) -> MusicLibraryStats:
        """获取音乐库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM tracks')
        total_tracks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT artist) FROM tracks WHERE artist IS NOT NULL')
        total_artists = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT album) FROM tracks WHERE album IS NOT NULL')
        total_albums = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT genre) FROM tracks WHERE genre IS NOT NULL')
        total_genres = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(duration) FROM tracks')
        total_duration = cursor.fetchone()[0] or 0.0
        
        cursor.execute('SELECT SUM(file_size) FROM tracks')
        total_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return MusicLibraryStats(
            total_tracks=total_tracks,
            total_artists=total_artists,
            total_albums=total_albums,
            total_genres=total_genres,
            total_duration=total_duration,
            total_size=total_size
        )
    
    def update_play_count(self, file_path: str):
        """更新播放次数"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE tracks 
            SET play_count = play_count + 1, last_played = CURRENT_TIMESTAMP
            WHERE file_path = ?
        ''', (file_path,))
        
        conn.commit()
        conn.close()
    
    def set_rating(self, file_path: str, rating: int):
        """设置曲目评分"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE tracks SET rating = ? WHERE file_path = ?', (rating, file_path))
        
        conn.commit()
        conn.close()
    
    def delete_track(self, file_path: str):
        """从数据库中删除曲目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tracks WHERE file_path = ?', (file_path,))
        
        conn.commit()
        conn.close()
    
    def refresh_library(self):
        """刷新音乐库 - 清理不存在的文件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT file_path FROM tracks')
        all_files = [row[0] for row in cursor.fetchall()]
        
        missing_files = []
        for file_path in all_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            cursor.executemany('DELETE FROM tracks WHERE file_path = ?', 
                              [(f,) for f in missing_files])
            conn.commit()
            print(f"已清理 {len(missing_files)} 个不存在的文件")
        
        conn.close()
        return len(missing_files)
    
    def clear_library(self):
        """清空音乐库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM tracks')
        cursor.execute('DELETE FROM artists')
        cursor.execute('DELETE FROM albums')
        
        conn.commit()
        conn.close()
        print("音乐库已清空")