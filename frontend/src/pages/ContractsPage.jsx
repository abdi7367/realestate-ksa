import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Checkbox,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import dayjs from 'dayjs'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

const PAYMENT_SCHEDULES = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'semi_annual', label: 'Semi-annual' },
  { value: 'annual', label: 'Annual' },
  { value: 'lump_sum', label: 'Lump sum' },
]

const PAYMENT_METHODS = [
  { value: 'bank_transfer', label: 'Bank transfer' },
  { value: 'cash', label: 'Cash' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'online', label: 'Online' },
]

const CONTRACT_STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'expired', label: 'Expired' },
  { value: 'terminated', label: 'Terminated' },
]

export function ContractsPage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [contractDraft, setContractDraft] = useState({
    search: '',
    status: undefined,
    payment_schedule: undefined,
  })
  const [contractFilters, setContractFilters] = useState({
    search: '',
    status: undefined,
    payment_schedule: undefined,
  })

  const [payPage, setPayPage] = useState(1)
  const [payDraft, setPayDraft] = useState({
    contract_number: '',
    status: undefined,
    payment_method: undefined,
    search: '',
  })
  const [payFilters, setPayFilters] = useState({
    contract_number: '',
    status: undefined,
    payment_method: undefined,
    search: '',
  })
  const [createOpen, setCreateOpen] = useState(false)
  const [payModal, setPayModal] = useState({ open: false, contract: null })
  const [terminateTarget, setTerminateTarget] = useState(null)
  const [editLeaseTarget, setEditLeaseTarget] = useState(null)

  const [createForm] = Form.useForm()
  const [payForm] = Form.useForm()
  const [terminateForm] = Form.useForm()
  const [termsForm] = Form.useForm()

  const canCreateContract = ['admin', 'property_manager'].includes(user?.role)
  const canRecordPayment = ['admin', 'accountant', 'property_manager'].includes(
    user?.role,
  )
  const canTerminate = ['admin', 'property_manager'].includes(user?.role)
  const canEditLeaseTerms = canTerminate

  const contractListParams = useMemo(() => {
    const p = { page }
    const s = contractFilters.search.trim()
    if (s) p.search = s
    if (contractFilters.status) p.status = contractFilters.status
    if (contractFilters.payment_schedule) {
      p.payment_schedule = contractFilters.payment_schedule
    }
    return p
  }, [page, contractFilters])

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['contracts', contractListParams],
    queryFn: () =>
      api.get('/api/contracts/', { params: contractListParams }).then((r) => r.data),
  })

  const payListParams = useMemo(() => {
    const p = { page: payPage }
    const cn = payFilters.contract_number.trim()
    if (cn && /^\d+$/.test(cn)) p.contract_number = cn
    if (payFilters.status) p.status = payFilters.status
    if (payFilters.payment_method) p.payment_method = payFilters.payment_method
    const ps = payFilters.search.trim()
    if (ps) p.search = ps
    return p
  }, [payPage, payFilters])

  const {
    data: payData,
    isLoading: payLoading,
    isError: payListError,
    error: payListErr,
  } = useQuery({
    queryKey: ['payments', payListParams],
    queryFn: () =>
      api.get('/api/payments/', { params: payListParams }).then((r) => r.data),
  })

  const { data: unitsData } = useQuery({
    queryKey: ['units', 'vacant'],
    queryFn: () =>
      api
        .get('/api/units/', {
          params: { rental_status: 'vacant', page_size: 1000 },
        })
        .then((r) => r.data),
    enabled: createOpen && canCreateContract,
  })

  const unitOptions = useMemo(() => {
    const raw = unitsData?.results ?? unitsData ?? []
    const list = Array.isArray(raw) ? raw : []
    return list.map((u) => ({
      value: u.id,
      label: `${u.property_name ?? 'Property'} — ${u.unit_number} · ${u.property_city ?? ''}`,
    }))
  }, [unitsData])

  const rows = useMemo(() => {
    const res = data?.results ?? data ?? []
    return Array.isArray(res) ? res : []
  }, [data])

  const createMutation = useMutation({
    mutationFn: (body) => api.post('/api/contracts/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      queryClient.invalidateQueries({ queryKey: ['units'] })
      queryClient.invalidateQueries({ queryKey: ['properties'] })
      setCreateOpen(false)
      createForm.resetFields()
    },
  })

  const payMutation = useMutation({
    mutationFn: ({ contractId, body }) =>
      api.post('/api/payments/', { ...body, contract: contractId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      queryClient.invalidateQueries({ queryKey: ['payments'] })
      setPayModal({ open: false, contract: null })
      payForm.resetFields()
    },
  })

  const terminateMutation = useMutation({
    mutationFn: ({ id, reason }) =>
      api.post(`/api/contracts/${id}/terminate/`, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      queryClient.invalidateQueries({ queryKey: ['units'] })
      queryClient.invalidateQueries({ queryKey: ['properties'] })
      setTerminateTarget(null)
      terminateForm.resetFields()
    },
  })

  const leaseTermsMutation = useMutation({
    mutationFn: ({ id, body }) => api.patch(`/api/contracts/${id}/`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] })
      queryClient.invalidateQueries({ queryKey: ['payments'] })
      setEditLeaseTarget(null)
      termsForm.resetFields()
    },
  })

  const onCreateSubmit = (v) => {
    const dob = v.tenant_data?.date_of_birth
    createMutation.mutate({
      unit: v.unit,
      tenant_data: {
        full_name: v.tenant_data.full_name,
        national_id: v.tenant_data.national_id,
        phone: v.tenant_data.phone?.trim() || '',
        email: v.tenant_data.email?.trim() || '',
        nationality: v.tenant_data.nationality?.trim() || '',
        date_of_birth: dob ? dob.format('YYYY-MM-DD') : null,
      },
      monthly_rent: v.monthly_rent,
      start_date: v.start_date.format('YYYY-MM-DD'),
      duration_months: v.duration_months,
      security_deposit: v.security_deposit ?? 0,
      payment_schedule: v.payment_schedule ?? 'monthly',
    })
  }

  const onPaySubmit = (v) => {
    if (!payModal.contract?.id) return
    payMutation.mutate({
      contractId: payModal.contract.id,
      body: {
        amount: v.amount,
        payment_date: v.payment_date.format('YYYY-MM-DD'),
        payment_method: v.payment_method,
        due_date: v.due_date ? v.due_date.format('YYYY-MM-DD') : undefined,
        notes: v.notes || '',
      },
    })
  }

  const onLeaseTermsSubmit = (v) => {
    if (!editLeaseTarget) return
    leaseTermsMutation.mutate({
      id: editLeaseTarget.id,
      body: {
        duration_months: v.duration_months,
        monthly_rent: v.monthly_rent,
        start_date: v.start_date.format('YYYY-MM-DD'),
        security_deposit: v.security_deposit ?? 0,
        security_deposit_paid: Boolean(v.security_deposit_paid),
        security_deposit_received_on: v.security_deposit_received_on
          ? dayjs(v.security_deposit_received_on).format('YYYY-MM-DD')
          : null,
      },
    })
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
    {
      title: 'Property / unit',
      key: 'loc',
      render: (_, row) => (
        <span>
          {row.property_name ?? '—'} · {row.unit_number ?? '—'}
        </span>
      ),
    },
    {
      title: 'Tenant',
      key: 'tenant',
      ellipsis: true,
      render: (_, row) => row.tenant_name || '—',
    },
    {
      title: 'Tenant ID',
      key: 'tenant_ref',
      width: 100,
      render: (_, row) => row.tenant?.tenant_reference || '—',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (s) => <Tag color={s === 'active' ? 'green' : 'default'}>{s}</Tag>,
    },
    {
      title: 'Schedule',
      dataIndex: 'payment_schedule',
      key: 'payment_schedule',
      render: (s) => (s ? <Tag>{s.replace(/_/g, ' ')}</Tag> : '—'),
    },
    {
      title: 'Period',
      key: 'period',
      render: (_, row) => (
        <span style={{ whiteSpace: 'nowrap' }}>
          {row.start_date} → {row.end_date}
        </span>
      ),
    },
    {
      title: 'Rent / mo',
      dataIndex: 'monthly_rent',
      key: 'monthly_rent',
      render: (v) => String(v ?? '—'),
    },
    {
      title: 'Security Deposit',
      key: 'dep',
      render: (_, row) => {
        const amt = row.security_deposit
        if (amt === undefined || amt === null || String(amt) === '0') return '—'
        const paid = row.security_deposit_paid
        return (
          <span>
            {String(amt)} ·{' '}
            {paid ? (
              <Tag color="green">Paid</Tag>
            ) : (
              <Tag color="orange">Not paid</Tag>
            )}
            {row.security_deposit_received_on
              ? ` (${row.security_deposit_received_on})`
              : ''}
          </span>
        )
      },
    },
    {
      title: 'Remaining (incl. VAT)',
      dataIndex: 'remaining_balance',
      key: 'rem',
      render: (v) => String(v ?? '—'),
    },
    {
      title: 'Next instalment (hint)',
      key: 'inst',
      width: 130,
      ellipsis: true,
      render: (_, row) => {
        const ig = row.installment_guidance
        if (!ig || !Number(ig.suggested_next_amount)) return '—'
        return (
          <span
            title={`${ig.installments_remaining} of ${ig.installments_planned} left (${(ig.payment_schedule || '').replace(/_/g, ' ')})`}
          >
            {ig.suggested_next_amount}
          </span>
        )
      },
    },
    {
      title: '',
      key: 'actions',
      fixed: 'right',
      width: 280,
      render: (_, row) => (
        <Space size="small" wrap>
          {canEditLeaseTerms && row.status === 'active' && (
            <Button
              type="link"
              size="small"
              onClick={() => {
                setEditLeaseTarget(row)
                leaseTermsMutation.reset()
                termsForm.setFieldsValue({
                  duration_months: row.duration_months,
                  monthly_rent: row.monthly_rent,
                  start_date: row.start_date ? dayjs(row.start_date) : undefined,
                  security_deposit: row.security_deposit,
                  security_deposit_paid: row.security_deposit_paid,
                  security_deposit_received_on: row.security_deposit_received_on
                    ? dayjs(row.security_deposit_received_on)
                    : undefined,
                })
              }}
            >
              Edit lease
            </Button>
          )}
          {canRecordPayment && row.status === 'active' && (
            <Button
              type="link"
              size="small"
              onClick={() => {
                setPayModal({ open: true, contract: row })
                payForm.resetFields()
              }}
            >
              Payment
            </Button>
          )}
          {canTerminate && row.status === 'active' && (
            <Button
              type="link"
              size="small"
              danger
              onClick={() => setTerminateTarget(row)}
            >
              Terminate
            </Button>
          )}
        </Space>
      ),
    },
  ]

  const createError =
    createMutation.error?.response?.data?.error ||
    createMutation.error?.response?.data?.detail
  const payError =
    payMutation.error?.response?.data?.error ||
    payMutation.error?.response?.data?.detail
  const termError =
    terminateMutation.error?.response?.data?.error ||
    terminateMutation.error?.response?.data?.detail
  const leaseTermsErrorRaw = leaseTermsMutation.error?.response?.data
  const leaseTermsDetail = leaseTermsErrorRaw?.detail
  const leaseTermsError =
    (typeof leaseTermsErrorRaw === 'string' && leaseTermsErrorRaw) ||
    leaseTermsErrorRaw?.error ||
    (Array.isArray(leaseTermsDetail) ? leaseTermsDetail.join(' ') : leaseTermsDetail) ||
    (leaseTermsErrorRaw && typeof leaseTermsErrorRaw === 'object'
      ? JSON.stringify(leaseTermsErrorRaw)
      : null)

  return (
    <Card bordered={false}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          <Typography.Title level={4} style={{ margin: 0 }}>
            Contracts & payments
          </Typography.Title>
          {canCreateContract && (
            <Button type="primary" onClick={() => setCreateOpen(true)}>
              New contract
            </Button>
          )}
        </div>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          Active contracts show rent received against total with VAT. Record
          payments for collections; remaining balance updates automatically.
        </Typography.Paragraph>

        {isError && (
          <Typography.Text type="danger">
            {error?.message || 'Could not load contracts'}
          </Typography.Text>
        )}

        <Card size="small" title="Filter contracts" style={{ marginBottom: 8 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Space wrap style={{ width: '100%' }} align="start">
              <Input
                allowClear
                placeholder="Search (property, unit, tenant, or contract #)"
                value={contractDraft.search}
                style={{ minWidth: 260 }}
                onChange={(e) =>
                  setContractDraft((d) => ({ ...d, search: e.target.value }))
                }
              />
              <Select
                allowClear
                placeholder="Status"
                style={{ width: 140 }}
                options={CONTRACT_STATUS_OPTIONS}
                value={contractDraft.status}
                onChange={(v) =>
                  setContractDraft((d) => ({ ...d, status: v }))
                }
              />
              <Select
                allowClear
                placeholder="Payment schedule"
                style={{ width: 180 }}
                options={PAYMENT_SCHEDULES}
                value={contractDraft.payment_schedule}
                onChange={(v) =>
                  setContractDraft((d) => ({ ...d, payment_schedule: v }))
                }
              />
              <Button
                type="primary"
                onClick={() => {
                  setPage(1)
                  setContractFilters({ ...contractDraft })
                }}
              >
                Apply
              </Button>
              <Button
                onClick={() => {
                  const empty = {
                    search: '',
                    status: undefined,
                    payment_schedule: undefined,
                  }
                  setContractDraft(empty)
                  setContractFilters(empty)
                  setPage(1)
                }}
              >
                Clear
              </Button>
            </Space>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              Backend: <code>search</code>, <code>status</code>,{' '}
              <code>payment_schedule</code>. Numeric search also matches contract id.
            </Typography.Text>
          </Space>
        </Card>

        <Table
          rowKey="id"
          loading={isLoading}
          columns={columns}
          dataSource={rows}
          expandable={{
            expandedRowRender: (row) => {
              const payments = row.payments ?? []
              return (
                <div style={{ margin: 0 }}>
                  <Typography.Text strong style={{ display: 'block' }}>
                    Payments ({payments.length})
                  </Typography.Text>
                  <Table
                    size="small"
                    rowKey="id"
                    pagination={false}
                    dataSource={payments}
                    columns={[
                      {
                        title: 'Date',
                        dataIndex: 'payment_date',
                        key: 'pd',
                      },
                      {
                        title: 'Due',
                        dataIndex: 'due_date',
                        key: 'dd',
                        render: (v) => v || '—',
                      },
                      {
                        title: 'Amount',
                        dataIndex: 'amount',
                        key: 'a',
                        render: (v) => String(v),
                      },
                      {
                        title: 'Method',
                        dataIndex: 'payment_method',
                        key: 'm',
                      },
                      {
                        title: 'Late',
                        dataIndex: 'is_late',
                        key: 'il',
                        render: (v) => (v ? <Tag color="red">Yes</Tag> : 'No'),
                      },
                    ]}
                  />
                </div>
              )
            },
            rowExpandable: () => true,
          }}
          pagination={
            data?.count
              ? {
                  current: page,
                  pageSize: 20,
                  total: data.count,
                  showSizeChanger: false,
                  onChange: (p) => setPage(p),
                }
              : false
          }
          scroll={{ x: true }}
        />

        <Card size="small" title="Search all payments" style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Space wrap style={{ width: '100%' }} align="start">
              <Input
                allowClear
                placeholder="Contract # (id)"
                value={payDraft.contract_number}
                style={{ width: 140 }}
                onChange={(e) =>
                  setPayDraft((d) => ({ ...d, contract_number: e.target.value }))
                }
              />
              <Select
                allowClear
                placeholder="Payment status"
                style={{ width: 160 }}
                options={[
                  { value: 'confirmed', label: 'Confirmed' },
                  { value: 'cancelled', label: 'Cancelled' },
                ]}
                value={payDraft.status}
                onChange={(v) => setPayDraft((d) => ({ ...d, status: v }))}
              />
              <Select
                allowClear
                placeholder="Payment method"
                style={{ width: 170 }}
                options={PAYMENT_METHODS}
                value={payDraft.payment_method}
                onChange={(v) =>
                  setPayDraft((d) => ({ ...d, payment_method: v }))
                }
              />
              <Input
                allowClear
                placeholder="Search (notes, tenant, property… or contract #)"
                value={payDraft.search}
                style={{ minWidth: 280 }}
                onChange={(e) =>
                  setPayDraft((d) => ({ ...d, search: e.target.value }))
                }
              />
              <Button
                type="primary"
                onClick={() => {
                  setPayPage(1)
                  setPayFilters({ ...payDraft })
                }}
              >
                Apply
              </Button>
              <Button
                onClick={() => {
                  const empty = {
                    contract_number: '',
                    status: undefined,
                    payment_method: undefined,
                    search: '',
                  }
                  setPayDraft(empty)
                  setPayFilters(empty)
                  setPayPage(1)
                }}
              >
                Clear
              </Button>
            </Space>
            {payListError && (
              <Typography.Text type="danger">
                {payListErr?.message || 'Could not load payments'}
              </Typography.Text>
            )}
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              Params: <code>contract_number</code>, <code>status</code>,{' '}
              <code>payment_method</code>, <code>search</code> (digits-only also
              matches that contract).
            </Typography.Text>
            <Table
              rowKey="id"
              size="small"
              loading={payLoading}
              scroll={{ x: true }}
              dataSource={
                Array.isArray(payData?.results)
                  ? payData.results
                  : Array.isArray(payData)
                    ? payData
                    : []
              }
              pagination={
                payData?.count
                  ? {
                      current: payPage,
                      pageSize: 20,
                      total: payData.count,
                      showSizeChanger: false,
                      onChange: (p) => setPayPage(p),
                    }
                  : false
              }
              columns={[
                { title: 'Pay #', dataIndex: 'id', key: 'id', width: 70 },
                {
                  title: 'Contract',
                  dataIndex: 'contract',
                  key: 'contract',
                  width: 90,
                },
                {
                  title: 'Date',
                  dataIndex: 'payment_date',
                  key: 'payment_date',
                },
                {
                  title: 'Amount',
                  dataIndex: 'amount',
                  key: 'amount',
                  render: (v) => String(v),
                },
                {
                  title: 'Status',
                  dataIndex: 'status',
                  key: 'status',
                  render: (s) => <Tag>{String(s)}</Tag>,
                },
                {
                  title: 'Method',
                  dataIndex: 'payment_method',
                  key: 'payment_method',
                },
                {
                  title: 'Late',
                  dataIndex: 'is_late',
                  key: 'is_late',
                  render: (v) => (v ? <Tag color="red">Yes</Tag> : 'No'),
                },
              ]}
            />
          </Space>
        </Card>
      </Space>

      <Modal
        title="New contract"
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false)
          createMutation.reset()
        }}
        footer={null}
        destroyOnClose
      >
        {createError && (
          <Typography.Paragraph type="danger">{String(createError)}</Typography.Paragraph>
        )}
        <Form
          form={createForm}
          layout="vertical"
          onFinish={onCreateSubmit}
          initialValues={{
            payment_schedule: 'monthly',
            duration_months: 12,
            security_deposit: 0,
            start_date: dayjs(),
          }}
        >
          <Form.Item
            name="unit"
            label="Vacant unit"
            rules={[{ required: true, message: 'Select a unit' }]}
          >
            <Select
              options={unitOptions}
              showSearch
              optionFilterProp="label"
              placeholder="Choose unit"
            />
          </Form.Item>
          <Typography.Paragraph strong style={{ marginBottom: 8 }}>
            Tenant (office record — not a login)
          </Typography.Paragraph>
          <Form.Item
            name={['tenant_data', 'full_name']}
            label="Full name"
            rules={[{ required: true, message: 'Enter full name' }]}
          >
            <Input placeholder="As on ID / Iqama" />
          </Form.Item>
          <Form.Item
            name={['tenant_data', 'national_id']}
            label="National ID / Iqama number"
            rules={[{ required: true, message: 'Enter national ID or Iqama' }]}
          >
            <Input placeholder="National ID or Iqama" />
          </Form.Item>
          <Form.Item name={['tenant_data', 'phone']} label="Phone number">
            <Input placeholder="Mobile" />
          </Form.Item>
          <Form.Item name={['tenant_data', 'email']} label="Email">
            <Input type="email" placeholder="Optional" />
          </Form.Item>
          <Form.Item name={['tenant_data', 'nationality']} label="Nationality">
            <Input placeholder="Optional" />
          </Form.Item>
          <Form.Item name={['tenant_data', 'date_of_birth']} label="Date of birth">
            <DatePicker style={{ width: '100%' }} allowClear />
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ fontSize: 12 }}>
            A tenant ID (e.g. T-000042) is assigned automatically when the contract
            is created.
          </Typography.Paragraph>
          <Form.Item
            name="monthly_rent"
            label="Monthly rent (SAR, excl. VAT in calculation — VAT added on total)"
            rules={[{ required: true, message: 'Enter rent' }]}
          >
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="start_date"
            label="Start date"
            rules={[{ required: true, message: 'Pick start date' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ fontSize: 12 }}>
            <strong>Lease length:</strong> full contract in months (e.g.{' '}
            <strong>12</strong> for one year). Payment schedule (semi-annual,
            etc.) is only how often rent is collected — totals are always monthly
            rent × duration + 15% VAT.
          </Typography.Paragraph>
          <Form.Item
            name="duration_months"
            label="Duration (months)"
            rules={[{ required: true, message: 'Enter duration' }]}
          >
            <InputNumber min={1} max={600} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="security_deposit" label="Security deposit (SAR)">
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="payment_schedule" label="Payment schedule">
            <Select options={PAYMENT_SCHEDULES} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
                Create
              </Button>
              <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Edit lease · contract #${editLeaseTarget?.id ?? ''}`}
        open={Boolean(editLeaseTarget)}
        onCancel={() => {
          setEditLeaseTarget(null)
          leaseTermsMutation.reset()
        }}
        footer={null}
        destroyOnClose
      >
        {leaseTermsError && (
          <Typography.Paragraph type="danger">
            {String(leaseTermsError)}
          </Typography.Paragraph>
        )}
        <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
          Updating duration or rent recalculates total + VAT and end date. You cannot
          set a total below confirmed payments already recorded.
        </Typography.Paragraph>
        <Form
          form={termsForm}
          layout="vertical"
          onFinish={onLeaseTermsSubmit}
        >
          <Form.Item
            name="monthly_rent"
            label="Monthly rent (SAR)"
            rules={[{ required: true, message: 'Enter rent' }]}
          >
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="start_date"
            label="Start date"
            rules={[{ required: true, message: 'Pick start date' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="duration_months"
            label="Duration (months) — full lease"
            rules={[{ required: true, message: 'Enter duration' }]}
          >
            <InputNumber min={1} max={600} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="security_deposit" label="Security deposit (SAR)">
            <InputNumber min={0} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="security_deposit_paid" valuePropName="checked">
            <Checkbox>Security deposit received</Checkbox>
          </Form.Item>
          <Form.Item name="security_deposit_received_on" label="Deposit received on">
            <DatePicker style={{ width: '100%' }} allowClear />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={leaseTermsMutation.isPending}
              >
                Save and recalculate
              </Button>
              <Button onClick={() => setEditLeaseTarget(null)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Record payment · contract #${payModal.contract?.id ?? ''}`}
        open={payModal.open}
        onCancel={() => {
          setPayModal({ open: false, contract: null })
          payMutation.reset()
        }}
        footer={null}
        destroyOnClose
      >
        {payError && (
          <Typography.Paragraph type="danger">{String(payError)}</Typography.Paragraph>
        )}
        {(() => {
          const ig = payModal.contract?.installment_guidance
          if (!ig || !Number(ig.suggested_next_amount)) return null
          const sched = (ig.payment_schedule || '').replace(/_/g, ' ')
          return (
            <Card size="small" type="inner" style={{ marginBottom: 16 }}>
              <Typography.Paragraph style={{ marginBottom: 8 }}>
                <strong>Suggested next payment</strong> (incl. VAT — even split of
                remaining):{' '}
                <Typography.Text strong>{ig.suggested_next_amount}</Typography.Text>{' '}
                SAR
              </Typography.Paragraph>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
                Schedule: {sched} · {ig.installments_recorded} payment(s) on file ·{' '}
                <strong>{ig.installments_remaining}</strong> instalment(s) left of{' '}
                <strong>{ig.installments_planned}</strong> · remaining balance{' '}
                {ig.remaining_balance} SAR.
              </Typography.Paragraph>
              <Typography.Paragraph type="secondary" style={{ fontSize: 12, margin: 0 }}>
                Each recorded payment counts as one instalment for this hint. Annual
                and lump-sum leases use one or two splits as appropriate.
              </Typography.Paragraph>
              <Button
                type="default"
                size="small"
                style={{ marginTop: 12 }}
                onClick={() =>
                  payForm.setFieldsValue({
                    amount: Number(ig.suggested_next_amount),
                  })
                }
              >
                Fill suggested amount
              </Button>
            </Card>
          )
        })()}
        <Form
          form={payForm}
          layout="vertical"
          onFinish={onPaySubmit}
          initialValues={{
            payment_date: dayjs(),
            payment_method: 'bank_transfer',
          }}
        >
          <Form.Item
            name="amount"
            label="Amount (SAR, incl. VAT allowed up to remaining balance)"
            rules={[{ required: true, message: 'Enter amount' }]}
          >
            <InputNumber min={0.01} step={100} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="payment_date"
            label="Payment date"
            rules={[{ required: true, message: 'Pick date' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="due_date" label="Due date (optional, for late tracking)">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="payment_method"
            label="Method"
            rules={[{ required: true, message: 'Select method' }]}
          >
            <Select options={PAYMENT_METHODS} />
          </Form.Item>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={payMutation.isPending}>
                Save payment
              </Button>
              <Button
                onClick={() => setPayModal({ open: false, contract: null })}
              >
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Terminate contract #${terminateTarget?.id ?? ''}`}
        open={Boolean(terminateTarget)}
        onCancel={() => {
          setTerminateTarget(null)
          terminateMutation.reset()
        }}
        footer={null}
        destroyOnClose
      >
        {termError && (
          <Typography.Paragraph type="danger">{String(termError)}</Typography.Paragraph>
        )}
        <Typography.Paragraph type="secondary">
          The unit will be set back to vacant after termination.
        </Typography.Paragraph>
        <Form
          form={terminateForm}
          layout="vertical"
          onFinish={(v) =>
            terminateTarget &&
            terminateMutation.mutate({
              id: terminateTarget.id,
              reason: v.reason || '',
            })
          }
        >
          <Form.Item name="reason" label="Reason (optional)">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button
                danger
                type="primary"
                htmlType="submit"
                loading={terminateMutation.isPending}
              >
                Terminate contract
              </Button>
              <Button onClick={() => setTerminateTarget(null)}>Cancel</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
