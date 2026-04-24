#!/bin/bash
# MusicPlayer 启动脚本 - 后台运行，不占用终端

cd "$(dirname "$0")"

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    osascript -e 'display alert "错误" message "未找到 Python3，请先安装"' &
    exit 1
fi

# 后台启动，丢弃所有输出
nohup python3 run.py > /dev/null 2>&1 &

# 显示启动通知（macOS）
if command -v osascript &> /dev/null; then
    osascript -e 'display notification "音乐播放器已启动" with title "MusicPlayer"' &
fi

echo "MusicPlayer 已在后台启动"
