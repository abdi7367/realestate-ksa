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
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const INSTALLMENT_STATUS = [
  { value: 'pending', label: 'Pending' },
  { value: 'paid', label: 'Paid' },
  { value: 'overdue', label: 'Overdue' },
]

function DebtInstallmentsPanel({ debtId, canWrite }) {
  const { t } = useTranslation()
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
            {t('debts.addInstallment')}
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
          { title: t('debts.dueDate'), dataIndex: 'due_date', key: 'due' },
          {
            title: t('common.amount'),
            dataIndex: 'amount',
            key: 'amt',
            render: (v) => String(v),
          },
          {
            title: t('common.status'),
            dataIndex: 'status',
            key: 'st',
            render: (s) => <Tag>{s}</Tag>,
          },
          { title: t('debts.paidOn'), dataIndex: 'paid_date', key: 'pd' },
        ]}
      />
      <Modal
        title={t('debts.newInstallment')}
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
            label={t('common.amountSAR')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="due_date"
            label={t('debts.dueDate')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="status" label={t('common.status')} initialValue="pending">
            <Select options={INSTALLMENT_STATUS} />
          </Form.Item>
          <Form.Item name="notes" label={t('common.notes')}>
            <Input.TextArea rows={2} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createInst.isPending}>
            {t('common.save')}
          </Button>
        </Form>
      </Modal>
    </div>
  )
}

export function DebtsPage() {
  const { t } = useTranslation()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const debtTypeOptions = useMemo(
    () => [
      { value: 'bank_loan', label: t('debts.debtTypes.bank_loan') },
      { value: 'construction', label: t('debts.debtTypes.construction') },
      { value: 'maintenance', label: t('debts.debtTypes.maintenance') },
      { value: 'contractor', label: t('debts.debtTypes.contractor') },
      { value: 'supplier', label: t('debts.debtTypes.supplier') },
      { value: 'other', label: t('debts.debtTypes.other') },
    ],
    [t],
  )
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
        {t('debts.title')}
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
        {t('debts.subtitle')}
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
            placeholder={t('debts.debtType')}
            style={{ minWidth: 180 }}
            options={debtTypeOptions}
            value={debtType}
            onChange={(v) => {
              setDebtType(v)
              setPage(1)
            }}
          />
          {canWrite && (
            <Button type="primary" onClick={() => setCreateOpen(true)}>
              {t('debts.addDebt')}
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
          { title: t('common.id'), dataIndex: 'id', width: 70 },
          {
            title: t('common.property'),
            key: 'prop',
            render: (_, row) => propertyNameById.get(row.property) ?? row.property,
          },
          {
            title: t('common.type'),
            dataIndex: 'debt_type',
            render: (typeVal) => typeVal?.replace(/_/g, ' ') ?? '—',
          },
          { title: t('debts.creditor'), dataIndex: 'creditor_name', ellipsis: true },
          {
            title: t('debts.total'),
            dataIndex: 'total_amount',
            render: (v) => String(v ?? '—'),
          },
          {
            title: t('debts.paid'),
            dataIndex: 'paid_amount',
            key: 'paid',
            render: (_, row) => String(row.paid_amount ?? '0'),
          },
          {
            title: t('debts.remaining'),
            dataIndex: 'remaining_balance',
            key: 'rem',
            render: (_, row) => String(row.remaining_balance ?? '—'),
          },
          { title: t('common.start'), dataIndex: 'start_date' },
        ]}
      />

      <Modal
        title={t('debts.newDebt')}
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={null}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={onCreate}>
          <Form.Item
            name="property"
            label={t('common.property')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select options={propertyOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            name="debt_type"
            label={t('debts.debtType')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select options={debtTypeOptions} />
          </Form.Item>
          <Form.Item
            name="creditor_name"
            label={t('debts.creditorName')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="total_amount"
            label={t('debts.totalAmount')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber min={0} step={1000} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="interest_rate" label={t('debts.interestRate')} initialValue={0}>
            <InputNumber min={0} max={100} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="start_date"
            label={t('debts.startDate')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="end_date" label={t('debts.endDate')}>
            <DatePicker style={{ width: '100%' }} allowClear />
          </Form.Item>
          <Form.Item name="notes" label={t('common.notes')}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createDebt.isPending}>
            {t('common.create')}
          </Button>
        </Form>
      </Modal>
    </Space>
  )
}
