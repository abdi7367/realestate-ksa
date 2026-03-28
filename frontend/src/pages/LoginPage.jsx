import { useEffect } from 'react'
import { Button, Card, Form, Input, Typography, message } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/'

  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true })
  }, [isAuthenticated, from, navigate])

  const onFinish = async ({ username, password }) => {
    try {
      await login(username, password)
      message.success('Signed in')
      navigate(from, { replace: true })
    } catch (e) {
      const detail =
        e.response?.data?.detail ||
        e.response?.data?.non_field_errors?.[0] ||
        'Login failed'
      message.error(typeof detail === 'string' ? detail : 'Invalid credentials')
    }
  }

  return (
    <div
      style={{
        maxWidth: 400,
        margin: '80px auto',
        padding: '0 16px',
      }}
    >
      <Typography.Title level={3} style={{ textAlign: 'center' }}>
        Real Estate KSA
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ textAlign: 'center' }}>
        Sign in with your Django admin username and password
      </Typography.Paragraph>
      <Card>
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Input autoComplete="username" size="large" />
          </Form.Item>
          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Input.Password autoComplete="current-password" size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              Sign in
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
