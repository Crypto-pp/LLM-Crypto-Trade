import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/api/settings'
import type {
  ExchangeConfigUpdate,
  SignalMonitorCreate,
  SignalMonitorUpdate,
  NotificationChannelCreate,
  NotificationChannelUpdate,
  NotificationSettings,
} from '@/types/settings'

/** 交易所配置查询 Hook */
export function useExchangeConfig() {
  return useQuery({
    queryKey: ['exchange-config'],
    queryFn: () => settingsApi.getExchangeConfig(),
    staleTime: 60_000,
  })
}

/** 交易所配置更新 Mutation Hook */
export function useExchangeConfigUpdate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ExchangeConfigUpdate) => settingsApi.updateExchangeConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exchange-config'] })
    },
  })
}

/** 信号监控任务查询 Hook */
export function useSignalMonitors() {
  return useQuery({
    queryKey: ['signal-monitors'],
    queryFn: () => settingsApi.getSignalMonitors(),
    staleTime: 30_000,
  })
}

/** 添加信号监控任务 Mutation Hook */
export function useAddSignalMonitor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: SignalMonitorCreate) => settingsApi.addSignalMonitor(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal-monitors'] })
    },
  })
}

/** 更新信号监控任务 Mutation Hook */
export function useUpdateSignalMonitor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SignalMonitorUpdate }) =>
      settingsApi.updateSignalMonitor(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal-monitors'] })
    },
  })
}

/** 删除信号监控任务 Mutation Hook */
export function useDeleteSignalMonitor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => settingsApi.deleteSignalMonitor(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal-monitors'] })
    },
  })
}

/** 手动触发执行信号监控任务 Mutation Hook */
export function useRunSignalMonitor() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => settingsApi.runSignalMonitor(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['signal-monitors'] })
    },
  })
}

// ========== 通知配置 Hooks ==========

/** 通知配置查询 Hook */
export function useNotificationConfig() {
  return useQuery({
    queryKey: ['notification-config'],
    queryFn: () => settingsApi.getNotificationConfig(),
    staleTime: 30_000,
  })
}

/** 更新通知全局设置 Mutation Hook */
export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<NotificationSettings>) =>
      settingsApi.updateNotificationSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-config'] })
    },
  })
}

/** 添加通知渠道 Mutation Hook */
export function useAddNotificationChannel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: NotificationChannelCreate) =>
      settingsApi.addNotificationChannel(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-config'] })
    },
  })
}

/** 更新通知渠道 Mutation Hook */
export function useUpdateNotificationChannel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NotificationChannelUpdate }) =>
      settingsApi.updateNotificationChannel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-config'] })
    },
  })
}

/** 删除通知渠道 Mutation Hook */
export function useDeleteNotificationChannel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => settingsApi.deleteNotificationChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notification-config'] })
    },
  })
}

/** 测试通知渠道 Mutation Hook */
export function useTestNotificationChannel() {
  return useMutation({
    mutationFn: (id: string) => settingsApi.testNotificationChannel(id),
  })
}
