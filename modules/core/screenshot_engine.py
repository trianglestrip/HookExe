"""
截图引擎模块
功能：窗口截图、多种截图方法、黑色图像检测
"""

import win32gui
import win32ui
import win32con
from PIL import Image, ImageGrab
import numpy as np
import time
from typing import Optional, Dict, Any

class ScreenshotEngine:
    """截图引擎类"""
    
    def __init__(self, logger=None):
        """初始化截图引擎
        
        Args:
            logger: 日志记录器实例
        """
        self.logger = logger
    
    def log_message(self, message: str, level: str = "INFO"):
        """记录日志消息"""
        if self.logger:
            self.logger.log_message(message, level)
        else:
            print(f"[{level}] {message}")
    
    def capture_window_standard(self, rect: tuple) -> Optional[Image.Image]:
        """标准截图方法
        
        Args:
            rect: 窗口矩形 (left, top, right, bottom)
            
        Returns:
            截图图像或None
        """
        try:
            left, top, right, bottom = rect
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            self.log_message(f"标准截图完成，尺寸: {right-left}x{bottom-top}")
            return screenshot
        except Exception as e:
            self.log_message(f"标准截图失败: {e}", "ERROR")
            return None
    
    def capture_window_by_handle(self, hwnd) -> Optional[Image.Image]:
        """通过窗口句柄截图
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            截图图像或None
        """
        try:
            # 获取窗口设备上下文
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 获取窗口大小
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # 创建位图
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 复制窗口内容到位图
            result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            if result:
                # 获取位图数据
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                
                # 创建PIL图像
                im = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
                
                # 清理资源
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
                
                self.log_message(f"窗口句柄截图完成，尺寸: {width}x{height}")
                return im
            else:
                # 清理资源
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
                return None
                
        except Exception as e:
            self.log_message(f"窗口句柄截图失败: {e}", "ERROR")
            return None
    
    def is_black_image(self, image: Image.Image, threshold: int = 10) -> bool:
        """检查图像是否为黑色或接近黑色
        
        Args:
            image: PIL图像
            threshold: 亮度阈值
            
        Returns:
            是否为黑色图像
        """
        try:
            # 转换为numpy数组
            img_array = np.array(image)
            # 计算平均亮度
            avg_brightness = np.mean(img_array)
            # 如果平均亮度低于阈值，认为是黑色图像
            is_black = avg_brightness < threshold
            
            if is_black:
                self.log_message(f"检测到黑色图像，平均亮度: {avg_brightness:.1f}")
            
            return bool(is_black)
        except Exception as e:
            self.log_message(f"黑色图像检测失败: {e}", "ERROR")
            return False
    
    def capture_window_background(self, hwnd) -> Optional[Image.Image]:
        """后台截图方法（不激活窗口）
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            截图图像或None
        """
        try:
            # 检查窗口是否最小化
            if win32gui.IsIconic(hwnd):
                self.log_message("目标窗口已最小化，后台截图可能失败")
                # 尝试后台恢复窗口（不激活）
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
                time.sleep(0.5)  # 等待窗口恢复
            
            # 使用窗口句柄直接截图（不改变窗口状态）
            screenshot = self.capture_window_by_handle(hwnd)
            
            if screenshot and not self.is_black_image(screenshot):
                self.log_message("后台截图成功")
                return screenshot
            else:
                self.log_message("后台截图失败或图像为黑色")
                return None
                
        except Exception as e:
            self.log_message(f"后台截图失败: {e}", "ERROR")
            return None
    
    def capture_window_with_fallback(self, hwnd, background_first: bool = True, process_manager=None) -> Optional[Image.Image]:
        """智能截图方法（后台优先，失败时回退到前台）
        
        Args:
            hwnd: 窗口句柄
            background_first: 是否优先尝试后台截图
            process_manager: 进程管理器实例
            
        Returns:
            截图图像或None
        """
        screenshot = None
        
        # 策略1: 优先尝试后台截图
        if background_first:
            self.log_message("尝试后台截图")
            screenshot = self.capture_window_background(hwnd)
            
            if screenshot:
                self.log_message("后台截图成功，无需激活窗口")
                return screenshot
            else:
                self.log_message("后台截图失败，切换到前台截图模式")
        
        # 策略2: 后台失败，使用传统的激活窗口截图
        if process_manager:
            # 获取窗口矩形
            rect = process_manager.get_window_rect(hwnd)
            if rect:
                # 先尝试基本激活
                if process_manager.activate_window(hwnd):
                    time.sleep(0.5)
                    screenshot = self.capture_window_standard(rect)
                    
                    # 如果还是黑色，尝试强制激活
                    if not screenshot or self.is_black_image(screenshot):
                        self.log_message("基本激活截图失败，尝试强制激活")
                        if process_manager.force_activate_window(hwnd):
                            time.sleep(1)
                            screenshot = self.capture_window_standard(rect)
        
        if screenshot:
            self.log_message("前台截图成功")
        else:
            self.log_message("所有截图方法都失败", "ERROR")
            
        return screenshot
    def capture_window_auto(self, hwnd, rect: tuple, process_manager=None) -> Optional[Image.Image]:
        """自动选择最佳截图方法（保持向后兼容）
        
        Args:
            hwnd: 窗口句柄
            rect: 窗口矩形
            process_manager: 进程管理器实例
            
        Returns:
            截图图像或None
        """
        # 使用新的智能截图方法，默认后台优先
        return self.capture_window_with_fallback(hwnd, background_first=True, process_manager=process_manager)
    
    def capture_window(self, hwnd, method: str = "standard", process_manager=None) -> Optional[Image.Image]:
        """根据指定方法截图窗口
        
        Args:
            hwnd: 窗口句柄
            method: 截图方法 ("standard", "handle", "auto", "background", "smart")
            process_manager: 进程管理器实例
            
        Returns:
            截图图像或None
        """
        # 获取窗口位置和大小
        if process_manager:
            rect = process_manager.get_window_rect(hwnd)
        else:
            try:
                rect = win32gui.GetWindowRect(hwnd)
            except Exception as e:
                self.log_message(f"获取窗口矩形失败: {e}", "ERROR")
                return None
        
        if not rect:
            self.log_message("无法获取窗口位置信息", "ERROR")
            return None
        
        left, top, right, bottom = rect
        
        # 检查窗口大小是否有效
        if right - left <= 0 or bottom - top <= 0:
            self.log_message("窗口大小无效", "ERROR")
            return None
        
        self.log_message(f"开始截图，方法: {method}，区域: {right-left}x{bottom-top}")
        
        if method == "standard":
            return self.capture_window_standard(rect)
        elif method == "handle":
            return self.capture_window_by_handle(hwnd)
        elif method == "auto":
            return self.capture_window_auto(hwnd, rect, process_manager)
        elif method == "background":
            # 纯后台截图，不激活窗口
            return self.capture_window_background(hwnd)
        elif method == "smart":
            # 智能截图，后台优先带回退
            return self.capture_window_with_fallback(hwnd, background_first=True, process_manager=process_manager)
        else:
            self.log_message(f"未知的截图方法: {method}", "ERROR")
            return None
    
    def get_timing_info(self) -> Dict[str, Any]:
        """获取时间统计信息
        
        Returns:
            时间信息字典
        """
        # 这个方法由调用者实现具体的时间记录逻辑
        return {}