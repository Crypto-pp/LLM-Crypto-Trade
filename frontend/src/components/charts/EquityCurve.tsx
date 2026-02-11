import ReactECharts from 'echarts-for-react'

interface EquityCurveProps {
  data: { time: string; value: number }[]
  height?: number
}

/** 资金曲线图（ECharts 面积图） */
export default function EquityCurve({
  data,
  height = 300,
}: EquityCurveProps) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis' as const,
      backgroundColor: '#21262d',
      borderColor: '#30363d',
      textStyle: { color: '#e6edf3' },
    },
    xAxis: {
      type: 'category' as const,
      data: data.map((d) => d.time),
      axisLine: { lineStyle: { color: '#30363d' } },
      axisLabel: { color: '#8b949e', fontSize: 11 },
    },
    yAxis: {
      type: 'value' as const,
      axisLine: { lineStyle: { color: '#30363d' } },
      axisLabel: { color: '#8b949e', fontSize: 11 },
      splitLine: { lineStyle: { color: '#21262d' } },
    },
    series: [
      {
        type: 'line',
        data: data.map((d) => d.value),
        smooth: true,
        lineStyle: { color: '#58a6ff', width: 2 },
        areaStyle: {
          color: {
            type: 'linear' as const,
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(88,166,255,0.3)' },
              { offset: 1, color: 'rgba(88,166,255,0.02)' },
            ],
          },
        },
        symbol: 'none',
      },
    ],
    grid: { left: 60, right: 20, top: 20, bottom: 30 },
  }

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      opts={{ renderer: 'canvas' }}
    />
  )
}
