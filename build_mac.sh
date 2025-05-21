#!/bin/bash

# 确保工作目录是项目根目录
cd "$(dirname "$0")"

# 清理旧的构建文件 (只清理DMG相关)
echo "清理旧的DMG构建文件..."
rm -f dist/mac/SpotifyExportTool.dmg
rm -rf dist/mac/dmg_build

# 创建必要的目录
mkdir -p dist/mac # 确保dist/mac目录存在

# 检查app_icon.png是否存在 (背景图和图标仍需)
if [ ! -f src/assets/app_icon.png ]; then
  echo "错误: src/assets/app_icon.png 不存在!"
  exit 1
fi

# 检查 SpotifyExportTool.app 是否存在
APP_PATH="dist/mac/SpotifyExportTool.app"
if [ ! -d "$APP_PATH" ]; then
  echo "$APP_PATH 不存在，将使用 PyInstaller 生成..."
else
  echo "使用已存在的 $APP_PATH 进行DMG打包。"
fi

# 创建DMG背景图像
echo "正在创建DMG背景图像..."
python3 src/tools/create_dmg_background.py

# 创建src/assets/app_icon.icns (Mac图标)
echo "正在创建Mac图标文件..."
ICONDIR="build/mac/AppIcon.iconset"
mkdir -p "$ICONDIR"

# 生成不同尺寸的图标
sips -z 16 16     src/assets/app_icon.png --out "$ICONDIR/icon_16x16.png"
sips -z 32 32     src/assets/app_icon.png --out "$ICONDIR/icon_16x16@2x.png"
sips -z 32 32     src/assets/app_icon.png --out "$ICONDIR/icon_32x32.png"
sips -z 64 64     src/assets/app_icon.png --out "$ICONDIR/icon_32x32@2x.png"
sips -z 128 128   src/assets/app_icon.png --out "$ICONDIR/icon_128x128.png"
sips -z 256 256   src/assets/app_icon.png --out "$ICONDIR/icon_128x128@2x.png"
sips -z 256 256   src/assets/app_icon.png --out "$ICONDIR/icon_256x256.png"
sips -z 512 512   src/assets/app_icon.png --out "$ICONDIR/icon_256x256@2x.png"
sips -z 512 512   src/assets/app_icon.png --out "$ICONDIR/icon_512x512.png"
sips -z 1024 1024 src/assets/app_icon.png --out "$ICONDIR/icon_512x512@2x.png"

# 转换为.icns格式
iconutil -c icns -o "src/assets/app_icon.icns" "$ICONDIR"

# 清理临时目录
rm -rf "$ICONDIR"

# 使用PyInstaller打包应用
echo "开始打包Mac版本..."
pyinstaller spotify_export.spec --distpath=dist/mac --workpath=build/mac --noconfirm

