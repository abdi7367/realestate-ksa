import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  DatePicker,
  Descriptions,
  Form,
  InputNumber,
  message,
  Row,
  Select,
  Space,
  Table,
  Typography,
} from 'antd'
import dayjs from 'dayjs'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../api/client'
import { REPORT_IDS, fetchReport, downloadCashFlowPdf } from '../api/reports'
import { useLocalizedDigits } from '../hooks/useLocalizedDigits'
import { arabicInputNumberProps } from '../utils/arabicNumerals'
import {
  isNumericCellValue,
  isReportMoneyColumnKey,
  sarDisplay,
} from '../utils/sarFormat'

function ReportBidiText({ value }) {
  const { localizeDigits } = useLocalizedDigits()
  if (value === null || value === undefined || value === '') {
    return <span>—</span>
  }
  return (
    <span dir="auto" className="report-bidi-value">
      {localizeDigits(String(value))}
    </span>
  )
}

function reportPropertyContextItems(data, t) {
  if (!data) return []
  const f = data.filters
  if (f && typeof f === 'object' && f.property_name) {
    return [
      {
        key: 'ctx-property',
        label: t('reports.property'),
        children: (
          <ReportBidiText
            value={
              f.property_id != null && f.property_id !== ''
                ? `${f.property_name} (ID ${f.property_id})`
                : String(f.property_name)
            }
          />
        ),
      },
    ]
  }
  if (f && typeof f === 'object' && f.property_id != null && f.property_id !== '') {
    return [
      {
        key: 'ctx-property',
        label: t('reports.property'),
        children: <ReportBidiText value={`ID ${f.property_id}`} />,
      },
    ]
  }
  if (data.property_name) {
    return [
      {
        key: 'ctx-property',
        label: t('reports.property'),
        children: (
          <ReportBidiText
            value={
              data.property_id != null && data.property_id !== ''
                ? `${data.property_name} (ID ${data.property_id})`
                : String(data.property_name)
            }
          />
        ),
      },
    ]
  }
  if (data.property_id != null && data.property_id !== '') {
    return [
      {
        key: 'ctx-property',
        label: t('reports.property'),
        children: <ReportBidiText value={`ID ${data.property_id}`} />,
      },
    ]
  }
  return []
}

function resultsTableColumns(sampleRow, currencyLabel, easternArabicDigits = false) {
  if (!sampleRow || typeof sampleRow !== 'object') return []
  return Object.keys(sampleRow).map((key) => ({
    title: key.replace(/_/g, ' '),
    dataIndex: key,
    key,
    ellipsis: true,
    render: (v) => {
      if (isReportMoneyColumnKey(key) && isNumericCellValue(v)) {
        return (
          <span dir="auto" className="report-bidi-value">
            {sarDisplay(v, currencyLabel, easternArabicDigits)}
          </span>
        )
      }
      return <ReportBidiText value={v} />
    },
  }))
}

