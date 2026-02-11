import { Menu } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  FundOutlined,
  ExperimentOutlined,
  HistoryOutlined,
  SettingOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表板' },
  { key: '/market', icon: <LineChartOutlined />, label: '行情' },
  { key: '/analysis', icon: <FundOutlined />, label: '分析' },
  { key: '/strategies', icon: <ExperimentOutlined />, label: '策略' },
  { key: '/backtest', icon: <HistoryOutlined />, label: '回测' },
  { key: '/ai-analysis', icon: <RobotOutlined />, label: 'AI分析' },
  { key: '/system', icon: <SettingOutlined />, label: '设置' },
]

/** 顶部导航栏 */
export default function TopBar() {
  const navigate = useNavigate()
  const location = useLocation()

  const activeKey =
    menuItems.find(
      (item) =>
        item.key !== '/' && location.pathname.startsWith(item.key),
    )?.key || '/'

  return (
    <div
      style={{
        height: 48,
        display: 'flex',
        alignItems: 'center',
        background: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border)',
        padding: '0 16px',
      }}
    >
      <div
        style={{
          fontWeight: 700,
          fontSize: 16,
          color: 'var(--accent)',
          marginRight: 32,
          whiteSpace: 'nowrap',
        }}
      >
        Crypto-Trade
      </div>
      <Menu
        mode="horizontal"
        selectedKeys={[activeKey]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
        style={{
          flex: 1,
          background: 'transparent',
          borderBottom: 'none',
          lineHeight: '46px',
        }}
      />
    </div>
  )
}
