"""
回测引擎

核心回测引擎，协调所有组件：
- 时间循环回测
- 事件处理循环
- 策略执行
- 订单管理
- 性能统计
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

from .event_engine import EventQueue, EventType, MarketEvent, SignalEvent, OrderEvent, FillEvent
from .data_handler import DataHandler
from .execution_handler import ExecutionHandler
from .portfolio import Portfolio

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎

    协调数据、策略、执行、投资组合等组件
    """

    def __init__(
        self,
        initial_capital: float,
        data_handler: DataHandler,
        execution_handler: ExecutionHandler,
        strategy,
        heartbeat: float = 0.0
    ):
        """
        初始化回测引擎

        Args:
            initial_capital: 初始资金
            data_handler: 数据处理器
            execution_handler: 执行处理器
            strategy: 策略对象
            heartbeat: 心跳间隔（秒），用于模拟实时
        """
        self.initial_capital = initial_capital
        self.data_handler = data_handler
        self.execution_handler = execution_handler
        self.strategy = strategy
        self.heartbeat = heartbeat

        # 初始化组件
        self.events = EventQueue()
        self.portfolio = Portfolio(initial_capital)

        # 状态
        self.current_time = None
        self.signals_count = 0
        self.orders_count = 0
        self.fills_count = 0

        # 止损止盈价格跟踪：{symbol: {'stop_loss': float, 'take_profit': float}}
        self._sl_tp: Dict[str, Dict[str, float]] = {}

        logger.info("BacktestEngine initialized")

    def run(self) -> Dict[str, Any]:
        """
        运行回测

        Returns:
            回测结果字典
        """
        logger.info("Starting backtest...")
        start_time = datetime.now()

        # 主循环
        while True:
            # 更新市场数据
            market_event = self.data_handler.update_bars()

            if market_event is None:
                # 没有更多数据，结束回测
                break

            # 添加市场事件到队列
            self.events.put(market_event)
            self.current_time = market_event.timestamp

            # 处理事件队列
            while not self.events.empty():
                event = self.events.get(block=False)

                if event is None:
                    continue

                # 根据事件类型分发处理
                if event.type == EventType.MARKET:
                    self._handle_market_event(event)
                elif event.type == EventType.SIGNAL:
                    self._handle_signal_event(event)
                elif event.type == EventType.ORDER:
                    self._handle_order_event(event)
                elif event.type == EventType.FILL:
                    self._handle_fill_event(event)

            # 更新权益曲线
            current_prices = {self.data_handler.symbol: market_event.close}
            self.portfolio.update_equity(self.current_time, current_prices)

        # 回测结束
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"Backtest completed in {duration:.2f} seconds")

        # 返回结果
        return self._generate_results(duration)

    def _handle_market_event(self, event: MarketEvent) -> None:
        """
        处理市场事件

        先检查持仓的止损/止盈条件，再让策略计算新信号。
        """
        # 1. 检查止损止盈
        self._check_stop_loss_take_profit(event)

        # 2. 让策略计算信号
        signals = self.strategy.calculate_signals(event, self.data_handler)

        # 将信号添加到事件队列
        if signals:
            for signal in signals:
                self.events.put(signal)
                self.signals_count += 1

    def _handle_signal_event(self, event: SignalEvent) -> None:
        """
        处理信号事件

        Args:
            event: 信号事件
        """
        # 根据信号生成订单
        orders = self._generate_orders_from_signal(event)

        # 将订单添加到事件队列
        for order in orders:
            self.events.put(order)
            self.orders_count += 1

    def _handle_order_event(self, event: OrderEvent) -> None:
        """
        处理订单事件

        Args:
            event: 订单事件
        """
        # 获取当前价格
        latest_bar = self.data_handler.get_latest_bar()
        if latest_bar is None:
            return

        current_price = latest_bar['close']

        # 执行订单
        fill = self.execution_handler.execute_order(event, current_price)

        # 将成交事件添加到队列
        self.events.put(fill)
        self.fills_count += 1

    def _handle_fill_event(self, event: FillEvent) -> None:
        """
        处理成交事件

        Args:
            event: 成交事件
        """
        # 更新投资组合
        self.portfolio.update_fill(event)

        # 卖出平仓时清除止损止盈
        if event.side == 'SELL':
            pos = self.portfolio.get_position(event.symbol)
            if pos is None or pos.quantity == 0:
                self._sl_tp.pop(event.symbol, None)

    def _generate_orders_from_signal(self, signal: SignalEvent) -> list:
        """
        根据信号生成订单

        Args:
            signal: 信号事件

        Returns:
            订单列表
        """
        orders = []

        # 获取当前持仓
        position = self.portfolio.get_position(signal.symbol)
        has_position = position is not None and position.quantity > 0

        # 根据信号类型生成订单
        if signal.signal_type == 'BUY' and not has_position:
            # 买入信号且无持仓
            quantity = self._calculate_position_size(signal)
            if quantity > 0:
                order = OrderEvent(
                    symbol=signal.symbol,
                    timestamp=signal.timestamp,
                    order_type='MARKET',
                    side='BUY',
                    quantity=quantity,
                    price=signal.price
                )
                orders.append(order)

                # 保存止损止盈价格（从信号元数据中获取）
                meta = signal.metadata or {}
                sl = meta.get('stop_loss')
                tp = meta.get('take_profit')
                if sl or tp:
                    self._sl_tp[signal.symbol] = {
                        'stop_loss': float(sl) if sl else None,
                        'take_profit': float(tp) if tp else None,
                    }

        elif signal.signal_type == 'SELL' and has_position:
            # 卖出信号且有持仓
            order = OrderEvent(
                symbol=signal.symbol,
                timestamp=signal.timestamp,
                order_type='MARKET',
                side='SELL',
                quantity=position.quantity,
                price=signal.price
            )
            orders.append(order)

        elif signal.signal_type == 'CLOSE' and has_position:
            # 平仓信号
            order = OrderEvent(
                symbol=signal.symbol,
                timestamp=signal.timestamp,
                order_type='MARKET',
                side='SELL',
                quantity=position.quantity,
                price=signal.price
            )
            orders.append(order)

        return orders

    def _calculate_position_size(self, signal: SignalEvent) -> float:
        """
        计算仓位大小

        Args:
            signal: 信号事件

        Returns:
            数量
        """
        # 简单的固定比例仓位管理
        position_ratio = 0.95  # 使用95%的可用资金
        available_cash = self.portfolio.cash * position_ratio

        if signal.price and signal.price > 0:
            quantity = available_cash / signal.price
        else:
            latest_bar = self.data_handler.get_latest_bar()
            if latest_bar:
                quantity = available_cash / latest_bar['close']
            else:
                quantity = 0

        return quantity

    def _check_stop_loss_take_profit(self, event: MarketEvent) -> None:
        """
        检查持仓是否触发止损或止盈

        使用当前K线的最高价和最低价判断是否触及止损/止盈价位，
        触发时生成平仓信号事件。
        """
        symbol = event.symbol
        sl_tp = self._sl_tp.get(symbol)
        if not sl_tp:
            return

        position = self.portfolio.get_position(symbol)
        if position is None or position.quantity <= 0:
            return

        stop_loss = sl_tp.get('stop_loss')
        take_profit = sl_tp.get('take_profit')

        # 止损：当前K线最低价触及止损价
        if stop_loss and event.low <= stop_loss:
            logger.info(
                f"止损触发: {symbol} 最低价 {event.low:.4f} "
                f"<= 止损价 {stop_loss:.4f}"
            )
            signal = SignalEvent(
                symbol=symbol,
                timestamp=event.timestamp,
                signal_type='CLOSE',
                strength=1.0,
                price=stop_loss,
                metadata={'reason': '止损触发'},
            )
            self.events.put(signal)
            self.signals_count += 1
            return

        # 止盈：当前K线最高价触及止盈价
        if take_profit and event.high >= take_profit:
            logger.info(
                f"止盈触发: {symbol} 最高价 {event.high:.4f} "
                f">= 止盈价 {take_profit:.4f}"
            )
            signal = SignalEvent(
                symbol=symbol,
                timestamp=event.timestamp,
                signal_type='CLOSE',
                strength=1.0,
                price=take_profit,
                metadata={'reason': '止盈触发'},
            )
            self.events.put(signal)
            self.signals_count += 1

    def _generate_results(self, duration: float) -> Dict[str, Any]:
        """
        生成回测结果

        Args:
            duration: 回测耗时（秒）

        Returns:
            结果字典
        """
        equity_curve = self.portfolio.get_equity_curve_df()
        trades = self.portfolio.get_trades_df()

        results = {
            'initial_capital': self.initial_capital,
            'final_capital': equity_curve['equity'].iloc[-1] if len(equity_curve) > 0 else self.initial_capital,
            'equity_curve': equity_curve,
            'trades': trades,
            'statistics': {
                'total_signals': self.signals_count,
                'total_orders': self.orders_count,
                'total_fills': self.fills_count,
                'total_trades': len(trades),
                'duration_seconds': duration
            },
            'portfolio': self.portfolio.get_statistics()
        }

        return results
