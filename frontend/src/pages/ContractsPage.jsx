import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
import { useLocalizedDigits } from '../hooks/useLocalizedDigits'
import { arabicInputNumberProps } from '../utils/arabicNumerals'
import { sarDisplay } from '../utils/sarFormat'

export function ContractsPage() {
  const { t } = useTranslation()
  const { isArabic, localizeDigits } = useLocalizedDigits()
  const PAYMENT_SCHEDULES = useMemo(
    () => [
      { value: 'monthly', label: t('contracts.scheduleMonthly') },
      { value: 'quarterly', label: t('contracts.scheduleQuarterly') },
      { value: 'semi_annual', label: t('contracts.scheduleSemiAnnual') },
      { value: 'annual', label: t('contracts.scheduleAnnual') },
      { value: 'lump_sum', label: t('contracts.scheduleLumpSum') },
    ],
    [t],
  )
  const PAYMENT_METHODS = useMemo(
    () => [
      { value: 'bank_transfer', label: t('contracts.methodBankTransfer') },
      { value: 'cash', label: t('contracts.methodCash') },
      { value: 'cheque', label: t('contracts.methodCheque') },
      { value: 'online', label: t('contracts.methodOnline') },
    ],
    [t],
  )
  const CONTRACT_STATUS_OPTIONS = useMemo(
    () => [
      { value: 'active', label: t('contracts.statusActive') },
      { value: 'expired', label: t('contracts.statusExpired') },
      { value: 'terminated', label: t('contracts.statusTerminated') },
    ],
    [t],
  )
  const PAYMENT_FILTER_STATUS_OPTIONS = useMemo(
    () => [
      { value: 'confirmed', label: t('contracts.paymentStatusConfirmed') },
      { value: 'cancelled', label: t('contracts.paymentStatusCancelled') },
    ],
    [t],
  )
  const scheduleLabelByValue = useMemo(
    () => Object.fromEntries(PAYMENT_SCHEDULES.map((o) => [o.value, o.label])),
    [PAYMENT_SCHEDULES],
  )
  const contractStatusLabelByValue = useMemo(
    () =>
      Object.fromEntries(CONTRACT_STATUS_OPTIONS.map((o) => [o.value, o.label])),
    [CONTRACT_STATUS_OPTIONS],
  )
  const paymentStatusLabelByValue = useMemo(
    () =>
      Object.fromEntries(
        PAYMENT_FILTER_STATUS_OPTIONS.map((o) => [o.value, o.label]),
      ),
    [PAYMENT_FILTER_STATUS_OPTIONS],
  )
  const paymentMethodLabelByValue = useMemo(
    () => Object.fromEntries(PAYMENT_METHODS.map((o) => [o.value, o.label])),
    [PAYMENT_METHODS],
  )
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
      label: `${u.property_name ?? t('contracts.propertyFallback')} — ${u.unit_number} · ${u.property_city ?? ''}`,
    }))
  }, [unitsData, t])

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

  const columns = useMemo(
    () => [
      {
        title: t('common.id'),
        dataIndex: 'id',
        key: 'id',
        width: 70,
        render: (v) => localizeDigits(String(v ?? '')),
      },
      {
        title: t('contracts.propertyUnit'),
        key: 'loc',
        render: (_, row) => (
          <span>
            {localizeDigits(
              `${row.property_name ?? '—'} · ${row.unit_number ?? '—'}`,
            )}
          </span>
        ),
      },
      {
        title: t('contracts.tenant'),
        key: 'tenant',
        ellipsis: true,
        render: (_, row) => row.tenant_name || '—',
      },
      {
        title: t('contracts.tenantId'),
        key: 'tenant_ref',
        width: 100,
        render: (_, row) =>
          localizeDigits(String(row.tenant?.tenant_reference || '—')),
      },
      {
        title: t('common.status'),
        dataIndex: 'status',
        key: 'status',
        render: (s) => (
          <Tag color={s === 'active' ? 'green' : 'default'}>
            {contractStatusLabelByValue[s] ?? s}
          </Tag>
        ),
      },
      {
        title: t('contracts.schedule'),
        dataIndex: 'payment_schedule',
        key: 'payment_schedule',
        render: (s) =>
          s ? (
            <Tag>{scheduleLabelByValue[s] ?? String(s).replace(/_/g, ' ')}</Tag>
          ) : (
            '—'
          ),
      },
      {
        title: t('contracts.period'),
        key: 'period',
        render: (_, row) => (
          <span style={{ whiteSpace: 'nowrap' }}>
            {localizeDigits(`${row.start_date} → ${row.end_date}`)}
          </span>
        ),
      },
      {
        title: t('contracts.rentPerMonth'),
        dataIndex: 'monthly_rent',
        key: 'monthly_rent',
        render: (v) => sarDisplay(v, t('common.currencySAR'), isArabic),
      },
      {
        title: t('contracts.securityDeposit'),
        key: 'dep',
        render: (_, row) => {
          const amt = row.security_deposit
          if (amt === undefined || amt === null || String(amt) === '0') return '—'
          const paid = row.security_deposit_paid
          return (
            <span>
              {sarDisplay(amt, t('common.currencySAR'), isArabic)} ·{' '}
              {paid ? (
                <Tag color="green">{t('contracts.paid')}</Tag>
              ) : (
                <Tag color="orange">{t('contracts.notPaid')}</Tag>
              )}
              {row.security_deposit_received_on
                ? localizeDigits(` (${row.security_deposit_received_on})`)
                : ''}
            </span>
          )
        },
      },
      {
        title: t('contracts.remainingInclVat'),
        dataIndex: 'remaining_balance',
        key: 'rem',
        render: (v) => sarDisplay(v, t('common.currencySAR'), isArabic),
      },
      {
        title: t('contracts.nextInstalment'),
        key: 'inst',
        width: 130,
        ellipsis: true,
        render: (_, row) => {
          const ig = row.installment_guidance
          if (!ig || !Number(ig.suggested_next_amount)) return '—'
          return (
            <span
              title={t('contracts.installmentTooltip', {
              remaining: ig.installments_remaining,
              planned: ig.installments_planned,
              schedule:
                scheduleLabelByValue[ig.payment_schedule] ??
                (ig.payment_schedule || '').replace(/_/g, ' '),
            })}
            >
              {sarDisplay(ig.suggested_next_amount, t('common.currencySAR'), isArabic)}
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
                {t('contracts.editLease')}
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
                {t('contracts.payment')}
              </Button>
            )}
            {canTerminate && row.status === 'active' && (
              <Button
                type="link"
                size="small"
                danger
                onClick={() => setTerminateTarget(row)}
              >
                {t('contracts.terminate')}
              </Button>
            )}
          </Space>
        ),
      },
    ],
    [
      t,
      isArabic,
      localizeDigits,
      canEditLeaseTerms,
      canRecordPayment,
      canTerminate,
      leaseTermsMutation,
      termsForm,
      payForm,
      contractStatusLabelByValue,
      scheduleLabelByValue,
      paymentMethodLabelByValue,
    ],
  )

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
            {t('contracts.title')}
          </Typography.Title>
          {canCreateContract && (
            <Button type="primary" onClick={() => setCreateOpen(true)}>
              {t('contracts.newContract')}
            </Button>
          )}
        </div>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {t('contracts.subtitle')}
        </Typography.Paragraph>

        {isError && (
          <Typography.Text type="danger">
            {error?.message || t('contracts.loadContractsError')}
          </Typography.Text>
        )}

        <Card size="small" title={t('contracts.filterTitle')} style={{ marginBottom: 8 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Space wrap style={{ width: '100%' }} align="start">
              <Input
                allowClear
                placeholder={t('contracts.searchPlaceholder')}
                value={contractDraft.search}
                style={{ minWidth: 260 }}
                onChange={(e) =>
                  setContractDraft((d) => ({ ...d, search: e.target.value }))
                }
              />
              <Select
                allowClear
                placeholder={t('common.status')}
                style={{ width: 140 }}
                options={CONTRACT_STATUS_OPTIONS}
                value={contractDraft.status}
                onChange={(v) =>
                  setContractDraft((d) => ({ ...d, status: v }))
                }
              />
              <Select
                allowClear
                placeholder={t('contracts.paymentSchedule')}
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
                {t('common.apply')}
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
                {t('common.clear')}
              </Button>
            </Space>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {t('contracts.backendNote')}
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
                    {t('contracts.paymentsCount', {
                      count: payments.length,
                    })}
                  </Typography.Text>
                  <Table
                    size="small"
                    rowKey="id"
                    pagination={false}
                    dataSource={payments}
                    columns={[
                      {
                        title: t('common.date'),
                        dataIndex: 'payment_date',
                        key: 'pd',
                        render: (v) => (v ? localizeDigits(String(v)) : '—'),
                      },
                      {
                        title: t('contracts.due'),
                        dataIndex: 'due_date',
                        key: 'dd',
                        render: (v) => (v ? localizeDigits(String(v)) : '—'),
                      },
                      {
                        title: t('common.amount'),
                        dataIndex: 'amount',
                        key: 'a',
                        render: (v) => sarDisplay(v, t('common.currencySAR'), isArabic),
                      },
                      {
                        title: t('contracts.method'),
                        dataIndex: 'payment_method',
                        key: 'm',
                        render: (v) =>
                          paymentMethodLabelByValue[v] ??
                          (v != null ? String(v).replace(/_/g, ' ') : '—'),
                      },
                      {
                        title: t('contracts.late'),
                        dataIndex: 'is_late',
                        key: 'il',
                        render: (v) =>
                          v ? (
                            <Tag color="red">{t('contracts.lateYes')}</Tag>
                          ) : (
                            t('contracts.lateNo')
                          ),
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

        <Card size="small" title={t('contracts.searchPayments')} style={{ marginTop: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Space wrap style={{ width: '100%' }} align="start">
              <Input
                allowClear
                placeholder={t('contracts.contractNum')}
                value={payDraft.contract_number}
                style={{ width: 140 }}
                onChange={(e) =>
                  setPayDraft((d) => ({ ...d, contract_number: e.target.value }))
                }
              />
              <Select
                allowClear
                placeholder={t('contracts.paymentStatus')}
                style={{ width: 160 }}
                options={PAYMENT_FILTER_STATUS_OPTIONS}
                value={payDraft.status}
                onChange={(v) => setPayDraft((d) => ({ ...d, status: v }))}
              />
              <Select
                allowClear
                placeholder={t('contracts.paymentMethod')}
                style={{ width: 170 }}
                options={PAYMENT_METHODS}
                value={payDraft.payment_method}
                onChange={(v) =>
                  setPayDraft((d) => ({ ...d, payment_method: v }))
                }
              />
              <Input
                allowClear
                placeholder={t('contracts.paySearchPlaceholder')}
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
                {t('common.apply')}
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
                {t('common.clear')}
              </Button>
            </Space>
            {payListError && (
              <Typography.Text type="danger">
                {payListErr?.message || t('contracts.loadPaymentsError')}
              </Typography.Text>
            )}
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {t('contracts.payBackendNote')}
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
                {
                  title: t('contracts.payNum'),
                  dataIndex: 'id',
                  key: 'id',
                  width: 70,
                  render: (v) => localizeDigits(String(v ?? '')),
                },
                {
                  title: t('contracts.contract'),
                  dataIndex: 'contract',
                  key: 'contract',
                  width: 90,
                  render: (v) => localizeDigits(String(v ?? '')),
                },
                {
                  title: t('common.date'),
                  dataIndex: 'payment_date',
                  key: 'payment_date',
                  render: (v) => localizeDigits(String(v ?? '')),
                },
                {
                  title: t('common.amount'),
                  dataIndex: 'amount',
                  key: 'amount',
                  render: (v) => sarDisplay(v, t('common.currencySAR'), isArabic),
                },
                {
                  title: t('common.status'),
                  dataIndex: 'status',
                  key: 'status',
                  render: (s) => (
                    <Tag>{paymentStatusLabelByValue[s] ?? String(s)}</Tag>
                  ),
                },
                {
                  title: t('contracts.method'),
                  dataIndex: 'payment_method',
                  key: 'payment_method',
                  render: (v) =>
                    paymentMethodLabelByValue[v] ??
                    (v != null ? String(v).replace(/_/g, ' ') : '—'),
                },
                {
                  title: t('contracts.late'),
                  dataIndex: 'is_late',
                  key: 'is_late',
                  render: (v) =>
                    v ? (
                      <Tag color="red">{t('contracts.lateYes')}</Tag>
                    ) : (
                      t('contracts.lateNo')
                    ),
                },
              ]}
            />
          </Space>
        </Card>
      </Space>

      <Modal
        title={t('contracts.newContractModal.title')}
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
            label={t('contracts.newContractModal.vacantUnit')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select
              options={unitOptions}
              showSearch
              optionFilterProp="label"
              placeholder={t('contracts.chooseUnitPlaceholder')}
            />
          </Form.Item>
          <Typography.Paragraph strong style={{ marginBottom: 8 }}>
            {t('contracts.newContractModal.tenantSection')}
          </Typography.Paragraph>
          <Form.Item
            name={['tenant_data', 'full_name']}
            label={t('contracts.newContractModal.fullName')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input placeholder={t('contracts.newContractModal.asOnIdPlaceholder')} />
          </Form.Item>
          <Form.Item
            name={['tenant_data', 'national_id']}
            label={t('contracts.newContractModal.nationalId')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Input placeholder={t('contracts.newContractModal.nationalIdPlaceholder')} />
          </Form.Item>
          <Form.Item
            name={['tenant_data', 'phone']}
            label={t('contracts.newContractModal.phone')}
          >
            <Input placeholder={t('contracts.newContractModal.mobilePlaceholder')} />
          </Form.Item>
          <Form.Item name={['tenant_data', 'email']} label={t('contracts.newContractModal.email')}>
            <Input type="email" placeholder={t('contracts.newContractModal.optionalPlaceholder')} />
          </Form.Item>
          <Form.Item
            name={['tenant_data', 'nationality']}
            label={t('contracts.newContractModal.nationality')}
          >
            <Input placeholder={t('contracts.newContractModal.optionalPlaceholder')} />
          </Form.Item>
          <Form.Item
            name={['tenant_data', 'date_of_birth']}
            label={t('contracts.newContractModal.dateOfBirth')}
          >
            <DatePicker style={{ width: '100%' }} allowClear />
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ fontSize: 12 }}>
            {t('contracts.newContractModal.tenantIdNote')}
          </Typography.Paragraph>
          <Form.Item
            name="monthly_rent"
            label={t('contracts.newContractModal.monthlyRent')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber
              min={0}
              step={100}
              style={{ width: '100%' }}
              {...arabicInputNumberProps(isArabic)}
            />
          </Form.Item>
          <Form.Item
            name="start_date"
            label={t('contracts.newContractModal.startDate')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Typography.Paragraph type="secondary" style={{ fontSize: 12 }}>
            {t('contracts.newContractModal.durationNote')}
          </Typography.Paragraph>
          <Form.Item
            name="duration_months"
            label={t('contracts.newContractModal.durationMonths')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber
              min={1}
              max={600}
              style={{ width: '100%' }}
              {...arabicInputNumberProps(isArabic)}
            />
          </Form.Item>
          <Form.Item
            name="security_deposit"
            label={t('contracts.newContractModal.securityDeposit')}
          >
            <InputNumber
              min={0}
              step={100}
              style={{ width: '100%' }}
              {...arabicInputNumberProps(isArabic)}
            />
          </Form.Item>
          <Form.Item
            name="payment_schedule"
            label={t('contracts.newContractModal.paymentSchedule')}
          >
            <Select options={PAYMENT_SCHEDULES} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={createMutation.isPending}>
                {t('common.create')}
              </Button>
              <Button onClick={() => setCreateOpen(false)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`${t('contracts.editLeaseModal.title')} #${localizeDigits(String(editLeaseTarget?.id ?? ''))}`}
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
          {t('contracts.editLeaseModal.subtitle')}
        </Typography.Paragraph>
        <Form
          form={termsForm}
          layout="vertical"
          onFinish={onLeaseTermsSubmit}
        >
          <Form.Item
            name="monthly_rent"
            label={t('contracts.editLeaseModal.monthlyRent')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber
              min={0}
              step={100}
              style={{ width: '100%' }}
              {...arabicInputNumberProps(isArabic)}
            />
          </Form.Item>
          <Form.Item
            name="start_date"
            label={t('contracts.editLeaseModal.startDate')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="duration_months"
            label={t('contracts.editLeaseModal.durationMonths')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber
              min={1}
              max={600}
              style={{ width: '100%' }}
              {...arabicInputNumberProps(isArabic)}
            />
          </Form.Item>
          <Form.Item
            name="security_deposit"
            label={t('contracts.editLeaseModal.securityDeposit')}
          >
            <InputNumber
              min={0}
              step={100}
              style={{ width: '100%' }}
              {...arabicInputNumberProps(isArabic)}
            />
          </Form.Item>
          <Form.Item name="security_deposit_paid" valuePropName="checked">
            <Checkbox>{t('contracts.editLeaseModal.depositReceived')}</Checkbox>
          </Form.Item>
          <Form.Item
            name="security_deposit_received_on"
            label={t('contracts.editLeaseModal.depositReceivedOn')}
          >
            <DatePicker style={{ width: '100%' }} allowClear />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={leaseTermsMutation.isPending}
              >
                {t('contracts.editLeaseModal.saveRecalculate')}
              </Button>
              <Button onClick={() => setEditLeaseTarget(null)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`${t('contracts.paymentModal.title')} #${localizeDigits(String(payModal.contract?.id ?? ''))}`}
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
          const sched =
            scheduleLabelByValue[ig.payment_schedule] ??
            (ig.payment_schedule || '').replace(/_/g, ' ')
          return (
            <Card size="small" type="inner" style={{ marginBottom: 16 }}>
              <Typography.Paragraph style={{ marginBottom: 8 }}>
                <strong>{t('contracts.paymentModal.suggestedTitle')}</strong>{' '}
                {t('contracts.paymentModal.suggestedDesc')}{' '}
                <Typography.Text strong>
                  {localizeDigits(String(ig.suggested_next_amount))}
                </Typography.Text>{' '}
                {t('common.currencySAR')}
              </Typography.Paragraph>
              <Typography.Paragraph type="secondary" style={{ marginBottom: 8 }}>
                {t('contracts.paymentModal.scheduleInfo')}: {sched} ·{' '}
                {localizeDigits(String(ig.installments_recorded))}{' '}
                {t('contracts.paymentModal.paymentsOnFile')} ·{' '}
                <strong>{localizeDigits(String(ig.installments_remaining))}</strong>{' '}
                {t('contracts.paymentModal.instalmentsLeft')}{' '}
                <strong>{localizeDigits(String(ig.installments_planned))}</strong> ·{' '}
                {t('contracts.paymentModal.remainingBalance')}{' '}
                {localizeDigits(String(ig.remaining_balance))} {t('common.currencySAR')}.
              </Typography.Paragraph>
              <Typography.Paragraph type="secondary" style={{ fontSize: 12, margin: 0 }}>
                {t('contracts.paymentModal.instNote')}
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
                {t('contracts.paymentModal.fillSuggested')}
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
            label={t('contracts.paymentModal.amount')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <InputNumber
              min={0.01}
              step={100}
              style={{ width: '100%' }}
              {...arabicInputNumberProps(isArabic)}
            />
          </Form.Item>
          <Form.Item
            name="payment_date"
            label={t('contracts.paymentModal.paymentDate')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="due_date"
            label={t('contracts.paymentModal.dueDate')}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="payment_method"
            label={t('contracts.method')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select options={PAYMENT_METHODS} />
          </Form.Item>
          <Form.Item name="notes" label={t('common.notes')}>
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={payMutation.isPending}>
                {t('contracts.paymentModal.savePayment')}
              </Button>
              <Button
                onClick={() => setPayModal({ open: false, contract: null })}
              >
                {t('common.cancel')}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`${t('contracts.terminateModal.title')} #${localizeDigits(String(terminateTarget?.id ?? ''))}`}
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
          {t('contracts.terminateModal.subtitle')}
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
          <Form.Item name="reason" label={t('contracts.terminateModal.reason')}>
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
                {t('contracts.terminateModal.terminateBtn')}
              </Button>
              <Button onClick={() => setTerminateTarget(null)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
