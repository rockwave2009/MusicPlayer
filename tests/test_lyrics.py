"""
歌词模块测试
"""

import sys
import tempfile
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.lyrics import LyricParser, LyricsManager, LyricLine


def test_lyric_parser():
    """测试歌词解析器"""
    print("测试歌词解析器...")
    
    try:
        parser = LyricParser()
        
        # 测试标准LRC格式
        lrc_content = """[ti:测试歌曲]
[ar:测试艺术家]
[al:测试专辑]

[00:01.00]第一行歌词
[00:05.50]第二行歌词
[00:10.00]第三行歌词
[00:15.30][00:20.00]多时间标签歌词
"""
        
        lines = parser.parse_string(lrc_content)
        
        assert len(lines) == 5, f"期望5行歌词，实际{len(lines)}行"
        print("✓ 歌词解析成功")
        
        # 验证时间解析
        assert lines[0].time == 1.0, f"第一行时间错误: {lines[0].time}"
        assert lines[1].time == 5.5, f"第二行时间错误: {lines[1].time}"
        print("✓ 时间解析正确")
        
        # 验证文本解析
        assert lines[0].text == "第一行歌词", f"第一行文本错误: {lines[0].text}"
        assert lines[1].text == "第二行歌词", f"第二行文本错误: {lines[1].text}"
        print("✓ 文本解析正确")
        
        # 验证元数据
        metadata = parser.get_metadata()
        assert metadata.get('ti') == '测试歌曲', "标题元数据错误"
        assert metadata.get('ar') == '测试艺术家', "艺术家元数据错误"
        print("✓ 元数据解析正确")
        
        # 验证多时间标签
        assert lines[3].time == 15.3, f"多时间标签解析错误: {lines[3].time}"
        assert lines[4].time == 20.0, f"多时间标签解析错误: {lines[4].time}"
        assert lines[3].text == "多时间标签歌词", "多时间标签文本错误"
        print("✓ 多时间标签解析正确")
        
        print("歌词解析器测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"歌词解析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lyrics_manager():
    """测试歌词管理器"""
    print("测试歌词管理器...")
    
    try:
        manager = LyricsManager()
        
        # 测试从字符串加载
        lrc_content = """[00:00.00]开始
[00:03.00]第一句
[00:06.00]第二句
[00:09.00]结束
"""
        
        result = manager.load_from_string(lrc_content)
        assert result == True, "加载歌词失败"
        assert manager.has_lyrics() == True, "歌词状态错误"
        assert len(manager.get_all_lyrics()) == 4, "歌词行数错误"
        print("✓ 从字符串加载歌词成功")
        
        # 测试位置同步
        manager.update_position(0.0)
        current = manager.get_current_line()
        assert current is not None, "当前行为空"
        assert current.text == "开始", f"当前行文本错误: {current.text}"
        print("✓ 位置同步（0秒）正确")
        
        manager.update_position(4.0)
        current = manager.get_current_line()
        assert current.text == "第一句", f"当前行文本错误: {current.text}"
        print("✓ 位置同步（4秒）正确")
        
        manager.update_position(7.0)
        current = manager.get_current_line()
        assert current.text == "第二句", f"当前行文本错误: {current.text}"
        print("✓ 位置同步（7秒）正确")
        
        # 测试文件加载
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lrc', delete=False, encoding='utf-8') as f:
            f.write(lrc_content)
            temp_file = f.name
        
        try:
            result = manager.load_lyrics(temp_file)
            assert result == True, "从文件加载失败"
            assert len(manager.get_all_lyrics()) == 4, "文件歌词行数错误"
            print("✓ 从文件加载歌词成功")
        finally:
            os.unlink(temp_file)
        
        # 测试清空
        manager.clear()
        assert manager.has_lyrics() == False, "清空后状态错误"
        assert manager.get_current_line() is None, "清空后当前行应为空"
        print("✓ 清空歌词成功")
        
        print("歌词管理器测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"歌词管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_find_lyrics():
    """测试自动查找歌词"""
    print("测试自动查找歌词...")
    
    try:
        manager = LyricsManager()
        
        # 创建临时目录结构
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建音频文件
            audio_file = os.path.join(temp_dir, "test.mp3")
            Path(audio_file).touch()
            
            # 测试未找到歌词
            result = manager.auto_find_lyrics(audio_file)
            assert result == False, "未创建歌词文件时应返回False"
            print("✓ 未找到歌词时返回False")
            
            # 创建同名歌词文件
            lrc_file = os.path.join(temp_dir, "test.lrc")
            with open(lrc_file, 'w', encoding='utf-8') as f:
                f.write("[00:01.00]测试歌词\n")
            
            result = manager.auto_find_lyrics(audio_file)
            assert result == True, "找到歌词文件后应返回True"
            assert manager.has_lyrics() == True, "应加载歌词"
            print("✓ 自动找到同目录歌词文件")
            
            # 测试lyrics子目录
            manager.clear()
            os.unlink(lrc_file)
            
            lyrics_dir = os.path.join(temp_dir, "lyrics")
            os.makedirs(lyrics_dir)
            lrc_file = os.path.join(lyrics_dir, "test.lrc")
            with open(lrc_file, 'w', encoding='utf-8') as f:
                f.write("[00:02.00]子目录歌词\n")
            
            result = manager.auto_find_lyrics(audio_file)
            assert result == True, "找到子目录歌词文件后应返回True"
            assert manager.has_lyrics() == True, "应加载子目录歌词"
            print("✓ 自动找到lyrics子目录歌词文件")
        
        print("自动查找歌词测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"自动查找歌词测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行歌词模块测试套件")
    print("=" * 50)
    print()
    
    all_passed = True
    
    if not test_lyric_parser():
        all_passed = False
    
    if not test_lyrics_manager():
        all_passed = False
    
    if not test_auto_find_lyrics():
        all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("所有歌词测试通过！")
    else:
        print("部分歌词测试失败！")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)