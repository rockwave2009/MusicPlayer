"""
在线音乐下载模块
使用 Playwright 从 jzmp3.com 搜索和下载音乐及歌词
"""

import os
import re
import time
import subprocess
import urllib.parse
import threading
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QThread

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    artist: str
    album: str = ""
    index: int = 0


@dataclass
class DownloadResult:
    """下载结果数据类"""
    success: bool
    filename: str = ""
    filepath: str = ""
    file_size: int = 0
    lyrics_file: str = ""
    error: str = ""


class SearchThread(QThread):
    """搜索线程"""
    
    finished = pyqtSignal(list, str, int)  # 歌曲列表, 查询词, 总页数
    error = pyqtSignal(str)
    
    def __init__(self, query: str, page: int = 1):
        super().__init__()
        self.query = query
        self.page = page
    
    def run(self):
        if not PLAYWRIGHT_AVAILABLE:
            self.error.emit("Playwright 未安装，请运行: pip install playwright")
            return
        
        browser = None
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                page = browser.new_page()
                page.set_default_timeout(30000)
                
                encoded_query = urllib.parse.quote(self.query)
                if self.page == 1:
                    search_url = f"https://jzmp3.com/so/{encoded_query}"
                else:
                    search_url = f"https://jzmp3.com/so/{encoded_query}/{self.page}/"
                
                response = page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
                
                # 等待页面加载
                time.sleep(3)
                
                # 尝试等待搜索结果出现
                try:
                    page.wait_for_selector('.result-info', timeout=5000)
                except:
                    pass
                
                items = page.query_selector_all('.result-info')
                
                songs = []
                for i, item in enumerate(items):
                    title_el = item.query_selector('.result-title')
                    artist_el = item.query_selector('.result-artist')
                    album_el = item.query_selector('.result-album')
                    
                    title = title_el.inner_text().strip() if title_el else ""
                    artist = artist_el.inner_text().strip() if artist_el else ""
                    album = album_el.inner_text().strip() if album_el else ""
                    
                    if title:
                        songs.append(SearchResult(
                            title=title,
                            artist=artist,
                            album=album,
                            index=i + 1
                        ))
                
                # 获取总页数
                total_pages = 1
                try:
                    total_el = page.query_selector('#total-pages')
                    if total_el:
                        total_text = total_el.inner_text()
                        if total_text.isdigit():
                            total_pages = int(total_text)
                except:
                    pass
                
                if total_pages < 1:
                    total_pages = 1
                
                browser.close()
                browser = None
                
                self.finished.emit(songs, self.query, total_pages)
                
        except Exception as e:
            if browser:
                try:
                    browser.close()
                except:
                    pass
            self.error.emit(str(e))


