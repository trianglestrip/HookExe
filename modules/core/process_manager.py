"""
进程管理模块
功能：进程查找、窗口管理、系统API调用
"""

import psutil
import win32gui
import win32process
import win32con
import win32api
from typing import List, Dict, Optional
import time

class ProcessManager:
    """进程管理类"""
    
    def __init__(self, logger=None):
        """初始化进程管理器
        
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
    
    def find_processes_by_name(self, keyword: str) -> List[Dict]:
        """查找包含关键字的进程
        
        Args:
            keyword: 进程名关键字
            
        Returns:
            匹配的进程信息列表
        """
        found_processes = []
        keyword_lower = keyword.lower()
        
        # 获取所有窗口句柄
        windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                windows.append(hwnd)
            return True
        
        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            for hwnd in windows:
                try:
                    # 获取窗口标题
                    window_title = win32gui.GetWindowText(hwnd)
                    if not window_title:
                        continue
                    
                    # 获取进程ID和进程信息
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                        
                        # 检查进程名或窗口标题是否包含关键字
                        if (keyword_lower in process_name.lower() or 
                            keyword_lower in window_title.lower()):
                            
                            found_processes.append({
                                'pid': pid,
                                'name': process_name,
                                'window_title': window_title,
                                'hwnd': hwnd
                            })
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
                except Exception:
                    continue
                    
        except Exception as e:
            self.log_message(f"枚举窗口失败: {e}", "ERROR")
        
        return found_processes
    
    def activate_window(self, hwnd) -> bool:
        """激活窗口的基本方法
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            是否成功激活
        """
        try:
            # 恢复窗口（如果最小化）
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 显示窗口
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            
            # 设置为前台窗口
            win32gui.SetForegroundWindow(hwnd)
            
            # 等待窗口激活
            time.sleep(0.5)
            
            self.log_message("基本窗口激活完成")
            return True
            
        except Exception as e:
            self.log_message(f"基本激活窗口失败: {e}", "ERROR")
            return False
    
    def force_activate_window(self, hwnd) -> bool:
        """强制激活窗口的高级方法
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            是否成功激活
        """
        try:
            # 获取当前前台窗口
            current_hwnd = win32gui.GetForegroundWindow()
            
            # 获取当前线程ID和目标窗口线程ID
            current_thread_id = win32api.GetCurrentThreadId()
            target_thread_id = win32process.GetWindowThreadProcessId(hwnd)[0]
            
            # 如果不是同一个线程，需要附加输入
            if current_thread_id != target_thread_id:
                win32process.AttachThreadInput(current_thread_id, target_thread_id, True)
            
            # 恢复窗口
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # 显示并激活窗口
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, 0, 0, 
                                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
            win32gui.SetForegroundWindow(hwnd)
            
            # 分离线程输入
            if current_thread_id != target_thread_id:
                win32process.AttachThreadInput(current_thread_id, target_thread_id, False)
            
            # 等待窗口激活
            time.sleep(1)
            
            self.log_message("强制窗口激活完成")
            return True
            
        except Exception as e:
            self.log_message(f"强制激活窗口失败: {e}", "ERROR")
            return False
    
    def is_window_valid(self, hwnd) -> bool:
        """检查窗口是否有效
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            窗口是否有效
        """
        try:
            return bool(win32gui.IsWindow(hwnd))
        except Exception:
            return False
    
    def get_window_rect(self, hwnd) -> Optional[tuple]:
        """获取窗口位置和大小
        
        Args:
            hwnd: 窗口句柄
            
        Returns:
            窗口矩形 (left, top, right, bottom) 或 None
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            return rect
        except Exception as e:
            self.log_message(f"获取窗口矩形失败: {e}", "ERROR")
            return None
    
    def get_process_info(self, pid: int) -> Optional[Dict]:
        """获取进程详细信息
        
        Args:
            pid: 进程ID
            
        Returns:
            进程信息字典或None
        """
        try:
            process = psutil.Process(pid)
            return {
                'pid': pid,
                'name': process.name(),
                'exe': process.exe(),
                'status': process.status(),
                'create_time': process.create_time(),
                'memory_info': process.memory_info(),
                'cpu_percent': process.cpu_percent(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.log_message(f"获取进程信息失败: {e}", "ERROR")
            return None