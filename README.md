# SpotifyExportTool

SpotifyExportTool是一个跨平台的桌面应用程序，用于管理和导出您的Spotify播放列表和音乐数据。该工具提供了直观的用户界面，让您可以轻松地查看和导出您的Spotify音乐库。

## 功能特性

- **Spotify账号登录与OAuth2授权**：安全的授权流程，无需存储您的Spotify密码
- **查看您的播放列表和收藏的音乐**：直观浏览您的Spotify音乐库
- **多种格式导出播放列表**：支持TXT、CSV等多种格式
- **自定义导出格式**：灵活选择导出内容（歌名-歌手、歌手-歌名、歌名-歌手-专辑等）
- **多语言支持**：内置中文和英文界面，可轻松扩展更多语言
- **缓存机制**：减少API请求次数，提高应用响应速度
- **可调节的日志级别**：方便调试和问题排查
- **现代化界面设计**：支持深色模式，提供舒适的视觉体验
- **跨平台支持**：兼容Mac和Windows系统

## 安装

### 下载预编译版本（推荐）

访问[发布页面](https://github.com/Cail-Gainey/SpotifyExportTool/releases)下载适用于您系统的预编译版本：

- **Mac用户**: 下载`SpotifyExportTool.dmg`文件，打开并拖动到应用程序文件夹
- **Windows用户**: 下载`SpotifyExportTool.zip`，解压后运行`SpotifyExportTool.exe`

### 从源代码运行

1. 克隆代码库：
   ```
   git clone https://github.com/Cail-Gainey/SpotifyExportTool.git
   cd SpotifyExportTool
   ```

2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

3. 运行应用程序：
   ```
   python main.py
   ```

## 打包应用程序

如果您想从源代码构建独立的可执行程序，我们提供了针对Mac和Windows平台的打包脚本。

### Mac平台打包

```bash
# 赋予脚本执行权限
chmod +x build_mac.sh

# 执行打包脚本
./build_mac.sh
```

打包完成后，您可以在`dist/mac`目录中找到应用程序（`.app`）和磁盘镜像（`.dmg`）。

### Windows平台打包

```batch
build_windows_en.bat
```

打包完成后，您可以在`dist/windows`目录中找到可执行文件和ZIP压缩包。

## 目录结构

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
│   ├── tools/            # 工具脚本
│   ├── ui/               # 用户界面模块
│   └── utils/            # 实用工具模块
├── build_mac.sh          # Mac打包脚本
├── build_windows_en.bat  # Windows打包脚本
├── main.py               # 主程序入口
├── README.md             # 项目说明文档
├── USER_GUIDE.md         # 用户指南
├── DEVELOPER_GUIDE.md    # 开发者指南
├── requirements.txt      # 依赖列表
└── spotify_export.spec   # PyInstaller配置文件
```

## 使用方法

### 初次使用

1. 启动应用程序
2. 使用您的Spotify账号登录（需要Spotify账号）
3. 授权应用程序访问您的Spotify数据
4. 登录成功后，您将看到主界面

### 浏览播放列表

1. 在左侧边栏中可以看到您的所有播放列表
2. 点击任意播放列表查看其中的歌曲
3. 播放列表内容会显示在主区域

### 导出播放列表

1. 打开您想要导出的播放列表
2. 点击右上角的"导出"按钮
3. 选择导出格式（TXT或CSV）
4. 选择导出内容格式（歌名-歌手、歌手-歌名等）
5. 选择保存位置
6. 点击"保存"完成导出

### 更改设置

1. 点击右上角的设置图标
2. 在设置页面中可以：
   - 更改语言（中文/英文）
   - 设置默认导出格式
   - 调整日志级别
   - 清理缓存
   - 查看日志文件

## 最近更新

### 2025年5月21日更新
- 改进了错误处理和日志记录
- 添加了详细的用户指南文档
- 添加了开发者指南文档
- 修复了多个问题

## 技术栈

- **Python 3.7+**：核心编程语言
- **PyQt5**：跨平台GUI框架
- **Spotipy**：Spotify API Python客户端
- **Loguru**：高级日志系统
- **PyInstaller**：应用打包工具

## 开发

要设置开发环境，请按照以下步骤操作：

1. 克隆代码库并安装依赖（见上述"从源代码运行"部分）
2. 确保您有一个Spotify开发者账号和API凭据
   - 访问 [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - 创建一个新应用
   - 设置重定向URI为 `http://localhost:8080/login/oauth2/code/spotify`
   - 记下Client ID和Client Secret
3. 在`src/config`目录中创建`config.py`文件，添加您的Spotify API凭据：
   ```python
   CLIENT_ID = "您的Client ID"
   CLIENT_SECRET = "您的Client Secret"
   REDIRECT_URI = "http://localhost:8080/login/oauth2/code/spotify"
   SCOPE = "user-library-read playlist-read-private playlist-read-collaborative"
   ```
4. 使用您喜欢的IDE开始开发

### 注意事项

- 资源文件（图标、语言包等）应放在根目录的相应文件夹中
- 语言文件应遵循JSON格式，并放在`locale`目录中
- 日志文件存储在`log`目录，可通过设置页面查看

## 贡献

我们欢迎各种形式的贡献，包括但不限于：

- 报告问题和提交错误修复
- 提出新功能建议
- 改进文档
- 提交代码改进

### 贡献流程

1. Fork 这个仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

更多详情请参阅[贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用MIT许可证 - 详情请参阅[LICENSE](LICENSE)文件。

## 致谢

- [Spotify Web API](https://developer.spotify.com/documentation/web-api/)
- [PyQt社区](https://www.riverbankcomputing.com/software/pyqt/)
- [Spotipy](https://spotipy.readthedocs.io/)
- 所有项目贡献者

## 联系方式

如有问题或建议，请通过以下方式联系我们：

- 在GitHub上提交[Issue](https://github.com/Cail-Gainey/SpotifyExportTool/issues)
- 发送电子邮件至：[cailgainey@foxmail.com]

---

**SpotifyExportTool** - 让Spotify音乐导出变得简单
