#!/usr/bin/env python3
"""
专业音乐播放器启动脚本
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 导入主模块
from main import main

if __name__ == "__main__":
    main()