"""
UI日志系统模块
功能：日志输出、时间记录、性能监控
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Callable

class UILogger:
    """UI日志系统类"""
    
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """初始化UI日志系统
        
        Args:
            log_callback: 日志回调函数，接收(message, level)参数
        """
        self.log_callback = log_callback
        self.timing_enabled = True
    
    def log_message(self, message: str, level: str = "INFO"):
        """在日志区域显示消息
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        try:
            if self.log_callback:
                self.log_callback(message, level)
            else:
                # 如果没有回调函数，打印到控制台
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] [{level}] {message}")
        except Exception as e:
            print(f"日志输出错误: {e}")
    
    def log_timing_info(self, timing_info: Dict[str, float], title: str = "时间统计"):
        """记录时间统计信息
        
        Args:
            timing_info: 时间信息字典
            title: 统计标题
        """
        if not self.timing_enabled:
            return
        
        self.log_message(f"=== {title} ===")
        for stage, duration in timing_info.items():
            if isinstance(duration, (int, float)):
                self.log_message(f"{stage}: {duration:.3f}秒")
            else:
                self.log_message(f"{stage}: {duration}")
        self.log_message("=" * (len(title) + 8))
    
    def is_timing_enabled(self) -> bool:
        """检查时间记录是否启用
        
        Returns:
            时间记录是否启用
        """
        return self.timing_enabled
    
    def set_timing_enabled(self, enabled: bool):
        """设置时间记录是否启用
        
        Args:
            enabled: 是否启用
        """
        self.timing_enabled = enabled

class TimingRecorder:
    """时间记录器类"""
    
    def __init__(self, logger: Optional[UILogger] = None):
        """初始化时间记录器
        
        Args:
            logger: UI日志器实例
        """
        self.logger = logger
        self.timing_data = {}
        self.start_times = {}
    
    def start_timing(self, task_name: str):
        """开始某个任务的计时
        
        Args:
            task_name: 任务名称
        """
        import time
        self.start_times[task_name] = time.time()
        
        if self.logger:
            self.logger.log_message(f"开始计时: {task_name}")
    
    def end_timing(self, task_name: str):
        """结束某个任务的计时
        
        Args:
            task_name: 任务名称
        """
        import time
        if task_name in self.start_times:
            elapsed_time = time.time() - self.start_times[task_name]
            self.timing_data[task_name] = elapsed_time
            
            if self.logger:
                self.logger.log_message(f"完成计时: {task_name}, 耗时: {elapsed_time:.3f}秒")
        else:
            if self.logger:
                self.logger.log_message(f"警告: 任务 {task_name} 没有开始计时", "WARNING")
    
    def add_timing(self, task_name: str, duration: float):
        """直接添加一个任务的耗时
        
        Args:
            task_name: 任务名称
            duration: 耗时（秒）
        """
        self.timing_data[task_name] = duration
        
        if self.logger:
            self.logger.log_message(f"记录耗时: {task_name}, 耗时: {duration:.3f}秒")
    
    def get_timing(self, task_name: str) -> Optional[float]:
        """获取某个任务的耗时
        
        Args:
            task_name: 任务名称
            
        Returns:
            耗时（秒），如果不存在返回None
        """
        return self.timing_data.get(task_name)
    
    def get_all_timings(self) -> Dict[str, float]:
        """获取所有任务的耗时
        
        Returns:
            所有任务的耗时字典
        """
        return self.timing_data.copy()
    
    def clear_timings(self):
        """清空所有计时数据"""
        self.timing_data.clear()
        self.start_times.clear()
        
        if self.logger:
            self.logger.log_message("计时数据已清空")
    
    def output_summary(self, title: str = "性能统计"):
        """输出时间统计摘要
        
        Args:
            title: 统计标题
        """
        if self.logger:
            self.logger.log_timing_info(self.timing_data, title)

# 保持向后兼容性
class PerformanceMonitor(TimingRecorder):
    """性能监控器（TimingRecorder的别名，保持向后兼容）"""
    pass