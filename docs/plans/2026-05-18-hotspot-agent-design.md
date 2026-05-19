# Hotspot Agent 设计文档

## 项目目标

构建一个 AI Agent，每日自动抓取 GitHub Trending、Hacker News、ArXiv 等源的热点内容，经过去重、AI 摘要后生成中文日报，推送到 GitHub 仓库并通过邮件通知。

## 技术栈

- Agent 框架：LangChain + LangGraph
- LLM：DeepSeek Chat API
- 向量记忆：ChromaDB + BGE 嵌入模型
- 爬取：httpx + BeautifulSoup + 各源官方 API
- 发布：GitPython + smtplib
- 调度：Windows 计划任务

## 架构概览

LangGraph 状态图编排 Agent 决策循环，Agent 自主决定爬取哪些数据源、判断是否有新内容、生成摘要并发布。非硬编码 pipeline。

### 数据流

爬取模块（GitHub Trending / HN / ArXiv）→ ChromaDB 去重检查 → DeepSeek 摘要生成 → Markdown 输出 → GitHub Push + Email 通知

### Agent 决策点

- 今天爬取哪些源？（根据日期/周几调整策略）
- 是否有足够新内容？（去重后全重复就跳过发布）
- 摘要风格？（每日可定制）

## 8 个 Tool

| Tool | 功能 | 数据源 |
|------|------|--------|
| fetch_github_trending | 抓取 GitHub 热门仓库 | GitHub Trending 页面 |
| fetch_hacker_news | 抓取 HN 热门 AI 帖子 | HN 官方 API |
| fetch_arxiv_papers | 抓取最新 AI 论文 | ArXiv 官方 API |
| query_memory | 查询历史去重 | ChromaDB |
| save_to_memory | 存储已处理项目 | ChromaDB |
| generate_report | 生成中文摘要 | DeepSeek API |
| push_to_github | 推送日报到仓库 | GitPython |
| send_email | 邮件通知 | SMTP |

## 项目结构

```
hotspot-agent/
├── agent/          # LangGraph 状态图 + Tool 定义 + 提示词
├── memory/         # ChromaDB 连接 + 嵌入模型
├── scrapers/       # 各数据源爬虫
├── publishers/     # GitHub 推送 + 邮件发送
├── config.py       # 配置
├── main.py         # 入口
├── reports/        # 生成的日报
└── requirements.txt
```

## 简历覆盖

- LangChain 框架构建智能体 ✓
- Function Calling / Tool Use ✓
- ChromaDB RAG 记忆系统 ✓
- DeepSeek 大模型调用 ✓
