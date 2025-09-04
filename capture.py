import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk, ImageGrab
import keyboard
import threading
import time
import os
from datetime import datetime
from modules.core import OCREngine
from modules.utils import UILogger, OCRProcessor

class ScreenCapture:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.capture_size = (600, 600)  # 默认截图大小
        self.selected_area = None
        
        # 初始化日志系统
        self.logger = UILogger(print)  # 使用print作为日志输出
        
        # 初始化OCR处理器（使用新的封装模块）
        self.logger.log_message("正在初始化OCR处理器...")
        try:
            # 创建OCR引擎
            ocr_engine = OCREngine(
                lang="ch",
                use_gpu=False,
                confidence_threshold=0.7  # 与main.py保持一致
            )
            
            # 创建OCR处理器
            self.ocr_processor = OCRProcessor(
                ocr_engine=ocr_engine,
                logger=self.logger,
                save_path="./screenshots"
            )
            
            self.logger.log_message("OCR处理器初始化完成（标准模式，平均识别时间~0.2秒）")
        except Exception as e:
            self.logger.log_message(f"OCR处理器初始化失败: {e}", "ERROR")
            self.ocr_processor = None
    
    def create_capture_window(self):
        """创建截图窗口"""
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black', cursor='cross')  # 修复 cursor 设置
        
        # 创建画布
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        
        # 绑定键盘事件
        self.root.bind('<Escape>', self.cancel_capture)
        self.root.focus_set()
        
        # 显示提示文本
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.canvas.create_text(
            screen_width // 2, 50,
            text="拖拽选择区域进行截图，按ESC取消",
            fill='white', font=('Arial', 16)
        )
    
    def on_click(self, event):
        """鼠标按下事件"""
        self.start_x = event.x
        self.start_y = event.y
        if self.rect and self.canvas:  # 添加空值检查
            self.canvas.delete(self.rect)
    
    def on_drag(self, event):
        """鼠标拖拽事件"""
        if self.rect and self.canvas:  # 添加空值检查
            self.canvas.delete(self.rect)
        
        if self.canvas and self.start_x is not None and self.start_y is not None:  # 添加空值检查
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline='red', width=2
            )
    
    def on_release(self, event):
        """鼠标释放事件"""
        if self.start_x is not None and self.start_y is not None:  # 添加空值检查
            # 获取选择区域坐标
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            
            # 确保选择区域有效
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                self.selected_area = (x1, y1, x2, y2)
                self.perform_capture()
            else:
                messagebox.showwarning("警告", "选择区域太小，请重新选择")
                self.cancel_capture()
    
    def cancel_capture(self, event=None):
        """取消截图"""
        if self.root:
            self.root.destroy()
            self.root = None
    
    def perform_capture(self):
        """执行截图"""
        if not self.selected_area:
            return
        
        try:
            # 隐藏截图窗口
            if self.root:  # 添加空值检查
                self.root.withdraw()
            time.sleep(0.1)  # 等待窗口完全隐藏
            
            # 进行截图
            x1, y1, x2, y2 = self.selected_area
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # 关闭截图窗口
            self.cancel_capture()
            
            # 转换为numpy数组进行OCR识别
            img_array = np.array(screenshot)
            
            self.logger.log_message(f"截图完成，尺寸: {img_array.shape}")
            self.logger.log_message("正在进行OCR识别...")
            
            # 调用OCR处理器进行识别和保存
            if self.ocr_processor:
                self.ocr_processor.recognize_and_save(screenshot, filename_prefix="capture_manual")
            else:
                self.logger.log_message("OCR处理器未初始化，无法进行识别", "ERROR")
            
        except Exception as e:
            print(f"截图失败: {e}")
            self.cancel_capture()

    def default_capture(self):
        """默认大小截图 (600x600)"""
        try:
            # 获取屏幕中心位置
            screen = ImageGrab.grab()
            screen_width, screen_height = screen.size
            
            # 计算居中的600x600区域
            width, height = self.capture_size
            left = (screen_width - width) // 2
            top = (screen_height - height) // 2
            right = left + width
            bottom = top + height
            
            # 截图
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            img_array = np.array(screenshot)
            
            self.logger.log_message(f"默认截图完成，尺寸: {img_array.shape}")
            self.logger.log_message("正在进行OCR识别...")
            
            # 调用OCR处理器进行识别和保存
            if self.ocr_processor:
                return self.ocr_processor.recognize_and_save(screenshot, filename_prefix="capture_manual_default")
            else:
                self.logger.log_message("OCR处理器未初始化，无法进行识别", "ERROR")
                return []
            
        except Exception as e:
            self.logger.log_message(f"默认截图失败: {e}", "ERROR")
            return []
    
    def start_capture(self, use_selection=True):
        """开始截图"""
        if use_selection:
            # 创建选择区域截图窗口
            self.create_capture_window()
        else:
            # 使用默认大小截图
            return self.default_capture()

def on_key_press():
    """键盘监听函数"""
    capture = ScreenCapture()
    
    def handle_g_key():
        capture.logger.log_message("检测到按键 'g'，开始区域截图...")
        capture.start_capture(use_selection=True)
    
    def handle_shift_g_key():
        capture.logger.log_message("检测到按键 'Shift+g'，开始默认大小截图...")
        result = capture.start_capture(use_selection=False)  # 存储结果但不返回
        return None  # 显式返回 None
    
    # 注册热键
    keyboard.add_hotkey('g', handle_g_key)
    keyboard.add_hotkey('shift+g', handle_shift_g_key)
    
    capture.logger.log_message("截图程序已启动！")
    capture.logger.log_message("按 'g' 键进行区域截图")
    capture.logger.log_message("按 'Shift+g' 键进行默认大小(600x600)截图")
    capture.logger.log_message("按 'Ctrl+C' 退出程序")
    
    try:
        keyboard.wait('ctrl+c')
    except KeyboardInterrupt:
        pass
    finally:
        capture.logger.log_message("\n程序已退出")

if __name__ == "__main__":
    # 创建主窗口（隐藏）
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 启动键盘监听
    keyboard_thread = threading.Thread(target=on_key_press, daemon=True)
    keyboard_thread.start()
    
    # 启动GUI主循环
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("程序被用户中断")