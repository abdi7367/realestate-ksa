import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  DatePicker,
  Descriptions,
  Form,
  Input,
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
import { REPORT_OPTIONS, fetchReport, downloadCashFlowPdf } from '../api/reports'

function reportPropertyContextItems(data) {
  if (!data) return []
  const f = data.filters
  if (f && typeof f === 'object' && f.property_name) {
    return [
      {
        key: 'ctx-property',
        label: 'Property',
        children:
          f.property_id != null && f.property_id !== ''
            ? `${f.property_name} (ID ${f.property_id})`
            : String(f.property_name),
      },
    ]
  }
  if (f && typeof f === 'object' && f.property_id != null && f.property_id !== '') {
    return [
      {
        key: 'ctx-property',
        label: 'Property',
        children: `ID ${f.property_id}`,
      },
    ]
  }
  if (data.property_name) {
    return [
      {
        key: 'ctx-property',
        label: 'Property',
        children:
          data.property_id != null && data.property_id !== ''
            ? `${data.property_name} (ID ${data.property_id})`
            : String(data.property_name),
      },
    ]
  }
  if (data.property_id != null && data.property_id !== '') {
    return [
      {
        key: 'ctx-property',
        label: 'Property',
        children: `ID ${data.property_id}`,
      },
    ]
  }
  return []
}

function resultsTableColumns(sampleRow) {
  if (!sampleRow || typeof sampleRow !== 'object') return []
  return Object.keys(sampleRow).map((key) => ({
    title: key.replace(/_/g, ' '),
    dataIndex: key,
    key,
    ellipsis: true,
    render: (v) =>
      v === null || v === undefined || v === '' ? '—' : String(v),
  }))
}

