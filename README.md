# SpotifyExportTool

SpotifyExportTool是一个跨平台的桌面应用程序，用于管理和导出您的Spotify播放列表和音乐数据。

## 功能特性

- Spotify账号登录与授权
- 查看您的播放列表和收藏的音乐
- 导出播放列表到CSV文件
- 现代化界面设计
- 跨平台支持（Mac和Windows）

## 安装

### 下载预编译版本（推荐）

访问[发布页面](https://github.com/yourusername/spotify_export/releases)下载适用于您系统的预编译版本：

- **Mac用户**: 下载`SpotifyExportTool.dmg`文件，打开并拖动到应用程序文件夹
- **Windows用户**: 下载`SpotifyExportTool.zip`，解压后运行`SpotifyExportTool.exe`

### 从源代码运行

1. 克隆代码库：
   ```
   git clone https://github.com/yourusername/spotify_export.git
   cd spotify_export
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
build_windows.bat
```

打包完成后，您可以在`dist/windows`目录中找到可执行文件和ZIP压缩包。

详细的打包说明请参阅[打包文档](README_packaging.md)。

## 使用方法

1. 启动应用程序
2. 使用您的Spotify账号登录
3. 浏览您的播放列表和音乐库
4. 使用导出按钮将选定的播放列表导出到CSV文件

## 技术栈

- Python 3.7+
- PyQt5（界面框架）
- Spotipy（Spotify API客户端）
- PyInstaller（应用打包）

## 开发

要设置开发环境，请按照以下步骤操作：

1. 克隆代码库并安装依赖（见上述"从源代码运行"部分）
2. 确保您有一个Spotify开发者账号和API凭据
3. 创建配置文件（详见`config/`目录）
4. 使用您喜欢的IDE开始开发

## 贡献

欢迎提交问题和合并请求！如果您想为项目做出贡献，请先查看[贡献指南](CONTRIBUTING.md)。

## 许可证

本项目采用MIT许可证 - 详情请参阅[LICENSE](LICENSE)文件。

## 致谢

- Spotify Web API
- PyQt社区
- 所有项目贡献者 