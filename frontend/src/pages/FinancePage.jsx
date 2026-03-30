import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  DatePicker,
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
} from 'antd'
import dayjs from 'dayjs'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const TX_TYPES = [
  { value: 'income', label: 'Income' },
  { value: 'expense', label: 'Expense' },
]

const INCOME_CATS = [
  { value: 'rental', label: 'Rental income' },
  { value: 'parking', label: 'Parking' },
  { value: 'service_charge', label: 'Service charge' },
  { value: 'utility_recovery', label: 'Utility recovery' },
  { value: 'other', label: 'Other income' },
]

const EXPENSE_CATS = [
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'security', label: 'Security' },
  { value: 'cleaning', label: 'Cleaning' },
  { value: 'government_fees', label: 'Government fees' },
  { value: 'management', label: 'Management' },
  { value: 'other', label: 'Other expense' },
]

export function FinancePage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [propertyId, setPropertyId] = useState(undefined)
  const [txType, setTxType] = useState(undefined)
  const [category, setCategory] = useState(undefined)
  const [dateRange, setDateRange] = useState(null)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const canWrite = ['admin', 'property_manager', 'accountant'].includes(user?.role)

  const { data: propsData } = useQuery({
    queryKey: ['properties', 'finance-picker'],
    queryFn: () =>
      api.get('/api/properties/', { params: { page_size: 500 } }).then((r) => r.data),
  })

  const propertyOptions = useMemo(() => {
    const raw = propsData?.results ?? propsData ?? []
    const list = Array.isArray(raw) ? raw : []
    return list.map((p) => ({ value: p.id, label: p.name ?? `Property #${p.id}` }))
  }, [propsData])

  const propertyNameById = useMemo(() => {
    const m = new Map()
    const raw = propsData?.results ?? propsData ?? []
    const list = Array.isArray(raw) ? raw : []
    list.forEach((p) => m.set(p.id, p.name ?? `#${p.id}`))
    return m
  }, [propsData])

  const listParams = useMemo(() => {
    const p = { page }
    if (propertyId) p.property = propertyId
    if (txType) p.transaction_type = txType
    if (category) p.category = category
    if (dateRange?.[0]) p.date_from = dateRange[0].format('YYYY-MM-DD')
    if (dateRange?.[1]) p.date_to = dateRange[1].format('YYYY-MM-DD')
    if (search.trim()) p.search = search.trim()
    return p
  }, [page, propertyId, txType, category, dateRange, search])

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['transactions', listParams],
    queryFn: () => api.get('/api/transactions/', { params: listParams }).then((r) => r.data),
  })

  const { data: summaryData } = useQuery({
    queryKey: ['transactions', 'summary', propertyId, dateRange?.[0]?.format('YYYY-MM-DD'), dateRange?.[1]?.format('YYYY-MM-DD')],
    queryFn: () =>
      api
        .get('/api/transactions/summary/', {
          params: {
            ...(propertyId ? { property_id: propertyId } : {}),
            ...(dateRange?.[0] ? { date_from: dateRange[0].format('YYYY-MM-DD') } : {}),
            ...(dateRange?.[1] ? { date_to: dateRange[1].format('YYYY-MM-DD') } : {}),
          },
        })
        .then((r) => r.data),
  })

  const rows = useMemo(() => {
    const raw = data?.results ?? data ?? []
    return Array.isArray(raw) ? raw : []
  }, [data])

  const createTx = useMutation({
    mutationFn: (body) => api.post('/api/transactions/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setCreateOpen(false)
      form.resetFields()
    },
  })

  const onCreate = (v) => {
    createTx.mutate({
      property: v.property,
      transaction_type: v.transaction_type,
      category: v.category,
      amount: String(v.amount),
      date: v.date.format('YYYY-MM-DD'),
      description: v.description || '',
      reference: v.reference || '',
    })
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        Finance
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
        Income and expense transactions by property. Categories must match the
        transaction type (validated by the API).
      </Typography.Paragraph>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card size="small" title="Income (filtered)">
            <Typography.Text strong>
              {summaryData?.income != null ? String(summaryData.income) : '—'} SAR
            </Typography.Text>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title="Expense (filtered)">
            <Typography.Text strong>
              {summaryData?.expense != null ? String(summaryData.expense) : '—'} SAR
            </Typography.Text>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title="Net (income − expense)">
            <Typography.Text strong>
              {summaryData?.profit != null ? String(summaryData.profit) : '—'} SAR
            </Typography.Text>
          </Card>
        </Col>
      </Row>

      <Card size="small">
        <Space wrap align="center">
          <Select
            allowClear
            placeholder="Property (filters list + summary)"
            style={{ minWidth: 220 }}
            options={propertyOptions}
            value={propertyId}
            onChange={(v) => {
              setPropertyId(v)
              setPage(1)
            }}
          />
          <Select
            allowClear
            placeholder="Type"
            style={{ width: 120 }}
            options={TX_TYPES}
            value={txType}
            onChange={(v) => {
              setTxType(v)
              setPage(1)
            }}
          />
          <Select
            allowClear
            placeholder="Category"
            style={{ minWidth: 160 }}
            options={[...INCOME_CATS, ...EXPENSE_CATS]}
            value={category}
            onChange={(v) => {
              setCategory(v)
              setPage(1)
            }}
          />
          <Input.Search
            allowClear
            placeholder="Search description / reference"
            style={{ width: 240 }}
            onSearch={(v) => {
              setSearch(v)
              setPage(1)
            }}
          />
          <DatePicker.RangePicker
            value={dateRange}
            onChange={(v) => {
              setDateRange(v)
              setPage(1)
            }}
            allowClear
          />
          {canWrite && (
            <Button type="primary" onClick={() => setCreateOpen(true)}>
              Add transaction
            </Button>
          )}
        </Space>
      </Card>

      {isError && (
        <Typography.Text type="danger">{String(error?.message || error)}</Typography.Text>
      )}

      <Table
        loading={isLoading}
        rowKey="id"
        dataSource={rows}
        scroll={{ x: true }}
        pagination={{
          current: page,
          pageSize: 20,
          total: data?.count,
          onChange: (p) => setPage(p),
        }}
        columns={[
          { title: 'ID', dataIndex: 'id', width: 70 },
          {
            title: 'Property',
            key: 'prop',
            render: (_, row) => propertyNameById.get(row.property) ?? row.property,
          },
          {
            title: 'Type',
            dataIndex: 'transaction_type',
            render: (t) => <Tag color={t === 'income' ? 'green' : 'orange'}>{t}</Tag>,
          },
          { title: 'Category', dataIndex: 'category' },
          {
            title: 'Amount',
            dataIndex: 'amount',
            render: (v) => String(v ?? '—'),
          },
          { title: 'Date', dataIndex: 'date' },
          { title: 'Description', dataIndex: 'description', ellipsis: true },
          { title: 'Reference', dataIndex: 'reference', ellipsis: true },
        ]}
      />

      <Modal
        title="New transaction"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ transaction_type: 'income' }}
          onFinish={onCreate}
        >
          <Form.Item
            name="property"
            label="Property"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Select options={propertyOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            name="transaction_type"
            label="Type"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Select
              options={TX_TYPES}
              onChange={() => form.setFieldsValue({ category: undefined })}
            />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, cur) => prev.transaction_type !== cur.transaction_type}
          >
            {() => (
              <Form.Item
                name="category"
                label="Category"
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select
                  options={
                    form.getFieldValue('transaction_type') === 'expense'
                      ? EXPENSE_CATS
                      : INCOME_CATS
                  }
                />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item
            name="amount"
            label="Amount (SAR)"
            rules={[{ required: true, message: 'Required' }]}
          >
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="date"
            label="Date"
            rules={[{ required: true, message: 'Required' }]}
            initialValue={dayjs()}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="reference" label="Reference">
            <Input />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createTx.isPending}>
            Save
          </Button>
        </Form>
      </Modal>
    </Space>
  )
}
