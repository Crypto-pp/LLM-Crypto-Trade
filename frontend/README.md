# Crypto-Trade 前端

加密货币自动化分析系统 Web 前端，基于 React + TypeScript + Vite 构建。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | React 18 + TypeScript 5 + Vite 7 |
| UI | Ant Design 6 (暗色主题) |
| 样式 | Tailwind CSS 4 |
| 状态 | Zustand 5 (客户端) + TanStack Query 5 (服务端) |
| 图表 | Lightweight Charts 5 (K线) + ECharts 6 (统计) |
| 路由 | React Router 7 (懒加载) |
| 实时 | 原生 WebSocket (指数退避重连) |

## 页面

| 路由 | 页面 | 说明 |
|------|------|------|
| `/dashboard` | 仪表盘 | 系统状态、热门行情、最新信号 |
| `/market` | 行情中心 | K线图、交易所切换、实时行情 |
| `/market/:symbol` | 行情详情 | 单交易对详情、信号列表 |
| `/analysis` | 技术分析 | 指标选择、支撑阻力、形态识别 |
| `/strategies` | 策略管理 | 策略卡片、信号表格 |
| `/strategies/:name` | 策略详情 | 策略分析执行、历史信号 |
| `/backtest` | 回测中心 | 创建回测、历史记录 |
| `/backtest/:id` | 回测报告 | 指标卡片、资金曲线、评级 |
| `/system` | 系统监控 | 服务状态、运行时间 |
