#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DMG背景图生成工具

该脚本用于为Mac DMG安装界面创建自定义背景图像，
显示应用图标、箭头和"拖拽到Applications文件夹"的提示。
"""

import os
import sys
import subprocess

def check_pillow():
    """
    检查Pillow库是否已安装，若未安装则尝试安装
    
    Returns:
        bool: 安装成功返回True，否则返回False
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        return True
    except ImportError:
        print("正在安装必要的依赖: Pillow...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            return True
        except Exception as e:
            print("安装Pillow失败: {}".format(e))
            print("请手动安装Pillow: pip install Pillow")
            return False

def ensure_dir_exists(path):
    """
    确保目录存在，支持旧版本Python
    
    Args:
        path: 目录路径
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except Exception as e:
            print("创建目录失败: {}".format(e))

def create_dmg_background():
    """
    创建DMG背景图像
    """
    # 检查Pillow是否已安装
    if not check_pillow():
        return False
        
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # 设置固定的背景图尺寸 - 这与在AppleScript中设置的窗口大小相匹配
        width, height = 500, 350  # 保持与之前相同的尺寸
        bg_color = (40, 40, 40)  # 深灰色背景
        
        # 创建新图像
        background = Image.new('RGBA', (width, height), bg_color)
        draw = ImageDraw.Draw(background)
        
        # DMG实际窗口中定位图标的准确位置
        # AppleScript中设置的图标位置是{125, 175}和{375, 175}
        # 这些坐标是相对于DMG窗口左上角的
        app_icon_center_x = 125
        app_icon_center_y = 175
        applications_icon_center_x = 375
        applications_icon_center_y = 175
        
        # 尝试加载应用图标
        icon_path = os.path.join("assets", "app_icon.png")
        app_icon = None
        if os.path.exists(icon_path):
            try:
                app_icon = Image.open(icon_path).convert("RGBA")
                # 调整图标大小
                icon_size = 96
                app_icon = app_icon.resize((icon_size, icon_size), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)
            except Exception as e:
                print("加载应用图标失败: {}".format(e))
        
        # 尝试加载应用商店图标
        app_store_icon = None
        applications_icon_path = os.path.join("assets", "applications_folder.png")
        if os.path.exists(applications_icon_path):
            try:
                app_store_icon = Image.open(applications_icon_path).convert("RGBA")
                icon_size = 96
                app_store_icon = app_store_icon.resize((icon_size, icon_size), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)
            except Exception as e:
                print("加载Applications图标失败: {}".format(e))
        
        # 如果没有Applications图标，创建一个简单的替代品
        if app_store_icon is None:
            icon_size = 96
            app_store_icon = Image.new('RGBA', (icon_size, icon_size), (75, 75, 75, 230))
            app_store_draw = ImageDraw.Draw(app_store_icon)
            app_store_draw.rectangle([(10, 10), (icon_size-10, icon_size-10)], outline=(200, 200, 200), width=2)
            try:
                # 尝试使用系统字体，如果不可用则使用默认
                font = ImageFont.truetype("Arial", 12)
                app_store_draw.text((icon_size//2-36, icon_size//2), "Applications", fill=(240, 240, 240), font=font)
            except:
                app_store_draw.text((icon_size//2-36, icon_size//2), "Applications", fill=(240, 240, 240))
        
        # 绘制图标
        if app_icon:
            # 应用图标位置：以图标中心点来定位
            icon_x = app_icon_center_x - icon_size//2
            icon_y = app_icon_center_y - icon_size//2
            background.paste(app_icon, (icon_x, icon_y), app_icon if app_icon.mode == 'RGBA' else None)
        
        if app_store_icon:
            # 应用商店图标位置：以图标中心点来定位
            store_x = applications_icon_center_x - icon_size//2
            store_y = applications_icon_center_y - icon_size//2
            background.paste(app_store_icon, (store_x, store_y), app_store_icon if app_store_icon.mode == 'RGBA' else None)
        
        # 绘制箭头
        arrow_color = (29, 185, 84)  # Spotify绿色
        arrow_width = 120  # 略微减小箭头宽度
        arrow_height = 30
        arrow_x = width // 2 - arrow_width // 2  # 水平居中
        arrow_y = height // 2 - arrow_height // 2  # 垂直居中
        
        # 绘制箭头线
        line_width = 6
        draw.line(
            [(arrow_x, arrow_y + arrow_height // 2), 
             (arrow_x + arrow_width, arrow_y + arrow_height // 2)], 
            fill=arrow_color, width=line_width
        )
        
        # 绘制箭头头部
        arrow_head_length = 20
        arrow_head_width = 16
        draw.polygon(
            [(arrow_x + arrow_width, arrow_y + arrow_height // 2),  # 箭头尖
             (arrow_x + arrow_width - arrow_head_length, arrow_y + arrow_height // 2 - arrow_head_width // 2),  # 上角
             (arrow_x + arrow_width - arrow_head_length, arrow_y + arrow_height // 2 + arrow_head_width // 2)],  # 下角
            fill=arrow_color
        )
        
        # 添加提示文字
        text_color = (220, 220, 220)  # 浅灰色文字
        try:
            # 尝试使用系统字体，如果不可用则使用默认
            font = ImageFont.truetype("Arial", 16)
            # 检查是否支持anchor参数
            if hasattr(draw, 'textbbox'):
                draw.text((width // 2, height // 2 + 70), "拖拽到Applications安装", fill=text_color, font=font, anchor="mm")
                # 应用名称
                font_title = ImageFont.truetype("Arial", 24)
                draw.text((width // 2, 40), "SpotifyExportTool", fill=(29, 185, 84), font=font_title, anchor="mm")
            else:
                # 不支持anchor参数的旧版本PIL
                text_width = font.getsize("拖拽到Applications安装")[0]
                draw.text((width // 2 - text_width // 2, height // 2 + 70), "拖拽到Applications安装", fill=text_color, font=font)
                # 应用名称
                font_title = ImageFont.truetype("Arial", 24)
                title_width = font_title.getsize("SpotifyExportTool")[0]
                draw.text((width // 2 - title_width // 2, 40), "SpotifyExportTool", fill=(29, 185, 84), font=font_title)
        except:
            # 如果无法加载字体，使用默认
            draw.text((width // 2 - 70, height // 2 + 70), "拖拽到Applications安装", fill=text_color)
            draw.text((width // 2 - 70, 40), "SpotifyExportTool", fill=(29, 185, 84))
        
        # 保存背景图
        output_dir = os.path.join("assets")
        ensure_dir_exists(output_dir)
        output_path = os.path.join(output_dir, "dmg_background.png")
        background.save(output_path)
        
        print("DMG背景图创建成功: {}".format(output_path))
        return True
    except Exception as e:
        print("创建DMG背景图失败: {}".format(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_dmg_background() 