class DownloadThread(QThread):
    """下载线程"""
    
    progress = pyqtSignal(str)  # 进度信息
    finished = pyqtSignal(DownloadResult)
    
    def __init__(self, song: SearchResult, download_dir: str):
        super().__init__()
        self.song = song
        self.download_dir = download_dir
    
    def run(self):
        if not PLAYWRIGHT_AVAILABLE:
            self.finished.emit(DownloadResult(
                success=False,
                error="Playwright 未安装"
            ))
            return

        browser = None
        browser = None
        page = None
        try:
            self.progress.emit("正在初始化浏览器...")
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                self.progress.emit("正在打开播放页面...")
                
                # 搜索歌曲
                self.progress.emit("正在搜索...")
                encoded_query = urllib.parse.quote(f"{self.song.title} {self.song.artist}")
                search_url = f"https://jzmp3.com/so/{encoded_query}"
                page.goto(search_url, timeout=20000)
                time.sleep(2)
                
                # 等待搜索结果出现
                try:
                    page.wait_for_selector('.result-info', timeout=5000)
                except:
                    pass
                
                # 点击播放按钮
                self.progress.emit("进入播放页...")
                play_icons = page.query_selector_all('.play-icon')
                if play_icons:
                    self.progress.emit(f"找到 {len(play_icons)} 个播放图标")
                    play_icons[0].click()
                    time.sleep(3)
                    
                    # 等待跳转到播放页面
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                        self.progress.emit("页面加载完成")
                    except Exception as e:
                        self.progress.emit(f"等待页面加载超时: {str(e)}")
                    
                    # 如果URL没变，尝试点击详情链接
                    current_url = page.url
                    if '/so/' in current_url or current_url == search_url:
                        self.progress.emit("仍在搜索页面，尝试查找详情链接...")
                        # 尝试找歌曲详情链接
                        song_links = page.query_selector_all('a[href*="/yinyue/"]')
                        self.progress.emit(f"找到 {len(song_links)} 个详情链接")
                        for i, link in enumerate(song_links[:3]):
                            href = link.get_attribute('href')
                            text = link.inner_text() if link else ""
                            self.progress.emit(f"链接{i}: href={href}, text={text}")
                            if href and '/yinyue/' in href:
                                full_url = f"https://jzmp3.com{href}"
                                self.progress.emit(f"跳转到详情页: {full_url}")
                                page.goto(full_url, timeout=15000)
                                time.sleep(3)
                                break
                else:
                    self.progress.emit("未找到播放图标")
                
                # 提取链接
                self.progress.emit("提取音频链接...")
                html = page.content()
                self.progress.emit(f"页面大小: {len(html)} 字符")
                
                # 提取音频链接 - 简化方法
                audio_urls = []
                
                # 方法1: 专门查找 kuwo.cn 域名的 MP3 链接（最可靠）
                kuwo_pattern = r'https?://[^\s\'"]*kuwo\.cn[^\s\'"]*\.mp3'
                kuwo_matches = re.findall(kuwo_pattern, html, re.I)
                audio_urls.extend(kuwo_matches)
                
                # 方法2: <audio> 或 <source> 标签的 src 属性
                source_matches = re.findall(r'<source[^>]+src=[\'"]([^\'"]+)[\'"]', html, re.I)
                audio_urls.extend(source_matches)
                
                # 方法3: 通用音频链接匹配
                audio_patterns = [
                    r'src=[\'"](https?://[^\s\'"]+\.(?:aac|mp3|flac|wav))[\'"]',
                    r'https?://[^\s\'"]+\.(?:aac|mp3|flac|wav)(?:\?[^\s\'"]*)?',
                ]
                
                for pattern in audio_patterns:
                    matches = re.findall(pattern, html, re.I)
                    audio_urls.extend(matches)
                
                # 去重并过滤无效链接
                audio_urls = list(dict.fromkeys([url for url in audio_urls if url and len(url) > 10]))
                
                if not audio_urls:
                    self.progress.emit("未找到任何音频链接！")
                    self.finished.emit(DownloadResult(
                        success=False,
                        error="未找到音频链接，请尝试其他来源"
                    ))
                    return
                
                # 简化音频链接选择策略
                audio_url = None
                
                # 策略1: 首选 kuwo.cn 域名（最可靠）
                for url in audio_urls:
                    if 'kuwo.cn' in url.lower():
                        audio_url = url
                        self.progress.emit(f"选择链接 (kuwo.cn): {audio_url}")
                        break
                
                # 策略2: 选择包含音频特征的URL
                if not audio_url:
                    scored_urls = []
                    for url in audio_urls:
                        score = 0
                        url_lower = url.lower()
                        if '.mp3' in url_lower: score += 3
                        if '.aac' in url_lower: score += 2
                        if 'kuwo' in url_lower: score += 2
                        if 'lv-sycdn' in url_lower: score += 2
                        if 'cdn' in url_lower: score += 1
                        if 50 < len(url) < 200: score += 1
                        scored_urls.append((score, url))
                    
                    if scored_urls:
                        scored_urls.sort(reverse=True)
                        audio_url = scored_urls[0][1]
                        self.progress.emit(f"选择链接 (最高分): {audio_url}")
                
                # 策略3: 直接取第一个
                if not audio_url:
                    audio_url = audio_urls[0]
                    self.progress.emit(f"选择链接 (第一个): {audio_url}")
                
                self.progress.emit(f"最终音频URL: {audio_url}")
                
                if not audio_url:
                    self.progress.emit("未找到任何音频链接")
                    self.finished.emit(DownloadResult(
                        success=False,
                        error="未找到音频链接，请尝试其他来源"
                    ))
                    return
                
                # 提取歌词
                self.progress.emit("提取歌词...")
                # 在关闭浏览器前获取歌词HTML
                lyrics_html = page.content()
                
                # 尝试提取歌词 - 简化方法
                lyrics = []
                lrc_filename = None
                
                # 方法1: 标准 lyric-line class + data-time
                lyric_matches = re.findall(r'class="lyric-line"\s+data-time="(\d+)"[^>]*>([^<]+)<', lyrics_html)
                
                # 方法2: 通用 data-time 属性
                if not lyric_matches:
                    lyric_matches = re.findall(r'data-time="(\d+)"[^>]*>([^<]+)<', lyrics_html)
                
                # 方法3: 传统 LRC 格式（备用）
                if not lyric_matches:
                    lrc_lines = re.findall(r'\[(\d{2}):(\d{2})\.(\d{2,3})\]([^\[\n]*)', lyrics_html)
                    for mins, sec, ms, text in lrc_lines:
                        if text.strip():
                            time_seconds = int(mins) * 60 + int(sec) + int(ms) / (1000 if len(ms) == 3 else 100)
                            lyric_matches.append((str(int(time_seconds)), text.strip()))
                
                for time_sec, text in lyric_matches:
                    if text.strip():
                        lyrics.append((float(time_sec), text.strip()))
                
                # 下载音频文件
                self.progress.emit("正在下载...")
                self.progress.emit(f"音频URL: {audio_url[:100]}...")

                ext = 'mp3'
                if '.aac' in audio_url:
                    ext = 'aac'
                elif '.flac' in audio_url:
                    ext = 'flac'
                elif '.wav' in audio_url:
                    ext = 'wav'

                artist = self.song.artist if self.song.artist else ""
                filename = f"{artist} - {self.song.title}.{ext}" if artist else f"{self.song.title}.{ext}"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                filepath = os.path.join(self.download_dir, filename)

                # 保存歌词文件 - 使用与音频文件相同的 stem 确保匹配
                if lyrics:
                    audio_stem = Path(filepath).stem
                    lrc_filename = f"{audio_stem}.lrc"
                    lrc_filename = "".join(c for c in lrc_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                    lrc_filepath = os.path.join(self.download_dir, lrc_filename)
                    lrc_content = '\n'.join([f"[{int(l[0]//60):02d}:{l[0]%60:05.2f}]{l[1]}" for l in lyrics])
                    with open(lrc_filepath, 'w', encoding='utf-8') as f:
                        f.write(lrc_content)

                # 设置请求头模拟浏览器
                headers = [
                    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    '-H', 'Referer: https://jzmp3.com/'
                ]
                
                # 构建curl命令并下载
                curl_cmd = ['curl', '-L', '-o', filepath, '--connect-timeout', '10',
                           '--max-time', '120'] + headers + [audio_url]
                           
                result = subprocess.run(
                    curl_cmd,
                    capture_output=True, text=True, timeout=130
                )

                if result.returncode == 0 and os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    self.progress.emit(f"下载完成，文件大小: {file_size} 字节")
                    if file_size > 1000:
                        self.finished.emit(DownloadResult(
                            success=True,
                            filename=filename,
                            filepath=filepath,
                            file_size=file_size,
                            lyrics_file=lrc_filename if lrc_filename else ""
                        ))
                    else:
                        # 删除太小的文件
                        try:
                            os.remove(filepath)
                        except:
                            pass
                        self.finished.emit(DownloadResult(
                            success=False,
                            error=f"下载的文件太小 ({file_size} 字节)，可能是无效文件"
                        ))
                else:
                    error_msg = result.stderr if result.stderr else "下载失败"
                    self.finished.emit(DownloadResult(
                        success=False,
                        error=f"下载失败: {error_msg[:100]}"
                    ))
                    
        except Exception as e:
            # 确保浏览器被正确关闭
            try:
                if 'browser' in locals() and browser:
                    browser.close()
            except:
                pass
            self.finished.emit(DownloadResult(
                success=False,
                error=f"下载出错: {str(e)[:100]}"
            ))


class OnlineMusicDownloader(QObject):
    """
    在线音乐下载器
    提供搜索和下载功能
    """
    
    # 信号定义
    search_finished = pyqtSignal(list, str, int)  # 搜索结果, 查询词, 总页数
    search_error = pyqtSignal(str)
    download_progress = pyqtSignal(str)  # 下载进度
    download_finished = pyqtSignal(DownloadResult)  # 下载完成
    
    def __init__(self, download_dir: str = None, parent=None):
        super().__init__(parent)
        
        # 设置下载目录
        if download_dir:
            self.download_dir = download_dir
        else:
            self.download_dir = os.path.join(os.path.expanduser('~'), 'Music', 'MusicPlayer')
        
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 线程引用
        self._search_thread = None
        self._download_thread = None
    
    def is_playwright_available(self) -> bool:
        """检查 Playwright 是否可用"""
        return PLAYWRIGHT_AVAILABLE
    
    def search(self, query: str, page: int = 1):
        """搜索歌曲"""
        if self._search_thread and self._search_thread.isRunning():
            return
        
        self._search_thread = SearchThread(query, page)
        self._search_thread.finished.connect(self._on_search_finished)
        self._search_thread.error.connect(self._on_search_error)
        self._search_thread.start()
    
    def _on_search_finished(self, songs: List[SearchResult], query: str, total_pages: int):
        """搜索完成"""
        self.search_finished.emit(songs, query, total_pages)
    
    def _on_search_error(self, error: str):
        """搜索错误"""
        self.search_error.emit(error)
    
    def download(self, song: SearchResult):
        """下载歌曲"""
        if self._download_thread and self._download_thread.isRunning():
            return
        
        self._download_thread = DownloadThread(song, self.download_dir)
        self._download_thread.progress.connect(self._on_download_progress)
        self._download_thread.finished.connect(self._on_download_finished)
        self._download_thread.start()
    
    def _on_download_progress(self, message: str):
        """下载进度"""
        self.download_progress.emit(message)
    
    def _on_download_finished(self, result: DownloadResult):
        """下载完成"""
        self.download_finished.emit(result)
    
    def get_download_dir(self) -> str:
        """获取下载目录"""
        return self.download_dir
    
    def set_download_dir(self, path: str):
        """设置下载目录"""
        self.download_dir = path
        os.makedirs(self.download_dir, exist_ok=True)
    
    def is_downloading(self) -> bool:
        """是否正在下载"""
        return self._download_thread is not None and self._download_thread.isRunning()
    
    def is_searching(self) -> bool:
        """是否正在搜索"""
        return self._search_thread is not None and self._search_thread.isRunning()