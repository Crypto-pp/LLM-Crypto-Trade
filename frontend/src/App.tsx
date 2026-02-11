import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import AppShell from '@/components/layout/AppShell'
import Dashboard from '@/pages/Dashboard'
import Market from '@/pages/Market'
import MarketDetail from '@/pages/MarketDetail'
import Analysis from '@/pages/Analysis'
import Strategies from '@/pages/Strategies'
import StrategyDetail from '@/pages/StrategyDetail'
import Backtest from '@/pages/Backtest'
import BacktestReport from '@/pages/BacktestReport'
import System from '@/pages/System'
import AIAnalysis from '@/pages/AIAnalysis'
import Login from '@/pages/Login'
import ChangePassword from '@/pages/ChangePassword'
import { useAuthStore } from '@/stores/auth'

/** 认证守卫：未登录跳转登录页，需改密码跳转改密页 */
function AuthGuard() {
  const { isAuthenticated, mustChangePassword } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  if (mustChangePassword) {
    return <Navigate to="/change-password" replace />
  }
  return <AppShell />
}

const router = createBrowserRouter([
  // 公开路由
  { path: '/login', element: <Login /> },
  { path: '/change-password', element: <ChangePassword /> },
  // 受保护路由
  {
    path: '/',
    element: <AuthGuard />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <Dashboard /> },
      { path: 'market', element: <Market /> },
      { path: 'market/:symbol', element: <MarketDetail /> },
      { path: 'analysis', element: <Analysis /> },
      { path: 'strategies', element: <Strategies /> },
      { path: 'strategies/:name', element: <StrategyDetail /> },
      { path: 'backtest', element: <Backtest /> },
      { path: 'backtest/:id', element: <BacktestReport /> },
      { path: 'system', element: <System /> },
      { path: 'ai-analysis', element: <AIAnalysis /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
