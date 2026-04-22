# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

# 获取项目根目录
project_root = Path(os.getcwd())

# 收集数据文件
datas = []

# 添加资源文件（如果存在）
if (project_root / 'resources').exists():
    datas.append((str(project_root / 'resources'), 'resources'))

# 检查图标文件是否存在
icon_file = None
if sys.platform == 'win32':
    ico_path = project_root / 'resources' / 'icons' / 'app_icon.ico'
    if ico_path.exists():
        icon_file = str(ico_path)
elif sys.platform == 'darwin':
    icns_path = project_root / 'resources' / 'icons' / 'app_icon.icns'
    if icns_path.exists():
        icon_file = str(icns_path)

a = Analysis(
    ['src/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'mutagen',
        'mutagen.mp3',
        'mutagen.flac',
        'mutagen.mp4',
        'mutagen.oggvorbis',
        'numpy',
        'numpy.random',
        'numpy.fft',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE配置 - 只有在图标文件存在时才使用图标
exe_kwargs = {
    'pyz': pyz,
    'a': a.scripts,
    'console': [],
    'exclude_binaries': True,
    'name': 'MusicPlayer',
    'debug': False,
    'bootloader_ignore_signals': False,
    'strip': False,
    'upx': True,
    'console': False,
    'disable_windowed_traceback': False,
    'argv_emulation': False,
    'target_arch': None,
    'codesign_identity': None,
    'entitlements_file': None,
}

# 只有图标文件存在时才添加icon参数
if icon_file:
    exe_kwargs['icon'] = icon_file

# 创建EXE对象
exe = EXE(**exe_kwargs)

# macOS app bundle
if sys.platform == 'darwin':
    # macOS直接使用EXE创建BUNDLE
    app = BUNDLE(
        exe,
        name='MusicPlayer.app',
        bundle_identifier='com.rockwave.musicplayer',
        info_plist={
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSAppleEventsUsageDescription': 'MusicPlayer needs to control audio playback.',
        },
        icon=icon_file if icon_file else None,
    )
else:
    # Windows使用COLLECT
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='MusicPlayer',
    )
