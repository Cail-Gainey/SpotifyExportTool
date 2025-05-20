# SpotifyExportTool 打包工具

本目录包含用于将SpotifyExportTool打包为独立应用程序的脚本和工具。

## 快速启动

如果要为当前平台打包应用程序，请参考以下说明：

### Mac平台

```bash
# 赋予脚本执行权限
chmod +x ../build_mac.sh

# 执行打包脚本
../build_mac.sh
```

### Windows平台

```batch
# 执行打包脚本
..\build_windows.bat
```

## 详细说明

有关打包过程的详细说明，请参阅项目根目录中的`README_packaging.md`文件。

## 打包后的文件

打包完成后，生成的文件将位于：

- **Mac版本**：`../dist/mac/SpotifyExportTool.app`和`../dist/mac/SpotifyExportTool.dmg`
- **Windows版本**：`../dist/windows/SpotifyExportTool`文件夹和`../dist/windows/SpotifyExportTool.zip` 