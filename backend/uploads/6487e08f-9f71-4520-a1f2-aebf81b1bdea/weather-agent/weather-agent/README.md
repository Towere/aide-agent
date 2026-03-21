# 智能天气穿搭助手

一个基于 ReAct Agent 模式的智能天气穿搭助手，使用火山方舟大模型 API 和 OpenWeatherMap 天气 API。

## 功能

- 输入城市名称，查询天气
- 自动绘制未来 5 天天气趋势图
- 基于天气给出穿搭建议
- 支持用户反馈（穿多了/穿少了/刚好）
- 根据用户反馈调整后续建议

## 快速开始

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量（已在 `.env` 中配置好）

3. 运行应用：
```bash
streamlit run src/ui/app.py
```

## 项目结构

```
weather-agent/
├── src/
│   ├── agent/          # ReAct Agent 核心
│   ├── api/            # 天气 API 客户端
│   ├── data/           # 数据库模块
│   ├── ui/             # Streamlit UI
│   └── utils/          # 工具函数
└── data/               # 数据目录
```
