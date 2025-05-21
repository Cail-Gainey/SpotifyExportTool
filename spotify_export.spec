# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import shutil


block_cipher = None


# 获取项目根目录
try:
    # 尝试使用__file__
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
except NameError:
    # 如果__file__未定义，则使用当前工作目录
    ROOT_DIR = os.path.abspath(os.getcwd())


# 设置输出目录
if sys.platform == 'darwin':
    OUTPUT_DIR = os.path.join('dist', 'mac')
else:
    OUTPUT_DIR = os.path.join('dist', 'windows')

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 应用图标路径
if sys.platform == 'darwin':
    icon_file = os.path.join(ROOT_DIR, 'assets', 'app_icon.icns')
else:
    icon_file = os.path.join(ROOT_DIR, 'assets', 'app_icon.ico')


# 创建必要的空目录
log_dir = os.path.join(ROOT_DIR, 'log')
data_dir = os.path.join(ROOT_DIR, 'data')
cache_dir = os.path.join(ROOT_DIR, 'cache')  # 缓存目录在项目根目录下
tracks_cache_dir = os.path.join(cache_dir, 'tracks')
images_cache_dir = os.path.join(cache_dir, 'images')
avatar_cache_dir = os.path.join(images_cache_dir, 'avatars')
playlist_cover_cache_dir = os.path.join(images_cache_dir, 'playlists')
track_cover_cache_dir = os.path.join(images_cache_dir, 'tracks')

# 创建所有必要的目录
os.makedirs(log_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)
os.makedirs(cache_dir, exist_ok=True)
os.makedirs(tracks_cache_dir, exist_ok=True)
os.makedirs(images_cache_dir, exist_ok=True)
os.makedirs(avatar_cache_dir, exist_ok=True)
os.makedirs(playlist_cover_cache_dir, exist_ok=True)
os.makedirs(track_cover_cache_dir, exist_ok=True)

# 创建空的占位文件，确保目录被包含
with open(os.path.join(log_dir, '.keep'), 'w') as f:
    f.write('# 此文件用于确保日志目录被包含在打包中\n')
    
with open(os.path.join(data_dir, '.keep'), 'w') as f:
    f.write('# 此文件用于确保数据目录被包含在打包中\n')

with open(os.path.join(cache_dir, '.keep'), 'w') as f:
    f.write('# 此文件用于确保缓存目录被包含在打包中\n')

with open(os.path.join(playlist_cover_cache_dir, '.keep'), 'w') as f:
    f.write('# 此文件用于确保歌单封面缓存目录被包含在打包中\n')


# 需要包含的数据文件
added_files = [
    # 添加资源文件 - 修改为直接复制到根目录
    ('assets', 'assets'),
    ('data', 'data'),
    ('cache', 'cache'),
    ('log', 'log'),
    ('src/config', 'config'),
    ('locale', 'locale'),  # 从根目录复制语言文件
    ('src/ui', 'ui'),
    ('src/utils', 'utils'),
]


# 确保图标文件存在
if not os.path.exists(icon_file):
    if sys.platform == 'darwin':
        print(f"警告: 图标文件 {icon_file} 不存在，将使用默认图标")
        icon_file = None
    else:
        print(f"警告: 图标文件 {icon_file} 不存在，将使用默认图标")
        icon_file = None


a = Analysis(
    ['main.py'],
    pathex=[ROOT_DIR],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'spotipy',
        'requests',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        # 添加视图模块 - 现在在src.ui下
        'src.ui.sidebar_view',
        'src.ui.error_view',
        'src.ui.loading_view',
        'src.ui.welcome_view',
        'src.ui.playlist_view',
        'src.ui.settings_view',
        'src.ui.topbar_view',
        'src.ui.home_view',
        # 添加工具模块 - 现在在src.utils下
        'src.utils.logger',
        'src.utils.loading_indicator',
        'src.utils.cache_manager',
        'src.utils.time_utils',
        'src.utils.language_manager',
        # 添加其他核心模块
        'src.ui.home',
        'src.ui.login',
        'src.ui.splash',
        'json',
        'datetime',
        'urllib.parse',
        'webbrowser',
        'http.server',
        'socketserver',
        'threading',
        'socket',
        'loguru',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)


pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SpotifyExportTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)


coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SpotifyExportTool',
    noconfirm=True,  # 添加noconfirm选项，自动删除输出目录
)

# 复制打包结果到正确的输出目录
if os.path.exists(os.path.join('dist', 'SpotifyExportTool')):
    # 如果目标目录已存在，先删除
    if os.path.exists(os.path.join(OUTPUT_DIR, 'SpotifyExportTool')):
        shutil.rmtree(os.path.join(OUTPUT_DIR, 'SpotifyExportTool'))
    
    # 确保目标目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 复制打包结果
    shutil.copytree(
        os.path.join('dist', 'SpotifyExportTool'),
        os.path.join(OUTPUT_DIR, 'SpotifyExportTool')
    )
    
    # 确保assets目录存在
    assets_dir = os.path.join(OUTPUT_DIR, 'SpotifyExportTool', 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # 复制资源文件
    src_assets_dir = os.path.join(ROOT_DIR, 'src', 'assets')
    if os.path.exists(src_assets_dir):
        print(f"复制资源文件从 {src_assets_dir} 到 {assets_dir}")
        for file in os.listdir(src_assets_dir):
            src_file = os.path.join(src_assets_dir, file)
            dst_file = os.path.join(assets_dir, file)
            if os.path.isfile(src_file):
                shutil.copy2(src_file, dst_file)
                print(f"已复制: {src_file} -> {dst_file}")
                
                # 同时复制到根目录，确保兼容性
                root_dst_file = os.path.join(OUTPUT_DIR, 'SpotifyExportTool', file)
                shutil.copy2(src_file, root_dst_file)
                print(f"已复制到根目录: {src_file} -> {root_dst_file}")
    
    # 删除原始打包结果
    shutil.rmtree(os.path.join('dist', 'SpotifyExportTool'))


# 为macOS创建应用程序包
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='SpotifyExportTool.app',
        icon=icon_file,
        bundle_identifier='com.cailgainey.spotifyexporttool',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSApplicationCategoryType': 'public.app-category.music',
            'NSPrincipalClass': 'NSApplication',
        },
    )
    
    # 复制Mac应用程序包到正确的输出目录
    if os.path.exists(os.path.join('dist', 'SpotifyExportTool.app')):
        # 如果目标目录已存在，先删除
        if os.path.exists(os.path.join(OUTPUT_DIR, 'SpotifyExportTool.app')):
            shutil.rmtree(os.path.join(OUTPUT_DIR, 'SpotifyExportTool.app'))
        
        # 复制应用程序包
        shutil.copytree(
            os.path.join('dist', 'SpotifyExportTool.app'),
            os.path.join(OUTPUT_DIR, 'SpotifyExportTool.app')
        )
        
        # 删除原始应用程序包
        shutil.rmtree(os.path.join('dist', 'SpotifyExportTool.app')) 
