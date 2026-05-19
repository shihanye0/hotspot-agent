# Hotspot Agent

每日自动抓取 GitHub Trending、Hacker News、ArXiv 的 AI/技术热点内容，经过去重和 DeepSeek 摘要生成中文日报，推送到 GitHub 仓库并通过邮件通知。

## 项目结构

```
hotspot-agent/
├── main.py                  # 入口，执行 python main.py 运行一次
├── config.py                # 配置中心（API Key、邮箱、路径）
├── .env                     # 敏感配置（不提交到 git）
├── .env.example             # 配置文件模板
├── requirements.txt         # Python 依赖
├── setup_task.bat           # Windows 计划任务注册脚本
├── agent/
│   ├── tools.py             # LangChain Tool 定义（8个工具）
│   ├── prompts.py           # DeepSeek 提示词模板
│   └── graph.py             # LangGraph 状态图（备用方案）
├── scrapers/
│   ├── github_trending.py   # GitHub Trending 爬虫（Trending页面 + Search API回退）
│   ├── hacker_news.py       # Hacker News 爬虫（30条并发 + AI关键词过滤）
│   └── arxiv.py             # ArXiv 论文爬虫（cs.AI，429自动重试）
├── memory/
│   ├── chroma_client.py     # 去重记忆库（JSON文件存储，30天自动清理）
│   └── embeddings.py        # 哈希嵌入向量生成
├── publishers/
│   ├── github_push.py       # Git 自动提交推送
│   └── email_sender.py      # SMTP 邮件通知
├── tests/                   # 测试套件（29个测试）
├── reports/                 # 生成的日报 Markdown
├── memory.json              # 去重记忆数据
└── docs/
    └── plans/               # 设计文档
```

## 快速启动

### 1. 环境准备

```bash
# 激活 conda 环境（E盘，避免占用C盘）
conda activate E:/conda_envs/hotspot-agent

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 配置

```bash
# 复制配置文件模板
cp .env.example .env

# 编辑 .env，填写你的配置：
#   DEEPSEEK_API_KEY=sk-xxx          DeepSeek API Key（必须）
#   SMTP_HOST=smtp.qq.com            SMTP 服务器
#   SMTP_USER=your_email@qq.com      发件邮箱
#   SMTP_PASS=授权码                  QQ邮箱授权码（不是QQ密码）
#   EMAIL_TO=recipient@example.com   收件邮箱
```

> QQ 邮箱授权码获取：QQ邮箱网页版 → 设置 → 账户 → POP3/SMTP服务 → 开启 → 生成授权码

### 3. 运行

```bash
# 手动运行一次
python main.py

# 运行测试
python -m pytest tests/ -v
```

### 4. 设置每日自动运行

```bash
# 方式一：双击运行（需管理员权限）
setup_task.bat

# 方式二：PowerShell（推荐）
powershell -Command "
\$action = New-ScheduledTaskAction -Execute 'E:\conda_envs\hotspot-agent\python' -Argument 'E:\hotspot-agent\main.py'
\$trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM
\$principal = New-ScheduledTaskPrincipal -UserId \$env:USERNAME -LogonType Interactive
Register-ScheduledTask -TaskName 'HotspotAgent' -Action \$action -Trigger \$trigger -Principal \$principal -Force
"

# 查看计划任务
schtasks /Query /TN HotspotAgent
```

## Agent 工作流程

1. **数据抓取** — 并行请求 GitHub Trending、Hacker News、ArXiv，每源取 10 条
2. **去重检查** — 查询 memory.json 中已处理过的记录，跳过重复内容
3. **日报生成** — DeepSeek 将原始数据汇总为结构化 Markdown 日报
4. **记忆存储** — 新内容存入 memory.json，用于后续去重
5. **发布** — 日报推送到 GitHub 仓库 + 邮件通知

## 数据源

| 数据源 | 内容 | 方式 |
|--------|------|------|
| GitHub Trending | 当日热门开源仓库 | Trending 页面（被墙时回退 Search API）|
| Hacker News | AI 相关热门讨论 | 官方 API（并行抓取30条，AI关键词过滤）|
| ArXiv | 最新 AI 论文（cs.AI）| 官方 API（429自动重试）|

## 技术栈

- **Agent 框架**：LangChain（Tool定义） + 直接 Pipeline（LangGraph备用）
- **大模型**：DeepSeek Chat API
- **记忆系统**：JSON 文件去重（30天轮转）
- **爬虫**：httpx + BeautifulSoup
- **通知**：GitPython + SMTP
- **调度**：Windows 计划任务

## 测试

```bash
python -m pytest tests/ -v    # 运行所有测试
python -m pytest tests/ -v -k scraper  # 只运行爬虫测试
```

## 环境要求

- Python 3.9+
- Windows（计划任务）或 Linux/Mac（cron）
- DeepSeek API Key
- SMTP 邮箱（可选，不配置则跳过邮件通知）
- Git（推送功能需要）

## 注意事项

- conda 环境必须创建在 E 盘（`--prefix E:/conda_envs/xxx`），避免占用 C 盘
- pip 安装优先使用清华源：`pip install xxx -i https://pypi.tuna.tsinghua.edu.cn/simple`
- .env 文件包含 API Key，已在 .gitignore 中排除
- GitHub 推送需要确保远程仓库已配置且 Token 有效
