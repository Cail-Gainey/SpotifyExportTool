#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
图标转换工具 - 将PNG转换为ICO格式
适用于Windows平台打包

该脚本依赖于Pillow库，若不存在会尝试自动安装
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
        from PIL import Image
        return True
    except ImportError:
        print("正在安装必要的依赖: Pillow...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
            return True
        except Exception as e:
            print(f"安装Pillow失败: {e}")
            print("请手动安装Pillow: pip install Pillow")
            return False

def convert_png_to_ico(png_path, ico_path, sizes=None):
    """
    将PNG图像转换为ICO格式
    
    Args:
        png_path (str): PNG文件路径
        ico_path (str): 输出ICO文件路径
        sizes (list): 图标尺寸列表，默认为[16, 32, 48, 64, 128, 256]
    
    Returns:
        bool: 转换成功返回True，否则返回False
    """
    if not os.path.exists(png_path):
        print(f"错误: 找不到PNG文件: {png_path}")
        return False
    
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    try:
        from PIL import Image
        
        # 打开原始图像
        img = Image.open(png_path)
        icon_images = []
        
        # 创建不同尺寸的图像
        for size in sizes:
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            icon_images.append(resized_img)
        
        # 保存为ICO格式
        icon_images[0].save(
            ico_path, 
            format='ICO', 
            sizes=[(img.width, img.height) for img in icon_images],
            append_images=icon_images[1:]
        )
        return True
    except Exception as e:
        print(f"转换过程中出错: {e}")
        return False

def main():
    """
    主函数，处理命令行参数并执行转换
    """
    # 检查Pillow库
    if not check_pillow():
        return
    
    # 设置默认路径
    png_path = "assets/app_icon.png"
    ico_path = "assets/app_icon.ico"
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        png_path = sys.argv[1]
    if len(sys.argv) > 2:
        ico_path = sys.argv[2]
    
    print(f"正在将 {png_path} 转换为 {ico_path}...")
    
    # 执行转换
    if convert_png_to_ico(png_path, ico_path):
        print(f"转换成功！ICO文件已保存到: {ico_path}")
    else:
        print("转换失败！")
        
if __name__ == "__main__":
    main() 