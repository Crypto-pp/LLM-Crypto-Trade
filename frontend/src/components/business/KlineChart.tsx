import { useEffect, useRef } from 'react'
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  ColorType,
  CandlestickSeries,
  type CandlestickData,
  type Time,
} from 'lightweight-charts'
import type { Kline } from '@/types/market'

interface KlineChartProps {
  data: Kline[]
  height?: number
}

/** 将后端K线数据转换为 Lightweight Charts 格式 */
function toChartData(klines: Kline[]): CandlestickData<Time>[] {
  return klines.map((k) => ({
    time: (new Date(k.timestamp).getTime() / 1000) as Time,
    open: parseFloat(k.open),
    high: parseFloat(k.high),
    low: parseFloat(k.low),
    close: parseFloat(k.close),
  }))
}

/** 根据价格数据自动计算合适的小数精度 */
function calcPrecision(klines: Kline[]): number {
  if (klines.length === 0) return 2
  const lastClose = parseFloat(klines[klines.length - 1].close)
  if (isNaN(lastClose) || lastClose === 0) return 2
  if (lastClose >= 1) return 2
  const leadingZeros = Math.floor(-Math.log10(Math.abs(lastClose)))
  return Math.min(leadingZeros + 2, 12)
}

/** K线图表组件，封装 TradingView Lightweight Charts */
export default function KlineChart({
  data,
  height = 400,
}: KlineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)

  // 初始化图表
  useEffect(() => {
    if (!containerRef.current) return

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: '#21262d' },
        horzLines: { color: '#21262d' },
      },
      crosshair: {
        vertLine: { color: '#58a6ff', width: 1 },
        horzLine: { color: '#58a6ff', width: 1 },
      },
      timeScale: {
        borderColor: '#30363d',
        timeVisible: true,
      },
      rightPriceScale: {
        borderColor: '#30363d',
      },
    })

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#3fb950',
      downColor: '#f85149',
      borderUpColor: '#3fb950',
      borderDownColor: '#f85149',
      wickUpColor: '#3fb950',
      wickDownColor: '#f85149',
    })

    chartRef.current = chart
    seriesRef.current = series

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({
          width: containerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)
    handleResize()

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [height])

  // 更新数据
  useEffect(() => {
    if (seriesRef.current && data.length > 0) {
      const precision = calcPrecision(data)
      const minMove = 1 / Math.pow(10, precision)
      seriesRef.current.applyOptions({
        priceFormat: { type: 'price', precision, minMove },
      })
      const chartData = toChartData(data)
      seriesRef.current.setData(chartData)
      chartRef.current?.timeScale().fitContent()
    }
  }, [data])

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        border: '1px solid var(--border)',
        borderRadius: 6,
      }}
    />
  )
}
