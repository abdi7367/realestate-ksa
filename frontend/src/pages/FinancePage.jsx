import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
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
import { useLocalizedDigits } from '../hooks/useLocalizedDigits'
import { arabicInputNumberProps } from '../utils/arabicNumerals'
import { sarDisplay } from '../utils/sarFormat'

export function FinancePage() {
  const { t } = useTranslation()
  const { isArabic, localizeDigits } = useLocalizedDigits()
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

  const txTypeOptions = useMemo(
    () => [
      { value: 'income', label: t('finance.transactionTypes.income') },
      { value: 'expense', label: t('finance.transactionTypes.expense') },
    ],
    [t],
  )
  const txTypeLabelByValue = useMemo(
    () => Object.fromEntries(txTypeOptions.map((o) => [o.value, o.label])),
    [txTypeOptions],
  )

  const incomeCategoryOptions = useMemo(
    () => [
      { value: 'rental', label: t('finance.incomeCategories.rental') },
      { value: 'parking', label: t('finance.incomeCategories.parking') },
      { value: 'service_charge', label: t('finance.incomeCategories.service_charge') },
      {
        value: 'utility_recovery',
        label: t('finance.incomeCategories.utility_recovery'),
      },
      { value: 'other', label: t('finance.incomeCategories.other') },
    ],
    [t],
  )
  const expenseCategoryOptions = useMemo(
    () => [
      { value: 'maintenance', label: t('finance.expenseCategories.maintenance') },
      { value: 'utilities', label: t('finance.expenseCategories.utilities') },
      { value: 'security', label: t('finance.expenseCategories.security') },
      { value: 'cleaning', label: t('finance.expenseCategories.cleaning') },
      {
        value: 'government_fees',
        label: t('finance.expenseCategories.government_fees'),
      },
      { value: 'management', label: t('finance.expenseCategories.management') },
      { value: 'other', label: t('finance.expenseCategories.other') },
    ],
    [t],
  )
  const allCategoryFilterOptions = useMemo(
    () => [...incomeCategoryOptions, ...expenseCategoryOptions],
    [incomeCategoryOptions, expenseCategoryOptions],
  )

  const categoryLabel = (categoryVal, transactionType) => {
    if (categoryVal == null || categoryVal === '') return '—'
    const prefix =
      transactionType === 'expense'
        ? 'finance.expenseCategories.'
        : 'finance.incomeCategories.'
    return t(`${prefix}${categoryVal}`, {
      defaultValue: String(categoryVal).replace(/_/g, ' '),
    })
  }

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
        {t('finance.title')}
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginTop: 0 }}>
        {t('finance.subtitle')}
      </Typography.Paragraph>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card size="small" title={t('finance.income')}>
            <Typography.Text strong>
              {sarDisplay(
                summaryData?.income != null ? summaryData.income : null,
                t('common.currencySAR'),
                isArabic,
              )}
            </Typography.Text>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title={t('finance.expense')}>
            <Typography.Text strong>
              {sarDisplay(
                summaryData?.expense != null ? summaryData.expense : null,
                t('common.currencySAR'),
                isArabic,
              )}
            </Typography.Text>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card size="small" title={t('finance.net')}>
            <Typography.Text strong>
              {sarDisplay(
                summaryData?.profit != null ? summaryData.profit : null,
                t('common.currencySAR'),
                isArabic,
              )}
            </Typography.Text>
          </Card>
        </Col>
      </Row>

      <Card size="small">
        <Space wrap align="center">
          <Select
            allowClear
            placeholder={t('finance.propertyPlaceholder')}
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
            placeholder={t('common.type')}
            style={{ width: 120 }}
            options={txTypeOptions}
            value={txType}
            onChange={(v) => {
              setTxType(v)
              setPage(1)
            }}
          />
          <Select
            allowClear
            placeholder={t('finance.category')}
            style={{ minWidth: 160 }}
            options={allCategoryFilterOptions}
            value={category}
            onChange={(v) => {
              setCategory(v)
              setPage(1)
            }}
          />
          <Input.Search
            allowClear
            placeholder={t('finance.searchPlaceholder')}
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
              {t('finance.addTransaction')}
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
          {
            title: t('common.id'),
            dataIndex: 'id',
            width: 70,
            render: (v) => localizeDigits(String(v ?? '')),
          },
          {
            title: t('common.property'),
            key: 'prop',
            render: (_, row) =>
              localizeDigits(
                String(propertyNameById.get(row.property) ?? row.property ?? ''),
              ),
          },
          {
            title: t('common.type'),
            dataIndex: 'transaction_type',
            render: (tx) => (
              <Tag color={tx === 'income' ? 'green' : 'orange'}>
                {txTypeLabelByValue[tx] ?? tx}
              </Tag>
            ),
          },
          {
            title: t('finance.category'),
            dataIndex: 'category',
            render: (cat, row) => categoryLabel(cat, row.transaction_type),
          },
          {
            title: t('common.amount'),
            dataIndex: 'amount',
            render: (v) => sarDisplay(v, t('common.currencySAR'), isArabic),
          },
          {
            title: t('common.date'),
            dataIndex: 'date',
            render: (v) => localizeDigits(String(v ?? '')),
          },
          { title: t('common.description'), dataIndex: 'description', ellipsis: true },
          {
            title: t('common.reference'),
            dataIndex: 'reference',
            ellipsis: true,
            render: (v) => localizeDigits(String(v ?? '')),
          },
        ]}
      />

      <Modal
        title={t('finance.newTransaction')}
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
            label={t('common.property')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select options={propertyOptions} showSearch optionFilterProp="label" />
          </Form.Item>
          <Form.Item
            name="transaction_type"
            label={t('common.type')}
            rules={[{ required: true, message: t('common.required') }]}
          >
            <Select
              options={txTypeOptions}
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
                label={t('finance.category')}
                rules={[{ required: true, message: t('common.required') }]}
              >
                <Select
                  options={
                    form.getFieldValue('transaction_type') === 'expense'
                      ? expenseCategoryOptions
                      : incomeCategoryOptions
                  }
                />
              </Form.Item>
            )}
          </Form.Item>
          <Form.Item
            name="amount"
            label={t('common.amountSAR')}
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
            name="date"
            label={t('common.date')}
            rules={[{ required: true, message: t('common.required') }]}
            initialValue={dayjs()}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="description" label={t('common.description')}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="reference" label={t('common.reference')}>
            <Input />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createTx.isPending}>
            {t('common.save')}
          </Button>
        </Form>
      </Modal>
    </Space>
  )
}
