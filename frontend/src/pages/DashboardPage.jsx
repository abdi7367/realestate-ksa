import { Card, Col, Row, Typography, Space } from 'antd'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  AccountBookOutlined,
  BankOutlined,
  FileDoneOutlined,
  FileTextOutlined,
  RightOutlined,
  LeftOutlined,
  SolutionOutlined,
  WalletOutlined,
} from '@ant-design/icons'
import { useAuth } from '../context/AuthContext'
import heroImg from '../assets/hero-new.jpg'

const MODULES = [
  {
    key: 'properties',
    to: '/properties',
    icon: BankOutlined,
    color: '#0d9488',
  },
  {
    key: 'contracts',
    to: '/contracts',
    icon: SolutionOutlined,
    color: '#2563eb',
  },
  {
    key: 'reports',
    to: '/reports',
    icon: FileTextOutlined,
    color: '#7c3aed',
  },
  {
    key: 'debts',
    to: '/debts',
    icon: AccountBookOutlined,
    color: '#c2410c',
  },
  {
    key: 'finance',
    to: '/finance',
    icon: WalletOutlined,
    color: '#047857',
  },
  {
    key: 'vouchers',
    to: '/vouchers',
    icon: FileDoneOutlined,
    color: '#b45309',
  },
]

function roleDisplayName(role, t, i18n) {
  if (!role) return t('dashboard.roleGuest')
  const key = `dashboard.roles.${role}`
  if (i18n.exists(key)) return t(key)
  return role
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

export function DashboardPage() {
  const { t, i18n } = useTranslation()
  const { user } = useAuth()
  const rtl = i18n.dir() === 'rtl'
  const Arrow = rtl ? LeftOutlined : RightOutlined
  const roleLabel = roleDisplayName(user?.role, t, i18n)

  return (
    <div className={`dashboard-page${rtl ? ' dashboard-page--rtl' : ''}`}>
      <div
        className={`dashboard-hero${rtl ? ' dashboard-hero--rtl' : ''}`}
        style={{
          '--dashboard-hero-image': `url(${heroImg})`,
        }}
      >
        <Row
          gutter={[24, 24]}
          align="middle"
          className={`dashboard-hero-row${rtl ? ' dashboard-hero-row--rtl' : ''}`}
        >
          <Col xs={24} lg={15} className={rtl ? 'dashboard-hero-copy dashboard-hero-copy--rtl' : 'dashboard-hero-copy'}>
            <Typography.Text type="secondary" className="dashboard-eyebrow">
              {t('dashboard.heroEyebrow')}
            </Typography.Text>
            <Typography.Title level={2} className="dashboard-hero-title">
              {t('dashboard.heroTitle')}
            </Typography.Title>
            <Typography.Paragraph className="dashboard-hero-desc">
              {t('dashboard.heroDesc')}
            </Typography.Paragraph>
            <Typography.Paragraph className="dashboard-welcome-line" style={{ marginBottom: 0 }}>
              {t('dashboard.signedInAs')}{' '}
              <strong>{roleLabel}</strong>
              {user?.username ? ` (${user.username})` : ''}
            </Typography.Paragraph>
          </Col>
          <Col xs={24} lg={9}>
            <div className="dashboard-hero-visual">
              <div className="dashboard-hero-art-wrapper">
                <img src={heroImg} alt={t('dashboard.heroImageAlt')} className="dashboard-hero-art" />
              </div>
            </div>
          </Col>
        </Row>
      </div>

      <Typography.Title level={4} className="dashboard-section-title">
        {t('dashboard.title')}
      </Typography.Title>

      <Row gutter={[20, 20]}>
        {MODULES.map(({ key, to, icon: Icon, color }) => (
          <Col xs={24} sm={12} xl={8} key={key}>
            <Card hoverable className="dashboard-card" bordered={false}>
              <Link to={to} className="dashboard-card-link">
                <Space align="start" size={16} wrap>
                  <div
                    className="dashboard-card-icon"
                    style={{
                      background: `${color}18`,
                      color,
                    }}
                  >
                    <Icon />
                  </div>
                  <div className="dashboard-card-body">
                    <Typography.Title level={5} className="dashboard-card-title">
                      {t(`dashboard.cards.${key}.title`)}
                    </Typography.Title>
                    <Typography.Paragraph type="secondary" className="dashboard-card-desc">
                      {t(`dashboard.cards.${key}.desc`)}
                    </Typography.Paragraph>
                    <Typography.Text type="primary" className="dashboard-card-cta">
                      {t('dashboard.open')} <Arrow />
                    </Typography.Text>
                  </div>
                </Space>
              </Link>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  )
}
