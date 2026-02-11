import { Skeleton } from 'antd'

interface LoadingSkeletonProps {
  rows?: number
  avatar?: boolean
}

/** 骨架屏加载态 */
export default function LoadingSkeleton({
  rows = 4,
  avatar = false,
}: LoadingSkeletonProps) {
  return (
    <div style={{ padding: 16 }}>
      <Skeleton active paragraph={{ rows }} avatar={avatar} />
    </div>
  )
}
