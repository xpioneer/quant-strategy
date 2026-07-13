# Stock Quant Strategy

量化交易策略系统后端 API

## 技术栈

- Web 框架: FastAPI >= 0.139.0
- ORM: SQLAlchemy >= 2.0.50
- 数据处理: Pandas >= 3.0.0, Polars >= 1.42.0
- 回测框架: Backtrader
- 数据源: AkShare, Tushare
- 依赖管理: uv
- 项目配置: pyproject.toml

## 项目结构

```
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config/
│   │   └── settings.py         # 配置管理
│   ├── common/
│   │   ├── schemas.py          # 统一响应模型
│   │   └── dashboard.py        # 仪表板 API
│   ├── database/
│   │   ├── __init__.py         # 数据库连接
│   │   ├── models.py           # SQLAlchemy 模型
│   │   └── repository.py       # 数据访问层
│   ├── market/
│   │   ├── data_loader.py      # 数据源加载器
│   │   ├── service.py          # 市场数据服务
│   │   └── api.py              # 市场数据 API
│   ├── indicator/
│   │   ├── calculator.py       # 指标计算器
│   │   └── api.py              # 指标 API
│   ├── strategy/
│   │   ├── strategies.py       # 策略实现
│   │   └── api.py              # 策略 API
│   ├── backtest/
│   │   ├── engine.py           # 回测引擎
│   │   └── api.py              # 回测 API
│   ├── report/
│   │   └── generator.py        # 报告生成
│   ├── risk/                   # 风险管理 (预留)
│   ├── portfolio/              # 投资组合 (预留)
│   ├── scheduler/              # 定时任务 (预留)
│   └── websocket/              # WebSocket (预留)
├── tests/                      # 测试
├── scripts/                    # 脚本
├── alembic/                    # 数据库迁移
├── storage/                    # 存储
│   ├── parquet/                # Parquet 文件
│   └── cache/                  # 缓存
├── pyproject.toml              # 项目配置
├── .env                        # 环境变量
├── .env.example                # 环境变量示例
├── .gitignore
└── README.md
```

## 快速开始

### 前置要求

- Python 3.10+
- uv (推荐)

### 方式一: 使用启动脚本 (推荐)

```bash
./start.sh
```

### 方式二: 手动启动

```bash
# 1. 安装 uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库等信息

# 4. 启动服务
uv run python -m app.main
# 或使用 uvicorn
uv run uvicorn app.main:app --reload
```

服务将在 `http://127.0.0.1:8120` 启动

## API 端点

直接访问：
- `GET /` - 服务状态
- `GET /health` - 健康检查

配合前端代理 `/api`，可通过以下地址访问：
- `GET /api/v1/dashboard/overview` - 仪表板概览
- `GET /api/v1/market/stocks` - 获取股票列表
- `GET /api/v1/market/kline/{symbol}` - 获取K线数据
- `GET /api/v1/indicator/indicators/{symbol}` - 获取指标数据
- `GET /api/v1/strategy/strategies` - 获取策略列表
- `GET /api/v1/strategy/available-strategies` - 获取可用策略
- `POST /api/v1/backtest/run` - 运行回测
- `POST /api/v1/backtest/compare` - 对比策略

## 开发命令

```bash
# 安装依赖
uv sync

# 安装开发依赖
uv sync --dev

# 运行代码格式化
uv run black .
uv run isort .

# 运行代码检查
uv run ruff check .

# 运行类型检查
uv run mypy app/

# 运行测试
uv run pytest
```

## 关于 __init__.py

Python 中的 `__init__.py` 文件用于标识一个目录为 Python 包，这样才能使用 `import` 语句导入该目录下的模块。即使文件内容为空，它也是必须的，不能删除或忽略。
