import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  theme,
} from 'antd'
import { PlusOutlined, HomeOutlined } from '@ant-design/icons'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const PROPERTY_TYPES = [
  { value: 'residential', label: 'Residential' },
  { value: 'commercial', label: 'Commercial' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'land', label: 'Land' },
]

function typeTagColor(t) {
  const map = {
    residential: 'green',
    commercial: 'blue',
    industrial: 'orange',
    land: 'default',
  }
  return map[t] || 'default'
}

export function PropertiesPage() {
  const { token } = theme.useToken()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [addOpen, setAddOpen] = useState(false)
  const [form] = Form.useForm()

  const canManage = ['admin', 'property_manager'].includes(user?.role)

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['properties', page],
    queryFn: () =>
      api.get('/api/properties/', { params: { page } }).then((r) => r.data),
  })

  const { data: managersData } = useQuery({
    queryKey: ['property-managers-pick'],
    queryFn: () => api.get('/api/auth/users/').then((r) => r.data),
    enabled: addOpen && canManage,
  })

  const managerOptions = useMemo(() => {
    const raw = Array.isArray(managersData) ? managersData : []
    return raw
      .filter(
        (u) =>
          u.role === 'property_manager' ||
          u.role === 'admin' ||
          u.role === 'finance_manager',
      )
      .map((u) => ({
        value: u.id,
        label: `${u.display_name ?? u.username} (${u.role})`,
      }))
  }, [managersData])

  const createMutation = useMutation({
    mutationFn: (body) => api.post('/api/properties/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['properties'] })
      setAddOpen(false)
      form.resetFields()
    },
  })

  const results = data?.results ?? data ?? []
  const rows = Array.isArray(results) ? results : []

  const createError = createMutation.error?.response?.data
  const createErrorText =
    (typeof createError === 'string' && createError) ||
    createError?.detail ||
    (createError && JSON.stringify(createError))

  const onCreate = (v) => {
    const body = {
      name: v.name,
      property_type: v.property_type,
      city: v.city,
      district: v.district,
      location: v.location || '',
      size_sqm: v.size_sqm,
      num_units: v.num_units ?? 1,
      ownership_status: v.ownership_status || '',
      property_code: v.property_code || null,
    }
    if (v.property_manager_id != null) {
      body.property_manager_id = v.property_manager_id
    }
    body.owner_full_name = v.owner_full_name
    body.owner_national_id = v.owner_national_id
    body.owner_phone = v.owner_phone
    body.owner_email = v.owner_email
    body.owner_bank_iban = v.owner_bank_iban
    body.owner_address = v.owner_address || ''
    createMutation.mutate(body)
  }

  const columns = [
    {
      title: 'Owner ID',
      dataIndex: 'owner_reference',
      key: 'owner_ref',
      width: 100,
      ellipsis: true,
      render: (v) => v || '—',
    },
    {
      title: 'Code',
      dataIndex: 'property_code',
      key: 'property_code',
      width: 100,
      render: (v) => v || '—',
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      render: (text, row) => (
        <span>
          <Typography.Text strong>{text}</Typography.Text>
          {row.owner_full_name ? (
            <Typography.Text
              type="secondary"
              style={{ display: 'block', fontSize: 12 }}
            >
              {row.owner_full_name}
            </Typography.Text>
          ) : null}
        </span>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'property_type',
      key: 'property_type',
      width: 130,
      render: (t) => (
        <Tag color={typeTagColor(t)}>{String(t || '').replace(/_/g, ' ')}</Tag>
      ),
    },
    { title: 'City', dataIndex: 'city', key: 'city', width: 110 },
    { title: 'District', dataIndex: 'district', key: 'district', width: 120 },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
      ellipsis: true,
      render: (v) => v || '—',
    },
    {
      title: 'Units',
      dataIndex: 'num_units',
      key: 'num_units',
      width: 72,
      align: 'center',
    },
    {
      title: 'Vacant / Occ.',
      key: 'occ',
      width: 120,
      align: 'center',
      render: (_, row) => (
        <Typography.Text type="secondary">
          <Typography.Text type="success">{row.vacant_units ?? 0}</Typography.Text>
          {' / '}
          <Typography.Text>{row.occupied_units ?? 0}</Typography.Text>
        </Typography.Text>
      ),
    },
  ]

  const openAddModal = () => {
    createMutation.reset()
    setAddOpen(true)
  }

  return (
    <div>
      <Card
        variant="borderless"
        style={{
          borderRadius: token.borderRadiusLG,
          boxShadow: token.boxShadowTertiary,
        }}
        styles={{
          header: { borderBottom: `1px solid ${token.colorBorderSecondary}` },
          body: { padding: token.paddingLG },
        }}
        title={
          <Space align="start" size="middle" wrap>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: token.borderRadiusLG,
                background: token.colorPrimaryBg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: token.colorPrimary,
                fontSize: 22,
              }}
            >
              <HomeOutlined />
            </div>
            <div style={{ paddingRight: 8 }}>
              <Typography.Title level={3} style={{ margin: 0 }}>
                Properties
              </Typography.Title>
              <Typography.Paragraph
                type="secondary"
                style={{ margin: '4px 0 0', maxWidth: 560, marginBottom: 0 }}
              >
                Register and track buildings across KSA: type, location, unit
                counts, and occupancy at a glance.
              </Typography.Paragraph>
            </div>
          </Space>
        }
        extra={
          canManage ? (
            <Button
              type="primary"
              size="large"
              icon={<PlusOutlined />}
              onClick={openAddModal}
            >
              Add property
            </Button>
          ) : null
        }
      >
        {isError ? (
          <Typography.Text type="danger">
            {error?.message || 'Could not load properties'}
          </Typography.Text>
        ) : rows.length === 0 && !isLoading ? (
          <Empty
            description="No properties yet"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            {canManage && (
              <Button type="primary" onClick={() => setAddOpen(true)}>
                Add your first property
              </Button>
            )}
          </Empty>
        ) : (
          <Table
            rowKey="id"
            loading={isLoading}
            columns={columns}
            dataSource={rows}
            pagination={
              data?.count
                ? {
                    current: page,
                    pageSize: 20,
                    total: data.count,
                    showSizeChanger: false,
                    onChange: (p) => setPage(p),
                    showTotal: (total) => `${total} properties`,
                  }
                : false
            }
            scroll={{ x: 1120 }}
            size="middle"
          />
        )}
      </Card>

      <Modal
        title="Add property"
        open={addOpen}
        onCancel={() => {
          setAddOpen(false)
          createMutation.reset()
        }}
        footer={null}
        width={640}
        destroyOnClose
      >
        {createErrorText && (
          <Typography.Paragraph type="danger" style={{ marginBottom: 16 }}>
            {String(createErrorText)}
          </Typography.Paragraph>
        )}
        <Form
          form={form}
          layout="vertical"
          onFinish={onCreate}
          initialValues={{ num_units: 1, property_type: 'residential' }}
        >
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="property_code"
                label="Property code (optional)"
                tooltip="Unique business ID if you use one"
              >
                <Input placeholder="e.g. OLAYA-001" allowClear />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="property_type"
                label="Type"
                rules={[{ required: true, message: 'Select type' }]}
              >
                <Select options={PROPERTY_TYPES} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="name"
            label="Name"
            rules={[{ required: true, message: 'Enter property name' }]}
          >
            <Input placeholder="Building or complex name" />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="city"
                label="City"
                rules={[{ required: true, message: 'Enter city' }]}
              >
                <Input placeholder="Riyadh" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="district"
                label="District"
                rules={[{ required: true, message: 'Enter district' }]}
              >
                <Input placeholder="Al Olaya" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="location" label="Location detail (optional)">
            <Input placeholder="Street, landmark…" />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="size_sqm"
                label="Size (m²)"
                rules={[{ required: true, message: 'Enter size' }]}
              >
                <InputNumber
                  min={0}
                  step={10}
                  style={{ width: '100%' }}
                  placeholder="Land / building area"
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="num_units"
                label="Number of units"
                rules={[{ required: true, message: 'Enter unit count' }]}
              >
                <InputNumber min={1} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Registered owner (office record)</Divider>
          <Typography.Paragraph type="secondary" style={{ marginTop: -8 }}>
            Owner ID is assigned automatically when the property is saved (e.g.{' '}
            <Typography.Text code>O-000042</Typography.Text>). Not a system login.
          </Typography.Paragraph>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_full_name"
                label="Full name"
                rules={[{ required: true, message: 'Enter owner name' }]}
              >
                <Input placeholder="Landlord / lessor name" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_national_id"
                label="National ID / Iqama"
                rules={[{ required: true, message: 'Enter ID' }]}
              >
                <Input placeholder="10-digit national ID or Iqama" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_phone"
                label="Phone"
                rules={[{ required: true, message: 'Enter phone' }]}
              >
                <Input placeholder="+966…" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_email"
                label="Email"
                rules={[
                  { required: true, message: 'Enter email' },
                  { type: 'email', message: 'Invalid email' },
                ]}
              >
                <Input type="email" placeholder="owner@example.com" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="owner_bank_iban"
            label="Bank account / IBAN (rent payouts)"
            rules={[{ required: true, message: 'Enter IBAN or account' }]}
          >
            <Input placeholder="SA…" />
          </Form.Item>
          <Form.Item name="owner_address" label="Address (optional)">
            <Input.TextArea rows={2} placeholder="Street, building, optional" />
          </Form.Item>

          <Divider orientation="left">Internal</Divider>
          <Form.Item name="ownership_status" label="Ownership status (optional)">
            <Input placeholder="e.g. Owned, leased land" />
          </Form.Item>
          <Form.Item
            name="property_manager_id"
            label="Property manager (optional)"
            tooltip="Users with manager / admin roles"
          >
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              placeholder="Assign a manager"
              options={managerOptions}
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={createMutation.isPending}
              >
                Create property
              </Button>
              <Button onClick={() => setAddOpen(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
