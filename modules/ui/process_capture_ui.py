"""
进程窗口截图工具 - GUI界面模块
功能：提供完整的tkinter用户界面，处理所有UI相关逻辑
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading
from typing import List, Dict, Optional, Callable


class ProcessCaptureUI:
    """进程窗口截图工具的GUI界面类"""
    
    def __init__(self):
        """初始化GUI界面"""
        self.root = tk.Tk()
        self.root.title("进程窗口OCR截图工具 - 回车搜索，双击截图识别")
        self.root.geometry("700x800")
        self.root.resizable(True, True)
        
        # UI变量
        self.process_name_var = tk.StringVar()
        self.save_path_var = tk.StringVar(value="./screenshots")
        self.auto_capture_var = tk.BooleanVar()
        self.capture_interval_var = tk.IntVar(value=5)
        self.capture_method_var = tk.StringVar(value="standard")  # 默认标准截图
        self.timing_enabled = tk.BooleanVar(value=True)  # 默认启用时间记录
        self.status_var = tk.StringVar(value="就绪")
        
        # 控制变量
        self.is_capturing = False
        self.capture_thread = None
        
        # 回调函数
        self.search_callback = None
        self.capture_single_callback = None
        self.start_auto_callback = None
        self.stop_auto_callback = None
        self.browse_path_callback = None
        
        # UI组件 - 这些组件在setup_ui中初始化
        self.process_listbox: Optional[tk.Listbox] = None
        self.log_text: Optional[tk.Text] = None
        self.capture_btn: Optional[ttk.Button] = None
        self.start_btn: Optional[ttk.Button] = None
        self.stop_btn: Optional[ttk.Button] = None
        
        # 初始化UI
        self.setup_ui()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化日志
        self.log_message("程序启动完成，请输入进程名关键字开始使用")
    
    def set_callbacks(self, 
                     search_callback: Callable[[str], List[Dict]],
                     capture_single_callback: Callable[[], bool],
                     start_auto_callback: Callable[[], bool],
                     stop_auto_callback: Callable[[], None],
                     browse_path_callback: Optional[Callable[[], str]] = None):
        """设置回调函数
        
        Args:
            search_callback: 搜索进程的回调函数
            capture_single_callback: 单次截图的回调函数  
            start_auto_callback: 开始自动截图的回调函数
            stop_auto_callback: 停止自动截图的回调函数
            browse_path_callback: 浏览路径的回调函数
        """
        self.search_callback = search_callback
        self.capture_single_callback = capture_single_callback
        self.start_auto_callback = start_auto_callback
        self.stop_auto_callback = stop_auto_callback
        self.browse_path_callback = browse_path_callback
    
    def setup_ui(self):
        """设置UI界面"""
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)  # type: ignore
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="进程窗口OCR截图工具", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 进程名输入
        ttk.Label(main_frame, text="进程名关键字:").grid(row=1, column=0, sticky=tk.W, pady=5)
        process_entry = ttk.Entry(main_frame, textvariable=self.process_name_var, width=30)
        process_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5, padx=(5, 5))  # type: ignore
        
        # 绑定回车键事件
        process_entry.bind('<Return>', lambda event: self.search_processes())
        
        # 搜索按钮
        search_btn = ttk.Button(main_frame, text="搜索进程", command=self.search_processes)
        search_btn.grid(row=1, column=2, pady=5, padx=(5, 0))
        
        # 进程列表
        ttk.Label(main_frame, text="找到的进程:").grid(row=2, column=0, sticky=tk.W, pady=(15, 5))
        
        # 创建进程列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)  # type: ignore
        list_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 进程列表和滚动条
        self.process_listbox = tk.Listbox(list_frame, height=8)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.process_listbox.yview)
        self.process_listbox.configure(yscrollcommand=scrollbar.set)
        
        # 绑定双击事件
        self.process_listbox.bind('<Double-Button-1>', lambda event: self.capture_single())
        
        self.process_listbox.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)  # type: ignore
        scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)  # type: ignore
        
        # 截图方法选择
        method_frame = ttk.LabelFrame(main_frame, text="截图方法", padding="10")
        method_frame.grid(row=4, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(10, 5))  # type: ignore
        
        # 第一行：基本截图方法
        ttk.Radiobutton(method_frame, text="标准截图（默认）", variable=self.capture_method_var, value="standard").grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(method_frame, text="窗口句柄", variable=self.capture_method_var, value="handle").grid(row=0, column=1, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(method_frame, text="自动选择", variable=self.capture_method_var, value="auto").grid(row=0, column=2, sticky=tk.W)
        
        # 第二行：智能截图方法
        ttk.Radiobutton(method_frame, text="后台截图", variable=self.capture_method_var, value="background").grid(row=1, column=0, sticky=tk.W, padx=(0, 15), pady=(5, 0))
        ttk.Radiobutton(method_frame, text="智能截图（推荐）", variable=self.capture_method_var, value="smart").grid(row=1, column=1, sticky=tk.W, padx=(0, 15), pady=(5, 0))
        
        # 时间记录选项
        timing_check = ttk.Checkbutton(method_frame, text="启用时间记录", variable=self.timing_enabled)
        timing_check.grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        
        # 提示文本
        tip_label = ttk.Label(method_frame, text="提示：智能截图优先尝试后台截图，失败时自动切换到前台模式。在输入框按回车搜索，双击进程直接截图OCR识别。", 
                            foreground="gray", wraplength=650)
        tip_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        # 保存路径设置
        path_frame = ttk.LabelFrame(main_frame, text="保存设置", padding="10")
        path_frame.grid(row=5, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(15, 10))  # type: ignore
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="保存路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        path_entry = ttk.Entry(path_frame, textvariable=self.save_path_var)
        path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=(5, 5))  # type: ignore
        
        browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_save_path)
        browse_btn.grid(row=0, column=2, pady=5)
        
        # 自动截图设置
        auto_frame = ttk.Frame(path_frame)
        auto_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(10, 0))  # type: ignore
        
        auto_check = ttk.Checkbutton(auto_frame, text="自动定时截图", variable=self.auto_capture_var)
        auto_check.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(auto_frame, text="间隔(秒):").grid(row=0, column=1, sticky=tk.W, padx=(20, 5))
        interval_spin = ttk.Spinbox(auto_frame, from_=1, to=3600, textvariable=self.capture_interval_var, width=10)
        interval_spin.grid(row=0, column=2, sticky=tk.W)
        
        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=(15, 0))
        
        self.capture_btn = ttk.Button(btn_frame, text="截图OCR识别", command=self.capture_single, style="Accent.TButton")
        self.capture_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.start_btn = ttk.Button(btn_frame, text="开始自动OCR", command=self.start_auto_capture)
        self.start_btn.grid(row=0, column=1, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="停止截图", command=self.stop_capture, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=(10, 0))
        
        # 日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="日志输出", padding="10")
        log_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W+tk.E+tk.N+tk.S, pady=(15, 10))  # type: ignore
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)  # 让日志区域可以扩展
        
        # 创建日志文本框和滚动条
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)  # type: ignore
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)  # type: ignore
        log_scrollbar.grid(row=0, column=1, sticky=tk.N+tk.S)  # type: ignore
        
        # 日志控制按钮
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        
        clear_log_btn = ttk.Button(log_btn_frame, text="清空日志", command=self.clear_log)
        clear_log_btn.grid(row=0, column=0, padx=(0, 10))
        
        export_log_btn = ttk.Button(log_btn_frame, text="导出日志", command=self.export_log)
        export_log_btn.grid(row=0, column=1)
        
        # 状态栏
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=8, column=0, columnspan=3, sticky=tk.W+tk.E, pady=(15, 0))  # type: ignore
    
    def log_message(self, message: str, level: str = "INFO"):
        """在日志区域显示消息"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 包含毫秒
            log_entry = f"[{timestamp}] [{level}] {message}\n"
            
            # 在UI线程中更新日志
            def update_log():
                if self.log_text:
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, log_entry)
                    self.log_text.see(tk.END)  # 自动滚动到最后
                    self.log_text.config(state=tk.DISABLED)
            
            # 如果在主线程中，直接更新；否则使用after方法
            if threading.current_thread() == threading.main_thread():
                update_log()
            else:
                self.root.after(0, update_log)
                
        except Exception as e:
            print(f"日志输出错误: {e}")
    
    def clear_log(self):
        """清空日志"""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.log_message("日志已清空")
    
    def export_log(self):
        """导出日志到文件"""
        try:
            filename = filedialog.asksaveasfilename(
                title="保存日志文件",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename and self.log_text:
                log_content = self.log_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.log_message(f"日志已导出到: {filename}")
                messagebox.showinfo("成功", f"日志已导出到:\n{filename}")
        except Exception as e:
            self.log_message(f"导出日志失败: {e}", "ERROR")
            messagebox.showerror("错误", f"导出日志失败: {e}")
    
    def search_processes(self):
        """搜索进程（调用回调函数）"""
        keyword = self.process_name_var.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入进程名关键字")
            return
        
        if self.search_callback:
            try:
                self.status_var.set("正在搜索进程...")
                if self.process_listbox:
                    self.process_listbox.delete(0, tk.END)
                
                found_processes = self.search_callback(keyword)
                
                if found_processes and self.process_listbox:
                    for proc_info in found_processes:
                        display_text = f"PID: {proc_info['pid']} | {proc_info['name']} | 窗口: {proc_info['window_title']}"
                        self.process_listbox.insert(tk.END, display_text)
                    
                    # 默认选中第一个进程
                    if len(found_processes) > 0:
                        self.process_listbox.selection_set(0)
                        self.process_listbox.activate(0)
                        self.process_listbox.focus_set()
                    
                    self.status_var.set(f"找到 {len(found_processes)} 个匹配的进程，已选中第一个")
                else:
                    self.status_var.set("未找到匹配的进程")
                    messagebox.showinfo("信息", f"未找到包含 '{keyword}' 的进程")
                    
            except Exception as e:
                self.log_message(f"搜索进程出错: {e}", "ERROR")
                self.status_var.set("搜索出错")
                messagebox.showerror("错误", f"搜索进程时出错: {e}")
        else:
            messagebox.showerror("错误", "搜索回调函数未设置")
    
    def capture_single(self):
        """单次截图（调用回调函数）"""
        if not self.process_listbox or not self.process_listbox.curselection():
            messagebox.showwarning("警告", "请先选择一个进程")
            return
        
        if self.capture_single_callback:
            try:
                self.status_var.set("正在截图和OCR识别...")
                success = self.capture_single_callback()
                
                if success:
                    self.status_var.set("OCR识别截图成功")
                else:
                    self.status_var.set("截图失败")
                    
            except Exception as e:
                self.status_var.set("截图出错")
                self.log_message(f"单次截图出错: {e}", "ERROR")
                messagebox.showerror("错误", f"截图时出错: {e}")
        else:
            messagebox.showerror("错误", "截图回调函数未设置")
    
    def start_auto_capture(self):
        """开始自动截图（调用回调函数）"""
        if not self.process_listbox or not self.process_listbox.curselection():
            messagebox.showwarning("警告", "请先选择一个进程")
            return
        
        if not self.auto_capture_var.get():
            messagebox.showwarning("警告", "请先勾选'自动定时截图'")
            return
        
        if self.start_auto_callback:
            try:
                success = self.start_auto_callback()
                if success:
                    self.is_capturing = True
                    if self.start_btn:
                        self.start_btn.config(state=tk.DISABLED)
                    if self.stop_btn:
                        self.stop_btn.config(state=tk.NORMAL)
                    if self.capture_btn:
                        self.capture_btn.config(state=tk.DISABLED)
                    self.status_var.set("自动OCR截图已开始")
                    self.log_message(f"开始自动OCR截图，间隔: {self.capture_interval_var.get()}秒")
            except Exception as e:
                self.log_message(f"开始自动截图出错: {e}", "ERROR")
                messagebox.showerror("错误", f"开始自动截图时出错: {e}")
        else:
            messagebox.showerror("错误", "自动截图回调函数未设置")
    
    def stop_capture(self):
        """停止自动截图（调用回调函数）"""
        if self.stop_auto_callback:
            try:
                self.stop_auto_callback()
                self.is_capturing = False
                if self.start_btn:
                    self.start_btn.config(state=tk.NORMAL)
                if self.stop_btn:
                    self.stop_btn.config(state=tk.DISABLED)
                if self.capture_btn:
                    self.capture_btn.config(state=tk.NORMAL)
                self.status_var.set("自动OCR截图已停止")
                self.log_message("自动OCR截图已停止")
            except Exception as e:
                self.log_message(f"停止自动截图出错: {e}", "ERROR")
                messagebox.showerror("错误", f"停止自动截图时出错: {e}")
        else:
            messagebox.showerror("错误", "停止截图回调函数未设置")
    
    def browse_save_path(self):
        """选择保存路径"""
        if self.browse_path_callback:
            try:
                folder = self.browse_path_callback()
                if folder:
                    self.save_path_var.set(folder)
                    self.log_message(f"保存路径已更新: {folder}")
            except Exception as e:
                self.log_message(f"选择路径出错: {e}", "ERROR")
                messagebox.showerror("错误", f"选择路径时出错: {e}")
        else:
            # 默认实现
            folder = filedialog.askdirectory(title="选择截图保存文件夹")
            if folder:
                self.save_path_var.set(folder)
                self.log_message(f"保存路径已更新: {folder}")
    
    def get_selected_process_index(self) -> Optional[int]:
        """获取选中的进程索引"""
        if not self.process_listbox:
            return None
        selection = self.process_listbox.curselection()
        return selection[0] if selection else None
    
    def get_process_keyword(self) -> str:
        """获取进程关键字"""
        return self.process_name_var.get().strip()
    
    def get_save_path(self) -> str:
        """获取保存路径"""
        return self.save_path_var.get()
    
    def get_capture_method(self) -> str:
        """获取截图方法"""
        return self.capture_method_var.get()
    
    def get_capture_interval(self) -> int:
        """获取截图间隔"""
        return self.capture_interval_var.get()
    
    def is_timing_enabled(self) -> bool:
        """是否启用时间记录"""
        return self.timing_enabled.get()
    
    def is_auto_capture_enabled(self) -> bool:
        """是否启用自动截图"""
        return self.auto_capture_var.get()
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_var.set(message)
    
    def show_error(self, title: str, message: str):
        """显示错误对话框"""
        messagebox.showerror(title, message)
    
    def show_warning(self, title: str, message: str):
        """显示警告对话框"""
        messagebox.showwarning(title, message)
    
    def show_info(self, title: str, message: str):
        """显示信息对话框"""
        messagebox.showinfo(title, message)
    
    def on_closing(self):
        """关闭程序时的处理"""
        if self.is_capturing and self.stop_auto_callback:
            self.stop_auto_callback()
        
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1)
        
        self.root.destroy()
    
    def run(self):
        """运行GUI主循环"""
        self.root.mainloop()