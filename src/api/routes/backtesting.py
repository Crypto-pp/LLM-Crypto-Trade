"""
回测API路由

提供回测相关的REST API接口：
- 启动回测（后台异步执行）
- 查询回测结果与性能分析
- 生成HTML报告
- 参数网格搜索优化
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import numpy as np
import pandas as pd

from src.backtesting.engine import (
    BacktestEngine,
    ExchangeDataHandler,
    ExecutionHandler,
    StrategyAdapter,
)
from src.backtesting.engine.execution_handler import SimulatedExecutionHandler
from src.backtesting.performance.performance_analyzer import PerformanceAnalyzer
from src.backtesting.performance.report_generator import ReportGenerator
from src.backtesting.optimization.grid_search import GridSearchOptimizer
from src.trading_engine.strategies import (
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    PriceActionStrategy,
)

logger = logging.getLogger(__name__)

# 策略名称到类的映射（与 signal_scheduler 保持一致）
STRATEGY_MAP = {
    "趋势跟踪": TrendFollowingStrategy,
    "均值回归": MeanReversionStrategy,
    "动量策略": MomentumStrategy,
    "价格行为": PriceActionStrategy,
}



def _sanitize(obj):
    """递归将 numpy/pandas 类型转为原生 Python 类型，确保 JSON 可序列化"""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(item) for item in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        if np.isnan(val) or np.isinf(val):
            return 0.0
        return val
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    return obj


def _resolve_strategy(name: str, params: Optional[Dict] = None):
    """根据策略名称创建策略实例"""
    strategy_cls = STRATEGY_MAP.get(name)
    if strategy_cls is None:
        raise ValueError(
            f"未知策略: {name}，可选: {list(STRATEGY_MAP.keys())}"
        )
    return strategy_cls(**(params or {}))


router = APIRouter(tags=["backtest"])


class BacktestRequest(BaseModel):
    """回测请求"""
    strategy: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    params: Optional[Dict] = None


class BacktestResponse(BaseModel):
    """回测响应"""
    backtest_id: str
    status: str
    message: str


class BacktestResult(BaseModel):
    """回测结果"""
    backtest_id: str
    summary: Dict
    metrics: Dict
    rating: Dict


# 持久化存储路径
BACKTEST_STORE_PATH = Path("/tmp/backtest_tasks.json")


def _load_tasks() -> Dict:
    """从文件加载回测任务"""
    if BACKTEST_STORE_PATH.exists():
        try:
            return json.loads(BACKTEST_STORE_PATH.read_text(encoding='utf-8'))
        except Exception as e:
            logger.warning(f"加载回测记录失败: {e}")
    return {}


def _save_tasks(tasks: Dict) -> None:
    """将回测任务保存到文件"""
    try:
        BACKTEST_STORE_PATH.write_text(
            json.dumps(tasks, ensure_ascii=False, default=str),
            encoding='utf-8',
        )
    except Exception as e:
        logger.warning(f"保存回测记录失败: {e}")


# 启动时从文件恢复
backtest_tasks: Dict = _load_tasks()


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """
    运行回测

    验证策略名称后，将回测任务提交到后台异步执行。
    """
    # 验证策略名称
    if request.strategy not in STRATEGY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"未知策略: {request.strategy}，"
                   f"可选: {list(STRATEGY_MAP.keys())}",
        )

    try:
        backtest_id = f"BT_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 记录任务
        backtest_tasks[backtest_id] = {
            'backtest_id': backtest_id,
            'status': 'running',
            'request': request.dict(),
            'created_at': datetime.now().isoformat(),
        }
        _save_tasks(backtest_tasks)

        # 提交后台执行
        background_tasks.add_task(execute_backtest, backtest_id, request)

        logger.info(f"回测任务已提交: {backtest_id}")

        return BacktestResponse(
            backtest_id=backtest_id,
            status='running',
            message='回测已启动',
        )

    except Exception as e:
        logger.error(f"启动回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_backtest(backtest_id: str, request: BacktestRequest) -> None:
    """
    后台执行回测的核心函数

    组装 ExchangeDataHandler → StrategyAdapter → SimulatedExecutionHandler →
    BacktestEngine，运行回测后通过 PerformanceAnalyzer 生成分析结果。
    """
    task = backtest_tasks[backtest_id]
    try:
        logger.info(f"开始执行回测 {backtest_id}: {request.strategy} {request.symbol}")

        # 1. 解析时间范围
        start_dt = datetime.fromisoformat(request.start_date)
        end_dt = datetime.fromisoformat(request.end_date)

        # 2. 创建数据处理器（从交易所拉取历史K线）
        data_handler = ExchangeDataHandler(
            symbol=request.symbol,
            start_date=start_dt,
            end_date=end_dt,
            exchange_id='binance',
            interval='1h',
        )

        # 3. 创建策略实例并用适配器包装
        strategy = _resolve_strategy(request.strategy, request.params)
        adapter = StrategyAdapter(strategy, min_bars=50)

        # 4. 创建模拟执行处理器
        execution_handler = SimulatedExecutionHandler(
            commission_rate=0.001,
            slippage_rate=0.0005,
        )

        # 5. 创建并运行回测引擎
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            data_handler=data_handler,
            execution_handler=execution_handler,
            strategy=adapter,
        )
        raw_results = engine.run()

        # 6. 性能分析
        equity_curve = raw_results['equity_curve']
        trades = raw_results['trades']
        trades_list = (
            trades.to_dict(orient='records')
            if isinstance(trades, pd.DataFrame) else trades
        )

        analyzer = PerformanceAnalyzer(
            initial_capital=request.initial_capital,
            equity_curve=equity_curve,
            trades=trades_list,
        )
        analysis = analyzer.analyze()

        # 7. 保存结果到任务字典（sanitize 确保 JSON 可序列化）
        task['status'] = 'completed'
        task['completed_at'] = datetime.now().isoformat()
        summary = _sanitize(analysis.get('summary', {}))
        task['summary'] = summary
        task['raw_metrics'] = _sanitize(analysis.get('metrics', {}))
        task['rating'] = _sanitize(analysis.get('rating', {}))
        task['analysis'] = _sanitize(analysis.get('analysis', {}))
        task['trades'] = _sanitize(trades_list)
        task['statistics'] = _sanitize(raw_results.get('statistics', {}))

        # 构建前端期望的扁平 metrics（从 summary 提取）
        task['metrics'] = {
            'total_return': summary.get('total_return', 0),
            'sharpe_ratio': summary.get('sharpe_ratio', 0),
            'max_drawdown': summary.get('max_drawdown', 0),
            'win_rate': summary.get('win_rate', 0),
            'total_trades': summary.get('total_trades', 0),
        }

        logger.info(f"回测完成 {backtest_id}: 评级 {task['rating'].get('rating', 'N/A')}")
        _save_tasks(backtest_tasks)

    except Exception as e:
        logger.error(f"回测执行失败 {backtest_id}: {e}", exc_info=True)
        task['status'] = 'failed'
        task['error'] = str(e)
        task['completed_at'] = datetime.now().isoformat()
        _save_tasks(backtest_tasks)


@router.get("/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    """查询回测任务状态"""
    if backtest_id not in backtest_tasks:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    task = backtest_tasks[backtest_id]
    resp = {
        'backtest_id': backtest_id,
        'status': task['status'],
        'created_at': task.get('created_at'),
    }
    if task['status'] == 'failed':
        resp['error'] = task.get('error', '')
    if task['status'] == 'completed':
        resp['completed_at'] = task.get('completed_at')
    return resp


@router.get("/{backtest_id}/results", response_model=BacktestResult)
async def get_backtest_results(backtest_id: str):
    """获取回测结果（需回测已完成）"""
    if backtest_id not in backtest_tasks:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    task = backtest_tasks[backtest_id]

    if task['status'] == 'running':
        raise HTTPException(status_code=400, detail="回测尚未完成")
    if task['status'] == 'failed':
        raise HTTPException(
            status_code=400,
            detail=f"回测执行失败: {task.get('error', '未知错误')}",
        )

    return BacktestResult(
        backtest_id=backtest_id,
        summary=task.get('summary', {}),
        metrics=task.get('metrics', {}),
        rating=task.get('rating', {}),
    )


@router.get("/{backtest_id}/report")
async def get_backtest_report(backtest_id: str):
    """获取回测 HTML 报告"""
    if backtest_id not in backtest_tasks:
        raise HTTPException(status_code=404, detail="回测任务不存在")

    task = backtest_tasks[backtest_id]

    if task['status'] != 'completed':
        raise HTTPException(status_code=400, detail="回测尚未完成，无法生成报告")

    try:
        analysis_result = {
            'summary': task.get('summary', {}),
            'metrics': task.get('metrics', {}),
            'rating': task.get('rating', {}),
            'analysis': task.get('analysis', {}),
        }
        generator = ReportGenerator(analysis_result, output_dir="/tmp/reports")
        report_path = generator.generate_html_report(
            filename=f"{backtest_id}.html"
        )

        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"生成报告失败 {backtest_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"报告生成失败: {e}")


@router.get("/list")
async def list_backtests(limit: int = 10, offset: int = 0):
    """获取回测历史列表（按创建时间倒序）"""
    items = sorted(
        backtest_tasks.values(),
        key=lambda t: t.get('created_at', ''),
        reverse=True,
    )
    total = len(items)

    # 返回摘要字段，保留 request 供前端表格渲染
    page = items[offset:offset + limit]
    summaries = []
    for t in page:
        summaries.append({
            'backtest_id': t.get('backtest_id', ''),
            'status': t.get('status', ''),
            'request': t.get('request', {}),
            'created_at': t.get('created_at'),
            'completed_at': t.get('completed_at'),
            'rating': t.get('rating', {}).get('rating') if t.get('rating') else None,
        })

    return {
        'total': total,
        'limit': limit,
        'offset': offset,
        'items': summaries,
    }


@router.post("/optimize")
async def optimize_strategy(request: Dict):
    """
    参数网格搜索优化

    请求体示例：
    {
        "strategy": "趋势跟踪",
        "symbol": "BTC/USDT",
        "start_date": "2024-01-01",
        "end_date": "2024-06-01",
        "initial_capital": 10000,
        "param_grid": {"fast_period": [5, 10, 20], "slow_period": [30, 50, 100]},
        "metric": "sharpe_ratio"
    }
    """
    required = ['strategy', 'symbol', 'start_date', 'end_date', 'param_grid']
    for field in required:
        if field not in request:
            raise HTTPException(status_code=400, detail=f"缺少必填字段: {field}")

    strategy_name = request['strategy']
    if strategy_name not in STRATEGY_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"未知策略: {strategy_name}，可选: {list(STRATEGY_MAP.keys())}",
        )

    try:
        start_dt = datetime.fromisoformat(request['start_date'])
        end_dt = datetime.fromisoformat(request['end_date'])
        initial_capital = float(request.get('initial_capital', 10000))
        param_grid = request['param_grid']
        metric = request.get('metric', 'sharpe_ratio')

        def run_single_backtest(**params):
            """单次回测函数，供 GridSearchOptimizer 调用"""
            data_handler = ExchangeDataHandler(
                symbol=request['symbol'],
                start_date=start_dt,
                end_date=end_dt,
                exchange_id='binance',
                interval='1h',
            )
            strategy = _resolve_strategy(strategy_name, params)
            adapter = StrategyAdapter(strategy, min_bars=50)
            execution_handler = SimulatedExecutionHandler()
            engine = BacktestEngine(
                initial_capital=initial_capital,
                data_handler=data_handler,
                execution_handler=execution_handler,
                strategy=adapter,
            )
            raw = engine.run()

            equity_curve = raw['equity_curve']
            trades = raw['trades']
            trades_list = (
                trades.to_dict(orient='records')
                if isinstance(trades, pd.DataFrame) else trades
            )
            analyzer = PerformanceAnalyzer(
                initial_capital=initial_capital,
                equity_curve=equity_curve,
                trades=trades_list,
            )
            return {'metrics': analyzer.analyze().get('metrics', {})}

        optimizer = GridSearchOptimizer(
            backtest_func=run_single_backtest,
            param_grid=param_grid,
            metric=metric,
            n_jobs=1,
        )
        results_df = optimizer.optimize()
        best_params = optimizer.get_best_params()

        # 取前 10 条结果
        top_results = results_df.head(10)
        rows = []
        for _, row in top_results.iterrows():
            rows.append(_sanitize(row.to_dict()))

        return {
            'best_params': _sanitize(best_params),
            'metric': metric,
            'best_value': _sanitize(
                results_df[metric].iloc[0] if len(results_df) > 0 else None
            ),
            'total_combinations': len(results_df),
            'top_results': rows,
        }

    except Exception as e:
        logger.error(f"参数优化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"优化失败: {e}")
