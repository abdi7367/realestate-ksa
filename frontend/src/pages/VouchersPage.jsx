import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
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

const STATUS_COLORS = {
  draft: 'default',
  pending_accountant: 'blue',
  pending_finance: 'gold',
  pending_admin: 'purple',
  approved: 'green',
  rejected: 'red',
}

export function VouchersPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [propertyId, setPropertyId] = useState(undefined)
  const [status, setStatus] = useState(undefined)
  const [search, setSearch] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [rejectState, setRejectState] = useState({ open: false, voucherId: null, reason: '' })
  const [form] = Form.useForm()

  const paymentMethodOptions = useMemo(
    () => [
      { value: 'cash', label: t('vouchers.methods.cash') },
      { value: 'bank_transfer', label: t('vouchers.methods.bank_transfer') },
      { value: 'cheque', label: t('vouchers.methods.cheque') },
      { value: 'online', label: t('vouchers.methods.online') },
    ],
    [t],
  )

  const voucherStatusFilterOptions = useMemo(
    () => [
      { value: 'draft', label: t('vouchers.statuses.draft') },
      { value: 'pending_accountant', label: t('vouchers.statuses.pending_accountant') },
      { value: 'pending_finance', label: t('vouchers.statuses.pending_finance') },
      { value: 'pending_admin', label: t('vouchers.statuses.pending_admin') },
      { value: 'approved', label: t('vouchers.statuses.approved') },
      { value: 'rejected', label: t('vouchers.statuses.rejected') },
    ],
    [t],
  )

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

  const openRejectModal = (voucherId) => {
    setRejectState({ open: true, voucherId, reason: '' })
  }

  const closeRejectModal = () => {
    setRejectState({ open: false, voucherId: null, reason: '' })
  }

  const submitReject = () => {
    if (!rejectState.voucherId) return
    rejectMut.mutate(
      { id: rejectState.voucherId, reason: rejectState.reason.trim() },
      { onSuccess: closeRejectModal },
    )
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Typography.Title level={4} style={{ margin: 0 }}>
        {t('vouchers.title')}
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
        {t('vouchers.subtitle')}
      </Typography.Paragraph>

      <Card size="small">
        <Space wrap align="center">
          <Select
            allowClear
            placeholder={t('common.property')}
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
            placeholder={t('common.status')}
            style={{ minWidth: 200 }}
            options={voucherStatusFilterOptions}
            value={status}
            onChange={(v) => {
              setStatus(v)
              setPage(1)
            }}
          />
          <Input.Search
            allowClear
            placeholder={t('common.search')}
            style={{ width: 280 }}
            onSearch={(v) => {
              setSearch(v)
              setPage(1)
            }}
          />
          {canCreate && (
            <Button type="primary" onClick={() => setCreateOpen(true)}>
              {t('vouchers.newVoucher')}
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
          { title: t('vouchers.number'), dataIndex: 'voucher_number', width: 130 },
          {
            title: t('common.property'),
            key: 'prop',
            render: (_, row) => propertyNameById.get(row.property) ?? row.property,
          },
          { title: t('common.date'), dataIndex: 'date' },
          {
            title: t('common.amount'),
            dataIndex: 'amount',
            render: (v) => String(v ?? '—'),
          },
          { title: t('vouchers.payee'), dataIndex: 'payee_name', ellipsis: true },
          { title: t('contracts.method'), dataIndex: 'payment_method' },
          {
            title: t('common.status'),
            dataIndex: 'approval_status',
            render: (s) => (
              <Tag color={STATUS_COLORS[s] || 'default'}>{s?.replace(/_/g, ' ')}</Tag>
            ),
          },
          {
            title: t('common.actions'),
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
                      {t('vouchers.advance')}
                    </Button>
                  )}
                {canAdvance &&
                  row.approval_status !== 'approved' &&
                  row.approval_status !== 'rejected' && (
                    <Button
                      size="small"
                      danger
                      loading={rejectMut.isPending}
                      onClick={() => openRejectModal(row.id)}
                    >
                      {t('vouchers.reject')}
                    </Button>
                  )}
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={t('vouchers.rejectModal.title')}
        open={rejectState.open}
        onCancel={closeRejectModal}
        onOk={submitReject}
        okText={t('vouchers.rejectModal.okText')}
        okButtonProps={{ danger: true, loading: rejectMut.isPending }}
      >
        <Form layout="vertical">
          <Form.Item label={t('vouchers.rejectModal.reason')}>
            <Input.TextArea
              rows={4}
              value={rejectState.reason}
              onChange={(e) =>
                setRejectState((prev) => ({ ...prev, reason: e.target.value }))
              }
              placeholder={t('vouchers.rejectModal.placeholder')}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={t('vouchers.createModal.title')}
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item
            name="voucher_number"
            label={t('vouchers.createModal.voucherNumber')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input placeholder={t('vouchers.createModal.voucherNumberPlaceholder')} />
          </Form.Item>
          <Form.Item
            name="property"
            label={t('common.property')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select options={propertyOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            name="date"
            label={t('vouchers.createModal.date')}
            rules={[{ required: true, message: t('common.required') }]}
            initialValue={dayjs()}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="amount"
            label={t('vouchers.createModal.amount')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="payee_name"
            label={t('vouchers.createModal.payee')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="payment_method"
            label={t('vouchers.createModal.paymentMethod')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select options={paymentMethodOptions} />
          </Form.Item>
          <Form.Item
            name="description"
            label={t('vouchers.createModal.description')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input.TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createVoucher.isPending}>
            {t('vouchers.createModal.createDraft')}
          </Button>
        </Form>
      </Modal>
    </Space>
  )
}