function ReportOutput({ data }) {
  if (!data) return null

  if (Array.isArray(data.results) && data.results.length > 0) {
    return (
      <Table
        rowKey={(_, i) => String(i)}
        size="small"
        scroll={{ x: true }}
        columns={resultsTableColumns(data.results[0])}
        dataSource={data.results}
        pagination={{ pageSize: 25, showSizeChanger: true }}
      />
    )
  }

  if (Array.isArray(data.results) && data.results.length === 0) {
    return (
      <Typography.Text type="secondary">No rows in this report.</Typography.Text>
    )
  }

  if (Array.isArray(data.by_category) && data.by_category.length > 0) {
    const propCtx = reportPropertyContextItems(data)
    const periodItem =
      data.date_from && data.date_to
        ? [
            {
              key: 'ctx-period',
              label: 'Period',
              children: `${data.date_from} → ${data.date_to}`,
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
          rowKey={(_, i) => String(i)}
          size="small"
          columns={[
            { title: 'Category', dataIndex: 'category', key: 'category' },
            { title: 'Total', dataIndex: 'total', key: 'total', render: (v) => String(v) },
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
      label: `${owner.owner_name} (${owner.owner_id})`,
      children: (
        <div>
          <Typography.Text type="secondary">
            {owner.ownership_type} · {owner.properties?.length ?? 0} properties
          </Typography.Text>
          <Table
            style={{ marginTop: 8 }}
            size="small"
            rowKey={(r) => `${r.property_id}-${r.property_name}`}
            pagination={false}
            dataSource={owner.properties || []}
            columns={[
              { title: 'Property', dataIndex: 'property_name', key: 'pn' },
              { title: 'City', dataIndex: 'property_city', key: 'pc' },
              {
                title: 'Ownership %',
                dataIndex: 'ownership_percentage',
                key: 'op',
              },
              {
                title: 'Mgmt fee %',
                dataIndex: 'management_fee_percentage',
                key: 'mf',
              },
              {
                title: 'Agreement',
                dataIndex: 'has_management_agreement',
                key: 'ha',
                render: (v) => (v ? 'Yes' : 'No'),
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

  const ctx = reportPropertyContextItems(data)
  const entries = Object.entries(data).filter(
    ([k]) => k !== 'filters' && !Array.isArray(data[k]),
  )
  const items = entries.map(([k, v]) => ({
    key: k,
    label: k.replace(/_/g, ' '),
    children:
      typeof v === 'object' && v !== null ? JSON.stringify(v) : String(v),
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
      <Card size="small" title="Cash Flow Snapshot" style={{ marginBottom: 16 }}>
        <div style={{ height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
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
          <Card size="small" title="Category Distribution">
            <div style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card size="small" title="Share by Category">
            <div style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={chartData} dataKey="total" nameKey="name" outerRadius={92} label>
                    {chartData.map((_, idx) => (
                      <Cell key={`pie-${idx}`} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>
    )
  }

  if (reportId === 'debt_repayment' && Array.isArray(data.results)) {
    const chartData = data.results.map((r) => ({
      name: r.property_name,
      paid: toNum(r.paid_amount),
      remaining: toNum(r.remaining_balance),
    }))
    return (
      <Card size="small" title="Debt Repayment Progress" style={{ marginBottom: 16 }}>
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ left: 30, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={150} />
              <Tooltip />
              <Legend />
              <Bar dataKey="paid" stackId="a" fill="#16a34a" />
              <Bar dataKey="remaining" stackId="a" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    )
  }

  return null
}

export function ReportsPage() {
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
      const blob = await downloadCashFlowPdf(submitted.params)
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

  const needsYear = ['property_income', 'property_profitability'].includes(
    reportId,
  )

  return (
    <Card bordered={false}>
      <Typography.Title level={4} style={{ marginTop: 0 }}>
        Reports
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Step 1: browse API-backed reports. Pick a report, set filters, then run.
      </Typography.Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          report_id: 'outstanding_balances',
          range: [dayjs().subtract(12, 'month'), dayjs()],
        }}
        style={{ maxWidth: 720 }}
      >
        <Form.Item
          name="report_id"
          label="Report"
          rules={[{ required: true, message: 'Choose a report' }]}
        >
          <Select options={REPORT_OPTIONS} showSearch optionFilterProp="label" />
        </Form.Item>

        <Row gutter={16}>
          {needsRange && (
            <Col xs={24} md={12}>
              <Form.Item name="range" label="Date range">
                <DatePicker.RangePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          )}
          {needsYear && (
            <>
              <Col xs={24} md={6}>
                <Form.Item name="year" label="Year (optional)">
                  <InputNumber min={2000} max={2100} style={{ width: '100%' }} placeholder="e.g. 2026" />
                </Form.Item>
              </Col>
              <Col xs={24} md={6}>
                <Form.Item name="month" label="Month 1–12 (optional)">
                  <InputNumber min={1} max={12} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </>
          )}
          <Col xs={24} md={12}>
            <Form.Item name="property_id" label="Property (optional)">
              <Select
                allowClear
                showSearch
                optionFilterProp="label"
                placeholder="All properties"
                options={propertyOptions}
              />
            </Form.Item>
          </Col>
          {reportId === 'contracts' && (
            <Col xs={24} md={6}>
              <Form.Item name="status" label="Status">
                <Select
                  allowClear
                  options={[
                    { value: 'active', label: 'Active' },
                    { value: 'expired', label: 'Expired' },
                    { value: 'terminated', label: 'Terminated' },
                  ]}
                />
              </Form.Item>
            </Col>
          )}
          {reportId === 'vouchers' && (
            <Col xs={24} md={12}>
              <Form.Item name="approval_status" label="Approval status">
                <Select
                  allowClear
                  options={[
                    { value: 'draft', label: 'Draft' },
                    { value: 'pending_accountant', label: 'Pending accountant' },
                    { value: 'pending_finance', label: 'Pending finance' },
                    { value: 'pending_admin', label: 'Pending admin' },
                    { value: 'approved', label: 'Approved' },
                    { value: 'rejected', label: 'Rejected' },
                  ]}
                />
              </Form.Item>
            </Col>
          )}
        </Row>

        {reportId === 'ownership' && (
          <Form.Item name="ownership_type" label="Ownership type">
            <Select
              allowClear
              options={[
                { value: 'personal', label: 'Personal' },
                { value: 'third_party', label: 'Third party' },
              ]}
            />
          </Form.Item>
        )}

        {(reportId === 'tenant_payments' || reportId === 'contracts') && (
          <Row gutter={16}>
            {reportId === 'tenant_payments' && (
              <Col xs={24} md={8}>
                <Form.Item name="tenant_id" label="Tenant user ID">
                  <Input placeholder="Numeric user id" />
                </Form.Item>
              </Col>
            )}
            <Col xs={24} md={8}>
              <Form.Item name="limit" label="Row limit">
                <InputNumber min={1} max={2000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        )}

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">
              Run report
            </Button>
            <Button
              type="button"
              disabled={!submitted?.reportId || submitted?.reportId !== 'cash_flow'}
              onClick={downloadPdf}
            >
              Download PDF
            </Button>
            <Button type="button" disabled={!submitted?.reportId} onClick={() => refetch()}>
              Refresh
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

      <Card size="small" title="Output" loading={isFetching} style={{ marginTop: 16 }}>
        <ReportOutput data={data} />
      </Card>
    </Card>
  )
}
