import { Card, Col, Row, Typography } from 'antd'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div>
      <Typography.Title level={4}>Dashboard</Typography.Title>
      <Typography.Paragraph type="secondary">
        Welcome{user?.username ? `, ${user.username}` : ''}. Use the sidebar to
        manage data.
      </Typography.Paragraph>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} lg={8}>
          <Card title="Properties" bordered={false}>
            <Link to="/properties">View properties and units</Link>
          </Card>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <Card title="Contracts" bordered={false}>
            <Link to="/contracts">Contracts, payments, termination</Link>
          </Card>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <Card title="Reports" bordered={false}>
            <Link to="/reports">Financial and operational reports</Link>
          </Card>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <Card title="Debts" bordered={false}>
            <Link to="/debts">Loans and installments</Link>
          </Card>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <Card title="Finance" bordered={false}>
            <Link to="/finance">Income and expense transactions</Link>
          </Card>
        </Col>
        <Col xs={24} md={12} lg={8}>
          <Card title="Vouchers" bordered={false}>
            <Link to="/vouchers">Payment vouchers and approvals</Link>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
