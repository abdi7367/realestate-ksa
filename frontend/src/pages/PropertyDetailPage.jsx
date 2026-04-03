import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import {
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

function asArray(data) {
  const raw = data?.results ?? data ?? []
  return Array.isArray(raw) ? raw : []
}

function unitTypeOptions(t) {
  return [
    { value: 'apartment', label: t('propertyDetail.unitTypes.apartment') },
    { value: 'office', label: t('propertyDetail.unitTypes.office') },
    { value: 'shop', label: t('propertyDetail.unitTypes.shop') },
    { value: 'villa', label: t('propertyDetail.unitTypes.villa') },
  ]
}

function rentalStatusOptions(t) {
  return [
    { value: 'vacant', label: t('propertyDetail.rentalStatuses.vacant') },
    { value: 'occupied', label: t('propertyDetail.rentalStatuses.occupied') },
    { value: 'maintenance', label: t('propertyDetail.rentalStatuses.maintenance') },
    { value: 'reserved', label: t('propertyDetail.rentalStatuses.reserved') },
  ]
}

export function PropertyDetailPage() {
  const { t } = useTranslation()
  const { id } = useParams()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const canManageUnits = ['admin', 'property_manager'].includes(user?.role)
  const [unitModal, setUnitModal] = useState({ open: false, unit: null })
  const [unitForm] = Form.useForm()

  const { data: property, isLoading: propertyLoading } = useQuery({
    queryKey: ['property', id],
    queryFn: () => api.get(`/api/properties/${id}/`).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: unitsData, isLoading: unitsLoading } = useQuery({
    queryKey: ['property', id, 'units'],
    queryFn: () =>
      api.get('/api/units/', { params: { property: id, page_size: 500 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: contractsData, isLoading: contractsLoading } = useQuery({
    queryKey: ['property', id, 'contracts'],
    queryFn: () => api.get('/api/contracts/', { params: { property: id, page_size: 200 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: debtsData, isLoading: debtsLoading } = useQuery({
    queryKey: ['property', id, 'debts'],
    queryFn: () => api.get('/api/debts/', { params: { property: id, page_size: 200 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const { data: txData, isLoading: txLoading } = useQuery({
    queryKey: ['property', id, 'transactions'],
    queryFn: () =>
      api.get('/api/transactions/', { params: { property: id, page_size: 200 } }).then((r) => r.data),
    enabled: Boolean(id),
  })

  const units = asArray(unitsData)
  const contracts = asArray(contractsData)
  const debts = asArray(debtsData)
  const transactions = asArray(txData)

  const upsertUnit = useMutation({
    mutationFn: async (values) => {
      if (!id) throw new Error('Missing property id')
      const payload = {
        property: Number(id),
        unit_number: String(values.unit_number || '').trim(),
        floor: Number(values.floor),
        size_sqm: String(values.size_sqm),
        unit_type: values.unit_type,
        rental_status: values.rental_status,
        monthly_rent: String(values.monthly_rent ?? 0),
        notes: values.notes || '',
      }
      if (unitModal.unit?.id) {
        return api.patch(`/api/units/${unitModal.unit.id}/`, payload)
      }
      return api.post('/api/units/', payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['property', id, 'units'] })
      queryClient.invalidateQueries({ queryKey: ['property', id] })
      setUnitModal({ open: false, unit: null })
      unitForm.resetFields()
    },
  })

  const openCreateUnit = () => {
    setUnitModal({ open: true, unit: null })
    unitForm.setFieldsValue({
      unit_number: '',
      floor: 1,
      size_sqm: 0,
      unit_type: 'apartment',
      rental_status: 'vacant',
      monthly_rent: 0,
      notes: '',
    })
  }

  const openEditUnit = (unit) => {
    setUnitModal({ open: true, unit })
    unitForm.setFieldsValue({
      unit_number: unit.unit_number,
      floor: unit.floor,
      size_sqm: unit.size_sqm,
      unit_type: unit.unit_type,
      rental_status: unit.rental_status,
      monthly_rent: unit.monthly_rent,
      notes: unit.notes,
    })
  }

  const closeUnitModal = () => {
    setUnitModal({ open: false, unit: null })
    unitForm.resetFields()
  }

  const totals = useMemo(() => {
    const activeContracts = contracts.filter((c) => c.status === 'active').length
    const occupied = units.filter((u) => u.rental_status === 'occupied').length
    const vacant = units.filter((u) => u.rental_status === 'vacant').length
    const debtTotal = debts.reduce((sum, d) => sum + Number(d.total_amount || 0), 0)
    const txIncome = transactions
      .filter((tx) => tx.transaction_type === 'income')
      .reduce((sum, tx) => sum + Number(tx.amount || 0), 0)
    const txExpense = transactions
      .filter((tx) => tx.transaction_type === 'expense')
      .reduce((sum, tx) => sum + Number(tx.amount || 0), 0)
    return { activeContracts, occupied, vacant, debtTotal, txIncome, txExpense }
  }, [contracts, units, debts, transactions])

  if (!id) return <Empty description={t('common.noData')} />

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Typography.Text type="secondary">
          <Link to="/properties">{t('propertyDetail.breadcrumb')}</Link> / {t('propertyDetail.detail')}
        </Typography.Text>
        <Typography.Title level={3} style={{ margin: '6px 0 0' }}>
          {propertyLoading ? t('common.loading') : property?.name || `Property #${id}`}
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {property?.city || '—'} · {property?.district || '—'} · {property?.location || 'No location detail'}
        </Typography.Paragraph>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic title={t('propertyDetail.unitsOccVacant')} value={`${totals.occupied} / ${totals.vacant}`} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic title={t('propertyDetail.activeContracts')} value={totals.activeContracts} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic title={t('propertyDetail.totalDebts')} value={totals.debtTotal.toFixed(2)} />
          </Card>
        </Col>
      </Row>

      <Card
        title={t('propertyDetail.unitsTitle')}
        extra={
          canManageUnits ? (
            <Button type="primary" onClick={openCreateUnit}>
              {t('propertyDetail.addUnit')}
            </Button>
          ) : null
        }
      >
        <Table
          rowKey="id"
          loading={unitsLoading}
          dataSource={units}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: t('propertyDetail.unitNumber'), dataIndex: 'unit_number', width: 100 },
            { title: t('propertyDetail.unitType'), dataIndex: 'unit_type', width: 130 },
            { title: t('propertyDetail.floor'), dataIndex: 'floor', width: 90 },
            { title: t('propertyDetail.sizeSqm'), dataIndex: 'size_sqm', width: 110 },
            { title: t('propertyDetail.monthlyRent'), dataIndex: 'monthly_rent', width: 120 },
            {
              title: t('common.status'),
              dataIndex: 'rental_status',
              render: (s) => <Tag color={s === 'occupied' ? 'orange' : 'green'}>{s}</Tag>,
            },
            {
              title: t('propertyDetail.activeTenant'),
              key: 'tenant',
              render: (_, row) => row.active_tenant?.name || '—',
            },
            ...(canManageUnits
              ? [
                  {
                    title: t('common.actions'),
                    key: 'actions',
                    width: 120,
                    render: (_, row) => (
                      <Button size="small" onClick={() => openEditUnit(row)}>
                        {t('common.edit')}
                      </Button>
                    ),
                  },
                ]
              : []),
          ]}
        />
      </Card>

      <Card title={`${t('propertyDetail.contractsTitle')} (${contracts.length})`}>
        <Table
          rowKey="id"
          loading={contractsLoading}
          dataSource={contracts}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: t('common.id'), dataIndex: 'id', width: 70 },
            { title: t('propertyDetail.unitNumber'), dataIndex: 'unit_number', width: 90 },
            { title: t('contracts.tenant'), dataIndex: 'tenant_name', width: 220 },
            { title: t('propertyDetail.monthlyRent'), dataIndex: 'monthly_rent', width: 120 },
            { title: t('common.start'), dataIndex: 'start_date', width: 120 },
            { title: t('common.end'), dataIndex: 'end_date', width: 120 },
            {
              title: t('common.status'),
              dataIndex: 'status',
              render: (s) => <Tag color={s === 'active' ? 'green' : 'default'}>{s}</Tag>,
            },
          ]}
        />
      </Card>

      <Card title={`${t('propertyDetail.debtsTitle')} (${debts.length})`}>
        <Table
          rowKey="id"
          loading={debtsLoading}
          dataSource={debts}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: t('common.type'), dataIndex: 'debt_type', width: 150 },
            { title: t('debts.creditor'), dataIndex: 'creditor_name' },
            { title: t('debts.total'), dataIndex: 'total_amount', width: 140 },
            { title: t('debts.remaining'), dataIndex: 'remaining_balance', width: 140 },
            { title: t('common.start'), dataIndex: 'start_date', width: 120 },
            { title: t('common.end'), dataIndex: 'end_date', width: 120 },
          ]}
        />
      </Card>

      <Card title={`${t('propertyDetail.txTitle')} (${transactions.length})`}>
        <Typography.Paragraph type="secondary">
          Income: {totals.txIncome.toFixed(2)} SAR · Expense: {totals.txExpense.toFixed(2)} SAR
        </Typography.Paragraph>
        <Table
          rowKey="id"
          loading={txLoading}
          dataSource={transactions}
          pagination={false}
          scroll={{ x: true }}
          columns={[
            { title: t('common.date'), dataIndex: 'date', width: 120 },
            {
              title: t('common.type'),
              dataIndex: 'transaction_type',
              width: 110,
              render: (txType) => <Tag color={txType === 'income' ? 'green' : 'orange'}>{txType}</Tag>,
            },
            { title: t('finance.category'), dataIndex: 'category', width: 150 },
            { title: t('common.amount'), dataIndex: 'amount', width: 120 },
            { title: t('common.description'), dataIndex: 'description' },
            { title: t('common.reference'), dataIndex: 'reference', width: 150 },
          ]}
        />
      </Card>

      <Modal
        title={
          unitModal.unit?.id
            ? `${t('propertyDetail.editUnit')} ${unitModal.unit.unit_number}`
            : t('propertyDetail.addUnit')
        }
        open={unitModal.open}
        onCancel={closeUnitModal}
        footer={null}
        destroyOnClose
      >
        <Form
          form={unitForm}
          layout="vertical"
          onFinish={(values) => upsertUnit.mutate(values)}
        >
          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="unit_number"
                label={t('propertyDetail.unitNumber')}
                rules={[{ required: true, message: t('common.required') }]}
              >
                <Input placeholder="e.g. 101, A-02, G01" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="floor"
                label={t('propertyDetail.floor')}
                rules={[{ required: true, message: t('common.required') }]}
              >
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="unit_type"
                label={t('propertyDetail.unitType')}
                rules={[{ required: true, message: t('common.required') }]}
              >
                <Select options={unitTypeOptions(t)} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="rental_status"
                label={t('propertyDetail.rentalStatus')}
                rules={[{ required: true, message: t('common.required') }]}
              >
                <Select options={rentalStatusOptions(t)} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="size_sqm"
                label={t('propertyDetail.sizeSqm')}
                rules={[{ required: true, message: t('common.required') }]}
              >
                <InputNumber min={0} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="monthly_rent"
                label={t('propertyDetail.monthlyRentSAR')}
                rules={[{ required: true, message: t('common.required') }]}
              >
                <InputNumber min={0} step={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label={t('propertyDetail.noteOptional')}>
            <Input.TextArea rows={3} />
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit" loading={upsertUnit.isPending}>
              {t('common.save')}
            </Button>
            <Button onClick={closeUnitModal}>{t('common.cancel')}</Button>
          </Space>
        </Form>
      </Modal>
    </Space>
  )
}
