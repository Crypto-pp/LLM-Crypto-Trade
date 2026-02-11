import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Form, Input, Button, Card, message, Alert } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import { authApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

export default function ChangePassword() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const mustChange = useAuthStore((s) => s.mustChangePassword)

  const onFinish = async (values: {
    old_password: string
    new_password: string
    confirm_password: string
  }) => {
    if (values.new_password !== values.confirm_password) {
      message.error('两次输入的新密码不一致')
      return
    }
    setLoading(true)
    try {
      await authApi.changePassword(values.old_password, values.new_password)
      message.success('密码修改成功，请重新登录')
      logout()
      navigate('/login', { replace: true })
    } catch (err: any) {
      message.error(err?.message || '密码修改失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'var(--bg-primary, #141414)',
      }}
    >
      <Card
        title="修改密码"
        style={{ width: 400 }}
        styles={{ header: { textAlign: 'center', fontSize: 18 } }}
      >
        {mustChange && (
          <Alert
            message="首次登录需要修改默认密码"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        <Form onFinish={onFinish} autoComplete="off" size="large">
          <Form.Item
            name="old_password"
            rules={[{ required: true, message: '请输入旧密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="旧密码" />
          </Form.Item>
          <Form.Item
            name="new_password"
            rules={[
              { required: true, message: '请输入新密码' },
              { min: 6, message: '密码长度不能少于6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="新密码" />
          </Form.Item>
          <Form.Item
            name="confirm_password"
            rules={[
              { required: true, message: '请确认新密码' },
              { min: 6, message: '密码长度不能少于6位' },
            ]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="确认新密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              确认修改
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
