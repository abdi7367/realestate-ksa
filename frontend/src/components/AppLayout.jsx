import { Layout, Menu, theme, Typography, Button, Space, Select } from 'antd'
import {
  AccountBookOutlined,
  BankOutlined,
  FileDoneOutlined,
  FileTextOutlined,
  GlobalOutlined,
  HomeOutlined,
  LogoutOutlined,
  SolutionOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { useMemo } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'

const { Header, Sider, Content } = Layout

export function AppLayout() {
  const { token } = theme.useToken()
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()
  const { t, i18n } = useTranslation()
  const isRtl = i18n.language === 'ar'

  const roleLabel = useMemo(() => {
    const role = user?.role
    if (!role) return ''
    const key = `dashboard.roles.${role}`
    return i18n.exists(key) ? t(key) : role
  }, [user?.role, t, i18n])

  const menuItems = useMemo(
    () => [
      {
        key: '/',
        icon: <HomeOutlined />,
        label: <Link to="/">{t('layout.nav.dashboard')}</Link>,
      },
      {
        key: '/properties',
        icon: <BankOutlined />,
        label: <Link to="/properties">{t('layout.nav.properties')}</Link>,
      },
      {
        key: '/reports',
        icon: <FileTextOutlined />,
        label: <Link to="/reports">{t('layout.nav.reports')}</Link>,
      },
      {
        key: '/contracts',
        icon: <SolutionOutlined />,
        label: <Link to="/contracts">{t('layout.nav.contracts')}</Link>,
      },
      {
        key: '/debts',
        icon: <AccountBookOutlined />,
        label: <Link to="/debts">{t('layout.nav.debts')}</Link>,
      },
      {
        key: '/finance',
        icon: <WalletOutlined />,
        label: <Link to="/finance">{t('layout.nav.finance')}</Link>,
      },
      {
        key: '/vouchers',
        icon: <FileDoneOutlined />,
        label: <Link to="/vouchers">{t('layout.nav.vouchers')}</Link>,
      },
    ],
    [t],
  )

  return (
    <Layout
      style={{
        minHeight: '100vh',
        width: '100%',
        flexDirection: isRtl ? 'row-reverse' : 'row',
      }}
    >
      <Sider breakpoint="lg" collapsedWidth="0" theme="dark" width={230}>
        <div
          style={{
            padding: '18px 14px',
            fontWeight: 600,
            color: token.colorWhite,
            fontSize: 15,
            letterSpacing: isRtl ? '0' : '0.02em',
            textAlign: isRtl ? 'right' : 'left',
            lineHeight: 1.35,
          }}
        >
          {t('brand')}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname === '/' ? '/' : location.pathname]}
          items={menuItems}
        />
      </Sider>
      <Layout style={{ flex: 1, minWidth: 0 }}>
        <Header
          style={{
            background: token.colorBgContainer,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}
        >
          <Typography.Text type="secondary">{t('layout.tagline')}</Typography.Text>
          <Space size="middle" wrap>
            <Space size={4}>
              <GlobalOutlined />
              <Typography.Text type="secondary">{t('layout.language')}</Typography.Text>
              <Select
                size="small"
                value={i18n.language}
                onChange={(lng) => i18n.changeLanguage(lng)}
                options={[
                  { value: 'en', label: 'English' },
                  { value: 'ar', label: 'العربية' },
                ]}
                style={{ width: 130 }}
                popupMatchSelectWidth={false}
              />
            </Space>
            {isAuthenticated && user && (
              <Typography.Text>
                {user.username}
                {user.role ? ` · ${roleLabel}` : ''}
              </Typography.Text>
            )}
            {isAuthenticated && (
              <Button
                icon={<LogoutOutlined />}
                onClick={() => {
                  logout()
                  navigate('/login')
                }}
              >
                {t('layout.logout')}
              </Button>
            )}
          </Space>
        </Header>
        <Content
          style={{
            margin: '16px 24px 24px',
            width: '100%',
            maxWidth: '100%',
            boxSizing: 'border-box',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
