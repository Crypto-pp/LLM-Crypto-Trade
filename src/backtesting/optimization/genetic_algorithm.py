"""
遗传算法优化器

使用遗传算法进行参数优化
"""

import logging
import random
import numpy as np
from typing import Dict, List, Callable, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class GeneticAlgorithmOptimizer:
    """
    遗传算法优化器

    使用进化算法搜索最优参数
    """

    def __init__(
        self,
        backtest_func: Callable,
        param_ranges: Dict[str, Tuple],
        metric: str = 'sharpe_ratio',
        population_size: int = 50,
        generations: int = 20,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7
    ):
        """
        初始化遗传算法优化器

        Args:
            backtest_func: 回测函数
            param_ranges: 参数范围 {'param': (min, max, step)}
            metric: 优化目标指标
            population_size: 种群大小
            generations: 进化代数
            mutation_rate: 变异率
            crossover_rate: 交叉率
        """
        self.backtest_func = backtest_func
        self.param_ranges = param_ranges
        self.metric = metric
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate

        self.population = []
        self.fitness_history = []
        self.best_individual = None
        self.best_fitness = float('-inf')

        logger.info(f"GeneticAlgorithmOptimizer initialized: "
                   f"pop_size={population_size}, generations={generations}")

    def optimize(self) -> Dict:
        """
        执行遗传算法优化

        Returns:
            最优参数字典
        """
        logger.info("Starting genetic algorithm optimization...")

        # 初始化种群
        self.population = self._initialize_population()

        # 进化循环
        for gen in range(self.generations):
            # 计算适应度
            fitness_scores = self._evaluate_population()

            # 记录最佳个体
            best_idx = np.argmax(fitness_scores)
            if fitness_scores[best_idx] > self.best_fitness:
                self.best_fitness = fitness_scores[best_idx]
                self.best_individual = self.population[best_idx].copy()

            self.fitness_history.append({
                'generation': gen,
                'best_fitness': fitness_scores[best_idx],
                'avg_fitness': np.mean(fitness_scores),
                'worst_fitness': np.min(fitness_scores)
            })

            logger.info(f"Generation {gen+1}/{self.generations}: "
                       f"Best={fitness_scores[best_idx]:.4f}, "
                       f"Avg={np.mean(fitness_scores):.4f}")

            # 选择
            selected = self._selection(fitness_scores)

            # 交叉
            offspring = self._crossover(selected)

            # 变异
            offspring = self._mutation(offspring)

            # 更新种群
            self.population = offspring

        logger.info(f"Optimization completed. Best {self.metric}: {self.best_fitness:.4f}")
        return self.best_individual

    def _initialize_population(self) -> List[Dict]:
        """初始化种群"""
        population = []
        for _ in range(self.population_size):
            individual = {}
            for param, (min_val, max_val, step) in self.param_ranges.items():
                if isinstance(min_val, int) and isinstance(max_val, int):
                    individual[param] = random.randint(min_val, max_val)
                else:
                    individual[param] = random.uniform(min_val, max_val)
            population.append(individual)
        return population

    def _evaluate_population(self) -> np.ndarray:
        """评估种群适应度"""
        fitness_scores = []
        for individual in self.population:
            fitness = self._evaluate_individual(individual)
            fitness_scores.append(fitness)
        return np.array(fitness_scores)

    def _evaluate_individual(self, individual: Dict) -> float:
        """评估单个个体"""
        try:
            result = self.backtest_func(**individual)
            metrics = result.get('metrics', {})

            # 提取目标指标
            for category in ['return_metrics', 'risk_metrics', 'risk_adjusted_metrics', 'trading_metrics']:
                if category in metrics and self.metric in metrics[category]:
                    return metrics[category][self.metric]

            return float('-inf')

        except Exception as e:
            logger.error(f"Evaluation failed for {individual}: {e}")
            return float('-inf')

    def _selection(self, fitness_scores: np.ndarray) -> List[Dict]:
        """选择操作（锦标赛选择）"""
        selected = []
        tournament_size = 3

        for _ in range(self.population_size):
            # 随机选择tournament_size个个体
            indices = random.sample(range(len(self.population)), tournament_size)
            tournament_fitness = [fitness_scores[i] for i in indices]

            # 选择最优个体
            winner_idx = indices[np.argmax(tournament_fitness)]
            selected.append(self.population[winner_idx].copy())

        return selected

    def _crossover(self, population: List[Dict]) -> List[Dict]:
        """交叉操作"""
        offspring = []

        for i in range(0, len(population), 2):
            parent1 = population[i]
            parent2 = population[i+1] if i+1 < len(population) else population[0]

            if random.random() < self.crossover_rate:
                # 执行交叉
                child1, child2 = {}, {}
                for param in parent1.keys():
                    if random.random() < 0.5:
                        child1[param] = parent1[param]
                        child2[param] = parent2[param]
                    else:
                        child1[param] = parent2[param]
                        child2[param] = parent1[param]

                offspring.extend([child1, child2])
            else:
                # 不交叉，直接复制
                offspring.extend([parent1.copy(), parent2.copy()])

        return offspring[:self.population_size]

    def _mutation(self, population: List[Dict]) -> List[Dict]:
        """变异操作"""
        for individual in population:
            if random.random() < self.mutation_rate:
                # 随机选择一个参数进行变异
                param = random.choice(list(individual.keys()))
                min_val, max_val, step = self.param_ranges[param]

                if isinstance(min_val, int) and isinstance(max_val, int):
                    individual[param] = random.randint(min_val, max_val)
                else:
                    individual[param] = random.uniform(min_val, max_val)

        return population

    def get_fitness_history(self) -> pd.DataFrame:
        """获取适应度历史"""
        return pd.DataFrame(self.fitness_history)

    def plot_evolution(self, save_path: str = None):
        """绘制进化过程"""
        import matplotlib.pyplot as plt

        df = self.get_fitness_history()

        plt.figure(figsize=(10, 6))
        plt.plot(df['generation'], df['best_fitness'], label='Best', linewidth=2)
        plt.plot(df['generation'], df['avg_fitness'], label='Average', linewidth=2)
        plt.xlabel('Generation')
        plt.ylabel(self.metric)
        plt.title('Genetic Algorithm Evolution')
        plt.legend()
        plt.grid(True, alpha=0.3)

        if save_path:
            plt.savefig(save_path)
            logger.info(f"Plot saved to {save_path}")
        else:
            plt.show()

        plt.close()
