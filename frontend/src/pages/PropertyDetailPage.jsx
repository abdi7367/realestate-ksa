import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import {
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

function asArray(data) {
  const raw = data?.results ?? data ?? []
  return Array.isArray(raw) ? raw : []
}

const UNIT_TYPES = [
  { value: 'apartment', label: 'Apartment' },
  { value: 'office', label: 'Office' },
  { value: 'shop', label: 'Shop' },
  { value: 'villa', label: 'Villa' },
]

const RENTAL_STATUSES = [
  { value: 'vacant', label: 'Vacant' },
  { value: 'occupied', label: 'Occupied' },
  { value: 'maintenance', label: 'Under maintenance' },
  { value: 'reserved', label: 'Reserved' },
]

export function PropertyDetailPage() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const canManageUnits = ['admin', 'property_manager'].includes(user?.role)
  const [unitModal, setUnitModal] = useState({ open: false, unit: null })
  const [unitForm] = Form.useForm()

  const { data: property, isLoading: propertyLoading } = useQuery({
    queryKey: ['property', id],
    queryFn: () => api.get(`/api/properties/${id}/`).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: unitsData, isLoading: unitsLoading } = useQuery({
    queryKey: ['property', id, 'units'],
    queryFn: () =>
      api.get('/api/units/', { params: { property: id, page_size: 500 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: contractsData, isLoading: contractsLoading } = useQuery({
    queryKey: ['property', id, 'contracts'],
    queryFn: () => api.get('/api/contracts/', { params: { property: id, page_size: 200 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: debtsData, isLoading: debtsLoading } = useQuery({
    queryKey: ['property', id, 'debts'],
    queryFn: () => api.get('/api/debts/', { params: { property: id, page_size: 200 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: txData, isLoading: txLoading } = useQuery({
    queryKey: ['property', id, 'transactions'],
    queryFn: () =>
      api.get('/api/transactions/', { params: { property: id, page_size: 200 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const units = asArray(unitsData)
  const contracts = asArray(contractsData)
  const debts = asArray(debtsData)
  const transactions = asArray(txData)

  const upsertUnit = useMutation({
    mutationFn: async (values) => {
      if (!id) throw new Error('Missing property id')
      const payload = {
        property: Number(id),
        unit_number: String(values.unit_number || '').trim(),
        floor: Number(values.floor),
        size_sqm: String(values.size_sqm),
        unit_type: values.unit_type,
        rental_status: values.rental_status,
        monthly_rent: String(values.monthly_rent ?? 0),
        notes: values.notes || '',
      }
      if (unitModal.unit?.id) {
        return api.patch(`/api/units/${unitModal.unit.id}/`, payload)
      }
      return api.post('/api/units/', payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['property', id, 'units'] })
      queryClient.invalidateQueries({ queryKey: ['property', id] })
      setUnitModal({ open: false, unit: null })
      unitForm.resetFields()
    },
  })

  const openCreateUnit = () => {
    setUnitModal({ open: true, unit: null })
    unitForm.setFieldsValue({
      unit_number: '',
      floor: 1,
      size_sqm: 0,
      unit_type: 'apartment',
      rental_status: 'vacant',
      monthly_rent: 0,
      notes: '',
    })
  }

  const openEditUnit = (unit) => {
    setUnitModal({ open: true, unit })
    unitForm.setFieldsValue({
      unit_number: unit.unit_number,
      floor: unit.floor,
      size_sqm: unit.size_sqm,
      unit_type: unit.unit_type,
      rental_status: unit.rental_status,
      monthly_rent: unit.monthly_rent,
      notes: unit.notes,
    })
  }

  const closeUnitModal = () => {
    setUnitModal({ open: false, unit: null })
    unitForm.resetFields()
  }

  const totals = useMemo(() => {
    const activeContracts = contracts.filter((c) => c.status === 'active').length
    const occupied = units.filter((u) => u.rental_status === 'occupied').length
    const vacant = units.filter((u) => u.rental_status === 'vacant').length
    const debtTotal = debts.reduce((sum, d) => sum + Number(d.total_amount || 0), 0)
    const txIncome = transactions
      .filter((t) => t.transaction_type === 'income')
      .reduce((sum, t) => sum + Number(t.amount || 0), 0)
    const txExpense = transactions
      .filter((t) => t.transaction_type === 'expense')
      .reduce((sum, t) => sum + Number(t.amount || 0), 0)
    return { activeContracts, occupied, vacant, debtTotal, txIncome, txExpense }
  }, [contracts, units, debts, transactions])

  if (!id) return <Empty description="Property not found" />

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Text type="secondary">
          <Link to="/properties">Properties</Link> / Detail
        </Typography.Text>
        <Typography.Title level={3} style={{ margin: '6px 0 0' }}>
          {propertyLoading ? 'Loading property...' : property?.name || `Property #${id}`}
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {property?.city || '—'} · {property?.district || '—'} · {property?.location || 'No location detail'}
        </Typography.Paragraph>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic title="Units (occupied / vacant)" value={`${totals.occupied} / ${totals.vacant}`} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic title="Active contracts" value={totals.activeContracts} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic title="Total debts (SAR)" value={totals.debtTotal.toFixed(2)} />
          </Card>
        </Col>
      </Row>

      <Card
        title="Units"
        extra={
          canManageUnits ? (
            <Button type="primary" onClick={openCreateUnit}>
              Add unit
            </Button>
          ) : null
        }
      >
        <Table
          rowKey="id"
          loading={unitsLoading}
          dataSource={units}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: 'Unit', dataIndex: 'unit_number', width: 100 },
            { title: 'Type', dataIndex: 'unit_type', width: 130 },
            { title: 'Floor', dataIndex: 'floor', width: 90 },
            { title: 'Size (m²)', dataIndex: 'size_sqm', width: 110 },
            { title: 'Monthly rent', dataIndex: 'monthly_rent', width: 120 },
            {
              title: 'Status',
              dataIndex: 'rental_status',
              render: (s) => <Tag color={s === 'occupied' ? 'orange' : 'green'}>{s}</Tag>,
            },
            {
              title: 'Active tenant',
              key: 'tenant',
              render: (_, row) => row.active_tenant?.name || '—',
            },
            ...(canManageUnits
              ? [
                  {
                    title: 'Actions',
                    key: 'actions',
                    width: 120,
                    render: (_, row) => (
                      <Button size="small" onClick={() => openEditUnit(row)}>
                        Edit
                      </Button>
                    ),
                  },
                ]
              : []),
          ]}
        />
      </Card>

      <Card title={`Contracts (${contracts.length})`}>
        <Table
          rowKey="id"
          loading={contractsLoading}
          dataSource={contracts}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 70 },
            { title: 'Unit', dataIndex: 'unit_number', width: 90 },
            { title: 'Tenant', dataIndex: 'tenant_name', width: 220 },
            { title: 'Monthly rent', dataIndex: 'monthly_rent', width: 120 },
            { title: 'Start', dataIndex: 'start_date', width: 120 },
            { title: 'End', dataIndex: 'end_date', width: 120 },
            {
              title: 'Status',
              dataIndex: 'status',
              render: (s) => <Tag color={s === 'active' ? 'green' : 'default'}>{s}</Tag>,
            },
          ]}
        />
      </Card>

      <Card title={`Debts (${debts.length})`}>
        <Table
          rowKey="id"
          loading={debtsLoading}
          dataSource={debts}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: 'Type', dataIndex: 'debt_type', width: 150 },
            { title: 'Creditor', dataIndex: 'creditor_name' },
            { title: 'Total amount', dataIndex: 'total_amount', width: 140 },
            { title: 'Remaining', dataIndex: 'remaining_balance', width: 140 },
            { title: 'Start', dataIndex: 'start_date', width: 120 },
            { title: 'End', dataIndex: 'end_date', width: 120 },
          ]}
        />
      </Card>

      <Card title={`Transactions (${transactions.length})`}>
        <Typography.Paragraph type="secondary">
          Income: {totals.txIncome.toFixed(2)} SAR · Expense: {totals.txExpense.toFixed(2)} SAR
        </Typography.Paragraph>
        <Table
          rowKey="id"
          loading={txLoading}
          dataSource={transactions}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: 'Date', dataIndex: 'date', width: 120 },
            {
              title: 'Type',
              dataIndex: 'transaction_type',
              width: 110,
              render: (t) => <Tag color={t === 'income' ? 'green' : 'orange'}>{t}</Tag>,
            },
            { title: 'Category', dataIndex: 'category', width: 150 },
            { title: 'Amount', dataIndex: 'amount', width: 120 },
            { title: 'Description', dataIndex: 'description' },
            { title: 'Reference', dataIndex: 'reference', width: 150 },
          ]}
        />
      </Card>

      <Modal
        title={unitModal.unit?.id ? `Edit unit ${unitModal.unit.unit_number}` : 'Add unit'}
        open={unitModal.open}
        onCancel={closeUnitModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={unitForm}
          layout="vertical"
          onFinish={(values) => upsertUnit.mutate(values)}
        >
          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="unit_number"
                label="Unit number"
                rules={[{ required: true, message: 'Required' }]}
              >
                <Input placeholder="e.g. 101, A-02, G01" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item name="floor" label="Floor" rules={[{ required: true, message: 'Required' }]}>
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="unit_type"
                label="Unit type"
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select options={UNIT_TYPES} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="rental_status"
                label="Rental status"
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select options={RENTAL_STATUSES} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="size_sqm"
                label="Size (m²)"
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={0} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="monthly_rent"
                label="Monthly rent (SAR)"
                rules={[{ required: true, message: 'Required' }]}
              >
                <InputNumber min={0} step={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Notes (optional)">
            <Input.TextArea rows={3} />
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit" loading={upsertUnit.isPending}>
              Save
            </Button>
            <Button onClick={closeUnitModal}>Cancel</Button>
          </Space>
        </Form>
      </Modal>
    </Space>
  )
}
