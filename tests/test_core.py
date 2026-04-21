"""
测试文件
测试音乐播放器的核心功能
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.player import AudioPlayer, AudioTrack
from core.library import MusicLibrary
from core.playlist import PlaylistManager


def test_player():
    """测试播放器核心功能"""
    print("测试播放器核心功能...")
    
    try:
        player = AudioPlayer()
        print("✓ 播放器实例创建成功")
        
        track = AudioTrack(
            file_path="/path/to/test.mp3",
            title="测试曲目",
            artist="测试艺术家",
            album="测试专辑"
        )
        print("✓ 音频轨道创建成功")
        
        player.load_playlist([track])
        print("✓ 播放列表加载成功")
        
        player.set_volume(50)
        assert player.get_volume() == 50
        print("✓ 音量控制测试通过")
        
        from core.player import RepeatMode
        player.set_repeat_mode(RepeatMode.ALL)
        assert player.repeat_mode == RepeatMode.ALL
        print("✓ 重复模式测试通过")
        
        player.set_shuffle_mode(True)
        assert player.shuffle_mode == True
        print("✓ 随机播放测试通过")
        
        player.cleanup()
        print("✓ 资源清理成功")
        
        print("播放器核心功能测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"播放器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_library():
    """测试音乐库功能"""
    print("测试音乐库功能...")
    
    db_path = None
    try:
        # 使用临时文件数据库
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        library = MusicLibrary(db_path)
        print("✓ 音乐库实例创建成功")
        
        tracks = library.get_all_tracks()
        assert len(tracks) == 0
        print("✓ 空音乐库测试通过")
        
        stats = library.get_library_stats()
        assert stats.total_tracks == 0
        print("✓ 统计信息测试通过")
        
        print("音乐库功能测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"音乐库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db_path and os.path.exists(db_path):
            os.unlink(db_path)


def test_playlist():
    """测试播放列表功能"""
    print("测试播放列表功能...")
    
    db_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        playlist_manager = PlaylistManager(db_path)
        print("✓ 播放列表管理器创建成功")
        
        playlists = playlist_manager.get_all_playlists()
        print(f"✓ 获取播放列表成功，数量: {len(playlists)}")
        
        playlist_id = playlist_manager.create_playlist("测试播放列表", "测试描述")
        print("✓ 创建播放列表成功")
        
        playlist = playlist_manager.get_playlist(playlist_id)
        assert playlist is not None
        assert playlist.name == "测试播放列表"
        print("✓ 获取播放列表成功")
        
        playlist_manager.update_playlist(playlist_id, name="更新后的播放列表")
        updated_playlist = playlist_manager.get_playlist(playlist_id)
        assert updated_playlist.name == "更新后的播放列表"
        print("✓ 更新播放列表成功")
        
        playlist_manager.delete_playlist(playlist_id)
        deleted_playlist = playlist_manager.get_playlist(playlist_id)
        assert deleted_playlist is None
        print("✓ 删除播放列表成功")
        
        print("播放列表功能测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"播放列表测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if db_path and os.path.exists(db_path):
            os.unlink(db_path)


def test_equalizer():
    """测试均衡器功能"""
    print("测试均衡器功能...")
    
    try:
        from core.equalizer import AudioEqualizer, AudioAnalyzer, AudioEffectProcessor
        import numpy as np
        
        equalizer = AudioEqualizer()
        print("✓ 均衡器创建成功")
        
        equalizer.set_band_gain(0, 5.0)
        assert equalizer.get_band_gain(0) == 5.0
        print("✓ 频段增益设置成功")
        
        equalizer.apply_preset("rock")
        print("✓ 均衡器预设应用成功")
        
        equalizer.reset()
        assert equalizer.get_band_gain(0) == 0.0
        print("✓ 均衡器重置成功")
        
        analyzer = AudioAnalyzer()
        print("✓ 音频分析器创建成功")
        
        test_audio = np.random.random(44100)
        freqs, magnitude = analyzer.compute_spectrum(test_audio)
        assert len(freqs) > 0
        assert len(magnitude) > 0
        print("✓ 频谱计算测试通过")
        
        waveform = analyzer.compute_waveform(test_audio, num_points=100)
        assert len(waveform) == 100
        print("✓ 波形计算测试通过")
        
        effect_processor = AudioEffectProcessor()
        print("✓ 音频效果处理器创建成功")
        
        normalized = effect_processor.normalize(test_audio, -3.0)
        assert len(normalized) == len(test_audio)
        print("✓ 音频标准化测试通过")
        
        print("均衡器功能测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"均衡器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行音乐播放器测试套件")
    print("=" * 50)
    print()
    
    all_passed = True
    
    if not test_player():
        all_passed = False
    
    if not test_library():
        all_passed = False
    
    if not test_playlist():
        all_passed = False
    
    if not test_equalizer():
        all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("所有测试通过！")
    else:
        print("部分测试失败！")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)