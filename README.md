# Zaphkiel-bot
> 一款基于 Tkinter 开发的图形化 AI 聊天客户端，支持本地 Ollama 与豆包 API 双模式，可监听微信消息并自动回复

[![License](https://img.shields.io/github/license/yourname/Zaphkiel-bot)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](README.md)

一个简洁优雅的图形化 AI 沟通界面，支持微信 ClawBot 交互方式，可灵活切换本地大模型与云端 API，自定义上下文、系统提示词与聊天记录管理。

---

## ✨ 功能特性

### 🎯 核心功能
- **双 API 无缝切换**：本地 Ollama 模式 / 豆包 API 模式自由切换
- **流式对话体验**：文本输入、流式回复、思考过程实时展示
- **灵活上下文管理**：自定义保留对话轮数，系统提示词永久生效
- **聊天记录持久化**：自动保存/加载历史，支持导出为文本文件
- **丰富参数配置**：模型名称、API 地址、角色名称、系统人设均可自定义
- **微信自动回复**：监听微信消息并自动 AI 回复（需配套脚本）

### 🎨 UI 特性
- 简洁清爽的 Tkinter 图形界面，原生中文支持
- 角色消息颜色区分，阅读体验更佳
- 状态栏实时显示当前状态：就绪 / 思考中 / 微信模式
- 快捷键支持：`Ctrl+N` 新建对话，`Ctrl+Q` 退出

---

## 🧩 环境要求

### 基础依赖
- Python 3.8+
- 核心 Python 库：
```bash
pip install tkinter requests pillow openai
```

> 说明：tkinter 一般随 Python 自带；Linux 缺失可执行  
> `sudo apt-get install python3-tk`

### 可选依赖
- **Ollama 模式**：本地部署 Ollama 服务（默认端口 11434）
- **微信模式**：配套 `auth.py`（登录认证）+ `api.py`（消息收发）
- **豆包 API 模式**：有效 API Key 与接口地址

---

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install requests pillow openai
```

### 2. 启动程序
```bash
python ollama-engine.py
```

### 3. 基础配置
#### Ollama 模式（默认）
- 确保本地 Ollama 已启动：`ollama serve`
- 默认模型：`deepseek-r1:14b`

#### 豆包 API 模式
1. 「设置」→「切换 API 模式」选择外部模式
2. 「设置」→「设置 API 地址」配置 Key 与接口地址
3. 设置对应豆包模型名称

---

## 📖 界面说明

### 主界面布局
- **菜单栏**：文件 / 设置 / 历史 / 帮助
- **上下文配置区**：设置保留对话轮数（0=不携带上下文）
- **聊天历史区**：多角色彩色消息展示
- **输入区**：多行输入，回车发送，Shift+回车换行
- **状态栏**：实时状态提示

### 核心操作
- **发送消息**：输入文本 → 回车 / 点击发送
- **配置上下文**：输入轮数 → 保存配置
- **切换 API**：设置 → 切换 API 模式
- **微信模式**：设置 → 开启/关闭微信监听

---

## 📁 配置文件

程序运行后自动生成：
- `chat_history.json`：聊天记录持久化
- `chat_config.json`：用户配置（轮数、模型、API 模式等）
- `data/credentials.json`：微信登录凭证（微信模式）

---

## 📑 菜单功能详解

### 文件菜单
- 新建对话：清空当前记录，重置上下文
- 保存聊天记录：写入 `chat_history.json`
- 导出为文本：导出纯文本聊天记录
- 退出：关闭程序

### 设置菜单
- 设置模型：切换当前使用模型
- 切换 API 模式：Ollama / 外部 API
- 设置 API 地址：修改接口地址
- 开启/关闭微信模式：控制消息监听
- 设置系统提示词：自定义 AI 人设
- 设置角色名称：自定义用户/助手显示名

### 历史菜单
- 查看所有聊天记录
- 清除当前聊天记录

### 帮助菜单
- 查看当前上下文
- 关于（版本信息）
- 使用说明

---

## ❓ 常见问题

### Q1：提示“正在生成回复，请稍候！”但无响应
- 检查 Ollama / 豆包 API 服务是否正常
- 查看状态栏错误提示
- 确认网络连接正常（云端 API 模式）

### Q2：微信模式无法开启
- 确认 `auth.py`、`api.py` 存在于同目录
- 检查 `data/credentials.json` 是否正常生成
- 核对微信接口配置：token / bot_id / base_url

### Q3：上下文配置不生效
- 确认已点击「保存配置」
- 检查配置文件写入权限
- 重启程序重试

### Q4：豆包 API 调用失败
- 检查 API Key 是否正确
- 确认接口地址与模型名称配置正确
- 检查网络能否访问豆包 API

---

## 📄 许可证
本项目采用 **MIT License**，可自由使用、修改、分发。

---

## 🤝 贡献
欢迎提交 Issue、Pull Request 或提出功能建议！
