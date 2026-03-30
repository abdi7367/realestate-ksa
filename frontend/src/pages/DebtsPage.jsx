import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  DatePicker,
} from 'antd'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const DEBT_TYPES = [
  { value: 'bank_loan', label: 'Bank loan' },
  { value: 'construction', label: 'Construction loan' },
  { value: 'maintenance', label: 'Maintenance debt' },
  { value: 'contractor', label: 'Contractor payment' },
  { value: 'supplier', label: 'Supplier payment' },
  { value: 'other', label: 'Other' },
]

const INSTALLMENT_STATUS = [
  { value: 'pending', label: 'Pending' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
]

function DebtInstallmentsPanel({ debtId, canWrite }) {
  const queryClient = useQueryClient()
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  const { data, isLoading } = useQuery({
    queryKey: ['installments', debtId],
    queryFn: () =>
      api
        .get('/api/installments/', { params: { debt: debtId, page_size: 200 } })
        .then((r) => r.data),
    enabled: Boolean(debtId),
  })

  const createInst = useMutation({
    mutationFn: (body) => api.post('/api/installments/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['installments', debtId] })
      queryClient.invalidateQueries({ queryKey: ['debts'] })
      setModalOpen(false)
      form.resetFields()
    },
  })

  const rows = useMemo(() => {
    const raw = data?.results ?? data ?? []
    return Array.isArray(raw) ? raw : []
  }, [data])

  return (
    <div style={{ padding: '8px 0 0 24px', background: '#fafafa' }}>
      <Space style={{ marginBottom: 8 }}>
        {canWrite && (
          <Button size="small" type="primary" onClick={() => setModalOpen(true)}>
            Add installment
          </Button>
        )}
      </Space>
      <Table
        size="small"
        loading={isLoading}
        rowKey="id"
        pagination={false}
        dataSource={rows}
        columns={[
          { title: 'Due', dataIndex: 'due_date', key: 'due' },
          { title: 'Amount', dataIndex: 'amount', key: 'amt', render: (v) => String(v) },
          {
            title: 'Status',
            dataIndex: 'status',
            key: 'st',
            render: (s) => <Tag>{s}</Tag>,
          },
          { title: 'Paid on', dataIndex: 'paid_date', key: 'pd' },
        ]}
      />
      <Modal
        title="New installment"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(v) =>
            createInst.mutate({
              debt: debtId,
              amount: v.amount,
              due_date: v.due_date.format('YYYY-MM-DD'),
              status: v.status || 'pending',
              notes: v.notes || '',
            })
          }
        >
          <Form.Item
            name="amount"
            label="Amount (SAR)"
            rules={[{ required: true, message: 'Required' }]}
          >
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="due_date"
            label="Due date"
            rules={[{ required: true, message: 'Required' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="status" label="Status" initialValue="pending">
            <Select options={INSTALLMENT_STATUS} />
          </Form.Item>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createInst.isPending}>
            Save
          </Button>
        </Form>
      </Modal>
    </div>
  )
}

export function DebtsPage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [propertyId, setPropertyId] = useState(undefined)
  const [debtType, setDebtType] = useState(undefined)
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const canWrite = ['admin', 'property_manager', 'accountant'].includes(user?.role)

  const { data: propsData } = useQuery({
    queryKey: ['properties', 'all-picker'],
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
    if (debtType) p.debt_type = debtType
    return p
  }, [page, propertyId, debtType])

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['debts', listParams],
    queryFn: () => api.get('/api/debts/', { params: listParams }).then((r) => r.data),
  })

  const rows = useMemo(() => {
    const raw = data?.results ?? data ?? []
    return Array.isArray(raw) ? raw : []
  }, [data])

  const createDebt = useMutation({
    mutationFn: (body) => api.post('/api/debts/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['debts'] })
      setCreateOpen(false)
      form.resetFields()
    },
  })

  const onCreate = (v) => {
    createDebt.mutate({
      property: v.property,
      debt_type: v.debt_type,
      creditor_name: v.creditor_name,
      total_amount: String(v.total_amount),
      interest_rate: String(v.interest_rate ?? 0),
      start_date: v.start_date.format('YYYY-MM-DD'),
      end_date: v.end_date ? v.end_date.format('YYYY-MM-DD') : null,
      notes: v.notes || '',
    })
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        Debts
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
        Property-linked loans and payables. Installments can be tracked under each debt.
      </Typography.Paragraph>

      <Card size="small">
        <Space wrap align="center">
          <Select
            allowClear
            placeholder="Property"
            style={{ minWidth: 200 }}
            options={propertyOptions}
            value={propertyId}
            onChange={(v) => {
              setPropertyId(v)
              setPage(1)
            }}
          />
          <Select
            allowClear
            placeholder="Debt type"
            style={{ minWidth: 180 }}
            options={DEBT_TYPES}
            value={debtType}
            onChange={(v) => {
              setDebtType(v)
              setPage(1)
            }}
          />
          {canWrite && (
            <Button type="primary" onClick={() => setCreateOpen(true)}>
              Add debt
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
        expandable={{
          expandedRowRender: (record) => (
            <DebtInstallmentsPanel debtId={record.id} canWrite={canWrite} />
          ),
        }}
        pagination={{
          current: page,
          pageSize: 20,
          total: data?.count,
          showSizeChanger: false,
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
            dataIndex: 'debt_type',
            render: (t) => t?.replace(/_/g, ' ') ?? '—',
          },
          { title: 'Creditor', dataIndex: 'creditor_name', ellipsis: true },
          {
            title: 'Total',
            dataIndex: 'total_amount',
            render: (v) => String(v ?? '—'),
          },
          {
            title: 'Paid',
            dataIndex: 'paid_amount',
            key: 'paid',
            render: (_, row) => String(row.paid_amount ?? '0'),
          },
          {
            title: 'Remaining',
            dataIndex: 'remaining_balance',
            key: 'rem',
            render: (_, row) => String(row.remaining_balance ?? '—'),
          },
          { title: 'Start', dataIndex: 'start_date' },
        ]}
      />

      <Modal
        title="New debt"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item
            name="property"
            label="Property"
            rules={[{ required: true, message: 'Select property' }]}
          >
            <Select options={propertyOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            name="debt_type"
            label="Debt type"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Select options={DEBT_TYPES} />
          </Form.Item>
          <Form.Item
            name="creditor_name"
            label="Creditor name"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="total_amount"
            label="Total amount (SAR)"
            rules={[{ required: true, message: 'Required' }]}
          >
            <InputNumber min={0} step={1000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="interest_rate" label="Interest rate (%)" initialValue={0}>
            <InputNumber min={0} max={100} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="start_date"
            label="Start date"
            rules={[{ required: true, message: 'Required' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="end_date" label="End date (optional)">
            <DatePicker style={{ width: '100%' }} allowClear />
          </Form.Item>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createDebt.isPending}>
            Create
          </Button>
        </Form>
      </Modal>
    </Space>
  )
}
