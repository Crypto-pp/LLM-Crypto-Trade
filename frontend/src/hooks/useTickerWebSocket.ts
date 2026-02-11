import { useEffect, useRef } from 'react'
import { useWebSocketStore } from '@/stores/websocket'

/** WebSocket 实时行情推送 Hook */
export function useTickerWebSocket(symbols: string[]) {
  const setConnected = useWebSocketStore((s) => s.setConnected)
  const updatePrice = useWebSocketStore((s) => s.updatePrice)
  const setLatency = useWebSocketStore((s) => s.setLatency)
  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)

  useEffect(() => {
    if (symbols.length === 0) return

    const wsUrl =
      import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/ticker'

    function connect() {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        retriesRef.current = 0
        ws.send(JSON.stringify({ action: 'subscribe', symbols }))
      }

      ws.onmessage = (event) => {
        const start = performance.now()
        const data = JSON.parse(event.data)
        if (data.symbol && data.price != null) {
          updatePrice(data.symbol, Number(data.price))
        }
        setLatency(Math.round(performance.now() - start))
      }

      ws.onclose = () => {
        setConnected(false)
        const delay = Math.min(1000 * 2 ** retriesRef.current, 30_000)
        retriesRef.current++
        setTimeout(connect, delay)
      }

      ws.onerror = () => ws.close()
    }

    connect()

    const heartbeat = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'ping' }))
      }
    }, 30_000)

    return () => {
      clearInterval(heartbeat)
      wsRef.current?.close()
    }
  }, [symbols.join(','), setConnected, updatePrice, setLatency])
}
