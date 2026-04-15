import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog, simpledialog
import threading
import requests
import json
import time
import os
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any

# 新增：导入OpenAI客户端（豆包API依赖）
try:
    from openai import OpenAI
except ImportError:
    raise ImportError("请安装openai库：pip install openai")

class OllamaChatGUI:
    """
    Ollama本地大模型聊天界面类
    基于tkinter实现图形化界面，对接Ollama API/外部豆包API实现交互功能
    支持聊天记录保存/加载、配置管理、模型切换、系统提示词设置等功能
    """
    
    def __init__(self, root: tk.Tk):
        """
        初始化聊天界面主类
        :param root: tkinter的根窗口对象
        """
        # 根窗口配置
        self.root = root
        self.root.title("智能助手")
        self.root.geometry("1000x700")  # 初始窗口大小
        self.root.minsize(800, 600)     # 最小窗口大小
        
        # 主题颜色配置（UI美化相关）
        self.bg_color = "#f5f5f5"          # 背景色
        self.text_bg_color = "#ffffff"     # 文本框背景色
        self.user_color = "#4a7abc"        # 用户消息名称颜色
        self.assistant_color = "#509e2f"   # 助手消息名称颜色
        self.button_color = "#4a7abc"      # 按钮颜色
        self.button_text_color = "#ffffff" # 按钮文字颜色
        self.highlight_color = "#e0f0ff"   # 高亮色
        self.thought_color = "#888888"     # 思考过程文字颜色
        
        self.root.configure(bg=self.bg_color)
        
        # 聊天角色名称配置
        self.user_name = "用户"                  # 用户显示名称
        self.assistant_name = "Deepseek-r1:14b" # 助手显示名称
        self.system_name = "系统"                # 系统消息显示名称
        self.assistant_persona = "你是由deepseek公司训练的大型语言模型deepseek-r1。请以中文回答用户的问题。" # 助手人设
        
        # 文件路径配置
        self.current_dir = os.path.dirname(os.path.abspath(__file__))  # 当前脚本目录
        self.history_file = os.path.join(self.current_dir, "chat_history.json")  # 聊天记录保存路径
        self.config_file = os.path.join(self.current_dir, "chat_config.json")    # 配置文件保存路径
        
        # API相关配置
        self.ollama_base_url = "http://localhost:11434"  # Ollama API基础地址
        self.model = "deepseek-r1:14b"                   # 默认使用的模型名称
        self.system_prompt = "你是由deepseek公司训练的大型语言模型deepseek-r1。请以中文回答用户的问题。"  # 系统提示词
        self.messages = [{"role": "system", "content": self.system_prompt}]  # 聊天消息列表（初始包含系统提示词）
        
        # 回复状态变量
        self.current_response_id = None      # 当前回复的唯一标识（时间戳）
        self.current_response_text = ""      # 当前回复的文本内容
        self.is_responding = False           # 是否正在生成回复（防止重复发送）
        
        # 新增：API模式配置（ollama/external）
        self.api_mode = "ollama"  # 默认使用ollama模式
        # 外部API（豆包）配置
        self.external_api_key = ""  # 豆包API密钥
        self.external_base_url = "https://ark.cn-beijing.volces.com/api/v3"  # 豆包基础地址
        self.external_model = "doubao-seed-2-0-lite-260215"  # 豆包模型名称

        # ========== 关键修改：提前定义 context_rounds 相关属性 ==========
        self.context_rounds = 5  # 默认传递最近5轮对话（可在界面配置）
        self.keep_system_prompt = True  # 始终保留系统提示词
        # ==============================================================
        
        # 初始化UI组件（现在context_rounds已定义，创建控件时不会报错）
        self.create_menu()      # 创建菜单栏
        self.create_widgets()   # 创建核心控件
        
        # 加载配置和历史记录（加载配置会覆盖context_rounds的默认值，不影响）
        self.load_config()      # 加载用户配置
        self.load_history()     # 加载历史聊天记录
        
        # 显示欢迎信息
        self.display_message(self.system_name, "欢迎使用本智能助手！请输入问题开始对话。")
    def create_menu(self) -> None:
        """
        创建菜单栏
        包含文件、设置、历史、帮助四大菜单，每个菜单下有对应的功能项
        """
        menubar = tk.Menu(self.root)
        
        # 菜单配置：键为菜单名称，值为菜单项列表（标签、命令、快捷键）
        menu_options = {
            "文件": [
                ("新建对话", self.new_chat, "Ctrl+N"),
                ("-",),  # 分隔符
                ("保存聊天记录", self.save_chat_history),
                ("导出为文本", self.export_to_text),
                ("-",),
                ("退出", self.quit_application, "Ctrl+Q")
            ],
            "设置": [
                ("设置模型", self.set_model),
                ("切换API模式", self.switch_api_mode),
                ("设置API地址", self.set_api_url),  # 恢复原方法（仅Ollama模式可用）
                ("-",),
                ("设置系统提示词", self.set_system_prompt),
                ("设置用户名称", self.set_user_name),
                ("设置助手名称", self.set_assistant_name),
                ("设置助手人设", self.set_assistant_persona),
                ("-",),
                ("设置系统名称", self.set_system_name)
            ],
            "历史": [
                ("查看所有聊天记录", self.view_all_histories),
                ("清除当前聊天记录", self.clear_current_history)
            ],
            "帮助": [
                ("查看当前上下文", self.show_current_context),
                ("关于", self.show_about),
                ("使用说明", self.show_help)
            ]
        }
        
        # 遍历创建菜单
        for menu_name, items in menu_options.items():
            menu = tk.Menu(menubar, tearoff=0)  # tearoff=0 禁用菜单分离
            for item in items:
                if item[0] == "-":
                    menu.add_separator()  # 添加分隔符
                else:
                    kwargs = {"label": item[0], "command": item[1]}
                    if len(item) > 2:
                        kwargs["accelerator"] = item[2]  # 设置快捷键显示
                    menu.add_command(**kwargs)
            menubar.add_cascade(label=menu_name, menu=menu)
        
        # 绑定菜单栏到根窗口
        self.root.config(menu=menubar)
        # 绑定快捷键事件
        self.root.bind("<Control-n>", lambda event: self.new_chat())
        self.root.bind("<Control-q>", lambda event: self.quit_application())

    def create_widgets(self) -> None:
        """
        创建核心UI控件
        包括聊天历史显示框、输入框、发送按钮、状态栏等
        """
        # 主框架（用于统一管理布局）
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 聊天历史显示区域
        history_frame = ttk.LabelFrame(main_frame, text="聊天历史")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        #上下文长度配置区域
        context_frame = ttk.LabelFrame(main_frame, text="上下文配置")
        context_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 上下文长度标签+输入框
        ttk.Label(context_frame, text="上下文轮数:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.context_rounds_var = tk.StringVar(value=str(self.context_rounds))
        self.context_rounds_entry = ttk.Entry(context_frame, textvariable=self.context_rounds_var, width=10)
        self.context_rounds_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # 保存上下文配置按钮
        self.save_context_btn = ttk.Button(context_frame, text="保存配置", command=self.save_context_config)
        self.save_context_btn.grid(row=0, column=2, padx=5, pady=5)
        
         # 提示文本
        ttk.Label(context_frame, text="（0=不传递上下文，正数=保留最近N轮）").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # 带滚动条的文本框，用于显示聊天记录
        self.chat_history = scrolledtext.ScrolledText(
            history_frame, 
            wrap=tk.WORD,  # 自动换行
            bg=self.text_bg_color, 
            font=("SimHei", 12)  # 字体设置（支持中文）
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_history.config(state=tk.DISABLED)  # 默认设为只读
        
        # 输入区域框架
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 用户输入框（带滚动条）
        self.user_input = scrolledtext.ScrolledText(
            input_frame, 
            wrap=tk.WORD, 
            height=3,  # 初始高度（行数）
            bg=self.text_bg_color, 
            font=("SimHei", 12)
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.focus_set()  # 默认聚焦输入框
        self.user_input.bind("<Return>", self.on_enter_key)  # 绑定回车事件
        
        # 发送按钮
        self.send_button = ttk.Button(input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)
        
        # 状态栏（显示当前状态）
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN,  # 凹陷样式
            anchor=tk.W        # 文字左对齐
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def send_message(self) -> None:
        """
        发送用户消息的核心方法
        1. 获取并校验用户输入
        2. 显示用户消息到聊天框
        3. 清空输入框
        4. 记录消息到消息列表
        5. 启动线程调用LLM接口获取回复
        """
        # 防止重复发送
        if self.is_responding:
            messagebox.showwarning("提示", "正在生成回复，请稍候！")
            return
            
        # 获取用户输入（从第一行第一列到最后一行最后一列）并去除首尾空白
        user_message = self.user_input.get(1.0, tk.END).strip()
        if not user_message:  # 空消息不处理
            return
        
        # 显示用户消息到聊天界面
        self.display_message(self.user_name, user_message)
        # 清空输入框
        self.user_input.delete(1.0, tk.END)
        # 将用户消息添加到消息列表（用于调用API）
        self.messages.append({"role": "user", "content": user_message})
        
        # 生成当前回复的唯一ID（时间戳，精确到微秒）
        self.current_response_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.current_response_text = ""  # 初始化回复文本
        
        # 更新状态
        self.is_responding = True
        self.send_button.config(state=tk.DISABLED)
        # 更新状态栏
        current_model = self.model if self.api_mode == "ollama" else self.external_model
        self.status_var.set(f"正在使用 {current_model} 思考...")
        # 启动线程调用LLM接口（避免阻塞UI）
        threading.Thread(target=self.get_llm_response, daemon=True).start()

    def build_controlled_context(self) -> list:
        """改造：调用外部程序处理上下文"""
        # 1. 打包上下文为JSON文件
        context_data = {
            "header": {
                "system_prompt": self.system_prompt,
                "context_rounds": self.context_rounds,
                "keep_system_prompt": self.keep_system_prompt,
                "api_mode": self.api_mode,
                "timestamp": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "model": self.model if self.api_mode == "ollama" else self.external_model
            },
            "body": self.messages  # 原始上下文
        }
        
        # 2. 创建临时文件存储上下文（避免文件冲突）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(context_data, f, ensure_ascii=False, indent=2)
            input_file = f.name
        
        # 3. 调用外部上下文处理程序
        output_file = tempfile.mktemp(suffix='.json')  # 处理后的输出文件
        try:
            # 启动外部处理程序（需保证context_processor.py在同目录）
            subprocess.run(
                ["python", "context_processor.py", input_file, output_file],
                check=True,
                timeout=300  # 5分钟超时
            )
            
            # 4. 读取处理后的上下文
            with open(output_file, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            controlled_context = processed_data["processed_context"]
            
        except subprocess.TimeoutExpired:
            self._handle_error("处理超时", "上下文处理程序响应超时，使用原始上下文")
            controlled_context = super().build_controlled_context()  # 降级使用原有逻辑
        except Exception as e:
            self._handle_error("处理失败", f"上下文处理出错：{e}，使用原始上下文")
            controlled_context = super().build_controlled_context()  # 降级使用原有逻辑
        finally:
            # 清理临时文件
            os.unlink(input_file)
            if os.path.exists(output_file):
                os.unlink(output_file)
        
        return controlled_context

    def get_llm_response(self) -> None:
        """
        调用API获取模型回复（异步执行）
        支持Ollama本地模式/外部豆包API模式
        """
        controlled_context = self.build_controlled_context()
        assistant_response = ""
        thought_process = ""
        
        try:
            if self.api_mode == "ollama":
                # Ollama本地模式（原有逻辑保留）
                url = f"{self.ollama_base_url}/api/chat"
                headers = {"Content-Type": "application/json"}
                data = {
            "model": self.model,
            "messages": controlled_context,  # 替换为受控上下文
            "stream": True  # 流式响应（逐字返回）
        }
                
                with requests.post(url, headers=headers, json=data, stream=True, timeout=60) as response:
                    if response.status_code != 200:
                        error_msg = f"API调用失败: HTTP {response.status_code}, {response.text}"
                        self.root.after(0, self._handle_error, "API调用失败", error_msg)
                        return
                    
                    self.root.after(0, self._start_new_response)
                    
                    for line in response.iter_lines():
                        if line and not self.is_responding:  # 支持中断回复
                            break
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                line = line[6:]
                            try:
                                chunk = json.loads(line)
                                if chunk.get("done"):
                                    break
                                if 'message' in chunk and 'content' in chunk['message']:
                                    content = chunk['message']['content']
                                    if content:
                                        if "[Thinking]" in content:
                                            thought_content = content.replace("[Thinking]", "").strip()
                                            thought_process += thought_content
                                            self.root.after(0, self._update_thought, thought_process.strip())
                                        else:
                                            assistant_response += content
                                            self.root.after(0, self._update_response, content)
                            except json.JSONDecodeError:
                                continue
            
            else:
                # 外部豆包API模式（新增分支，放入你提供的格式转换代码）
                if not self.external_api_key:
                    self.root.after(0, self._handle_error, "配置错误", "外部API密钥未设置！")
                    return
                
                # 先导入OpenAI客户端（如果还没导入，需要在文件顶部加：from openai import OpenAI）
                from openai import OpenAI
                client = OpenAI(
                    base_url=self.external_base_url,
                    api_key=self.external_api_key,
                )
                
                # ========== 这里就是你要插入的格式转换代码 ==========
                # 转换消息格式（包含历史上下文）
                input_messages = []
                for msg in self.messages:
                    if msg["role"] == "system":
                        # 系统消息直接使用字符串格式
                        input_messages.append({
                            "role": "system",
                            "content": msg["content"]
                        })
                    elif msg["role"] in ["user", "assistant"]:
                        # 用户/助手消息使用正确的type格式（text而非input_text）
                        input_messages.append({
                            "role": msg["role"],
                            "content": [{"type": "text", "text": msg["content"]}]
                        })
                # ========== 格式转换代码结束 ==========
                
                # 初始化回复显示
                self.root.after(0, self._start_new_response)
                
                # 调用豆包API（流式响应）
                stream = client.chat.completions.create(
                    model=self.external_model,
                    messages=input_messages,
                    stream=True,
                    temperature=0.7,
                    timeout=60  # 超时控制
                )
                
                # 处理流式响应
                for chunk in stream:
                    if not self.is_responding:  # 支持中断
                        break
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        assistant_response += content
                        self.root.after(0, self._update_response, content)
            
            # 记录回复到消息列表
            if assistant_response:
                self.messages.append({"role": "assistant", "content": assistant_response})
                self.root.after(0, self.save_history)
        
        except requests.exceptions.RequestException as e:
            self.root.after(0, self._handle_error, "网络请求错误", str(e))
        except Exception as e:
            self.root.after(0, self._handle_error, "外部API调用失败", str(e))
        finally:
            # 重置UI状态
            self.root.after(0, self.reset_ui_state)

    def _start_new_response(self) -> None:
        """
        内部方法：初始化助手回复的显示格式
        在聊天框中添加助手名称和回复ID标识
        """
        self.chat_history.config(state=tk.NORMAL)  # 临时解除只读
        # 添加助手名称
        self.chat_history.insert(tk.END, f"{self.assistant_name}: ", f"name_{self.assistant_name}")
        # 添加回复ID（用于区分不同回复）
        self.chat_history.insert(tk.END, f"[{self.current_response_id}]\n", "response_id")
        
        # 配置文字样式
        self.chat_history.tag_configure(f"name_{self.assistant_name}", foreground=self.assistant_color, font=("SimHei", 12, "bold"))
        self.chat_history.tag_configure("response_id", foreground="#999999", font=("SimHei", 8))
        
        # 滚动到最新消息
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)  # 恢复只读

    def _update_response(self, content: str) -> None:
        """
        内部方法：实时更新助手回复内容到聊天框
        :param content: 新增的回复文本片段
        """
        if not content:
            return
        self.chat_history.config(state=tk.NORMAL)
        self.chat_history.insert(tk.END, content)  # 追加文本
        self.chat_history.see(tk.END)             # 滚动到末尾
        self.chat_history.config(state=tk.DISABLED)

    def _update_thought(self, thought_content: str) -> None:
        """
        内部方法：更新思考过程显示
        特殊处理思考过程的文本替换（避免重复显示）
        :param thought_content: 思考过程文本
        """
        if not thought_content:
            return
        self.chat_history.config(state=tk.NORMAL)
        # 获取当前聊天框所有内容
        content = self.chat_history.get(1.0, tk.END)
        # 查找思考过程的起始位置
        thought_marker = "思考过程: "
        thought_start = content.rfind(thought_marker)
        
        if thought_start == -1:
            # 首次添加思考过程
            self.chat_history.insert(tk.END, f"\n{thought_marker}", f"name_思考过程")
            self.chat_history.insert(tk.END, thought_content)
        else:
            # 计算思考过程文本的起始索引
            content_start = thought_start + len(thought_marker)
            line_count = content[:content_start].count('\n')
            content_start_index = f"{1 + line_count}.0"
            
            # 计算思考过程文本的结束索引
            next_newline = content.find('\n', content_start)
            if next_newline != -1:
                next_line = content.count('\n', 0, next_newline) + 1
                content_end_index = f"{next_line}.0"
            else:
                content_end_index = tk.END
            
            # 删除原有思考过程，插入新内容
            self.chat_history.delete(content_start_index, content_end_index)
            self.chat_history.insert(content_start_index, thought_content)
        
        self.chat_history.see(tk.END)
        self.chat_history.tag_configure("name_思考过程", foreground=self.thought_color, font=("SimHei", 10, "italic"))
        self.chat_history.config(state=tk.DISABLED)

    def reset_ui_state(self) -> None:
        """
        重置UI状态
        恢复状态栏、发送按钮、输入框焦点
        """
        self.is_responding = False
        self.status_var.set("准备就绪")
        self.send_button.config(state=tk.NORMAL)
        self.user_input.focus_set()

    def on_enter_key(self, event: tk.Event) -> str:
        """
        处理回车按键事件
        - 按住Shift+回车：换行
        - 直接回车：发送消息
        :param event: 按键事件对象
        :return: "break" 阻止事件冒泡
        """
        # 判断是否按下Shift键（event.state & 0x0001是Shift键，0x0004是CapsLock，0x0008是Alt，0x0002是Ctrl）
        if event.state & 0x0001:  # Shift键按下
            self.user_input.insert(tk.INSERT, "\n")  # 插入换行符
            return "break"
        else:
            # 先判断输入框是否为空，避免发送空消息
            user_message = self.user_input.get(1.0, tk.END).strip()
            if user_message:
                self.send_message()  # 发送消息
            return "break"

    def save_context_config(self) -> None:
        """保存上下文长度配置"""
        try:
            rounds = int(self.context_rounds_var.get())
            if rounds < 0:
                raise ValueError("不能为负数")
            self.context_rounds = rounds
            self.display_message(self.system_name, f"上下文轮数已设置为: {rounds}")
            self.save_config()  # 同步保存到配置文件
        except ValueError as e:
            messagebox.showerror("错误", f"无效的数值：{e}")
            self.context_rounds_var.set(str(self.context_rounds))  # 恢复原值

    def display_message(self, sender: str, message: str) -> None:
        """
        通用消息显示方法
        根据发送者类型设置不同的文字样式
        :param sender: 发送者名称（用户/助手/系统）
        :param message: 消息内容
        """
        self.chat_history.config(state=tk.NORMAL)
        # 插入发送者名称
        self.chat_history.insert(tk.END, f"{sender}: ", f"name_{sender}")
        # 插入消息内容（末尾加两个换行分隔）
        self.chat_history.insert(tk.END, f"{message}\n\n")
        
        # 根据发送者类型配置文字样式
        if sender == self.user_name:
            self.chat_history.tag_configure(f"name_{sender}", foreground=self.user_color, font=("SimHei", 12, "bold"))
        elif sender == self.assistant_name:
            self.chat_history.tag_configure(f"name_{sender}", foreground=self.assistant_color, font=("SimHei", 12, "bold"))
        elif sender == self.system_name:
            self.chat_history.tag_configure(f"name_{sender}", foreground="#880000", font=("SimHei", 12, "bold"))
        elif sender == "思考过程":
            self.chat_history.tag_configure(f"name_{sender}", foreground=self.thought_color, font=("SimHei", 12, "bold"))
        
        # 滚动到最新消息
        self.chat_history.see(tk.END)
        self.chat_history.config(state=tk.DISABLED)

    def save_history(self) -> None:
        """
        保存聊天历史到JSON文件
        包含消息列表和时间戳
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            # 写入JSON文件（格式化输出，支持中文）
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "messages": self.messages,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 处理保存异常
            self._handle_error("保存聊天历史失败", str(e))

    def load_history(self) -> None:
        """
        从JSON文件加载聊天历史
        并将历史消息显示到聊天界面
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # 加载消息列表（默认使用系统提示词）
                    self.messages = history.get("messages", [{"role": "system", "content": self.system_prompt}])
                
                # 遍历历史消息并显示
                for msg in self.messages:
                    if msg["role"] == "user":
                        self.display_message(self.user_name, msg["content"])
                    elif msg["role"] == "assistant":
                        self.display_message(self.assistant_name, msg["content"])
        except Exception as e:
            # 处理加载异常
            self._handle_error("加载聊天历史失败", str(e))
            # 重置为默认消息列表
            self.messages = [{"role": "system", "content": self.system_prompt}]

    def save_config(self) -> None:
        """
        保存用户配置到JSON文件
        包括名称、模型、API地址、提示词等配置项
        """
        try:
            # 构造配置字典
            config = {
                "user_name": self.user_name,
                "assistant_name": self.assistant_name,
                "system_name": self.system_name,
                "system_prompt": self.system_prompt,
                "model": self.model,
                "ollama_base_url": self.ollama_base_url,
                "assistant_persona": self.assistant_persona,
                "api_mode": self.api_mode,
                "external_api_key": self.external_api_key,
                "external_base_url": self.external_base_url,
                "external_model": self.external_model,
                "context_rounds": self.context_rounds,  
                "keep_system_prompt": self.keep_system_prompt  
            }
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # 处理保存异常
            self._handle_error("保存配置失败", str(e))

    def load_config(self) -> None:
        """
        从JSON文件加载用户配置
        并更新到类属性中
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 加载配置项（带默认值）
                self.user_name = config.get("user_name", self.user_name)
                self.assistant_name = config.get("assistant_name", self.assistant_name)
                self.system_name = config.get("system_name", self.system_name)
                self.system_prompt = config.get("system_prompt", self.system_prompt)
                self.model = config.get("model", self.model)
                self.ollama_base_url = config.get("ollama_base_url", self.ollama_base_url)
                self.assistant_persona = config.get("assistant_persona", self.assistant_persona)
                self.api_mode = config.get("api_mode", self.api_mode)
                self.external_api_key = config.get("external_api_key", self.external_api_key)
                self.external_base_url = config.get("external_base_url", self.external_base_url)
                self.external_model = config.get("external_model", self.external_model)
                self.context_rounds = config.get("context_rounds", 5)
                self.keep_system_prompt = config.get("keep_system_prompt", True)
                self.context_rounds_var.set(str(self.context_rounds))  
                
                # 校验外部API配置
                if self.api_mode == "external" and not self.external_api_key:
                    self.root.after(0, messagebox.showwarning, "配置提示", "外部API密钥未设置，将自动切换到Ollama模式！")
                    self.api_mode = "ollama"
                
                # 更新系统提示词到消息列表
                if self.messages and len(self.messages) > 0 and self.messages[0]["role"] == "system":
                    self.messages[0]["content"] = self.system_prompt
        except Exception as e:
            # 处理加载异常
            self._handle_error("加载配置失败", str(e))

    def new_chat(self) -> None:
        """
        开始新的聊天对话
        1. 提示用户确认
        2. 保存当前聊天记录
        3. 清空消息列表和聊天界面
        4. 重置回复状态变量
        5. 显示新对话提示
        """
        if self.messages and len(self.messages) > 1:
            # 有历史消息时确认是否新建
            if messagebox.askyesno("确认", "是否开始新的聊天？当前记录将保存。"):
                self.save_history()
                # 完全重置消息列表（只保留最新的系统提示词）
                self.messages = [{"role": "system", "content": self.system_prompt}]
                # 重置回复状态变量（关键修复）
                self.current_response_id = None
                self.current_response_text = ""
                # 清空聊天界面
                self.chat_history.config(state=tk.NORMAL)
                self.chat_history.delete(1.0, tk.END)
                self.chat_history.config(state=tk.DISABLED)
                # 显示新对话提示
                self.display_message(self.system_name, f"已开始新对话 | 模型: {self.model}")
        else:
            # 无历史消息直接新建
            self.messages = [{"role": "system", "content": self.system_prompt}]
            self.current_response_id = None
            self.current_response_text = ""
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.delete(1.0, tk.END)
            self.chat_history.config(state=tk.DISABLED)
            self.display_message(self.system_name, f"已开始新对话 | 模型: {self.model}")
    def save_chat_history(self) -> None:
        """
        手动保存聊天记录（菜单调用）
        保存后显示提示信息
        """
        self.save_history()
        self.display_message(self.system_name, "聊天记录已保存。")

    def export_to_text(self) -> None:
        """
        导出聊天记录为纯文本文件
        1. 校验是否有可导出的记录
        2. 弹出保存文件对话框
        3. 按格式写入文本文件
        """
        if not self.messages or len(self.messages) <= 1:
            messagebox.showinfo("导出", "无聊天记录可导出。")
            return
        
        try:
            # 弹出保存文件对话框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt", 
                filetypes=[("文本文件", "*.txt")],
                title="导出聊天记录"
            )
            if file_path:
                # 写入文本文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"聊天记录 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"模式: {self.api_mode} | 模型: {self.model if self.api_mode == 'ollama' else self.external_model}\n\n")
                    # 遍历消息列表写入
                    for msg in self.messages:
                        if msg["role"] == "system":
                            f.write(f"系统提示:\n{msg['content']}\n\n")
                        elif msg["role"] == "user":
                            f.write(f"{self.user_name}:\n{msg['content']}\n\n")
                        elif msg["role"] == "assistant":
                            f.write(f"{self.assistant_name}:\n{msg['content']}\n\n")
                # 显示导出成功提示
                self.display_message(self.system_name, f"已导出至: {file_path}")
        except Exception as e:
            # 处理导出异常
            self._handle_error("导出失败", str(e))

    def set_model(self) -> None:
        """
        设置模型名称
        弹出输入框，确认后更新模型并保存配置
        """
        if self.is_responding:
            messagebox.showwarning("提示", "正在生成回复，无法修改模型！")
            return
            
        current_model = self.model if self.api_mode == "ollama" else self.external_model
        model = simpledialog.askstring(
            "设置模型", 
            f"请输入{'Ollama' if self.api_mode == 'ollama' else '豆包'}模型名称:", 
            initialvalue=current_model
        )
        if model and model.strip():
            if self.api_mode == "ollama":
                self.model = model.strip()
            else:
                self.external_model = model.strip()
            self.display_message(self.system_name, f"模型已设为: {model.strip()}")
            self.save_config()

    def set_api_url(self) -> None:
        """
        设置API地址（区分模式）
        """
        if self.is_responding:
            messagebox.showwarning("提示", "正在生成回复，无法修改API地址！")
            return
            
        if self.api_mode != "ollama":
            messagebox.showinfo("提示", "当前为外部API模式，请在切换API模式窗口中修改地址！")
            return
            
        url = simpledialog.askstring("设置Ollama API地址", "请输入API地址:", initialvalue=self.ollama_base_url)
        if url and url.strip():
            self.ollama_base_url = url.strip()
            self.display_message(self.system_name, f"Ollama API地址已设为: {self.ollama_base_url}")
            self.save_config()

    def switch_api_mode(self) -> None:
        """
        切换API模式（Ollama/外部豆包模型）
        弹出窗口选择模式，并配置外部API参数
        """
        if self.is_responding:
            messagebox.showwarning("提示", "正在生成回复，无法切换API模式！")
            return
            
        # 创建模式切换窗口
        mode_window = tk.Toplevel(self.root)
        mode_window.title("切换API模式")
        mode_window.geometry("500x350")
        mode_window.transient(self.root)
        mode_window.grab_set()  # 模态窗口
        
        # 模式选择框架
        mode_frame = ttk.LabelFrame(mode_window, text="选择API模式")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)

        # 单选按钮：模式选择
        mode_var = tk.StringVar(value=self.api_mode)
        ttk.Radiobutton(mode_frame, text="Ollama本地模式", variable=mode_var, value="ollama").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Radiobutton(mode_frame, text="外部豆包模型模式", variable=mode_var, value="external").pack(anchor=tk.W, padx=10, pady=5)

        # 外部API配置框架
        external_frame = ttk.LabelFrame(mode_window, text="外部豆包API配置")
        external_frame.pack(fill=tk.X, padx=10, pady=10)

        # API密钥输入
        ttk.Label(external_frame, text="API密钥:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        api_key_entry = ttk.Entry(external_frame, width=50, show="*")  # 密码隐藏
        api_key_entry.grid(row=0, column=1, padx=5, pady=5)
        api_key_entry.insert(0, self.external_api_key)

        # 基础地址输入
        ttk.Label(external_frame, text="基础地址:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        base_url_entry = ttk.Entry(external_frame, width=50)
        base_url_entry.grid(row=1, column=1, padx=5, pady=5)
        base_url_entry.insert(0, self.external_base_url)

        # 模型名称输入
        ttk.Label(external_frame, text="模型名称:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        model_entry = ttk.Entry(external_frame, width=50)
        model_entry.grid(row=2, column=1, padx=5, pady=5)
        model_entry.insert(0, self.external_model)

        # 确认按钮回调（修正缩进和self绑定）
        def on_confirm():
            new_mode = mode_var.get()
            # 如果是外部模式，更新配置
            if new_mode == "external":
                api_key = api_key_entry.get().strip()
                base_url = base_url_entry.get().strip()
                model_name = model_entry.get().strip()
                
                # 校验必填项
                if not api_key:
                    messagebox.showwarning("警告", "外部模式必须填写API密钥！")
                    return
                if not base_url:
                    messagebox.showwarning("警告", "外部模式必须填写基础地址！")
                    return
                if not model_name:
                    messagebox.showwarning("警告", "外部模式必须填写模型名称！")
                    return
                
                # 更新外部API配置
                self.external_api_key = api_key
                self.external_base_url = base_url
                self.external_model = model_name
                self.api_mode = new_mode
                self.display_message(self.system_name, f"已切换至外部豆包模型模式，模型：{self.external_model}")
            else:
                # 切回ollama模式
                self.api_mode = new_mode
                self.display_message(self.system_name, f"已切换至Ollama本地模式，地址：{self.ollama_base_url}")
            
            # 保存配置
            self.save_config()
            mode_window.destroy()

        # 按钮布局（修正变量名拼写错误）
        btn_frame = tk.Frame(mode_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="确认", command=on_confirm).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(btn_frame, text="取消", command=mode_window.destroy).pack(side=tk.RIGHT, padx=10, pady=10)

    def set_system_prompt(self) -> None:
        """
        设置系统提示词（带多行输入框）
        弹出新窗口，支持多行编辑，确认后更新并保存配置
        """
        # 创建新窗口
        prompt_window = tk.Toplevel(self.root)
        prompt_window.title("设置系统提示词")
        prompt_window.geometry("600x400")
        prompt_window.transient(self.root)  # 设为临时窗口（依附于主窗口）
        
        # 多行文本输入框
        prompt_text = scrolledtext.ScrolledText(
            prompt_window, 
            wrap=tk.WORD, 
            height=15, 
            font=("SimHei", 10)
        )
        prompt_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        prompt_text.insert(tk.END, self.system_prompt)  # 填充当前提示词
        
        # 确认按钮回调
        def on_confirm():
            new_prompt = prompt_text.get(1.0, tk.END).strip()
            if new_prompt:
                self.system_prompt = new_prompt
                # 完全重置消息列表（只保留新的系统提示词，关键修复）
                self.messages = [{"role": "system", "content": self.system_prompt}]
                self.current_response_id = None
                self.current_response_text = ""
                # 清空界面并提示
                self.chat_history.config(state=tk.NORMAL)
                self.chat_history.delete(1.0, tk.END)
                self.chat_history.config(state=tk.DISABLED)
                self.display_message(self.system_name, "系统提示词已更新，已重置对话上下文。")
                self.save_config()
            prompt_window.destroy()
        
        # 按钮布局
        ttk.Button(prompt_window, text="确认", command=on_confirm).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(prompt_window, text="取消", command=prompt_window.destroy).pack(side=tk.RIGHT, padx=10, pady=10)

    def set_user_name(self) -> None:
        """
        设置用户显示名称
        弹出输入框，确认后更新名称并保存配置
        """
        name = simpledialog.askstring("设置用户名称", "请输入您的名称:", initialvalue=self.user_name)
        if name and name.strip():
            self.user_name = name.strip()
            self.display_message(self.system_name, f"用户名已设为: {self.user_name}")
            self.save_config()

    def set_assistant_name(self) -> None:
        """
        设置助手显示名称
        弹出输入框，确认后更新名称并保存配置
        """
        name = simpledialog.askstring("设置助手名称", "请输入助手名称:", initialvalue=self.assistant_name)
        if name and name.strip():
            self.assistant_name = name.strip()
            self.display_message(self.system_name, f"助手名称已设为: {self.assistant_name}")
            self.save_config()

    def set_assistant_persona(self) -> None:
        """
        设置助手人设
        弹出多行输入框，确认后更新人设并保存配置
        """
        # 创建新窗口
        persona_window = tk.Toplevel(self.root)
        persona_window.title("设置助手人设")
        persona_window.geometry("600x300")
        persona_window.transient(self.root)
        persona_window.grab_set()
        
        # 多行文本输入框
        persona_text = scrolledtext.ScrolledText(
            persona_window, 
            wrap=tk.WORD, 
            height=10, 
            font=("SimHei", 10)
        )
        persona_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        persona_text.insert(tk.END, self.assistant_persona)
        
        # 确认按钮回调
        def on_confirm():
            new_persona = persona_text.get(1.0, tk.END).strip()
            if new_persona:
                self.assistant_persona = new_persona
                self.display_message(self.system_name, "助手人设已更新。")
                self.save_config()
            persona_window.destroy()
        
        # 按钮布局
        btn_frame = tk.Frame(persona_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="确认", command=on_confirm).pack(side=tk.LEFT, padx=10, pady=10)
        ttk.Button(btn_frame, text="取消", command=persona_window.destroy).pack(side=tk.RIGHT, padx=10, pady=10)

    def set_system_name(self) -> None:
        """
        设置系统消息显示名称
        弹出输入框，确认后更新名称并保存配置
        """
        name = simpledialog.askstring("设置系统名称", "请输入系统消息显示名称:", initialvalue=self.system_name)
        if name and name.strip():
            self.system_name = name.strip()
            self.display_message(self.system_name, f"系统名称已设为: {self.system_name}")
            self.save_config()

    def view_all_histories(self) -> None:
        """
        查看所有聊天记录
        弹出窗口显示完整历史记录
        """
        if not self.messages or len(self.messages) <= 1:
            messagebox.showinfo("查看历史", "暂无聊天记录！")
            return
            
        # 创建历史记录窗口
        history_window = tk.Toplevel(self.root)
        history_window.title("所有聊天记录")
        history_window.geometry("800x600")
        history_window.transient(self.root)
        history_window.grab_set()
        
        # 历史记录文本框
        history_text = scrolledtext.ScrolledText(
            history_window, 
            wrap=tk.WORD, 
            font=("SimHei", 10)
        )
        history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        history_text.config(state=tk.NORMAL)
        
        # 写入历史记录
        history_text.insert(tk.END, f"聊天记录 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        history_text.insert(tk.END, f"当前模式: {self.api_mode} | 模型: {self.model if self.api_mode == 'ollama' else self.external_model}\n")
        history_text.insert(tk.END, "="*50 + "\n\n")
        
        for msg in self.messages:
            if msg["role"] == "system":
                history_text.insert(tk.END, "【系统提示】\n", "system")
                history_text.insert(tk.END, f"{msg['content']}\n\n")
            elif msg["role"] == "user":
                history_text.insert(tk.END, f"【{self.user_name}】\n", "user")
                history_text.insert(tk.END, f"{msg['content']}\n\n")
            elif msg["role"] == "assistant":
                history_text.insert(tk.END, f"【{self.assistant_name}】\n", "assistant")
                history_text.insert(tk.END, f"{msg['content']}\n\n")
        
        # 设置样式
        history_text.tag_configure("system", foreground="#880000", font=("SimHei", 10, "bold"))
        history_text.tag_configure("user", foreground=self.user_color, font=("SimHei", 10, "bold"))
        history_text.tag_configure("assistant", foreground=self.assistant_color, font=("SimHei", 10, "bold"))
        
        history_text.config(state=tk.DISABLED)
        
        # 关闭按钮
        ttk.Button(history_window, text="关闭", command=history_window.destroy).pack(pady=10)

    def clear_current_history(self) -> None:
        """
        清除当前聊天记录
        确认后清空聊天界面和消息列表（保留系统提示词）
        同时重置回复状态变量
        """
        if messagebox.askyesno("确认", "是否清除当前聊天记录？"):
            # 重置消息列表（只保留系统提示词）
            self.messages = [{"role": "system", "content": self.system_prompt}]
            # 重置回复状态变量（关键修复）
            self.current_response_id = None
            self.current_response_text = ""
            # 清空界面
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.delete(1.0, tk.END)
            self.chat_history.config(state=tk.DISABLED)
            self.display_message(self.system_name, "当前聊天记录已清除。")

    def show_about(self) -> None:
        """
        显示关于信息
        弹出关于窗口，展示软件版本、作者等信息
        """
        about_text = f"""
低成本智能助手 v2.0
基于tkinter实现的多模式聊天界面
支持：
- Ollama本地大模型（如DeepSeek-R1）
- 外部豆包API模型

当前模式：{self.api_mode}
当前模型：{self.model if self.api_mode == 'ollama' else self.external_model}

使用前请确保：
1. Ollama模式：本地已启动Ollama服务
2. 豆包模式：配置正确的API密钥和地址
        """
        messagebox.showinfo("关于", about_text)

    def show_help(self) -> None:
        """
        显示使用说明
        弹出帮助窗口，展示操作指南
        """
        help_text = """
使用说明：
1. 输入框中输入问题，按回车或点击发送按钮发送
2. Ctrl+回车可在输入框中换行
3. 可通过菜单栏设置模型、API地址、提示词等
4. 聊天记录会自动保存，也可手动导出为文本文件
5. 新建对话会保存当前记录并清空界面

API模式说明：
- Ollama模式：对接本地Ollama服务（默认地址：http://localhost:11434）
- 豆包模式：对接火山方舟豆包API（需配置密钥）

快捷键：
- Ctrl+N: 新建对话
- Ctrl+Q: 退出程序
        """
        messagebox.showinfo("使用说明", help_text)
        
    def show_current_context(self) -> None:
        """
        调试功能：显示当前的消息上下文
        用于验证新建对话/清除记录是否真的清空了上下文
        """
        # 过滤掉system消息，只显示用户/助手的对话记录
        dialog_messages = [msg for msg in self.messages if msg["role"] in ["user", "assistant"]]
        if not dialog_messages:
            context_text = "当前无对话上下文（仅保留系统提示词）"
        else:
            context_text = f"当前对话上下文共 {len(dialog_messages)} 条：\n"
            for i, msg in enumerate(dialog_messages, 1):
                context_text += f"{i}. {msg['role']}: {msg['content'][:50]}...\n"
        
        messagebox.showinfo("当前上下文", context_text)

    def quit_application(self) -> None:
        """
        退出应用程序
        确认后保存聊天记录并关闭窗口
        """
        if self.is_responding:
            if not messagebox.askyesno("退出", "正在生成回复，确定要退出吗？"):
                return
        
        if messagebox.askyesno("退出", "是否退出应用？当前聊天记录将自动保存。"):
            self.save_history()
            self.root.quit()

    def _handle_error(self, title: str, message: str) -> None:
        """
        内部方法：统一错误处理
        显示错误提示并更新状态栏
        :param title: 错误标题
        :param message: 错误详情
        """
        messagebox.showerror(title, message)
        self.status_var.set(f"错误: {title}")
        # 重置响应状态
        self.is_responding = False
        self.send_button.config(state=tk.NORMAL)

# 程序入口
if __name__ == "__main__":
    # 设置中文显示（Windows/Linux/Mac兼容）
    try:
        import platform
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    app = OllamaChatGUI(root)
    root.mainloop()