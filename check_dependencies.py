#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖库验证脚本
检查OCR截图工具所需的所有依赖库是否正确安装
"""

import sys
import importlib
import platform

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    print(f"Python版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python版本过低，建议使用Python 3.7或以上版本")
        return False
    else:
        print("✓ Python版本符合要求")
        return True

def check_library(name, package=None, description=""):
    """检查单个库是否可用"""
    try:
        if package:
            importlib.import_module(package)
        else:
            importlib.import_module(name)
        
        print(f"✓ {name:<15} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {name:<15} - {description} (导入失败: {e})")
        return False
    except Exception as e:
        print(f"⚠️ {name:<15} - {description} (其他错误: {e})")
        return False

def check_optional_library(name, package=None, description="", reason=""):
    """检查可选库"""
    try:
        if package:
            importlib.import_module(package)
        else:
            importlib.import_module(name)
        
        print(f"✓ {name:<15} - {description}")
        return True
    except ImportError:
        print(f"! {name:<15} - {description} ({reason})")
        return False

def check_specific_functions():
    """检查特定功能是否可用"""
    print("\n=== 功能验证 ===")
    
    # 检查tkinter GUI
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        root.destroy()
        print("✓ tkinter GUI - 可以创建窗口")
    except Exception as e:
        print(f"❌ tkinter GUI - 创建窗口失败: {e}")
    
    # 检查OCR引擎
    try:
        from paddleocr import PaddleOCR
        print("✓ PaddleOCR - 可以导入OCR引擎")
    except Exception as e:
        print(f"❌ PaddleOCR - OCR引擎导入失败: {e}")
    
    # 检查图像处理
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np
        # 创建测试图像
        img = Image.new('RGB', (100, 100), color='white')
        arr = np.array(img)
        print("✓ 图像处理 - PIL和NumPy协作正常")
    except Exception as e:
        print(f"❌ 图像处理 - PIL/NumPy协作失败: {e}")
    
    # 检查OpenCV
    try:
        import cv2
        # 测试基本功能
        version = getattr(cv2, '__version__', '未知版本')
        print(f"✓ OpenCV - 版本 {version}")
    except Exception as e:
        print(f"❌ OpenCV - 功能测试失败: {e}")

def check_system_specific():
    """检查系统特定的库"""
    system = platform.system()
    print(f"\n=== 系统特定库检查 ({system}) ===")
    
    if system == "Windows":
        # Windows特定库
        check_library("pywin32", "win32gui", "Windows API调用")
        check_library("win32process", "win32process", "进程管理API")
        check_library("win32con", "win32con", "Windows常量")
        check_library("win32api", "win32api", "Windows基础API")
    else:
        print("! pywin32相关库 - 非Windows系统，跳过检查")

def main():
    """主函数"""
    print("OCR截图工具 - 依赖库验证")
    print("=" * 50)
    
    # 检查Python版本
    if not check_python_version():
        print("\n⚠️ 建议升级Python版本后重新运行")
    
    print("\n=== 核心依赖库检查 ===")
    
    # 核心库检查
    required_libs = [
        ("tkinter", None, "GUI界面框架"),
        ("PIL", "PIL", "图像处理库"),
        ("paddleocr", "paddleocr", "OCR文字识别"),
        ("cv2", "cv2", "计算机视觉库"),
        ("numpy", "numpy", "数值计算库"),
        ("psutil", "psutil", "进程管理库"),
    ]
    
    success_count = 0
    total_count = len(required_libs)
    
    for name, package, desc in required_libs:
        if check_library(name, package, desc):
            success_count += 1
    
    # 系统特定库
    check_system_specific()
    
    print("\n=== 可选依赖库检查 ===")
    
    # 可选库检查
    optional_libs = [
        ("shapely", "shapely", "几何形状处理", "PaddleOCR可能需要"),
        ("pyclipper", "pyclipper", "多边形裁剪", "OCR区域处理"),
        ("requests", "requests", "HTTP请求库", "模型下载"),
        ("threading", "threading", "多线程支持", "Python内置"),
    ]
    
    for name, package, desc, reason in optional_libs:
        check_optional_library(name, package, desc, reason)
    
    # 功能验证
    check_specific_functions()
    
    # 总结
    print("\n" + "=" * 50)
    print(f"核心库检查结果: {success_count}/{total_count} 通过")
    
    if success_count == total_count:
        print("🎉 所有核心依赖库安装正确，可以运行OCR截图工具！")
        print("\n启动命令:")
        print("  python process_capture.py")
    else:
        print("❌ 部分依赖库缺失，请参考以下安装命令:")
        print("\n安装命令:")
        print("  pip install -r requirements.txt")
        print("  或者:")
        print("  pip install pillow paddleocr opencv-python psutil pywin32 numpy")
    
    print("\n详细安装指南请查看 INSTALL.md 文件")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断检查")
    except Exception as e:
        print(f"\n\n检查过程中出现错误: {e}")
        print("请确保在正确的Python环境中运行此脚本")