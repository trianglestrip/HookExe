# 依赖库安装指南

## 快速安装

### 方法1：使用 requirements.txt（推荐）
```bash
pip install -r requirements.txt
```

### 方法2：手动安装
```bash
pip install pillow paddleocr opencv-python psutil pywin32 numpy
```

## 详细说明

### 核心依赖库

| 库名 | 版本要求 | 用途 | 平台支持 |
|------|----------|------|----------|
| `tkinter` | 内置 | GUI界面框架 | 全平台 |
| `Pillow` | >=9.0.0 | 图像处理和截图 | 全平台 |
| `paddleocr` | >=2.6.0 | OCR文字识别引擎 | 全平台 |
| `opencv-python` | >=4.5.0 | 计算机视觉处理 | 全平台 |
| `numpy` | >=1.21.0 | 数值计算和数组处理 | 全平台 |
| `psutil` | >=5.8.0 | 进程管理和监控 | 全平台 |
| `pywin32` | >=305.0 | Windows API调用 | 仅Windows |

### 可选依赖

| 库名 | 用途 | 说明 |
|------|------|------|
| `shapely` | 几何形状处理 | PaddleOCR可能需要 |
| `pyclipper` | 多边形裁剪 | OCR文本区域处理 |
| `requests` | HTTP请求 | 模型下载等 |

## 安装说明

### Windows 系统
```bash
# 1. 更新pip
python -m pip install --upgrade pip

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证安装
python -c "import paddleocr, cv2, PIL, psutil, win32gui; print('所有依赖库安装成功')"
```

### Linux/macOS 系统
```bash
# 1. 更新pip
python3 -m pip install --upgrade pip

# 2. 安装依赖（跳过pywin32）
pip3 install pillow paddleocr opencv-python numpy psutil

# 3. 验证安装
python3 -c "import paddleocr, cv2, PIL, psutil; print('所有依赖库安装成功')"
```

## 常见问题

### 1. PaddleOCR 安装慢
```bash
# 使用国内镜像源
pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. OpenCV 安装失败
```bash
# 尝试安装无GUI版本
pip install opencv-python-headless

# 或者使用conda
conda install opencv
```

### 3. pywin32 安装问题（Windows）
```bash
# 手动安装
pip install pywin32
python Scripts/pywin32_postinstall.py -install
```

### 4. 权限问题
```bash
# 使用用户目录安装
pip install --user -r requirements.txt
```

## 版本兼容性

- **Python版本**：建议 Python 3.7 或以上
- **系统要求**：Windows 10+、Ubuntu 18.04+、macOS 10.14+
- **内存要求**：建议 4GB 以上（OCR模型较大）

## 验证安装

运行以下脚本验证所有功能：

```python
# test_dependencies.py
def test_imports():
    try:
        import tkinter
        print("✓ tkinter - GUI框架")
        
        import PIL
        print("✓ Pillow - 图像处理")
        
        import paddleocr
        print("✓ PaddleOCR - OCR引擎")
        
        import cv2
        print("✓ OpenCV - 计算机视觉")
        
        import numpy
        print("✓ NumPy - 数值计算")
        
        import psutil
        print("✓ psutil - 进程管理")
        
        try:
            import win32gui
            print("✓ pywin32 - Windows API")
        except ImportError:
            print("! pywin32 - 未安装（仅Windows需要）")
        
        print("\n🎉 所有依赖库检查完成！")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请检查依赖库安装")

if __name__ == "__main__":
    test_imports()
```

运行验证：
```bash
python test_dependencies.py
```