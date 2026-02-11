import { Input, Spin } from 'antd'
import { SearchOutlined, StarFilled, StarOutlined } from '@ant-design/icons'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMarketStore } from '@/stores/market'
import { useFavoriteStore } from '@/stores/favorites'
import { useUIStore } from '@/stores/ui'
import { useWebSocketStore } from '@/stores/websocket'
import { useSymbols } from '@/hooks/useSymbols'
import { formatPrice } from '@/utils/format'

/** 列表最大显示条数，避免DOM过多 */
const MAX_DISPLAY = 50

/** 侧边栏：交易对列表 */
export default function Sidebar() {
  const [search, setSearch] = useState('')
  const collapsed = useUIStore((s) => s.sidebarCollapsed)
  const { exchange, symbol: activeSymbol, setSymbol } = useMarketStore()
  const { symbols: favorites, addFavorite, removeFavorite } =
    useFavoriteStore()
  const prices = useWebSocketStore((s) => s.prices)
  const navigate = useNavigate()
  const { data: symbolData, isLoading: symbolsLoading } = useSymbols(exchange)

  const allSymbols = symbolData?.symbols ?? []

  /** 按搜索词过滤并限制显示条数 */
  const filtered = useMemo(() => {
    const keyword = search.toLowerCase()
    const matched = keyword
      ? allSymbols.filter((s) => s.toLowerCase().includes(keyword))
      : allSymbols
    return matched.slice(0, MAX_DISPLAY)
  }, [allSymbols, search])

  if (collapsed) return null

  const handleSelect = (sym: string) => {
    setSymbol(sym)
    navigate(`/market/${encodeURIComponent(sym)}`)
  }

  return (
    <div
      style={{
        width: 220,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <div style={{ padding: '8px 12px' }}>
        <Input
          size="small"
          placeholder="搜索交易对"
          prefix={<SearchOutlined />}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
      </div>

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {/* 收藏列表 */}
        {favorites.length > 0 && (
          <div style={{ padding: '4px 0' }}>
            <div
              style={{
                padding: '4px 12px',
                fontSize: 11,
                color: 'var(--text-secondary)',
              }}
            >
              收藏
            </div>
            {favorites
              .filter((s) =>
                s.toLowerCase().includes(search.toLowerCase()),
              )
              .map((sym) => (
                <SymbolRow
                  key={`fav-${sym}`}
                  symbol={sym}
                  price={prices[sym]}
                  active={sym === activeSymbol}
                  favorited
                  onSelect={() => handleSelect(sym)}
                  onToggleFav={() => removeFavorite(sym)}
                />
              ))}
          </div>
        )}

        {/* 全部交易对 */}
        <div style={{ padding: '4px 0' }}>
          <div
            style={{
              padding: '4px 12px',
              fontSize: 11,
              color: 'var(--text-secondary)',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <span>全部</span>
            <span>
              {symbolsLoading ? (
                <Spin size="small" />
              ) : (
                `${filtered.length}/${allSymbols.length}`
              )}
            </span>
          </div>
          {filtered.map((sym) => (
            <SymbolRow
              key={sym}
              symbol={sym}
              price={prices[sym]}
              active={sym === activeSymbol}
              favorited={favorites.includes(sym)}
              onSelect={() => handleSelect(sym)}
              onToggleFav={() =>
                favorites.includes(sym)
                  ? removeFavorite(sym)
                  : addFavorite(sym)
              }
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function SymbolRow({
  symbol,
  price,
  active,
  favorited,
  onSelect,
  onToggleFav,
}: {
  symbol: string
  price?: number
  active: boolean
  favorited: boolean
  onSelect: () => void
  onToggleFav: () => void
}) {
  return (
    <div
      onClick={onSelect}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '6px 12px',
        cursor: 'pointer',
        background: active
          ? 'var(--bg-tertiary)'
          : 'transparent',
        fontSize: 13,
      }}
    >
      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span
          onClick={(e) => {
            e.stopPropagation()
            onToggleFav()
          }}
          style={{ cursor: 'pointer', fontSize: 12 }}
        >
          {favorited ? (
            <StarFilled style={{ color: 'var(--warning)' }} />
          ) : (
            <StarOutlined style={{ color: 'var(--text-secondary)' }} />
          )}
        </span>
        <span>{symbol}</span>
      </span>
      {price != null && (
        <span style={{ fontVariantNumeric: 'tabular-nums' }}>
          {formatPrice(price)}
        </span>
      )}
    </div>
  )
}
