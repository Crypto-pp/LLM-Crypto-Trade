import { Suspense } from 'react'
import { Outlet } from 'react-router-dom'
import { Spin } from 'antd'
import TopBar from './TopBar'
import Sidebar from './Sidebar'
import StatusBar from './StatusBar'

/** 应用外壳：TopBar + Sidebar + Content + StatusBar */
export default function AppShell() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
      }}
    >
      <TopBar />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />
        <main
          style={{
            flex: 1,
            overflow: 'auto',
            background: 'var(--bg-primary)',
            padding: 16,
          }}
        >
          <Suspense
            fallback={
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  height: '100%',
                }}
              >
                <Spin size="large" />
              </div>
            }
          >
            <Outlet />
          </Suspense>
        </main>
      </div>
      <StatusBar />
    </div>
  )
}
