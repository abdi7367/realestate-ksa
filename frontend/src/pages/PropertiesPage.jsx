import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography,
  theme,
} from 'antd'
import { PlusOutlined, HomeOutlined } from '@ant-design/icons'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useLocalizedDigits } from '../hooks/useLocalizedDigits'
import { arabicInputNumberProps } from '../utils/arabicNumerals'

function typeTagColor(propertyType) {
  const map = {
    residential: 'green',
    commercial: 'blue',
    industrial: 'orange',
    land: 'default',
  }
  return map[propertyType] || 'default'
}

export function PropertiesPage() {
  const { t } = useTranslation()
  const { isArabic, localizeDigits } = useLocalizedDigits()
  const { token } = theme.useToken()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [page, setPage] = useState(1)
  const [addOpen, setAddOpen] = useState(false)
  const [ownerModalProperty, setOwnerModalProperty] = useState(null)
  const [form] = Form.useForm()

  const canManage = ['admin', 'property_manager'].includes(user?.role)

  const propertyTypeOptions = useMemo(
    () => [
      { value: 'residential', label: t('properties.types.residential') },
      { value: 'commercial', label: t('properties.types.commercial') },
      { value: 'industrial', label: t('properties.types.industrial') },
      { value: 'land', label: t('properties.types.land') },
    ],
    [t],
  )

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['properties', page],
    queryFn: () =>
      api.get('/api/properties/', { params: { page } }).then((r) => r.data),
  })

  const { data: managersData } = useQuery({
    queryKey: ['property-managers-pick'],
    queryFn: () => api.get('/api/auth/users/').then((r) => r.data),
    enabled: addOpen && canManage,
  })

  const managerOptions = useMemo(() => {
    const raw = Array.isArray(managersData) ? managersData : []
    return raw
      .filter(
        (u) =>
          u.role === 'property_manager' ||
          u.role === 'admin' ||
          u.role === 'finance_manager',
      )
      .map((u) => ({
        value: u.id,
        label: `${u.display_name ?? u.username} (${u.role})`,
      }))
  }, [managersData])

  const createMutation = useMutation({
    mutationFn: (body) => api.post('/api/properties/', body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['properties'] })
      setAddOpen(false)
      form.resetFields()
    },
  })

  const results = data?.results ?? data ?? []
  const rows = Array.isArray(results) ? results : []

  const createError = createMutation.error?.response?.data
  const createErrorText =
    (typeof createError === 'string' && createError) ||
    createError?.detail ||
    (createError && JSON.stringify(createError))

  const columns = useMemo(
    () => [
      {
        title: '',
        key: 'owner_btn',
        width: 56,
        align: 'center',
        fixed: 'left',
        render: (_, row) => (
          <Tooltip title={t('properties.ownerDetails')}>
            <Button
              type="primary"
              shape="circle"
              size="small"
              icon={<PlusOutlined />}
              aria-label={t('properties.ownerDetailsAria')}
              onClick={() => setOwnerModalProperty(row)}
            />
          </Tooltip>
        ),
      },
      {
        title: t('properties.ownerId'),
        dataIndex: 'owner_reference',
        key: 'owner_ref',
        width: 100,
        ellipsis: true,
        render: (v) => (v ? localizeDigits(v) : '—'),
      },
      {
        title: t('properties.code'),
        dataIndex: 'property_code',
        key: 'property_code',
        width: 100,
        render: (v) => (v ? localizeDigits(v) : '—'),
      },
      {
        title: t('properties.name'),
        dataIndex: 'name',
        key: 'name',
        ellipsis: true,
        render: (text, row) => (
          <span>
            <Typography.Text strong>
              <Link
                to={`/properties/${row.id}`}
                onClick={(e) => {
                  e.stopPropagation()
                }}
              >
                {text}
              </Link>
            </Typography.Text>
            {row.owner_full_name ? (
              <Typography.Text
                type="secondary"
                style={{ display: 'block', fontSize: 12 }}
              >
                {row.owner_full_name}
              </Typography.Text>
            ) : null}
          </span>
        ),
      },
      {
        title: t('properties.type'),
        dataIndex: 'property_type',
        key: 'property_type',
        width: 130,
        render: (typeVal) => (
          <Tag color={typeTagColor(typeVal)}>
            {typeVal
              ? t(`properties.types.${typeVal}`, {
                  defaultValue: String(typeVal).replace(/_/g, ' '),
                })
              : ''}
          </Tag>
        ),
      },
      { title: t('properties.city'), dataIndex: 'city', key: 'city', width: 110 },
      {
        title: t('properties.district'),
        dataIndex: 'district',
        key: 'district',
        width: 120,
      },
      {
        title: t('properties.location'),
        dataIndex: 'location',
        key: 'location',
        ellipsis: true,
        render: (v) => v || '—',
      },
      {
        title: t('properties.units'),
        dataIndex: 'num_units',
        key: 'num_units',
        width: 72,
        align: 'center',
        render: (v) => localizeDigits(v ?? '—'),
      },
      {
        title: t('properties.vacantOcc'),
        key: 'occ',
        width: 120,
        align: 'center',
        render: (_, row) => (
          <Typography.Text type="secondary">
            <Typography.Text type="success">
              {localizeDigits(String(row.vacant_units ?? 0))}
            </Typography.Text>
            {' / '}
            <Typography.Text>
              {localizeDigits(String(row.occupied_units ?? 0))}
            </Typography.Text>
          </Typography.Text>
        ),
      },
    ],
    [t, localizeDigits],
  )

  const onCreate = (v) => {
    const body = {
      name: v.name,
      property_type: v.property_type,
      city: v.city,
      district: v.district,
      location: v.location || '',
      size_sqm: v.size_sqm,
      num_units: v.num_units ?? 1,
      ownership_status: v.ownership_status || '',
      property_code: v.property_code || null,
    }
    if (v.property_manager_id != null) {
      body.property_manager_id = v.property_manager_id
    }
    body.owner_full_name = v.owner_full_name
    body.owner_national_id = v.owner_national_id
    body.owner_phone = v.owner_phone
    body.owner_email = v.owner_email
    body.owner_bank_iban = v.owner_bank_iban
    body.owner_address = v.owner_address || ''
    createMutation.mutate(body)
  }

  const openAddModal = () => {
    createMutation.reset()
    setAddOpen(true)
  }

  return (
    <div>
      <Card
        variant="borderless"
        style={{
          borderRadius: token.borderRadiusLG,
          boxShadow: token.boxShadowTertiary,
        }}
        styles={{
          header: { borderBottom: `1px solid ${token.colorBorderSecondary}` },
          body: { padding: token.paddingLG },
        }}
        title={
          <Space align="start" size="middle" wrap>
            <div
              style={{
                width: 48,
                height: 48,
                borderRadius: token.borderRadiusLG,
                background: token.colorPrimaryBg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: token.colorPrimary,
                fontSize: 22,
              }}
            >
              <HomeOutlined />
            </div>
            <div style={{ paddingRight: 8 }}>
              <Typography.Title level={3} style={{ margin: 0 }}>
                {t('properties.title')}
              </Typography.Title>
              <Typography.Paragraph
                type="secondary"
                style={{ margin: '4px 0 0', maxWidth: 560, marginBottom: 0 }}
              >
                {t('properties.subtitle')}
              </Typography.Paragraph>
            </div>
          </Space>
        }
        extra={
          canManage ? (
            <Button
              type="primary"
              size="large"
              icon={<PlusOutlined />}
              onClick={openAddModal}
            >
              {t('properties.addProperty')}
            </Button>
          ) : null
        }
      >
        {isError ? (
          <Typography.Text type="danger">
            {error?.message || t('properties.loadError')}
          </Typography.Text>
        ) : rows.length === 0 && !isLoading ? (
          <Empty
            description={t('properties.noProperties')}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            {canManage && (
              <Button type="primary" onClick={() => setAddOpen(true)}>
                {t('properties.addFirst')}
              </Button>
            )}
          </Empty>
        ) : (
          <Table
            rowKey="id"
            loading={isLoading}
            columns={columns}
            dataSource={rows}
            pagination={
              data?.count
                ? {
                    current: page,
                    pageSize: 20,
                    total: data.count,
                    showSizeChanger: false,
                    onChange: (p) => setPage(p),
                    showTotal: (total) =>
                      localizeDigits(t('properties.paginationTotal', { count: total })),
                  }
                : false
            }
            scroll={{ x: 1180 }}
            size="middle"
          />
        )}
      </Card>

      <Modal
        title={t('properties.addModal.title')}
        open={addOpen}
        onCancel={() => {
          setAddOpen(false)
          createMutation.reset()
        }}
        footer={null}
        width={640}
        destroyOnClose
      >
        {createErrorText && (
          <Typography.Paragraph type="danger" style={{ marginBottom: 16 }}>
            {String(createErrorText)}
          </Typography.Paragraph>
        )}
        <Form
          form={form}
          layout="vertical"
          onFinish={onCreate}
          initialValues={{ num_units: 1, property_type: 'residential' }}
        >
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="property_code"
                label={t('properties.addModal.propertyCode')}
                tooltip={t('properties.addModal.propertyCodeHelp')}
              >
                <Input placeholder={t('properties.addModal.phCode')} allowClear />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="property_type"
                label={t('properties.type')}
                rules={[
                  { required: true, message: t('properties.addModal.ruleSelectType') },
                ]}
              >
                <Select options={propertyTypeOptions} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="name"
            label={t('properties.addModal.name')}
            rules={[{ required: true, message: t('properties.addModal.ruleName') }]}
          >
            <Input placeholder={t('properties.addModal.phName')} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="city"
                label={t('properties.addModal.city')}
                rules={[{ required: true, message: t('properties.addModal.ruleCity') }]}
              >
                <Input placeholder={t('properties.addModal.phCity')} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="district"
                label={t('properties.addModal.district')}
                rules={[
                  { required: true, message: t('properties.addModal.ruleDistrict') },
                ]}
              >
                <Input placeholder={t('properties.addModal.phDistrict')} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="location"
            label={t('properties.addModal.locationDetail')}
          >
            <Input placeholder={t('properties.addModal.phLocation')} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="size_sqm"
                label={t('properties.addModal.sizeSqm')}
                rules={[{ required: true, message: t('properties.addModal.ruleSize') }]}
              >
                <InputNumber
                  min={0}
                  step={10}
                  style={{ width: '100%' }}
                  placeholder={t('properties.addModal.phSize')}
                  {...arabicInputNumberProps(isArabic)}
                />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="num_units"
                label={t('properties.addModal.numUnits')}
                rules={[
                  { required: true, message: t('properties.addModal.ruleNumUnits') },
                ]}
              >
                <InputNumber
                  min={1}
                  max={10000}
                  style={{ width: '100%' }}
                  {...arabicInputNumberProps(isArabic)}
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">{t('properties.addModal.ownerSection')}</Divider>
          <Typography.Paragraph type="secondary" style={{ marginTop: -8 }}>
            {t('properties.addModal.ownerIdNote')}
          </Typography.Paragraph>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_full_name"
                label={t('properties.addModal.ownerFullName')}
                rules={[
                  { required: true, message: t('properties.addModal.ruleOwnerName') },
                ]}
              >
                <Input placeholder={t('properties.addModal.phOwnerName')} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_national_id"
                label={t('properties.addModal.ownerNationalId')}
                rules={[
                  { required: true, message: t('properties.addModal.ruleOwnerId') },
                ]}
              >
                <Input placeholder={t('properties.addModal.phNationalId')} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_phone"
                label={t('properties.addModal.ownerPhone')}
                rules={[{ required: true, message: t('properties.addModal.rulePhone') }]}
              >
                <Input placeholder={t('properties.addModal.phPhone')} />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12}>
              <Form.Item
                name="owner_email"
                label={t('properties.addModal.ownerEmail')}
                rules={[
                  { required: true, message: t('properties.addModal.ruleEmail') },
                  { type: 'email', message: t('common.invalidEmail') },
                ]}
              >
                <Input type="email" placeholder={t('properties.addModal.phEmail')} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="owner_bank_iban"
            label={t('properties.addModal.ownerIBAN')}
            rules={[{ required: true, message: t('properties.addModal.ruleIban') }]}
          >
            <Input placeholder={t('properties.addModal.phIban')} />
          </Form.Item>
          <Form.Item
            name="owner_address"
            label={t('properties.addModal.ownerAddress')}
          >
            <Input.TextArea
              rows={2}
              placeholder={t('properties.addModal.phOwnerAddress')}
            />
          </Form.Item>

          <Divider orientation="left">
            {t('properties.addModal.internalSection')}
          </Divider>
          <Form.Item
            name="ownership_status"
            label={t('properties.addModal.ownershipStatus')}
          >
            <Input placeholder={t('properties.addModal.phOwnership')} />
          </Form.Item>
          <Form.Item
            name="property_manager_id"
            label={t('properties.addModal.propertyManager')}
            tooltip={t('properties.addModal.propertyManagerHelp')}
          >
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              placeholder={t('properties.addModal.propertyManagerPlaceholder')}
              options={managerOptions}
            />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={createMutation.isPending}
              >
                {t('properties.addModal.createBtn')}
              </Button>
              <Button onClick={() => setAddOpen(false)}>{t('common.cancel')}</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={
          ownerModalProperty ? (
            <Space direction="vertical" size={0}>
              <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                {t('properties.registeredOwner')}
              </Typography.Text>
              <Typography.Title level={5} style={{ margin: 0 }}>
                {ownerModalProperty.name}
              </Typography.Title>
            </Space>
          ) : null
        }
        open={Boolean(ownerModalProperty)}
        onCancel={() => setOwnerModalProperty(null)}
        footer={
          <Button type="primary" onClick={() => setOwnerModalProperty(null)}>
            {t('properties.close')}
          </Button>
        }
        width={520}
        destroyOnClose
      >
        {ownerModalProperty && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label={t('properties.ownerId')}>
              {ownerModalProperty.owner_reference
                ? localizeDigits(ownerModalProperty.owner_reference)
                : '—'}
            </Descriptions.Item>
            <Descriptions.Item label={t('properties.ownerFullName')}>
              {ownerModalProperty.owner_full_name || '—'}
            </Descriptions.Item>
            <Descriptions.Item label={t('properties.ownerNationalId')}>
              {ownerModalProperty.owner_national_id
                ? localizeDigits(ownerModalProperty.owner_national_id)
                : '—'}
            </Descriptions.Item>
            <Descriptions.Item label={t('properties.ownerPhone')}>
              {ownerModalProperty.owner_phone
                ? localizeDigits(ownerModalProperty.owner_phone)
                : '—'}
            </Descriptions.Item>
            <Descriptions.Item label={t('properties.ownerEmail')}>
              {ownerModalProperty.owner_email || '—'}
            </Descriptions.Item>
            <Descriptions.Item label={t('properties.ownerIBAN')}>
              {ownerModalProperty.owner_bank_iban
                ? localizeDigits(ownerModalProperty.owner_bank_iban)
                : '—'}
            </Descriptions.Item>
            <Descriptions.Item label={t('properties.ownerAddress')}>
              {ownerModalProperty.owner_address?.trim()
                ? localizeDigits(ownerModalProperty.owner_address)
                : '—'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}
