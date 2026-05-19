# Hotspot Agent 实现进度

## 当前状态：已完成，可投产

### 已实现

1. **数据抓取模块** `scrapers/`
   - GitHub Trending（Trending 页面 + Search API 自动回退）
   - Hacker News（30 条并发抓取 + AI 关键词过滤）
   - ArXiv（cs.AI 论文，429 自动重试）

2. **记忆去重模块** `memory/`
   - JSON 文件存储，30 天自动清理
   - ID 级去重，避免重复推送

3. **日报生成** DeepSeek API
   - 结构化 Markdown 日报（GitHub + HN + ArXiv 三大板块）
   - 中文摘要 + 分类标签 + 趋势分析

4. **发布模块** `publishers/`
   - GitHub 推送：自动 commit + push 到 https://github.com/shihanye0/hotspot-agent
   - 邮件通知：QQ 邮箱 SMTP，已测试通过

5. **定时调度**
   - Windows 计划任务：每天 09:00 自动运行

### 验证结果

- 数据抓取：26 条/次（GitHub 10 + HN 10 + ArXiv 6）
- 日报生成：3000-4700 字符，结构清晰
- 邮件发送：QQ SMTP 测试通过
- 代码已推送：https://github.com/shihanye0/hotspot-agent
- 计划任务：已注册 "HotspotAgent"

### 快速使用

```bash
# 手动运行
cd E:/hotspot-agent && python main.py

# 查看日报
ls reports/

# 查看计划任务
schtasks /Query /TN HotspotAgent
```

### 踩坑记录

| 问题 | 解决 |
|------|------|
| GitHub Trending 被墙 | 回退到 GitHub Search API |
| HuggingFace 无法下载模型 | 改用 JSON 文件做记忆去重 |
| ChromaDB 默认 ONNX 模型需下载 | 自定义嵌入函数 → 最终弃用 ChromaDB |
| sentence-transformers segfault | 移除依赖 |
| LangGraph 线程池 segfault | 改用直接 pipeline |
| GitPython 找不到 git.exe | 设置 GIT_PYTHON_GIT_EXECUTABLE 环境变量 |
| Python 3.9 类型语法 | Optional[X] 替代 X \| None |
| Windows schtasks 编码问题 | 用 PowerShell 创建任务 |
