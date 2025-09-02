"""
核心功能模块包
包含进程管理、截图引擎、OCR引擎等核心功能
"""

# 导入核心模块
from .process_manager import ProcessManager
from .screenshot_engine import ScreenshotEngine
from .ocr_engine import OCREngine, get_default_ocr_engine, recognize_image

__all__ = [
    'ProcessManager',
    'ScreenshotEngine', 
    'OCREngine',
    'get_default_ocr_engine',
    'recognize_image'
]