if [ $? -eq 0 ]; then
    echo "Mac应用包创建成功，开始进行DMG打包。"
    
    # 确保资源文件被正确复制
    echo "确保资源文件被正确复制..."
    
    # 确保应用程序包中的资源目录存在
    RESOURCES_DIR="$APP_PATH/Contents/Resources"
    mkdir -p "$RESOURCES_DIR"
    
    # 复制图标文件到根目录和资源目录
    echo "复制图标文件到资源目录..."
    cp src/assets/app_icon.png "$APP_PATH/Contents/MacOS/"
    cp src/assets/app_icon.icns "$RESOURCES_DIR/"
    
    # 复制SVG图标文件
    echo "复制SVG图标文件..."
    cp src/assets/*.svg "$APP_PATH/Contents/MacOS/"
    
    # 确保assets目录存在
    mkdir -p "$APP_PATH/Contents/MacOS/assets"
    
    # 复制所有资源文件到assets目录
    echo "复制所有资源文件到assets目录..."
    cp src/assets/*.* "$APP_PATH/Contents/MacOS/assets/"
    
    # 创建DMG镜像（添加拖拽安装功能）
    echo "正在创建DMG镜像..."

    # 创建dmg构建目录
    DMG_DIR="dist/mac/dmg_build"
    mkdir -p "$DMG_DIR"

    # 复制.app文件到构建目录
    cp -R "$APP_PATH" "$DMG_DIR/"

    # 创建一个指向Applications文件夹的链接
    ln -s /Applications "$DMG_DIR/Applications"

    # 如果我们已经成功创建了背景图像，则使用自定义的DMG
    if [ -f "src/assets/dmg_background.png" ]; then
        echo "检测到DMG背景图，创建自定义DMG..."
        
        # 显示背景图信息
        echo "背景图路径: src/assets/dmg_background.png"
        ls -la src/assets/dmg_background.png
        
        # 创建DMG背景图像目录
        mkdir -p "$DMG_DIR/.background"
        cp "src/assets/dmg_background.png" "$DMG_DIR/.background/background.png"
        echo "已将背景图复制到: $DMG_DIR/.background/background.png"
        ls -la "$DMG_DIR/.background/background.png"
        
        # 获取背景图尺寸
        BG_WIDTH=$(sips -g pixelWidth src/assets/dmg_background.png | grep pixelWidth | awk '{print $2}')
        BG_HEIGHT=$(sips -g pixelHeight src/assets/dmg_background.png | grep pixelHeight | awk '{print $2}')
        echo "背景图尺寸: ${BG_WIDTH}x${BG_HEIGHT}"
        
        # 设置DMG窗口尺寸和位置
        WINDOW_WIDTH=$BG_WIDTH
        WINDOW_HEIGHT=$BG_HEIGHT
        WINDOW_LEFT=400
        WINDOW_TOP=100
        
        # 创建临时DMG文件
        TEMP_DMG="dist/mac/temp.dmg"
        FINAL_DMG="dist/mac/SpotifyExportTool.dmg"
        
        # 创建临时可写入的DMG
        echo "创建临时DMG: $TEMP_DMG"
        hdiutil create -volname "SpotifyExportTool" \
                       -srcfolder "$DMG_DIR" \
                       -ov \
                       -format UDRW \
                       "$TEMP_DMG"
        
        # 挂载DMG以设置外观
        echo "挂载DMG并配置外观..."
        MOUNT_OUTPUT=$(hdiutil attach -readwrite -noverify -noautoopen "$TEMP_DMG")
        echo "挂载输出: $MOUNT_OUTPUT"
        
        # 从挂载输出中提取设备和挂载点
        DEVICE=$(echo "$MOUNT_OUTPUT" | egrep '^/dev/' | sed 1q | awk '{print $1}')
        MOUNT_POINT=$(echo "$MOUNT_OUTPUT" | tail -1 | awk '{print $3}')
        
        echo "挂载设备: $DEVICE"
        echo "挂载点: $MOUNT_POINT"
        
        # 如果挂载点为空或没有获取到，尝试其他方法
        if [ -z "$MOUNT_POINT" ] || [ "$MOUNT_POINT" = "" ]; then
            echo "尝试使用其他方法获取挂载点..."
            MOUNT_POINT=$(diskutil info "$DEVICE" | grep "Mount Point" | awk -F':' '{print $2}' | xargs)
            echo "新的挂载点: $MOUNT_POINT"
        fi
        
        # 确保.background目录存在
        if [ -n "$MOUNT_POINT" ]; then
            BACKGROUND_DIR="$MOUNT_POINT/.background"
            echo "检查挂载点下的.background目录: $BACKGROUND_DIR"
            
            if [ ! -d "$BACKGROUND_DIR" ]; then
                echo "创建.background目录"
                mkdir -p "$BACKGROUND_DIR"
                cp "src/assets/dmg_background.png" "$BACKGROUND_DIR/background.png"
                echo "已复制背景图到: $BACKGROUND_DIR/background.png"
            fi
            
            if [ -d "$BACKGROUND_DIR" ]; then
                ls -la "$BACKGROUND_DIR" || echo ".background目录访问失败"
            fi
            
            # 设置DMG窗口外观
            echo "执行AppleScript设置DMG外观..."
            osascript -e "
            tell application \"Finder\"
              tell disk \"SpotifyExportTool\"
                open
                set current view of container window to icon view
                set toolbar visible of container window to false
                set statusbar visible of container window to false
                
                -- 设置窗口大小和位置
                set the bounds of container window to {$WINDOW_LEFT, $WINDOW_TOP, $((WINDOW_LEFT + WINDOW_WIDTH)), $((WINDOW_TOP + WINDOW_HEIGHT))}
                
                -- 设置图标视图选项
                set theViewOptions to the icon view options of container window
                set arrangement of theViewOptions to not arranged
                set icon size of theViewOptions to 80
                set text size of theViewOptions to 12
                set shows item info of theViewOptions to false
                set shows icon preview of theViewOptions to true
                
                -- 设置背景图片
                set background picture of theViewOptions to file \".background:background.png\"
                
                -- 设置图标位置
                set position of item \"SpotifyExportTool.app\" of container window to {125, 175}
                set position of item \"Applications\" of container window to {375, 175}
                
                update without registering applications
                delay 3
                
                close
              end tell
            end tell
            " || echo "警告: AppleScript执行可能有错误，但将继续处理"
            
            # 等待Finder完成
            echo "等待Finder完成操作..."
            sleep 3
        else
            echo "警告: 无法确定挂载点，DMG背景可能不会显示"
        fi
        
        # 卸载DMG
        if [ -n "$DEVICE" ]; then
            echo "卸载DMG: $DEVICE"
            hdiutil detach "$DEVICE" -force
        else
            echo "警告: 无法确定挂载设备，跳过卸载步骤"
        fi
        
        # 压缩DMG
        echo "压缩DMG为最终文件: $FINAL_DMG"
        hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$FINAL_DMG"
        
        # 清理临时文件
        echo "清理临时文件..."
        rm -f "$TEMP_DMG"
        
        echo "DMG创建完成，总结:"
        echo "- 背景图: src/assets/dmg_background.png (${BG_WIDTH}x${BG_HEIGHT})"
        echo "- 最终DMG: $FINAL_DMG"
        ls -la "$FINAL_DMG"
    else
        # 创建简单版本的DMG，不自定义外观
        echo "创建简单版本的DMG文件..."
        FINAL_DMG="dist/mac/SpotifyExportTool.dmg"
        
        # 创建压缩的DMG
        hdiutil create -volname "SpotifyExportTool" \
                       -srcfolder "$DMG_DIR" \
                       -ov \
                       -format UDZO \
                       "$FINAL_DMG"
    fi

    # 清理临时文件
    rm -rf "$DMG_DIR"

    echo "DMG镜像创建完成: $FINAL_DMG"

    # 为了确保权限正确，设置DMG文件权限
    chmod 644 "$FINAL_DMG"

    echo "提示: 如果DMG文件无法打开，可以直接使用应用程序文件夹中的SpotifyExportTool.app"
    echo "      可以尝试运行: open dist/mac/SpotifyExportTool.app"
else
    echo "Mac版本打包失败！"
    exit 1
fi 