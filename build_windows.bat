@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo 清理旧的构建文件...
if exist build\windows rmdir /s /q build\windows
if exist dist\windows rmdir /s /q dist\windows

echo 创建必要的目录...
mkdir build\windows
mkdir dist\windows

echo 检查app_icon.png是否存在...
if not exist assets\app_icon.png (
  echo 错误: assets\app_icon.png 不存在!
  exit /b 1
)

echo 正在创建Windows图标文件...
if not exist assets\app_icon.ico (
  echo 使用自动转换工具创建ICO图标...
  python convert_icon_windows.py
  
  if not exist assets\app_icon.ico (
    echo 警告: 自动转换失败，需要手动转换PNG到ICO格式
    echo 提示: 您可以使用在线工具将app_icon.png转换为app_icon.ico
    echo       然后将ico文件放在assets文件夹
    echo 当前将使用默认图标继续打包
  ) else (
    echo ICO图标创建成功！
  )
) else (
  echo ICO图标已存在，直接使用...
)

echo 开始打包Windows版本...
pyinstaller spotify_export.spec --distpath=dist\windows --workpath=build\windows

if %ERRORLEVEL% equ 0 (
  echo Windows版本打包完成！
  echo 程序位于: dist\windows\SpotifyExportTool\SpotifyExportTool.exe
  
  echo 创建安装包...
  echo 注意: 此脚本不会自动创建安装程序
  echo 您可以使用Inno Setup等工具来创建Windows安装程序
  echo 或者直接将dist\windows\SpotifyExportTool文件夹压缩为ZIP文件分发

  echo 创建ZIP归档...
  cd dist\windows
  powershell -Command "Compress-Archive -Path 'SpotifyExportTool' -DestinationPath 'SpotifyExportTool.zip' -Force"
  cd ..\..
  
  if exist dist\windows\SpotifyExportTool.zip (
    echo ZIP归档创建完成: dist\windows\SpotifyExportTool.zip
  ) else (
    echo 创建ZIP归档失败!
  )
) else (
  echo Windows版本打包失败！
  exit /b 1
) 