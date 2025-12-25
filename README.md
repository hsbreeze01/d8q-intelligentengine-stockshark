# StockShark - 股票分析系统

一个基于 Flask 的股票分析系统，提供以下核心功能：

- **单个股票分析**：按照设定的规则分析股票，给出投资价值和风险评估
- **主题/行业股票筛选**：基于主题或行业查找相关股票，支持多条件过滤和排序
- **场景/新闻驱动分析**：输入场景或新闻，识别相关供应链企业，标记上市状态和控股关系

## 技术栈

- **后端框架**: Flask
- **数据库**: MySQL + MongoDB
- **数据处理**: pandas, numpy
- **自然语言处理**: jieba, hanlp, spacy
- **数据源**: akshare
- **机器学习**: scikit-learn
- **可视化**: matplotlib, seaborn

## 项目结构

```
stockshark/
├── stockshark/           # 主包目录
│   ├── api/             # API 模块
│   │   ├── app.py       # Flask 应用工厂
│   │   └── routes/      # API 路由
│   ├── analysis/        # 分析模块
│   │   ├── stock_analyzer.py
│   │   ├── search_engine.py
│   │   └── supply_chain_analyzer.py
│   ├── data/            # 数据模块
│   │   ├── akshare_data.py
│   │   ├── data_processor.py
│   │   └── database.py
│   ├── models/          # 数据模型
│   └── utils/           # 工具模块
│       ├── logger.py
│       ├── exceptions.py
│       └── validators.py
├── tests/               # 测试目录
│   ├── unit/           # 单元测试
│   ├── integration/    # 集成测试
│   └── fixtures/       # 测试固件
├── scripts/            # 脚本目录
├── venv/               # 虚拟环境
├── requirements.txt     # 依赖列表
├── .env.example       # 环境变量示例
└── .gitignore         # Git 忽略文件
```

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- MongoDB 4.0+

### 安装

1. 克隆仓库
```bash
git clone <repository-url>
cd d8q-intelligentengine-stockshark
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息
```

5. 初始化数据库
```bash
python -c "from stockshark.data.database import DatabaseManager; DatabaseManager.init_database()"
```

6. 启动服务
```bash
python -m stockshark.api.app
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行测试并生成覆盖率报告
pytest --cov=stockshark --cov-report=html
```

### API 文档

启动服务后，访问以下端点：

- 健康检查: `GET /health`
- 股票分析: `POST /api/analysis/stock/analyze`
- 行业搜索: `GET /api/search/stock/by-industry`
- 概念搜索: `GET /api/search/stock/by-concept`
- 供应链分析: `POST /api/supply-chain/analyze`

详细的 API 文档请参考 `TEST_GUIDE.md`。

## 开发指南

### 代码风格

项目遵循 PEP 8 代码风格规范。使用以下工具进行代码检查：

```bash
# 代码格式化
black stockshark/

# 代码检查
flake8 stockshark/

# 类型检查
mypy stockshark/
```

### 添加新功能

1. 在相应的模块目录下创建新文件
2. 实现功能并添加单元测试
3. 更新 API 路由（如需要）
4. 更新文档

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
