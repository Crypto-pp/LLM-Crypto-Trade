import { Radio } from 'antd'
import { INTERVALS } from '@/utils/constants'
import { useMarketStore } from '@/stores/market'

/** 时间周期选择器 */
export default function IntervalSelector() {
  const { interval, setInterval } = useMarketStore()

  return (
    <Radio.Group
      value={interval}
      onChange={(e) => setInterval(e.target.value)}
      size="small"
      optionType="button"
      buttonStyle="solid"
    >
      {INTERVALS.map((item) => (
        <Radio.Button key={item.value} value={item.value}>
          {item.label}
        </Radio.Button>
      ))}
    </Radio.Group>
  )
}
