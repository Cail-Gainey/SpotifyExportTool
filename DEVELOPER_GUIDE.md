# SpotifyExportTool 开发者指南

本文档旨在帮助开发者了解 SpotifyExportTool 的项目结构、代码规范和开发流程，以便能够顺利地参与项目开发。

## 目录

1. [项目概述](#项目概述)
2. [开发环境设置](#开发环境设置)
3. [项目结构](#项目结构)
4. [核心模块说明](#核心模块说明)
5. [UI 组件](#ui-组件)
6. [代码规范](#代码规范)
7. [测试](#测试)
8. [打包流程](#打包流程)
9. [贡献流程](#贡献流程)

## 项目概述

SpotifyExportTool 是一个使用 Python 和 PyQt5 开发的桌面应用程序，用于管理和导出 Spotify 播放列表。项目主要功能包括：

- Spotify OAuth2 授权
- 播放列表浏览和管理
- 多格式导出功能
- 多语言支持
- 缓存机制

技术栈：
- Python 3.7+
- PyQt5 (GUI 框架)
- Spotipy (Spotify API 客户端)
- Loguru (日志系统)
- PyInstaller (应用打包)

## 开发环境设置

### 基础环境

1. 安装 Python 3.7 或更高版本
2. 克隆代码库：
   ```bash
   git clone https://github.com/Cail-Gainey/SpotifyExportTool.git
   cd SpotifyExportTool
   ```
3. 创建虚拟环境（推荐）：
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### Spotify 开发者账号设置

1. 访问 [Spotify 开发者平台](https://developer.spotify.com/dashboard/)
2. 创建一个新应用
3. 设置重定向 URI 为 `http://localhost:8080/login/oauth2/code/spotify`
4. 复制 Client ID 和 Client Secret
5. 创建 `src/config/config.py` 文件（参考 `config.py.example`）：
   ```python
   # Spotify API 配置
   CLIENT_ID = "您的客户端ID"
   CLIENT_SECRET = "您的客户端密钥"
   REDIRECT_URI = "http://localhost:8080/login/oauth2/code/spotify"
   SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"
   ```

### 运行开发版本

```bash
python main.py
```

## 项目结构

```
SpotifyExportTool/
├── assets/               # 应用程序资源文件（图标等）
├── build/                # 构建临时文件
├── cache/                # 缓存目录
│   ├── images/           # 图片缓存
│   └── tracks/           # 歌曲信息缓存
├── config/               # 配置文件
├── data/                 # 数据文件（包括token）
├── dist/                 # 打包输出目录
├── locale/               # 语言文件
│   ├── en_US.json        # 英文语言包
│   └── zh_CN.json        # 中文语言包
├── log/                  # 日志文件
├── src/                  # 源代码
│   ├── config/           # 配置模块
│   │   ├── __init__.py
│   │   ├── config.py     # Spotify API 配置（需自行创建）
│   │   └── settings.py   # 应用程序设置管理
│   ├── tools/            # 工具脚本
│   │   └── convert_icon_windows.py  # 图标转换工具
│   ├── ui/               # 用户界面模块
│   │   ├── __init__.py
│   │   ├── error_view.py         # 错误页面
│   │   ├── home.py              # 主页面容器
│   │   ├── loading_view.py      # 加载页面
│   │   ├── login.py             # 登录页面
│   │   ├── playlist_view.py     # 播放列表页面
│   │   ├── settings_view.py     # 设置页面
│   │   ├── sidebar_view.py      # 侧边栏
│   │   ├── topbar_view.py       # 顶部栏
│   │   └── welcome_view.py      # 欢迎页面
│   └── utils/            # 实用工具模块
│       ├── __init__.py
│       ├── cache_manager.py     # 缓存管理
│       ├── language_manager.py  # 语言管理
│       ├── loading_indicator.py # 加载指示器
│       ├── logger.py            # 日志工具
│       └── time_utils.py        # 时间工具
├── build_mac.sh          # Mac打包脚本
├── build_windows_en.bat  # Windows打包脚本
├── main.py               # 主程序入口
├── README.md             # 项目说明文档
├── requirements.txt      # 依赖列表
└── spotify_export.spec   # PyInstaller配置文件
```

## 核心模块说明

### 主程序入口 (main.py)

主程序入口负责初始化应用程序、检查认证状态，并加载适当的界面（登录或主页）。

### 配置模块 (src/config/)

- **config.py**: 存储 Spotify API 凭据和配置
- **settings.py**: 管理用户设置，包括窗口大小、语言偏好等

### 工具模块 (src/utils/)

- **logger.py**: 使用 Loguru 实现的日志系统
- **cache_manager.py**: 管理播放列表、歌曲和图片缓存
- **language_manager.py**: 多语言支持实现
- **loading_indicator.py**: 加载动画组件
- **time_utils.py**: 时间格式化工具

### UI 模块 (src/ui/)

- **login.py**: 登录窗口和 OAuth2 授权流程
- **home.py**: 主窗口容器，管理侧边栏和内容区域
- **sidebar_view.py**: 侧边栏，显示播放列表列表
- **playlist_view.py**: 播放列表详情和导出功能
- **settings_view.py**: 设置页面
- **topbar_view.py**: 顶部导航栏

## UI 组件

SpotifyExportTool 使用 PyQt5 构建用户界面。主要的 UI 组件包括：

### 主窗口 (HomePage)

主窗口是应用程序的核心容器，包含侧边栏、顶部栏和内容区域。

```python
class HomePage(QMainWindow):
    def __init__(self, token):
        # 初始化主窗口
        # ...
```

### 侧边栏 (SidebarView)

侧边栏显示用户的播放列表，并允许用户选择要查看的播放列表。

```python
class SidebarView(QWidget):
    playlist_selected = pyqtSignal(object)  # 发送选中的播放列表数据
    collapsed_changed = pyqtSignal(bool)    # 侧边栏折叠状态变化信号
    # ...
```

### 播放列表视图 (PlaylistView)

播放列表视图显示选定播放列表的歌曲，并提供导出功能。

```python
class PlaylistView(QWidget):
    def __init__(self, sp, playlist_data, parent=None, language_manager=None, cache_manager=None):
        # 初始化播放列表视图
        # ...
```

### 设置视图 (SettingsView)

设置视图允许用户配置应用程序设置，如语言、导出格式等。

```python
class SettingsView(QWidget):
    def __init__(self, parent=None):
        # 初始化设置视图
        # ...
```

## 代码规范

### 命名约定

- **类名**: 使用 PascalCase (例如: `PlaylistView`)
- **方法和函数**: 使用 snake_case (例如: `load_playlists`)
- **变量**: 使用 snake_case (例如: `playlist_items`)
- **常量**: 使用大写 SNAKE_CASE (例如: `CLIENT_ID`)
- **私有方法和变量**: 使用下划线前缀 (例如: `_load_translations`)

### 文档字符串

使用 Google 风格的文档字符串：

```python
def function_name(param1, param2):
    """函数简短描述。

    更详细的函数描述。

    Args:
        param1: 第一个参数的描述。
        param2: 第二个参数的描述。

    Returns:
        返回值的描述。

    Raises:
        ValueError: 异常的描述。
    """
    # 函数实现
```

### 导入顺序

1. 标准库导入
2. 相关第三方导入
3. 本地应用/库特定导入

例如：

```python
# 标准库
import os
import json
import sys

# 第三方库
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

# 本地模块
from src.utils.logger import logger
from src.config import settings
```

## 测试

目前项目没有自动化测试。计划添加单元测试和集成测试。

## 打包流程

### Windows 打包

使用 `build_windows_en.bat` 脚本打包 Windows 版本：

```batch
build_windows_en.bat
```

脚本会执行以下操作：
1. 清理旧的构建文件
2. 检查应用图标
3. 使用 PyInstaller 打包应用程序
4. 复制资源文件到输出目录
5. 创建 ZIP 压缩包

### Mac 打包

使用 `build_mac.sh` 脚本打包 Mac 版本：

```bash
chmod +x build_mac.sh
./build_mac.sh
```

脚本会执行以下操作：
1. 清理旧的构建文件
2. 检查应用图标
3. 使用 PyInstaller 打包应用程序
4. 创建 .app 应用程序包
5. 创建 DMG 磁盘镜像

### PyInstaller 配置

打包配置在 `spotify_export.spec` 文件中定义，包括：
- 应用程序名称和图标
- 隐藏导入模块
- 数据文件
- 输出选项

## 贡献流程

### 提交 Pull Request

1. Fork 项目仓库
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 提交更改：`git commit -am 'Add some feature'`
4. 推送到分支：`git push origin feature/your-feature-name`
5. 提交 Pull Request

### 代码审查标准

- 代码应符合上述代码规范
- 新功能应包含适当的文档
- 不应引入新的警告或错误
- UI 更改应保持一致的设计风格
- 性能敏感的代码应注意效率

### 版本控制

项目使用语义化版本控制：

- **主版本号**：不兼容的 API 更改
- **次版本号**：向后兼容的功能性新增
- **修订号**：向后兼容的问题修正

## 常见开发问题

### Q: 如何添加新的语言支持？

A: 在 `locale` 目录中创建新的语言文件（例如 `fr_FR.json`），并在 `language_manager.py` 中更新 `supported_languages` 列表。

### Q: 如何添加新的导出格式？

A: 修改 `playlist_view.py` 中的 `export_playlist` 方法，添加新的格式处理逻辑。

### Q: 如何调试 OAuth 授权流程？

A: 设置日志级别为 "debug"，查看详细的授权流程日志。可以在 `login.py` 中添加额外的日志语句。

---

如有任何问题或建议，请联系项目维护者或提交 Issue。 