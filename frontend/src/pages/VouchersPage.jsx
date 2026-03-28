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
import dayjs from 'dayjs'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const PAYMENT_METHODS = [
  { value: 'cash', label: 'Cash' },
  { value: 'bank_transfer', label: 'Bank transfer' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'online', label: 'Online' },
]

const STATUS_COLORS = {
  draft: 'default',
  pending_accountant: 'blue',
  pending_finance: 'gold',
  pending_admin: 'purple',
  approved: 'green',
  rejected: 'red',
}

export function VouchersPage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [propertyId, setPropertyId] = useState(undefined)
  const [status, setStatus] = useState(undefined)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [form] = Form.useForm()

  const role = user?.role
  const canCreate = ['admin', 'accountant'].includes(role)
  const canAdvance =
    role === 'admin' ||
    ['accountant', 'finance_manager'].includes(role)

  const { data: propsData } = useQuery({
    queryKey: ['properties', 'voucher-picker'],
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
    if (status) p.approval_status = status
    if (search.trim()) p.search = search.trim()
    return p
  }, [page, propertyId, status, search])

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['vouchers', listParams],
    queryFn: () => api.get('/api/vouchers/', { params: listParams }).then((r) => r.data),
  })

  const rows = useMemo(() => {
    const raw = data?.results ?? data ?? []
    return Array.isArray(raw) ? raw : []
  }, [data])

  const createVoucher = useMutation({
    mutationFn: (body) => api.post('/api/vouchers/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] })
      setCreateOpen(false)
      form.resetFields()
    },
  })

  const approveMut = useMutation({
    mutationFn: (id) => api.post(`/api/vouchers/${id}/approve/`, {}),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['vouchers'] }),
  })

  const rejectMut = useMutation({
    mutationFn: ({ id, reason }) =>
      api.post(`/api/vouchers/${id}/reject/`, { reason }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['vouchers'] }),
  })

  const onCreate = (v) => {
    createVoucher.mutate({
      voucher_number: v.voucher_number.trim(),
      date: v.date.format('YYYY-MM-DD'),
      amount: String(v.amount),
      payee_name: v.payee_name.trim(),
      payment_method: v.payment_method,
      description: v.description || '',
      property: v.property,
      approval_status: 'draft',
    })
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        Vouchers
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
        Payment vouchers: draft → accountant → finance manager → admin approval.
        Use <strong>Advance</strong> to move one step (role must match the current stage,
        unless you are admin).
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
            placeholder="Status"
            style={{ minWidth: 200 }}
            options={[
              { value: 'draft', label: 'Draft' },
              { value: 'pending_accountant', label: 'Pending accountant' },
              { value: 'pending_finance', label: 'Pending finance' },
              { value: 'pending_admin', label: 'Pending admin' },
              { value: 'approved', label: 'Approved' },
              { value: 'rejected', label: 'Rejected' },
            ]}
            value={status}
            onChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
          />
          <Input.Search
            allowClear
            placeholder="Search number, payee, description"
            style={{ width: 280 }}
            onSearch={(v) => {
              setSearch(v)
              setPage(1)
            }}
          />
          {canCreate && (
            <Button type="primary" onClick={() => setCreateOpen(true)}>
              New voucher
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
          { title: 'No.', dataIndex: 'voucher_number', width: 130 },
          {
            title: 'Property',
            key: 'prop',
            render: (_, row) => propertyNameById.get(row.property) ?? row.property,
          },
          { title: 'Date', dataIndex: 'date' },
          {
            title: 'Amount',
            dataIndex: 'amount',
            render: (v) => String(v ?? '—'),
          },
          { title: 'Payee', dataIndex: 'payee_name', ellipsis: true },
          { title: 'Method', dataIndex: 'payment_method' },
          {
            title: 'Status',
            dataIndex: 'approval_status',
            render: (s) => (
              <Tag color={STATUS_COLORS[s] || 'default'}>{s?.replace(/_/g, ' ')}</Tag>
            ),
          },
          {
            title: 'Actions',
            key: 'act',
            width: 200,
            render: (_, row) => (
              <Space size="small" wrap>
                {canAdvance &&
                  row.approval_status !== 'approved' &&
                  row.approval_status !== 'rejected' && (
                    <Button
                      size="small"
                      type="primary"
                      loading={approveMut.isPending}
                      onClick={() => approveMut.mutate(row.id)}
                    >
                      Advance
                    </Button>
                  )}
                {canAdvance &&
                  row.approval_status !== 'approved' &&
                  row.approval_status !== 'rejected' && (
                    <Button
                      size="small"
                      danger
                      loading={rejectMut.isPending}
                      onClick={() => {
                        const reason = window.prompt('Rejection reason (optional)') || ''
                        rejectMut.mutate({ id: row.id, reason })
                      }}
                    >
                      Reject
                    </Button>
                  )}
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title="New voucher"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item
            name="voucher_number"
            label="Voucher number (unique)"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Input placeholder="e.g. V-2026-0001" />
          </Form.Item>
          <Form.Item
            name="property"
            label="Property"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Select options={propertyOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            name="date"
            label="Date"
            rules={[{ required: true, message: 'Required' }]}
            initialValue={dayjs()}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="amount"
            label="Amount (SAR)"
            rules={[{ required: true, message: 'Required' }]}
          >
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="payee_name"
            label="Payee"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="payment_method"
            label="Payment method"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Select options={PAYMENT_METHODS} />
          </Form.Item>
          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Required' }]}
          >
            <Input.TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createVoucher.isPending}>
            Create draft
          </Button>
        </Form>
      </Modal>
    </Space>
  )
}
