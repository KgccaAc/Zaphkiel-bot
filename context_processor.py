import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import json
import sys
from datetime import datetime
import os

# 固定存储历史勾选时间戳的文件（使用绝对路径避免目录问题）
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_deleted_timestamps.json")

class ContextProcessorGUI:
    def __init__(self, root: tk.Tk, input_file: str, output_file: str):
        self.root = root
        self.root.title("上下文处理器")
        self.root.geometry("900x650")

        self.input_file = input_file
        self.output_file = output_file

        self.header = {}
        self.messages = []
        self.check_vars = []
        self.auto_trim_var = tk.BooleanVar(value=True)
        # 核心：记录用户手动操作的状态（区分保留/删除，避免自动逻辑覆盖）
        self.manual_ops = {"keep": set(), "delete": set()}

        # 绑定关闭事件 → 关闭前保存手动操作记录
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_save)

        self.create_widgets()
        self.load_all_data()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 配置区域
        header_frame = ttk.LabelFrame(main_frame, text="配置")
        header_frame.pack(fill=tk.X, pady=(0,10))
        self.header_text = scrolledtext.ScrolledText(header_frame, height=4)
        self.header_text.pack(fill=tk.X, padx=5, pady=5)
        self.header_text.config(state=tk.DISABLED)

        # 消息勾选区域
        ctx_frame = ttk.LabelFrame(main_frame, text="勾选=删除")
        ctx_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(ctx_frame)
        self.scroll = ttk.Scrollbar(ctx_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮栏（新增重置手动标记按钮）
        btn_bar = ttk.Frame(main_frame)
        btn_bar.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(btn_bar, text="自动按轮勾选", variable=self.auto_trim_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="重置手动标记", command=self.reset_manual_ops).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar, text="保存并删除", command=self.save_and_delete).pack(side=tk.RIGHT, padx=5)

    # ----------------------
    # 工具方法：获取消息时间戳
    # ----------------------
    def get_ts(self, msg):
        if msg["role"] == "system":
            return "SYSTEM"
        return msg.get("timestamp", "")

    # ----------------------
    # 核心：加载用户手动操作记录（含过期清理）
    # ----------------------
    def load_manual_ops(self):
        """加载并清理过期的手动操作记录（只保留当前消息列表中存在的时间戳）"""
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                keep_candidate = set(data.get("keep", []))
                delete_candidate = set(data.get("delete", []))
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            # 首次使用/文件损坏，初始化空集合
            self.manual_ops = {"keep": set(), "delete": set()}
            return

        # 清理过期记录：只保留当前消息列表中存在的时间戳
        current_ts = {self.get_ts(msg) for msg in self.messages if self.get_ts(msg) != "SYSTEM"}
        self.manual_ops["keep"] = keep_candidate & current_ts
        self.manual_ops["delete"] = delete_candidate & current_ts

    # ----------------------
    # 核心：自动勾选逻辑（尊重用户手动操作优先级）
    # ----------------------
    def auto_trim_with_manual(self):
        """
        优先级规则（从高到低）：
        1. 用户手动标记保留 → 强制不勾选
        2. 用户手动标记删除 → 强制勾选
        3. 自动逻辑 → 勾选需要删除的消息
        """
        keep_rounds = int(self.header.get("context_rounds", 5))  # 确保是整数
        keep_sys = self.header.get("keep_system_prompt", True)

        # 1. 基础自动勾选逻辑（生成候选删除列表）
        sys_msg = [m for m in self.messages if m["role"] == "system"]
        chat_msg = [m for m in self.messages if m["role"] != "system"]
        keep_chat = chat_msg[-(keep_rounds * 2):] if keep_rounds > 0 else []
        keep_all_auto = sys_msg + keep_chat if keep_sys else keep_chat

        # 2. 结合手动操作设置最终勾选状态
        for idx, msg in enumerate(self.messages):
            ts = self.get_ts(msg)
            if ts == "SYSTEM":  # 系统消息默认不勾选
                self.check_vars[idx].set(False)
                continue

            # 优先级1：用户手动保留 → 强制不勾选
            if ts in self.manual_ops["keep"]:
                self.check_vars[idx].set(False)
            # 优先级2：用户手动删除 → 强制勾选
            elif ts in self.manual_ops["delete"]:
                self.check_vars[idx].set(True)
            # 优先级3：自动逻辑 → 勾选需要删除的
            else:
                self.check_vars[idx].set(msg not in keep_all_auto)

    # ----------------------
    # 核心：实时记录用户手动勾选/取消操作
    # ----------------------
    def on_check_toggle(self, idx, var):
        """用户手动切换勾选框时，实时更新手动操作记录"""
        ts = self.get_ts(self.messages[idx])
        if ts == "SYSTEM":  # 系统消息不记录
            return

        # 取消勾选 → 加入保留列表，移除删除列表
        if not var.get():
            self.manual_ops["keep"].add(ts)
            self.manual_ops["delete"].discard(ts)
        # 勾选 → 加入删除列表，移除保留列表
        else:
            self.manual_ops["delete"].add(ts)
            self.manual_ops["keep"].discard(ts)

    # ----------------------
    # 核心：关闭/保存时持久化手动操作记录
    # ----------------------
    def on_close_save(self):
        """保存用户手动操作记录到JSON文件"""
        # 转换集合为列表（JSON不支持集合）
        save_data = {
            "keep": list(self.manual_ops["keep"]),
            "delete": list(self.manual_ops["delete"])
        }

        # 确保保存目录存在
        save_dir = os.path.dirname(SAVE_FILE)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except PermissionError as e:
            messagebox.showerror("错误", f"保存手动操作记录失败：{str(e)}")

        self.root.destroy()

    # ----------------------
    # 优化：重置手动标记（恢复纯自动逻辑）
    # ----------------------
    def reset_manual_ops(self):
        """清空所有手动操作记录，恢复自动勾选逻辑"""
        self.manual_ops = {"keep": set(), "delete": set()}
        # 重新执行自动勾选逻辑
        if self.auto_trim_var.get():
            self.auto_trim_with_manual()
        self.refresh_checkbutton_state()
        messagebox.showinfo("提示", "已重置所有手动标记，恢复自动勾选逻辑")

    # ----------------------
    # 工具方法：刷新勾选框状态
    # ----------------------
    def refresh_checkbutton_state(self):
        """刷新所有Checkbutton的状态，确保变量绑定生效"""
        for idx, widget in enumerate(self.frame.winfo_children()):
            if isinstance(widget, ttk.Checkbutton) and idx < len(self.check_vars):
                widget.config(variable=self.check_vars[idx])
        # 刷新canvas滚动区域（防止内容溢出）
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ----------------------
    # 核心：加载输入JSON并初始化界面
    # ----------------------
    def load_all_data(self):
        try:
            with open(self.input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            messagebox.showerror("错误", f"加载输入文件失败：{str(e)}")
            self.root.quit()
            return

        # 解析JSON数据（兼容body/processed_context字段）
        self.header = data.get("header", {})
        self.messages = data.get("body") or data.get("processed_context", [])

        # 更新配置文本框
        self.header_text.config(state=tk.NORMAL)
        self.header_text.delete(1.0, tk.END)
        self.header_text.insert(1.0, json.dumps(self.header, ensure_ascii=False, indent=2))
        self.header_text.config(state=tk.DISABLED)

        # 1. 渲染消息勾选列表（绑定手动操作事件）
        self.refresh_list()

        # 2. 加载用户手动操作记录（含过期清理）
        self.load_manual_ops()

        # 3. 执行自动勾选逻辑（结合手动操作）
        if self.auto_trim_var.get():
            self.auto_trim_with_manual()

        # 4. 刷新界面确保状态生效
        self.refresh_checkbutton_state()

    # ----------------------
    # 核心：渲染消息勾选列表（绑定手动操作事件）
    # ----------------------
    def refresh_list(self):
        """清空并重新创建消息勾选列表，绑定手动切换事件"""
        # 清空原有控件和变量
        for w in self.frame.winfo_children():
            w.destroy()
        self.check_vars.clear()

        # 重新创建勾选框（每条消息对应一个）
        for idx, msg in enumerate(self.messages):
            var = tk.BooleanVar(value=False)
            self.check_vars.append(var)

            # 格式化显示文本（截断长内容）
            role = msg["role"]
            content = msg.get("content", "")[:50]
            ts = self.get_ts(msg)[:16]
            txt = f"[{idx}] {ts} | {role}: {content}..."

            # 创建勾选框并绑定手动操作事件
            cb = ttk.Checkbutton(
                self.frame, 
                text=txt, 
                variable=var,
                command=lambda idx=idx, var=var: self.on_check_toggle(idx, var)
            )
            cb.pack(anchor="w", pady=1)

    # ----------------------
    # 核心：保存筛选后的结果到输出JSON
    # ----------------------
    def save_and_delete(self):
        """筛选保留的消息，生成输出JSON并保存"""
        # 筛选保留/删除的消息
        kept = []
        deleted_ts = []
        for idx, msg in enumerate(self.messages):
            if not self.check_vars[idx].get():
                kept.append(msg)
            else:
                ts = self.get_ts(msg)
                if ts != "SYSTEM":
                    deleted_ts.append(ts)

        # 构造输出JSON结构
        out = {
            "header": self.header,
            "processed_context": kept,
            "deleted_timestamps": deleted_ts,
            "process_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # 保存输出文件
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
        except PermissionError as e:
            messagebox.showerror("错误", f"保存输出文件失败：权限不足 {str(e)}")
            return

        # 保存手动操作记录并提示结果
        self.on_close_save()
        messagebox.showinfo("完成", f"已保存！共保留 {len(kept)} 条消息，删除 {len(deleted_ts)} 条消息")
        self.root.quit()

if __name__ == "__main__":
    # 检查命令行参数合法性
    if len(sys.argv) != 3:
        messagebox.showerror("参数错误", "使用方式：python context_processor.py <输入文件路径> <输出文件路径>")
        sys.exit(1)

    # 启动GUI
    root = tk.Tk()
    app = ContextProcessorGUI(root, sys.argv[1], sys.argv[2])
    root.mainloop()
