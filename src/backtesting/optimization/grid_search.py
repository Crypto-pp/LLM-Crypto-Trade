"""
网格搜索优化器

遍历所有参数组合，找到最优参数
"""

import logging
from typing import Dict, List, Callable, Any
from itertools import product
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

logger = logging.getLogger(__name__)


class GridSearchOptimizer:
    """
    网格搜索优化器

    遍历参数空间的所有组合
    """

    def __init__(
        self,
        backtest_func: Callable,
        param_grid: Dict[str, List],
        metric: str = 'sharpe_ratio',
        n_jobs: int = 1
    ):
        """
        初始化网格搜索优化器

        Args:
            backtest_func: 回测函数
            param_grid: 参数网格 {'param_name': [value1, value2, ...]}
            metric: 优化目标指标
            n_jobs: 并行任务数
        """
        self.backtest_func = backtest_func
        self.param_grid = param_grid
        self.metric = metric
        self.n_jobs = n_jobs
        self.results = []

        logger.info(f"GridSearchOptimizer initialized with {self._count_combinations()} combinations")

    def optimize(self) -> pd.DataFrame:
        """
        执行网格搜索

        Returns:
            结果DataFrame，按指标排序
        """
        logger.info("Starting grid search optimization...")

        # 生成所有参数组合
        param_combinations = self._generate_combinations()

        if self.n_jobs > 1:
            # 并行执行
            results = self._parallel_optimize(param_combinations)
        else:
            # 串行执行
            results = self._serial_optimize(param_combinations)

        # 转换为DataFrame并排序
        df = pd.DataFrame(results)
        df = df.sort_values(self.metric, ascending=False).reset_index(drop=True)

        self.results = df
        logger.info(f"Grid search completed. Best {self.metric}: {df[self.metric].iloc[0]:.4f}")

        return df

    def _generate_combinations(self) -> List[Dict]:
        """生成所有参数组合"""
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())

        combinations = []
        for combo in product(*values):
            param_dict = dict(zip(keys, combo))
            combinations.append(param_dict)

        return combinations

    def _count_combinations(self) -> int:
        """计算组合总数"""
        count = 1
        for values in self.param_grid.values():
            count *= len(values)
        return count

    def _serial_optimize(self, param_combinations: List[Dict]) -> List[Dict]:
        """串行优化"""
        results = []
        for params in tqdm(param_combinations, desc="Grid Search"):
            result = self._run_backtest(params)
            results.append(result)
        return results

    def _parallel_optimize(self, param_combinations: List[Dict]) -> List[Dict]:
        """并行优化"""
        results = []
        with ProcessPoolExecutor(max_workers=self.n_jobs) as executor:
            futures = {
                executor.submit(self._run_backtest, params): params
                for params in param_combinations
            }

            for future in tqdm(as_completed(futures), total=len(futures), desc="Grid Search"):
                result = future.result()
                results.append(result)

        return results

    def _run_backtest(self, params: Dict) -> Dict:
        """运行单次回测"""
        try:
            # 执行回测
            backtest_result = self.backtest_func(**params)

            # 提取指标
            metrics = backtest_result.get('metrics', {})
            result = {'params': params}

            # 提取所有指标
            for category in ['return_metrics', 'risk_metrics', 'risk_adjusted_metrics', 'trading_metrics']:
                if category in metrics:
                    for key, value in metrics[category].items():
                        if isinstance(value, (int, float)):
                            result[key] = value

            return result

        except Exception as e:
            logger.error(f"Backtest failed for params {params}: {e}")
            return {'params': params, self.metric: float('-inf')}

    def get_best_params(self) -> Dict:
        """获取最优参数"""
        if len(self.results) == 0:
            return {}
        return self.results.iloc[0]['params']

    def plot_results(self, param_name: str, save_path: str = None):
        """
        绘制参数与指标的关系图

        Args:
            param_name: 参数名称
            save_path: 保存路径
        """
        import matplotlib.pyplot as plt

        if len(self.results) == 0:
            logger.warning("No results to plot")
            return

        # 提取参数值
        param_values = [params[param_name] for params in self.results['params']]
        metric_values = self.results[self.metric].values

        plt.figure(figsize=(10, 6))
        plt.scatter(param_values, metric_values, alpha=0.6)
        plt.xlabel(param_name)
        plt.ylabel(self.metric)
        plt.title(f'{self.metric} vs {param_name}')
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path)
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()

        plt.close()
