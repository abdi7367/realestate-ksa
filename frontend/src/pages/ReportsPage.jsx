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
  Row,
  Select,
  Space,
  Table,
  Typography,
} from 'antd'
import dayjs from 'dayjs'
import { api } from '../api/client'
import { REPORT_OPTIONS, fetchReport } from '../api/reports'

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
    return (
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

  const entries = Object.entries(data).filter(
    ([k]) => k !== 'filters' && !Array.isArray(data[k]),
  )
  const items = entries.map(([k, v]) => ({
    key: k,
    label: k.replace(/_/g, ' '),
    children:
      typeof v === 'object' && v !== null ? JSON.stringify(v) : String(v),
  }))
  return <Descriptions bordered size="small" column={1} items={items} />
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
          range: [dayjs().startOf('month'), dayjs()],
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
            <Button disabled={!submitted?.reportId} onClick={() => refetch()}>
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

      <Card size="small" title="Output" loading={isFetching} style={{ marginTop: 16 }}>
        <ReportOutput data={data} />
      </Card>
    </Card>
  )
}