function ReportOutput({ data }) {
  const { t } = useTranslation()
  const { isArabic, localizeDigits } = useLocalizedDigits()
  const sar = t('common.currencySAR')
  if (!data) return null

  if (Array.isArray(data.results) && data.results.length > 0) {
    return (
      <Table
        className="report-bidi-table"
        rowKey={(_, i) => String(i)}
        size="small"
        scroll={{ x: true }}
        columns={resultsTableColumns(data.results[0], sar, isArabic)}
        dataSource={data.results}
        pagination={{ pageSize: 25, showSizeChanger: true }}
      />
    )
  }

  if (Array.isArray(data.results) && data.results.length === 0) {
    return (
      <Typography.Text type="secondary">{t('reports.noRows')}</Typography.Text>
    )
  }

  if (Array.isArray(data.by_category) && data.by_category.length > 0) {
    const propCtx = reportPropertyContextItems(data, t)
    const periodItem =
      data.date_from && data.date_to
        ? [
            {
              key: 'ctx-period',
              label: t('reports.period'),
              children: (
                <ReportBidiText value={`${data.date_from} → ${data.date_to}`} />
              ),
            },
          ]
        : []
    const ctx = [...propCtx, ...periodItem]
    return (
      <>
        {ctx.length > 0 && (
          <Descriptions
            bordered
            size="small"
            column={1}
            items={ctx}
            style={{ marginBottom: 16 }}
          />
        )}
        <Table
          className="report-bidi-table"
          rowKey={(_, i) => String(i)}
          size="small"
          columns={[
            {
              title: t('reports.category'),
              dataIndex: 'category',
              key: 'category',
              render: (v) => <ReportBidiText value={v} />,
            },
            {
              title: t('reports.total'),
              dataIndex: 'total',
              key: 'total',
              render: (v) =>
                isNumericCellValue(v) ? (
                  <span dir="auto" className="report-bidi-value">
                    {sarDisplay(v, sar, isArabic)}
                  </span>
                ) : (
                  <ReportBidiText value={v} />
                ),
            },
          ]}
          dataSource={data.by_category}
          pagination={false}
        />
      </>
    )
  }

  if (Array.isArray(data.owners) && data.owners.length > 0) {
    const items = data.owners.map((owner, idx) => ({
      key: String(idx),
      label: (
        <ReportBidiText value={`${owner.owner_name} (${owner.owner_id})`} />
      ),
      children: (
        <div>
          <Typography.Text type="secondary">
            {owner.ownership_type} · {localizeDigits(String(owner.properties?.length ?? 0))}{' '}
            properties
          </Typography.Text>
          <Table
            className="report-bidi-table"
            style={{ marginTop: 8 }}
            size="small"
            rowKey={(r) => `${r.property_id}-${r.property_name}`}
            pagination={false}
            dataSource={owner.properties || []}
            columns={[
              {
                title: t('reports.property'),
                dataIndex: 'property_name',
                key: 'pn',
                render: (v) => <ReportBidiText value={v} />,
              },
              {
                title: t('reports.city'),
                dataIndex: 'property_city',
                key: 'pc',
                render: (v) => <ReportBidiText value={v} />,
              },
              {
                title: t('reports.ownershipPct'),
                dataIndex: 'ownership_percentage',
                key: 'op',
                render: (v) => <ReportBidiText value={v} />,
              },
              {
                title: t('reports.mgmtFeePct'),
                dataIndex: 'management_fee_percentage',
                key: 'mf',
                render: (v) => <ReportBidiText value={v} />,
              },
              {
                title: t('reports.agreement'),
                dataIndex: 'has_management_agreement',
                key: 'ha',
                render: (v) => (v ? t('reports.yes') : t('reports.no')),
              },
            ]}
          />
        </div>
      ),
    }))
    return (
      <Descriptions bordered size="small" column={1} items={items} />
    )
  }

  const ctx = reportPropertyContextItems(data, t)
  const entries = Object.entries(data).filter(
    ([k]) => k !== 'filters' && !Array.isArray(data[k]),
  )
  const items = entries.map(([k, v]) => ({
    key: k,
    label: <ReportBidiText value={k.replace(/_/g, ' ')} />,
    children:
      typeof v === 'object' && v !== null ? (
        <span dir="ltr" className="report-bidi-value">
          {localizeDigits(JSON.stringify(v))}
        </span>
      ) : (
        <ReportBidiText value={v} />
      ),
  }))
  return (
    <Descriptions bordered size="small" column={1} items={[...ctx, ...items]} />
  )
}

function toNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : 0
}

