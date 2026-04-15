import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import json
import sys
from datetime import datetime

class ContextProcessorGUI:
    """
    上下文处理程序图形界面类
    功能：加载JSON格式的上下文数据，提供可视化界面进行上下文裁剪、单条删除，最终保存处理结果
    依赖：tkinter（Python内置GUI库）、json（数据解析）、datetime（时间戳记录）
    """
    
    def __init__(self, root: tk.Tk, input_file: str, output_file: str):
        """
        类初始化方法，完成界面初始化、数据加载
        
        Args:
            root (tk.Tk): tkinter的主窗口对象，作为GUI的根容器
            input_file (str): 输入JSON文件的路径，包含原始上下文数据
            output_file (str): 输出JSON文件的路径，用于保存处理后的上下文数据
        """
        # 主窗口配置
        self.root = root
        self.root.title("上下文处理程序")  # 设置窗口标题
        self.root.geometry("800x600")      # 设置初始窗口尺寸（宽x高）
        self.root.minsize(600, 400)        # 设置窗口最小尺寸，防止缩放过小
        
        # 输入/输出文件路径（实例变量，供全类调用）
        self.input_file = input_file
        self.output_file = output_file
        
        # 上下文数据存储变量
        self.header = {}                  # 存储上下文的头信息（配置项）
        self.messages = []                # 存储原始对话消息列表
        self.processed_context = []       # 存储处理中的/最终的对话消息列表
        
        # 初始化UI组件
        self.create_widgets()
        
        # 加载输入文件数据并初始化界面显示
        self.load_input_data()
        
    def create_widgets(self) -> None:
        """
        创建并布局所有GUI组件（界面元素）
        包含：头信息显示区、上下文列表区、功能按钮区
        返回值：None
        """
        # 主框架：作为所有组件的父容器，设置内边距和填充规则
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 1. 头信息显示区域（带标签的框架）
        header_frame = ttk.LabelFrame(main_frame, text="头信息")
        header_frame.pack(fill=tk.X, pady=(0, 10))  # 横向填充，仅底部留间距
        
        # 滚动文本框：显示JSON格式的头信息，初始禁用编辑
        self.header_text = scrolledtext.ScrolledText(header_frame, height=4, wrap=tk.WORD)
        self.header_text.pack(fill=tk.X, padx=5, pady=5)
        self.header_text.config(state=tk.DISABLED)  # 设为只读状态
        
        # 2. 上下文列表区域（带标签的框架）
        context_frame = ttk.LabelFrame(main_frame, text="上下文列表（可删除单条）")
        context_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))  # 横向+纵向填充，支持拉伸
        
        # 列表框：显示每条上下文的简要信息，支持单行选中
        self.context_listbox = tk.Listbox(
            context_frame, 
            width=80, 
            height=15,
            selectmode=tk.SINGLE  # 仅允许选中单行
        )
        self.context_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 垂直滚动条：绑定列表框，实现列表滚动
        scrollbar = ttk.Scrollbar(context_frame, orient=tk.VERTICAL, command=self.context_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.context_listbox.config(yscrollcommand=scrollbar.set)  # 列表框联动滚动条
        
        # 删除按钮：触发删除选中行的方法
        self.delete_btn = ttk.Button(main_frame, text="删除选中对话", command=self.delete_selected)
        self.delete_btn.pack(fill=tk.X, pady=(0, 5))
        
        # 3. 操作按钮区域（功能按钮容器）
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 裁剪按钮：按配置的轮数裁剪上下文
        self.trim_btn = ttk.Button(btn_frame, text="按长度裁剪上下文", command=self.trim_context)
        self.trim_btn.pack(side=tk.LEFT, padx=5)
        
        # 保存按钮：保存处理后的结果到输出文件
        self.save_btn = ttk.Button(btn_frame, text="保存处理结果", command=self.save_processed_data)
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
    def load_input_data(self) -> None:
        """
        加载输入JSON文件的核心方法
        流程：读取文件 → 解析JSON → 初始化数据变量 → 更新界面显示
        异常处理：捕获文件读取/JSON解析错误，弹窗提示并退出程序
        返回值：None
        """
        try:
            # 以UTF-8编码读取JSON文件（避免中文乱码）
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)  # 解析JSON为Python字典
            
            # 解析数据到实例变量
            self.header = data["header"]          # 提取头信息（配置项）
            self.messages = data["body"]          # 提取原始对话消息体
            self.processed_context = self.messages.copy()  # 初始化处理列表（深拷贝避免原数据污染）
            
            # 更新头信息显示框
            self.header_text.config(state=tk.NORMAL)  # 临时启用编辑状态
            self.header_text.delete(1.0, tk.END)      # 清空原有内容（1.0表示第1行第0列，tk.END表示末尾）
            # 插入格式化后的JSON字符串（ensure_ascii=False保留中文，indent=2格式化缩进）
            self.header_text.insert(tk.END, json.dumps(self.header, ensure_ascii=False, indent=2))
            self.header_text.config(state=tk.DISABLED)  # 恢复只读状态
            
            # 刷新上下文列表的显示内容
            self.refresh_context_list()
            
        except Exception as e:
            # 捕获所有异常（文件不存在、JSON格式错误、键缺失等），弹窗提示
            messagebox.showerror("错误", f"加载输入文件失败：{e}")
            self.root.quit()  # 退出主窗口，终止程序
    
    def refresh_context_list(self) -> None:
        """
        刷新上下文列表框的显示内容
        流程：清空列表 → 遍历处理后的上下文 → 逐行插入简要信息
        返回值：None
        """
        self.context_listbox.delete(0, tk.END)  # 清空列表所有内容
        
        # 遍历处理后的上下文，逐个插入列表
        for idx, msg in enumerate(self.processed_context):
            role = msg.get("role", "未知")  # 获取消息角色（无则默认"未知"）
            # 截取内容前50字（避免过长），去除首尾空格
            content = msg.get("content", "").strip()[:50]
            # 格式化显示：[索引] 角色: 内容摘要...
            self.context_listbox.insert(tk.END, f"[{idx}] {role}: {content}...")
    
    def trim_context(self) -> None:
        """
        按头信息配置裁剪上下文的核心方法
        核心逻辑：
        1. 分离系统消息和用户/助手对话消息
        2. 按配置的轮数裁剪对话消息（每轮=user+assistant）
        3. 保留/剔除系统消息（按配置）
        4. 合并结果并刷新界面
        异常处理：捕获裁剪过程中的错误，弹窗提示
        返回值：None
        """
        try:
            # 从头部配置读取参数（无则默认值）
            context_rounds = self.header.get("context_rounds", 5)  # 保留的对话轮数，默认5轮
            keep_system = self.header.get("keep_system_prompt", True)  # 是否保留系统消息，默认保留
            
            # 1. 分离系统消息和对话消息（分类筛选）
            # 系统消息：role=system的消息（通常是初始提示词）
            system_msgs = [msg for msg in self.processed_context if msg["role"] == "system"]
            # 对话消息：role=user/assistant的消息（用户和助手的交互）
            dialog_msgs = [msg for msg in self.processed_context if msg["role"] in ["user", "assistant"]]
            
            # 2. 裁剪对话消息（保留最近N轮）
            if context_rounds > 0:
                keep_count = context_rounds * 2  # 每轮包含user+assistant，故×2
                # 截取最后N轮（列表切片：-keep_count表示取最后keep_count条）
                trimmed_dialog = dialog_msgs[-keep_count:] if len(dialog_msgs) > keep_count else dialog_msgs
            else:
                trimmed_dialog = []  # 若轮数为0，清空所有对话消息
            
            # 3. 合并最终上下文（系统消息+裁剪后的对话消息）
            self.processed_context = system_msgs if keep_system else []  # 按配置保留/清空系统消息
            self.processed_context.extend(trimmed_dialog)  # 追加裁剪后的对话消息
            
            # 4. 刷新列表显示并提示成功
            self.refresh_context_list()
            messagebox.showinfo("成功", f"已裁剪上下文至{context_rounds}轮")
            
        except Exception as e:
            # 捕获裁剪过程中的异常（如配置参数类型错误、列表操作错误等）
            messagebox.showerror("错误", f"裁剪上下文失败：{e}")
    
    def delete_selected(self) -> None:
        """
        删除列表中选中的单条上下文消息
        流程：检查选中状态 → 获取选中索引 → 删除对应数据 → 刷新列表
        异常处理：捕获删除过程中的错误，弹窗提示
        返回值：None
        """
        try:
            # 获取选中项的索引（curselection()返回元组，如(0,)表示选中第0行）
            selected_idx = self.context_listbox.curselection()
            if not selected_idx:
                # 无选中项时弹窗提示
                messagebox.showwarning("提示", "请选中要删除的对话")
                return
            
            # 提取选中的索引（取元组第一个元素）
            idx = selected_idx[0]
            del self.processed_context[idx]  # 删除处理列表中对应索引的消息
            self.refresh_context_list()      # 刷新列表显示
            
        except Exception as e:
            # 捕获删除过程中的异常（如索引越界、列表为空等）
            messagebox.showerror("错误", f"删除对话失败：{e}")
    
    def save_processed_data(self) -> None:
        """
        保存处理后的上下文数据到输出JSON文件
        流程：构造结果字典 → 写入文件 → 提示成功并退出程序
        异常处理：捕获文件写入错误，弹窗提示
        返回值：None
        """
        try:
            # 构造最终保存的结果字典
            result = {
                "header": self.header,  # 保留原始头信息
                "processed_context": self.processed_context,  # 处理后的上下文消息
                # 记录处理时间戳（精确到微秒，格式：年月日时分秒微秒）
                "process_timestamp": datetime.now().strftime("%Y%m%d%H%M%S%f")
            }
            
            # 以UTF-8编码写入JSON文件（ensure_ascii=False保留中文，indent=2格式化）
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 提示保存成功并关闭窗口
            messagebox.showinfo("成功", f"处理结果已保存至：{self.output_file}")
            self.root.quit()  # 退出主窗口循环，终止程序
            
        except Exception as e:
            # 捕获文件写入异常（如权限不足、路径不存在、磁盘满等）
            messagebox.showerror("错误", f"保存结果失败：{e}")

if __name__ == "__main__":
    """
    程序入口函数
    逻辑：
    1. 检查命令行参数数量（必须传入输入/输出文件路径）
    2. 解析参数并初始化GUI主窗口
    3. 启动GUI事件循环
    """
    # 检查命令行参数：sys.argv[0]是脚本名，sys.argv[1]和[2]是输入/输出文件
    if len(sys.argv) != 3:
        print("用法：python context_processor.py <输入JSON文件> <输出JSON文件>")
        sys.exit(1)  # 非0退出码表示执行失败
    
    # 解析命令行参数
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 初始化tkinter主窗口
    root = tk.Tk()
    # 创建GUI应用实例
    app = ContextProcessorGUI(root, input_file, output_file)
    # 启动主事件循环（阻塞，直到窗口关闭）
    root.mainloop()