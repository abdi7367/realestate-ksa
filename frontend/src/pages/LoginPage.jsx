import { useEffect } from 'react'
import { Button, Card, Form, Input, Typography, message, Select, Space } from 'antd'
import { GlobalOutlined } from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'

export function LoginPage() {
  const { t, i18n } = useTranslation()
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
      message.success(t('login.signedIn'))
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
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
        <Space size={8}>
          <GlobalOutlined />
          <Select
            size="small"
            value={i18n.language}
            onChange={(lng) => i18n.changeLanguage(lng)}
            options={[
              { value: 'en', label: 'English' },
              { value: 'ar', label: 'العربية' },
            ]}
            style={{ width: 130 }}
          />
        </Space>
      </div>
      <Typography.Title level={3} style={{ textAlign: 'center' }}>
        {t('brand')}
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ textAlign: 'center' }}>
        {t('login.subtitle')}
      </Typography.Paragraph>
      <Card>
        <Form layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            name="username"
            label={t('login.username')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input autoComplete="username" size="large" />
          </Form.Item>
          <Form.Item
            name="password"
            label={t('login.password')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input.Password autoComplete="current-password" size="large" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              {t('login.submit')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