function toSafeFilenamePart(value) {
  if (!value) return ''
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

const CHART_COLORS = ['#0d9488', '#2563eb', '#f59e0b', '#7c3aed', '#ef4444', '#14b8a6']

function ReportCharts({ reportId, data }) {
  const { t } = useTranslation()
  const { localizeDigits } = useLocalizedDigits()
  const sar = t('common.currencySAR')
  if (!data) return null

  if (reportId === 'cash_flow') {
    const chartData = [
      { name: 'Tx income', value: toNum(data.operating_income_from_transactions) },
      { name: 'Tx expense', value: toNum(data.operating_expense_from_transactions) },
      { name: 'Disbursements', value: toNum(data.approved_disbursements) },
      { name: 'Collections', value: toNum(data.tenant_payment_collections) },
      { name: 'Net tx', value: toNum(data.net_operating_transactions) },
    ]
    return (
      <Card size="small" title={t('reports.charts.cashFlow')} style={{ marginBottom: 16 }}>
        <div className="report-chart-ltr" style={{ height: 280, minHeight: 280, minWidth: 0 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip
                formatter={(value, name) => [
                  localizeDigits(`${value} ${sar}`),
                  name,
                ]}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {chartData.map((_, idx) => (
                  <Cell key={`cell-${idx}`} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    )
  }

  if ((reportId === 'income_statement' || reportId === 'expenses') && Array.isArray(data.by_category)) {
    const chartData = data.by_category.map((x) => ({ name: x.category, total: toNum(x.total) }))
    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={14}>
          <Card size="small" title={t('reports.charts.categoryDist')}>
            <div className="report-chart-ltr" style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip
                    formatter={(value, name) => [
                      localizeDigits(`${value} ${sar}`),
                      name,
                    ]}
                  />
                  <Bar dataKey="total" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card size="small" title={t('reports.charts.categoryShare')}>
            <div className="report-chart-ltr" style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartData} dataKey="total" nameKey="name" outerRadius={92} label>
                    {chartData.map((_, idx) => (
                      <Cell key={`pie-${idx}`} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value, name) => [
                      localizeDigits(`${value} ${sar}`),
                      name,
                    ]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>
    )
  }

  return null
}

export function ReportsPage() {
  const { t, i18n } = useTranslation()
  const { isArabic } = useLocalizedDigits()
  const [form] = Form.useForm()
  const [submitted, setSubmitted] = useState(null)

  const { data: propertiesData } = useQuery({
    queryKey: ['properties-options'],
    queryFn: () => api.get('/api/properties/', { params: { page_size: 500 } }).then((r) => r.data),
  })

  const propertyOptions = useMemo(() => {
    const raw = propertiesData?.results ?? propertiesData ?? []
    const list = Array.isArray(raw) ? raw : []
    return list.map((p) => ({
      value: p.id,
      label: [p.property_code, p.name].filter(Boolean).join(' · ') || p.name,
    }))
  }, [propertiesData])

  const reportOptions = useMemo(
    () =>
      REPORT_IDS.map((id) => ({
        value: id,
        label: t(`reports.types.${id}`),
      })),
    [t],
  )

  const reportId = Form.useWatch('report_id', form)

  const { data, isFetching, isError, error, refetch } = useQuery({
    queryKey: ['report', submitted],
    queryFn: () => fetchReport(submitted.reportId, submitted.params),
    enabled: Boolean(submitted?.reportId),
  })

  const onFinish = (values) => {
    const {
      report_id,
      range,
      property_id,
      year,
      month,
      status,
      approval_status,
      ownership_type,
      tenant_id,
      limit,
    } = values

    const params = {}

    if (property_id != null) params.property_id = property_id
    if (year != null) params.year = year
    if (month != null) params.month = month
    if (status) params.status = status
    if (approval_status) params.approval_status = approval_status
    if (ownership_type) params.ownership_type = ownership_type
    if (tenant_id !== undefined && tenant_id !== '') {
      const n = Number(tenant_id)
      if (!Number.isNaN(n)) params.tenant_id = n
    }
    if (limit != null) params.limit = limit

    if (range?.length === 2 && range[0] && range[1]) {
      params.date_from = range[0].format('YYYY-MM-DD')
      params.date_to = range[1].format('YYYY-MM-DD')
    }

    setSubmitted({ reportId: report_id, params })
  }

  const downloadPdf = async () => {
    if (!submitted?.reportId) return
    if (submitted.reportId !== 'cash_flow') return
    try {
      const pdfLang = i18n?.language?.toLowerCase().startsWith('ar') ? 'ar' : 'en'
      const blob = await downloadCashFlowPdf({ ...submitted.params, lang: pdfLang })
      if (!(blob instanceof Blob) || blob.size === 0) {
        message.error('PDF download failed (empty response). Please refresh and try again.')
        return
      }

      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      const df = submitted.params?.date_from || 'from'
      const dt = submitted.params?.date_to || 'to'
      const selectedProperty = propertyOptions.find(
        (opt) => String(opt.value) === String(submitted.params?.property_id),
      )
      const slug =
        toSafeFilenamePart(data?.filters?.property_name || data?.property_name) ||
        toSafeFilenamePart(selectedProperty?.label) ||
        (submitted.params?.property_id != null && submitted.params?.property_id !== ''
          ? `property-${submitted.params.property_id}`
          : '')
      const propertyPart = slug ? `${slug}_` : ''
      a.href = url
      a.download = `cash-flow_${propertyPart}${df}_to_${dt}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      // Allow the browser to start the download before revoking.
      setTimeout(() => window.URL.revokeObjectURL(url), 1000)
    } catch (e) {
      const status = e?.response?.status
      if (status === 401) {
        message.error('Session expired. Please login again, then retry the PDF download.')
        return
      }
      const serverMsg =
        typeof e?.response?.data === 'string'
          ? e.response.data
          : e?.response?.data
            ? JSON.stringify(e.response.data)
            : null
      message.error(serverMsg || e?.message || 'PDF download failed. Please try again.')
    }
  }

  const needsRange = [
    'cash_flow',
    'income_statement',
    'expenses',
  ].includes(reportId)

  return (
    <Card bordered={false}>
      <Typography.Title level={4} style={{ marginTop: 0 }}>
        {t('reports.title')}
      </Typography.Title>
      <Typography.Paragraph type="secondary">{t('reports.intro')}</Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          report_id: 'income_statement',
          range: [dayjs().subtract(12, 'month'), dayjs()],
        }}
        style={{ maxWidth: 720 }}
      >
        <Form.Item
          name="report_id"
          label={t('reports.reportType')}
          rules={[{ required: true, message: t('reports.chooseReport') }]}
        >
          <Select options={reportOptions} optionFilterProp="label" />
        </Form.Item>

        <Row gutter={16}>
          {needsRange && (
            <Col xs={24} md={12}>
              <Form.Item name="range" label={t('reports.dateRange')}>
                <DatePicker.RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          )}
          <Col xs={24} md={12}>
            <Form.Item name="property_id" label={t('reports.propertyOptional')}>
              <Select
                allowClear
                showSearch
                optionFilterProp="label"
                placeholder={t('reports.allProperties')}
                options={propertyOptions}
              />
            </Form.Item>
          </Col>
          {reportId === 'vouchers' && (
            <>
              <Col xs={24} md={12}>
                <Form.Item name="approval_status" label={t('reports.approvalStatus')}>
                  <Select
                    allowClear
                    options={[
                      { value: 'draft', label: t('vouchers.statuses.draft') },
                      {
                        value: 'pending_accountant',
                        label: t('vouchers.statuses.pending_accountant'),
                      },
                      {
                        value: 'pending_finance',
                        label: t('vouchers.statuses.pending_finance'),
                      },
                      {
                        value: 'pending_admin',
                        label: t('vouchers.statuses.pending_admin'),
                      },
                      { value: 'approved', label: t('vouchers.statuses.approved') },
                      { value: 'rejected', label: t('vouchers.statuses.rejected') },
                    ]}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12}>
                <Form.Item name="limit" label={t('reports.rowLimit')}>
                  <InputNumber
                    min={1}
                    max={2000}
                    style={{ width: '100%' }}
                    placeholder="500"
                    {...arabicInputNumberProps(isArabic)}
                  />
                </Form.Item>
              </Col>
            </>
          )}
        </Row>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              {t('reports.runReport')}
            </Button>
            <Button
              type="button"
              disabled={!submitted?.reportId || submitted?.reportId !== 'cash_flow'}
              onClick={downloadPdf}
            >
              {t('reports.downloadPdf')}
            </Button>
            <Button type="button" disabled={!submitted?.reportId} onClick={() => refetch()}>
              {t('reports.refresh')}
            </Button>
          </Space>
        </Form.Item>
      </Form>

      {isError && (
        <Typography.Paragraph type="danger" style={{ marginTop: 16 }}>
          {error?.response?.data
            ? JSON.stringify(error.response.data)
            : error?.message || 'Request failed'}
        </Typography.Paragraph>
      )}

      <ReportCharts reportId={submitted?.reportId} data={data} />

      <Card size="small" title={t('reports.output')} loading={isFetching} style={{ marginTop: 16 }}>
        <ReportOutput data={data} />
      </Card>
    </Card>
  )
}
