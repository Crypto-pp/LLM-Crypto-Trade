import type { ThemeConfig } from 'antd'

/** Ant Design 暗色主题令牌 */
export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#58a6ff',
    colorBgContainer: '#161b22',
    colorBgElevated: '#21262d',
    colorBgLayout: '#0d1117',
    colorBorder: '#30363d',
    colorText: '#e6edf3',
    colorTextSecondary: '#8b949e',
    colorSuccess: '#3fb950',
    colorError: '#f85149',
    colorWarning: '#d29922',
    colorLink: '#58a6ff',
    borderRadius: 6,
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  components: {
    Layout: {
      headerBg: '#161b22',
      siderBg: '#161b22',
      bodyBg: '#0d1117',
    },
    Menu: {
      darkItemBg: '#161b22',
      darkItemSelectedBg: '#21262d',
    },
    Table: {
      headerBg: '#161b22',
      rowHoverBg: '#21262d',
    },
    Card: {
      colorBgContainer: '#161b22',
    },
  },
}
