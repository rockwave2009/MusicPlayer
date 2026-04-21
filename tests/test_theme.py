"""
主题模块测试
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.theme import ThemeManager, Theme


def test_theme_manager():
    """测试主题管理器"""
    print("测试主题管理器...")
    
    try:
        # 创建主题管理器
        manager = ThemeManager()
        print("✓ 主题管理器创建成功")
        
        # 测试默认主题
        assert manager.get_theme() == Theme.LIGHT or manager.get_theme() == Theme.DARK
        print(f"✓ 默认主题: {manager.get_theme().value}")
        
        # 测试获取颜色
        primary_color = manager.get_color("primary")
        assert primary_color.startswith("#"), "颜色格式错误"
        print(f"✓ 获取颜色成功: {primary_color}")
        
        # 测试主题切换
        initial_theme = manager.get_theme()
        manager.toggle_theme()
        assert manager.get_theme() != initial_theme, "主题切换失败"
        print(f"✓ 主题切换成功: {manager.get_theme().value}")
        
        # 测试再次切换
        manager.toggle_theme()
        assert manager.get_theme() == initial_theme, "主题切换回原主题失败"
        print("✓ 主题再次切换成功")
        
        # 测试设置主题
        manager.set_theme(Theme.DARK)
        assert manager.get_theme() == Theme.DARK, "设置深色主题失败"
        assert manager.is_dark() == True, "is_dark()方法错误"
        print("✓ 设置深色主题成功")
        
        manager.set_theme(Theme.LIGHT)
        assert manager.get_theme() == Theme.LIGHT, "设置浅色主题失败"
        assert manager.is_dark() == False, "is_dark()方法错误"
        print("✓ 设置浅色主题成功")
        
        # 测试获取样式表
        stylesheet = manager.get_stylesheet()
        assert len(stylesheet) > 0, "样式表为空"
        assert "background-color" in stylesheet, "样式表格式错误"
        print("✓ 获取样式表成功")
        
        # 测试所有主题颜色
        for theme in [Theme.LIGHT, Theme.DARK]:
            manager.set_theme(theme)
            colors = manager.themes[theme]
            
            # 验证必需的颜色
            required_colors = [
                "primary", "bg_main", "bg_secondary", "text_primary",
                "text_secondary", "border", "button_bg"
            ]
            
            for color_name in required_colors:
                assert color_name in colors, f"缺少颜色: {color_name}"
                color_value = colors[color_name]
                assert color_value.startswith("#") or color_value.startswith("rgba"), \
                    f"颜色格式错误: {color_name} = {color_value}"
            
            print(f"✓ {theme.value}主题颜色验证通过")
        
        print("主题管理器测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"主题管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_theme_colors():
    """测试主题颜色对比"""
    print("测试主题颜色对比...")
    
    try:
        manager = ThemeManager()
        
        # 验证浅色和深色主题的区别
        light_colors = manager.themes[Theme.LIGHT]
        dark_colors = manager.themes[Theme.DARK]
        
        # 浅色主题背景应该比深色主题背景亮
        assert light_colors["bg_main"] > dark_colors["bg_main"], \
            "浅色主题背景应该比深色主题背景亮"
        print("✓ 背景色对比正确")
        
        # 浅色主题文本应该比深色主题文本暗
        assert light_colors["text_primary"] < dark_colors["text_primary"], \
            "浅色主题文本应该比深色主题文本暗"
        print("✓ 文本色对比正确")
        
        # 主色调应该一致
        assert light_colors["primary"] == dark_colors["primary"], \
            "两个主题的主色调应该一致"
        print("✓ 主色调一致")
        
        print("主题颜色对比测试全部通过！\n")
        return True
        
    except Exception as e:
        print(f"主题颜色对比测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始运行主题模块测试套件")
    print("=" * 50)
    print()
    
    all_passed = True
    
    if not test_theme_manager():
        all_passed = False
    
    if not test_theme_colors():
        all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("所有主题测试通过！")
    else:
        print("部分主题测试失败！")
    print("=" * 50)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)