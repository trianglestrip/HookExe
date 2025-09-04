"""
进程窗口OCR截图工具 - 主程序入口
功能：整合所有模块，提供统一的程序入口
"""

import os
import time
import threading
from datetime import datetime
from tkinter import messagebox, filedialog
from typing import List, Dict, Optional

# 导入各个功能模块
from modules.ui import ProcessCaptureUI
from modules.core import ProcessManager, ScreenshotEngine, OCREngine
from modules.utils import UILogger, TimingRecorder, OCRProcessor


class ProcessCaptureApp:
    """进程截图OCR应用程序主控制器"""
    
    def __init__(self):
        """初始化应用程序"""
        # 初始化UI界面
        self.ui = ProcessCaptureUI()
        
        # 初始化核心组件
        self.logger = UILogger(self.ui.log_message)
        self.process_manager = ProcessManager(self.logger)
        self.screenshot_engine = ScreenshotEngine(self.logger)
        self.timing_recorder = TimingRecorder()
        
        # 初始化OCR处理器
        self.ocr_processor = None
        self.init_ocr_processor()
        
        # 设置UI回调函数
        self.setup_ui_callbacks()
        
        # 自动截图控制
        self.is_auto_capturing = False
        self.auto_capture_thread = None
        
        # 进程列表缓存
        self.cached_processes = []
        
        self.logger.log_message("应用程序初始化完成")
    
    def init_ocr_processor(self):
        """初始化OCR处理器"""
        try:
            self.logger.log_message("正在初始化OCR处理器...")
            
            # 创建OCR引擎
            ocr_engine = OCREngine(
                lang="ch",
                use_gpu=False,  # 避免GPU兼容性问题
                confidence_threshold=0.7  # 优化置信度阈值，过滤低质量结果
            )
            
            # 创建OCR处理器
            self.ocr_processor = OCRProcessor(
                ocr_engine=ocr_engine,
                logger=self.logger,
                save_path=self.ui.get_save_path()
            )
            
            self.logger.log_message("OCR处理器初始化完成（标准模式，平均识别时间~0.2秒）")
            
        except Exception as e:
            self.logger.log_message(f"OCR处理器初始化失败: {e}", "ERROR")
            self.ocr_processor = None
    
    def setup_ui_callbacks(self):
        """设置UI回调函数"""
        self.ui.set_callbacks(
            search_callback=self.search_processes,
            capture_single_callback=self.capture_single_window,
            start_auto_callback=self.start_auto_capture,
            stop_auto_callback=self.stop_auto_capture,
            browse_path_callback=self.browse_save_path
        )
    
    def search_processes(self, keyword: str) -> List[Dict]:
        """搜索包含关键字的进程
        
        Args:
            keyword: 搜索关键字
            
        Returns:
            匹配的进程列表
        """
        start_time = time.time()
        self.logger.log_message(f"开始搜索进程: '{keyword}'")
        
        try:
            found_processes = self.process_manager.find_processes_by_name(keyword)
            search_time = time.time() - start_time
            
            # 缓存搜索结果
            self.cached_processes = found_processes
            
            if found_processes:
                self.logger.log_message(f"搜索完成，找到 {len(found_processes)} 个进程，耗时: {search_time:.3f}秒")
            else:
                self.logger.log_message(f"搜索完成，未找到匹配的进程，耗时: {search_time:.3f}秒")
            
            return found_processes
            
        except Exception as e:
            search_time = time.time() - start_time
            self.logger.log_message(f"搜索进程出错: {e}，耗时: {search_time:.3f}秒", "ERROR")
            return []
    
    def capture_single_window(self) -> bool:
        """单次截图和OCR识别
        
        Returns:
            是否成功
        """
        selection_index = self.ui.get_selected_process_index()
        if selection_index is None:
            return False
        
        if selection_index >= len(self.cached_processes):
            self.ui.show_warning("警告", "选中的进程已不存在，请重新搜索")
            return False
        
        process_info = self.cached_processes[selection_index]
        return self.capture_process_window(process_info)
    
    def capture_process_window(self, process_info: Dict) -> bool:
        """截图指定进程的窗口
        
        Args:
            process_info: 进程信息字典
            
        Returns:
            是否成功
        """
        # 开始时间记录
        if self.ui.is_timing_enabled():
            self.timing_recorder.start_timing("总耗时")
        
        hwnd = process_info['hwnd']
        self.logger.log_message(f"开始截图进程: {process_info['name']} (PID: {process_info['pid']})")
        
        try:
            # 检查窗口是否仍然存在
            if not self.process_manager.is_window_valid(hwnd):
                self.ui.show_warning("警告", "选中的窗口已关闭")
                return False
            
            # 获取截图方法
            method = self.ui.get_capture_method()
            
            # 阶段1: 窗口激活（仅在非后台模式下）
            if method not in ["background", "smart"]:
                if self.ui.is_timing_enabled():
                    self.timing_recorder.start_timing("窗口激活")
                
                self.process_manager.activate_window(hwnd)
                
                if self.ui.is_timing_enabled():
                    self.timing_recorder.end_timing("窗口激活")
                    activation_time = self.timing_recorder.get_timing("窗口激活")
                    self.logger.log_message(f"窗口激活完成，耗时: {activation_time:.3f}秒")
            else:
                self.logger.log_message(f"使用{method}模式，跳过窗口激活")
            
            # 阶段2: 截图
            if self.ui.is_timing_enabled():
                self.timing_recorder.start_timing("截图阶段")
            
            screenshot = self.screenshot_engine.capture_window(hwnd, method, self.process_manager)
            
            if self.ui.is_timing_enabled():
                self.timing_recorder.end_timing("截图阶段")
                screenshot_time = self.timing_recorder.get_timing("截图阶段")
                self.logger.log_message(f"截图阶段完成，耗时: {screenshot_time:.3f}秒")
            
            if screenshot is None:
                self.logger.log_message("截图失败，所有方法都无法获取有效图像", "ERROR")
                self.ui.show_warning("警告", "截图失败，可能是应用程序有渲染保护或窗口被遮挡")
                return False
            
            # 阶段3: OCR识别和保存（使用新的OCRProcessor）
            if self.ocr_processor:
                if self.ui.is_timing_enabled():
                    self.timing_recorder.start_timing("OCR识别")
                
                try:
                    self.logger.log_message("开始OCR文字识别...")
                    
                    # 更新OCR处理器的保存路径
                    self.ocr_processor.set_save_path(self.ui.get_save_path())
                    
                    # 使用OCR处理器进行识别和保存
                    high_confidence_results = self.ocr_processor.recognize_and_save(
                        screenshot, 
                        process_info=process_info
                    )
                    
                    if self.ui.is_timing_enabled():
                        self.timing_recorder.end_timing("OCR识别")
                        ocr_time = self.timing_recorder.get_timing("OCR识别")
                        self.logger.log_message(f"OCR识别完成，耗时: {ocr_time:.3f}秒")
                    
                    # 更新UI状态
                    if self.ui.is_timing_enabled():
                        total_time = self.timing_recorder.get_timing("总耗时")
                        if total_time:
                            self.ui.update_status(f"OCR识别截图成功，耗时: {total_time:.3f}秒")
                        else:
                            self.ui.update_status("OCR识别截图成功")
                    else:
                        self.ui.update_status("OCR识别截图成功")
                    
                    return True
                        
                except Exception as e:
                    if self.ui.is_timing_enabled():
                        self.timing_recorder.add_timing("OCR识别", 0)
                    self.logger.log_message(f"OCR识别出错: {e}", "ERROR")
                    return False
            else:
                self.logger.log_message("警告：OCR处理器未初始化，直接保存原始截图", "ERROR")
                # 使用传统方式保存
                success = self.save_screenshot_fallback(screenshot, process_info)
                return success
            
        except Exception as e:
            if self.ui.is_timing_enabled():
                self.timing_recorder.end_timing("总耗时")
                total_time = self.timing_recorder.get_timing("总耗时")
                self.logger.log_message(f"截图过程出错: {e}，总耗时: {total_time:.3f}秒", "ERROR")
            else:
                self.logger.log_message(f"截图过程出错: {e}", "ERROR")
            return False
    
    def save_screenshot_fallback(self, screenshot, process_info: Dict) -> bool:
        """备用保存方法（当OCR处理器未初始化时）
        
        Args:
            screenshot: 截图图像
            process_info: 进程信息
            
        Returns:
            是否保存成功
        """
        try:
            # 确保保存路径存在
            save_path = self.ui.get_save_path()
            if not os.path.exists(save_path):
                os.makedirs(save_path, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{process_info['name']}_{process_info['pid']}_{timestamp}_无OCR.png"
            
            file_path = os.path.join(save_path, filename)
            
            # 保存截图
            screenshot.save(file_path)
            
            self.logger.log_message(f"截图完成，已保存到: {file_path}")
            self.logger.log_message("OCR结果: 0 个高置信度文字")
            self.ui.update_status("截图成功（未进行OCR）")
            
            return True
            
        except Exception as e:
            self.logger.log_message(f"备用保存截图失败: {e}", "ERROR")
            return False
    
    
    def output_timing_statistics(self):
        """输出详细的时间统计"""
        try:
            self.logger.log_message("=== 截图耗时统计 ===")
            
            timing_items = ["窗口激活", "截图阶段", "OCR识别", "绘制标记", "文件保存", "总耗时"]
            for item in timing_items:
                timing = self.timing_recorder.get_timing(item)
                if timing is not None:
                    self.logger.log_message(f"{item}: {timing:.3f}秒")
            
            self.logger.log_message("========================")
        except Exception as e:
            self.logger.log_message(f"输出时间统计出错: {e}", "ERROR")
    
    def start_auto_capture(self) -> bool:
        """开始自动截图
        
        Returns:
            是否成功启动
        """
        if self.is_auto_capturing:
            return False
        
        selection_index = self.ui.get_selected_process_index()
        if selection_index is None or selection_index >= len(self.cached_processes):
            self.ui.show_warning("警告", "请先选择一个有效的进程")
            return False
        
        self.is_auto_capturing = True
        
        # 启动自动截图线程
        self.auto_capture_thread = threading.Thread(
            target=self.auto_capture_loop,
            args=(self.cached_processes[selection_index],),
            daemon=True
        )
        self.auto_capture_thread.start()
        
        return True
    
    def stop_auto_capture(self):
        """停止自动截图"""
        self.is_auto_capturing = False
        
        if self.auto_capture_thread and self.auto_capture_thread.is_alive():
            self.auto_capture_thread.join(timeout=1)
    
    def auto_capture_loop(self, process_info: Dict):
        """自动截图循环
        
        Args:
            process_info: 进程信息
        """
        while self.is_auto_capturing:
            try:
                success = self.capture_process_window(process_info)
                
                if success:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    self.ui.root.after(0, lambda: self.ui.update_status(f"自动OCR截图进行中... 上次截图: {timestamp}"))
                else:
                    self.ui.root.after(0, lambda: self.ui.update_status("自动OCR截图进行中... 上次截图失败"))
                
                # 等待指定间隔
                interval = self.ui.get_capture_interval()
                for _ in range(interval):
                    if not self.is_auto_capturing:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.log_message(f"自动截图循环出错: {e}", "ERROR")
                self.ui.root.after(0, lambda: self.ui.show_error("错误", f"自动截图时出错: {e}"))
                break
    
    def browse_save_path(self) -> str:
        """浏览保存路径
        
        Returns:
            选择的路径，如果用户取消则返回当前路径
        """
        folder = filedialog.askdirectory(title="选择截图保存文件夹")
        if folder:
            return folder
        else:
            # 用户取消选择，返回当前保存路径
            return self.ui.get_save_path()
    
    def run(self):
        """运行应用程序"""
        try:
            self.ui.run()
        except Exception as e:
            messagebox.showerror("启动错误", f"程序运行失败: {e}")


def main():
    """主函数"""
    try:
        app = ProcessCaptureApp()
        app.run()
    except Exception as e:
        messagebox.showerror("启动错误", f"程序启动失败: {e}")


if __name__ == "__main__":
    main()