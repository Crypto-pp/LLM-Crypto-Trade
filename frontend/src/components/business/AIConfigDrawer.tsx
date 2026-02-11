import { Drawer } from 'antd'
import AIConfigPanel from './AIConfigPanel'

interface Props {
  open: boolean
  onClose: () => void
}

/** AI配置抽屉（包装 AIConfigPanel） */
export default function AIConfigDrawer({ open, onClose }: Props) {
  return (
    <Drawer
      title="AI模型配置"
      placement="right"
      width={420}
      open={open}
      onClose={onClose}
    >
      <AIConfigPanel />
    </Drawer>
  )
}
