import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk, ImageGrab
import keyboard
import threading
import time
from modules.core import OCREngine, recognize_image

class ScreenCapture:
    def __init__(self):
        self.root = None
        self.canvas = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.capture_size = (600, 600)  # 默认截图大小
        self.selected_area = None
        
        # 初始化OCR引擎
        print("正在初始化OCR引擎...")
        try:
            self.ocr_engine = OCREngine(
                lang="ch",
                use_gpu=False,
                confidence_threshold=0.8
            )
            print("OCR引擎初始化完成")
        except Exception as e:
            print(f"OCR引擎初始化失败: {e}")
            self.ocr_engine = None
    
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
            
            print(f"截图完成，尺寸: {img_array.shape}")
            print("正在进行OCR识别...")
            
            # 调用OCR识别
            self.recognize_text(img_array)
            
        except Exception as e:
            print(f"截图失败: {e}")
            self.cancel_capture()
    
    def recognize_text(self, img_array):
        """OCR文字识别"""
        if self.ocr_engine is None:
            print("OCR引擎未初始化，无法进行识别")
            return []
        
        try:
            # 使用OCR引擎识别图像数组
            high_confidence_results = self.ocr_engine.recognize_image_array(img_array)
            
            if high_confidence_results:
                print(f"\n找到 {len(high_confidence_results)} 个高置信度结果")
                return high_confidence_results
            else:
                print("没有找到置信度大于0.8的识别结果")
                return []
                
        except Exception as e:
            print(f"OCR识别出错: {e}")
            return []
    
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
            
            print(f"默认截图完成，尺寸: {img_array.shape}")
            print("正在进行OCR识别...")
            
            # 调用OCR识别
            return self.recognize_text(img_array)
            
        except Exception as e:
            print(f"默认截图失败: {e}")
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
        print("检测到按键 'g'，开始区域截图...")
        capture.start_capture(use_selection=True)
    
    def handle_shift_g_key():
        print("检测到按键 'Shift+g'，开始默认大小截图...")
        result = capture.start_capture(use_selection=False)  # 存储结果但不返回
        return None  # 显式返回 None
    
    # 注册热键
    keyboard.add_hotkey('g', handle_g_key)
    keyboard.add_hotkey('shift+g', handle_shift_g_key)
    
    print("截图程序已启动！")
    print("按 'g' 键进行区域截图")
    print("按 'Shift+g' 键进行默认大小(600x600)截图")
    print("按 'Ctrl+C' 退出程序")
    
    try:
        keyboard.wait('ctrl+c')
    except KeyboardInterrupt:
        pass
    finally:
        print("\n程序已退出")

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