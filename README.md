# Zaphkiel-bot
一个简易的图形化AI沟通界面
OllamaChatGUI - 本地大模型 + 豆包 API 双模式聊天客户端

基于 Python Tkinter 开发的可视化本地大模型聊天工具，支持 Ollama 本地模型 与 火山方舟・豆包 API 无缝切换，自带上下文管理、聊天记录持久化、导出、个性化配置等完整功能。
🌟 项目亮点
双引擎支持：Ollama 本地模型 + 豆包在线 API 一键切换
可视化界面：Tkinter 原生 GUI，无浏览器依赖
上下文可控：自定义保留最近 N 轮对话，节省 Token / 显存
流式输出：逐字显示回复，支持思考过程展示
持久化存储：自动保存聊天记录与配置文件
一键导出：支持将对话导出为 TXT 文本
快捷键：回车发送、Shift + 回车换行、Ctrl+N 新建对话
🎨 界面样式规范
颜色配置
表格
元素	颜色值	显示效果
背景色	#f5f5f5	浅灰底色
用户名称	#4a7abc	蓝色粗体
助手名称	#509e2f	绿色粗体
系统消息	#880000	红色粗体
思考过程	#888888	灰色斜体
按钮主色	#4a7abc	蓝色按钮
字体配置
聊天文本：SimHei 12px
思考过程：SimHei 10px 斜体
标识文字：SimHei 8px
📦 环境安装
bash
运行
# 安装依赖
pip install requests openai
tkinter 一般随 Python 自带，Linux 缺失可执行：
bash
运行
sudo apt-get install python3-tk
🚀 快速运行
下载 / 克隆项目
运行主程序
bash
运行
python ollama-engine.py
📖 使用说明
1. 模式切换
Ollama 本地模式（默认）
启动本地 Ollama 服务
设置模型名：deepseek-r1:14b 等
API 地址默认：http://localhost:11434
豆包 API 模式
填写 API Key
基础地址：https://ark.cn-beijing.volces.com/api/v3
设置模型名：doubao-seed-2-0-lite-260215
2. 上下文配置
0：不携带历史对话
5：携带最近 5 轮对话
系统提示词默认始终保留
修改后点击 保存配置 生效
3. 常用操作
发送消息：回车
输入框换行：Shift + 回车
新建对话：Ctrl + N
退出：Ctrl + Q
导出记录：文件 → 导出为文本
清空对话：历史 → 清除当前聊天记录
📁 文件结构
plaintext
ollama-engine.py          # 主程序（GUI + 双API逻辑）
chat_history.json         # 自动保存聊天记录
chat_config.json          # 自动保存配置
README.md                 # 说明文档
requirements.txt           # 依赖清单
⚙️ 核心功能清单
✅ 新建 / 保存 / 加载 / 导出对话
✅ 切换 Ollama / 豆包 API
✅ 自定义系统提示词
✅ 自定义用户名、助手名、系统名
✅ 自定义上下文轮数
✅ 流式输出 + 思考过程显示
✅ 自动保存配置
✅ 状态栏实时提示
🐛 常见问题
1. 启动报错：缺少 openai
plaintext
pip install openai
2. Ollama 连接失败
确认 Ollama 已启动：ollama serve
确认模型已拉取：ollama list
检查 API 地址是否正确
3. 豆包 API 无响应
检查 API Key 是否正确
检查模型名与火山方舟控制台一致
检查网络可访问外网
📄 许可证
MIT License，自由使用、修改、分发。
🤝 贡献
欢迎提交 Issue、PR，或提出功能建议！
