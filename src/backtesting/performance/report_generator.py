"""
报告生成器

生成回测报告：
- HTML报告
- 图表生成
- 交易记录表
- 性能摘要
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
from typing import Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    报告生成器

    生成HTML格式的回测报告
    """

    def __init__(self, analysis_result: Dict, output_dir: str = "reports"):
        """
        初始化报告生成器

        Args:
            analysis_result: 分析结果字典
            output_dir: 输出目录
        """
        self.analysis = analysis_result
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ReportGenerator initialized, output_dir: {self.output_dir}")

    def generate_html_report(self, filename: str = "backtest_report.html") -> str:
        """
        生成HTML报告

        Args:
            filename: 文件名

        Returns:
            报告文件路径
        """
        report_path = self.output_dir / filename

        html_content = self._build_html()

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {report_path}")
        return str(report_path)

    def _build_html(self) -> str:
        """构建HTML内容"""
        summary = self.analysis['summary']
        metrics = self.analysis['metrics']
        rating = self.analysis['rating']
        analysis = self.analysis.get('analysis', {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>回测报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metric-card.positive {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .metric-card.negative {{
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
        }}
        .rating {{
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin: 20px 0;
        }}
        .rating-grade {{
            font-size: 72px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .rating-score {{
            font-size: 24px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .analysis-section {{
            margin: 20px 0;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            background-color: #f9f9f9;
        }}
        .strength {{
            color: #4CAF50;
        }}
        .weakness {{
            color: #f44336;
        }}
        .recommendation {{
            color: #2196F3;
        }}
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }}
        li:before {{
            content: "•";
            position: absolute;
            left: 0;
            font-size: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 回测报告</h1>

        <div class="rating">
            <div>策略评级</div>
            <div class="rating-grade">{rating['rating']}</div>
            <div class="rating-score">综合得分: {rating['total_score']:.1f}/100</div>
        </div>

        <h2>📈 核心指标</h2>
        <div class="summary">
            <div class="metric-card">
                <div class="metric-label">初始资金</div>
                <div class="metric-value">${summary['initial_capital']:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">最终资金</div>
                <div class="metric-value">${summary['final_capital']:,.2f}</div>
            </div>
            <div class="metric-card {'positive' if summary['total_return'] > 0 else 'negative'}">
                <div class="metric-label">总收益率</div>
                <div class="metric-value">{summary['total_return']:.2f}%</div>
            </div>
            <div class="metric-card {'positive' if summary['annualized_return'] > 0 else 'negative'}">
                <div class="metric-label">年化收益率</div>
                <div class="metric-value">{summary['annualized_return']:.2f}%</div>
            </div>
            <div class="metric-card negative">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value">{summary['max_drawdown']:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">{summary['sharpe_ratio']:.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">胜率</div>
                <div class="metric-value">{summary['win_rate']:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">交易次数</div>
                <div class="metric-value">{summary['total_trades']}</div>
            </div>
        </div>

        <h2>📊 详细指标</h2>

        <h3>收益指标</h3>
        <table>
            <tr>
                <th>指标</th>
                <th>数值</th>
            </tr>
            <tr>
                <td>总收益率</td>
                <td>{metrics['return_metrics']['total_return']:.2f}%</td>
            </tr>
            <tr>
                <td>年化收益率</td>
                <td>{metrics['return_metrics']['annualized_return']:.2f}%</td>
            </tr>
            <tr>
                <td>日均收益率</td>
                <td>{metrics['return_metrics']['avg_daily_return']:.4f}%</td>
            </tr>
            <tr>
                <td>总盈亏</td>
                <td>${metrics['return_metrics']['total_pnl']:,.2f}</td>
            </tr>
        </table>

        <h3>风险指标</h3>
        <table>
            <tr>
                <th>指标</th>
                <th>数值</th>
            </tr>
            <tr>
                <td>最大回撤</td>
                <td>{metrics['risk_metrics']['max_drawdown']:.2f}%</td>
            </tr>
            <tr>
                <td>波动率（年化）</td>
                <td>{metrics['risk_metrics']['volatility']:.2f}%</td>
            </tr>
            <tr>
                <td>下行波动率</td>
                <td>{metrics['risk_metrics']['downside_deviation']:.2f}%</td>
            </tr>
        </table>

        <h3>风险调整收益指标</h3>
        <table>
            <tr>
                <th>指标</th>
                <th>数值</th>
            </tr>
            <tr>
                <td>夏普比率</td>
                <td>{metrics['risk_adjusted_metrics']['sharpe_ratio']:.3f}</td>
            </tr>
            <tr>
                <td>索提诺比率</td>
                <td>{metrics['risk_adjusted_metrics']['sortino_ratio']:.3f}</td>
            </tr>
            <tr>
                <td>卡玛比率</td>
                <td>{metrics['risk_adjusted_metrics']['calmar_ratio']:.3f}</td>
            </tr>
        </table>

        <h3>交易指标</h3>
        <table>
            <tr>
                <th>指标</th>
                <th>数值</th>
            </tr>
            <tr>
                <td>总交易次数</td>
                <td>{metrics['trading_metrics']['total_trades']}</td>
            </tr>
            <tr>
                <td>盈利交易</td>
                <td>{metrics['trading_metrics']['winning_trades']}</td>
            </tr>
            <tr>
                <td>亏损交易</td>
                <td>{metrics['trading_metrics']['losing_trades']}</td>
            </tr>
            <tr>
                <td>胜率</td>
                <td>{metrics['trading_metrics']['win_rate']:.2f}%</td>
            </tr>
            <tr>
                <td>盈亏比</td>
                <td>{metrics['trading_metrics']['profit_loss_ratio']:.2f}</td>
            </tr>
            <tr>
                <td>盈利因子</td>
                <td>{metrics['trading_metrics']['profit_factor']:.2f}</td>
            </tr>
            <tr>
                <td>平均盈利</td>
                <td>${metrics['trading_metrics']['avg_win']:,.2f}</td>
            </tr>
            <tr>
                <td>平均亏损</td>
                <td>${metrics['trading_metrics']['avg_loss']:,.2f}</td>
            </tr>
            <tr>
                <td>最大单笔盈利</td>
                <td>${metrics['trading_metrics']['max_win']:,.2f}</td>
            </tr>
            <tr>
                <td>最大单笔亏损</td>
                <td>${metrics['trading_metrics']['max_loss']:,.2f}</td>
            </tr>
            <tr>
                <td>平均持仓时间</td>
                <td>{metrics['trading_metrics']['avg_holding_hours']:.2f} 小时</td>
            </tr>
        </table>

        {self._generate_analysis_html(analysis)}

        <h2>📊 评分详情</h2>
        <table>
            <tr>
                <th>维度</th>
                <th>得分</th>
            </tr>
            <tr>
                <td>收益</td>
                <td>{rating['component_scores']['return']:.2f}/100</td>
            </tr>
            <tr>
                <td>风险</td>
                <td>{rating['component_scores']['risk']:.2f}/100</td>
            </tr>
            <tr>
                <td>稳定性</td>
                <td>{rating['component_scores']['stability']:.2f}/100</td>
            </tr>
            <tr>
                <td>交易</td>
                <td>{rating['component_scores']['trading']:.2f}/100</td>
            </tr>
        </table>

        <footer style="margin-top: 50px; text-align: center; color: #999;">
            <p>报告生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
"""
        return html

    def _generate_analysis_html(self, analysis: Dict) -> str:
        """生成分析建议HTML"""
        if not analysis:
            return ""

        html = "<h2>💡 策略分析</h2>"

        if analysis.get('strengths'):
            html += '<div class="analysis-section">'
            html += '<h3 class="strength">✓ 优势</h3><ul>'
            for strength in analysis['strengths']:
                html += f'<li class="strength">{strength}</li>'
            html += '</ul></div>'

        if analysis.get('weaknesses'):
            html += '<div class="analysis-section">'
            html += '<h3 class="weakness">✗ 劣势</h3><ul>'
            for weakness in analysis['weaknesses']:
                html += f'<li class="weakness">{weakness}</li>'
            html += '</ul></div>'

        if analysis.get('recommendations'):
            html += '<div class="analysis-section">'
            html += '<h3 class="recommendation">→ 建议</h3><ul>'
            for rec in analysis['recommendations']:
                html += f'<li class="recommendation">{rec}</li>'
            html += '</ul></div>'

        return html
