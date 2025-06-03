# SpotifyExportTool

SpotifyExportTool 是一个跨平台的桌面应用程序，用于管理和导出您的 Spotify 播放列表和音乐数据。该工具提供了直观的用户界面，让您可以轻松地查看和导出您的 Spotify 音乐库。

## 功能特性

- **Spotify 账号登录与 OAuth2 授权**：安全的授权流程，无需存储您的 Spotify 密码
- **查看您的播放列表和收藏的音乐**：直观浏览您的 Spotify 音乐库
- **多种格式导出播放列表**：支持 TXT、CSV 等多种格式
- **自定义导出格式**：灵活选择导出内容（歌名-歌手、歌手-歌名、歌名-歌手-专辑等）
- **多语言支持**：内置中文和英文界面，可轻松扩展更多语言
- **缓存机制**：减少 API 请求次数，提高应用响应速度
- **可调节的日志级别**：方便调试和问题排查
- **现代化界面设计**：支持深色模式，提供舒适的视觉体验
- **跨平台支持**：兼容 Mac 和 Windows 系统

## 目录结构

```
SpotifyExportTool/
├── assets/               # 应用程序资源文件（图标等）
├── cache/                # 缓存目录
│   ├── images/           # 图片缓存
│   └── tracks/           # 歌曲信息缓存
├── config/               # 配置文件
├── data/                 # 数据文件（包括 token）
├── dist/                 # 打包输出目录
├── locale/               # 语言文件
│   ├── en_US.json        # 英文语言包
│   └── zh_CN.json        # 中文语言包
├── log/                  # 日志文件
├── src/                  # 源代码
│   ├── config/           # 配置模块
│   ├── exporters/        # 导出器模块
│   ├── tools/            # 工具脚本
│   ├── ui/               # 用户界面模块
│   │   ├── home.py       # 主页视图
│   │   ├── login.py      # 登录视图
│   │   ├── sidebar_view.py  # 侧边栏视图
│   │   └── ...           # 其他 UI 组件
│   └── utils/            # 实用工具模块
│       ├── cache_manager.py  # 缓存管理
│       ├── logger.py     # 日志系统
│       └── ...           # 其他工具
├── main.py               # 主程序入口
└── requirements.txt      # 依赖列表
```

## 安装与运行

### 依赖要求

- Python 3.7+
- PyQt5
- Spotipy
- Loguru

### 开发环境设置

1. 克隆仓库
```bash
git clone https://github.com/Cail-Gainey/SpotifyExportTool.git
cd SpotifyExportTool
```

2. 创建虚拟环境（可选但推荐）
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate    # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 运行应用
```bash
python main.py
```

## 打包应用

### Windows
```bash
pyinstaller spotify_export.spec
```

### macOS
```bash
pyinstaller spotify_export.spec
```

## 贡献指南

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '添加一些令人惊叹的特性'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

## 许可证

MIT 许可证 - 详情请参阅 LICENSE 文件。

## 联系方式

- GitHub Issues: [提交问题](https://github.com/Cail-Gainey/SpotifyExportTool/issues)
- 邮箱: cailgainey@foxmail.com

## 技术栈

- Python 3.7+
- PyQt5
- Spotipy
- Loguru
- PyInstaller

---

**SpotifyExportTool** - 让 Spotify 音乐导出变得简单！