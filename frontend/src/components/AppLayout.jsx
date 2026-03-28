import { Layout, Menu, theme, Typography, Button, Space } from 'antd'
import {
  AccountBookOutlined,
  BankOutlined,
  FileDoneOutlined,
  FileTextOutlined,
  HomeOutlined,
  LogoutOutlined,
  SolutionOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const { Header, Sider, Content } = Layout

const items = [
  { key: '/', icon: <HomeOutlined />, label: <Link to="/">Dashboard</Link> },
  {
    key: '/properties',
    icon: <BankOutlined />,
    label: <Link to="/properties">Properties</Link>,
  },
  {
    key: '/reports',
    icon: <FileTextOutlined />,
    label: <Link to="/reports">Reports</Link>,
  },
  {
    key: '/contracts',
    icon: <SolutionOutlined />,
    label: <Link to="/contracts">Contracts</Link>,
  },
  {
    key: '/debts',
    icon: <AccountBookOutlined />,
    label: <Link to="/debts">Debts</Link>,
  },
  {
    key: '/finance',
    icon: <WalletOutlined />,
    label: <Link to="/finance">Finance</Link>,
  },
  {
    key: '/vouchers',
    icon: <FileDoneOutlined />,
    label: <Link to="/vouchers">Vouchers</Link>,
  },
]

export function AppLayout() {
  const { token } = theme.useToken()
  const location = useLocation()
  const navigate = useNavigate()
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <Layout style={{ minHeight: '100vh', width: '100%' }}>
      <Sider breakpoint="lg" collapsedWidth="0" theme="dark" width={220}>
        <div
          style={{
            padding: '16px 12px',
            fontWeight: 600,
            color: token.colorWhite,
            fontSize: 14,
          }}
        >
          Real Estate KSA
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname === '/' ? '/' : location.pathname]}
          items={items}
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
          <Typography.Text type="secondary">
            Property management
          </Typography.Text>
          <Space>
            {isAuthenticated && user && (
              <Typography.Text>
                {user.username}
                {user.role ? ` · ${user.role}` : ''}
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
                Log out
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
