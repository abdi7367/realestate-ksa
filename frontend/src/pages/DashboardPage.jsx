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
import heroImg from '../assets/hero.svg'

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

export function DashboardPage() {
  const { t, i18n } = useTranslation()
  const { user } = useAuth()
  const rtl = i18n.dir() === 'rtl'
  const Arrow = rtl ? LeftOutlined : RightOutlined

  return (
    <div className="dashboard-page">
      <div className="dashboard-hero">
        <Row gutter={[32, 32]} align="middle">
          <Col xs={24} lg={14}>
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
              <strong>{t('dashboard.welcome')}</strong>
              {user?.username ? `, ${user.username}` : ''}. {t('dashboard.chooseModule')}
            </Typography.Paragraph>
          </Col>
          <Col xs={24} lg={10} className="dashboard-hero-visual">
            <img src={heroImg} alt="" className="dashboard-hero-art" />
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
