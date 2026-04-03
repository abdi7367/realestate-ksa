from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APITestCase

from properties.models import Property, PropertyUnit

from .models import Contract, Tenant
from .services import ContractService, VAT_RATE

User = get_user_model()


def _property_and_vacant_unit():
    prop = Property.objects.create(
        name='Test Tower',
        property_type='residential',
        city='Riyadh',
        district='Olaya',
        size_sqm=Decimal('5000.00'),
        num_units=10,
    )
    unit = PropertyUnit.objects.create(
        property=prop,
        unit_number='101',
        floor=1,
        size_sqm=Decimal('120.00'),
        unit_type='apartment',
        rental_status='vacant',
    )
    return prop, unit


class TenantModelTests(TestCase):
    def test_tenant_reference_assigned_after_save(self):
        t = Tenant.objects.create(
            full_name='Ahmed Ali',
            national_id='1234567890',
        )
        t.refresh_from_db()
        self.assertTrue(t.tenant_reference)
        self.assertRegex(t.tenant_reference, r'^T-\d{6}$')


class ContractServiceTests(TestCase):
    def setUp(self):
        self.pm = User.objects.create_user(
            username='pm_test',
            password='pass12345',
            role='property_manager',
        )
        _, self.unit = _property_and_vacant_unit()
        self.tenant = Tenant.objects.create(
            full_name='Sara Khan',
            national_id='9988776655',
        )

    def test_create_contract_marks_unit_occupied_and_sets_totals(self):
        start = date(2026, 1, 1)
        rent = Decimal('5000.00')
        months = 12
        c = ContractService.create_contract(
            property_unit=self.unit,
            tenant=self.tenant,
            monthly_rent=rent,
            start_date=start,
            duration_months=months,
            created_by=self.pm,
        )
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.rental_status, 'occupied')
        self.assertEqual(c.tenant_id, self.tenant.id)
        self.assertEqual(c.status, 'active')
        expected_total = rent * months
        self.assertEqual(c.total_value, expected_total)
        self.assertEqual(c.vat_amount, (expected_total * VAT_RATE).quantize(Decimal('0.01')))
        self.assertEqual(c.total_value_with_vat, expected_total + c.vat_amount)

    def test_create_contract_rejects_non_vacant_unit(self):
        self.unit.rental_status = 'occupied'
        self.unit.save(update_fields=['rental_status'])
        with self.assertRaises(ValidationError):
            ContractService.create_contract(
                property_unit=self.unit,
                tenant=self.tenant,
                monthly_rent=Decimal('3000.00'),
                start_date=date(2026, 2, 1),
                duration_months=6,
                created_by=self.pm,
            )

    def test_create_contract_rejects_second_active_on_same_unit(self):
        ContractService.create_contract(
            property_unit=self.unit,
            tenant=self.tenant,
            monthly_rent=Decimal('4000.00'),
            start_date=date(2026, 3, 1),
            duration_months=12,
            created_by=self.pm,
        )
        other = Tenant.objects.create(full_name='Other', national_id='1111111111')
        with self.assertRaises(ValidationError):
            ContractService.create_contract(
                property_unit=self.unit,
                tenant=other,
                monthly_rent=Decimal('4000.00'),
                start_date=date(2026, 3, 1),
                duration_months=12,
                created_by=self.pm,
            )

    def test_terminate_contract_frees_unit(self):
        c = ContractService.create_contract(
            property_unit=self.unit,
            tenant=self.tenant,
            monthly_rent=Decimal('3500.00'),
            start_date=date(2026, 4, 1),
            duration_months=12,
            created_by=self.pm,
        )
        ContractService.terminate_contract(c, terminated_by=self.pm, reason='move out')
        c.refresh_from_db()
        self.unit.refresh_from_db()
        self.assertEqual(c.status, 'terminated')
        self.assertEqual(self.unit.rental_status, 'vacant')


class ContractCreateAPITests(APITestCase):
    """POST /api/contracts/ with tenant_data (JWT-style auth via force_authenticate)."""

    def setUp(self):
        self.pm = User.objects.create_user(
            username='api_pm',
            password='testpass123',
            role='property_manager',
        )
        _, self.unit = _property_and_vacant_unit()

    def test_create_contract_201_with_tenant_data(self):
        self.client.force_authenticate(user=self.pm)
        payload = {
            'unit': self.unit.id,
            'tenant_data': {
                'full_name': 'API Tenant',
                'national_id': '1122334455',
                'phone': '+966500000000',
                'email': 'tenant@example.com',
                'nationality': 'SA',
                'date_of_birth': '1990-05-15',
            },
            'monthly_rent': '4000.00',
            'start_date': '2026-06-01',
            'duration_months': 12,
            'security_deposit': '0',
            'payment_schedule': 'monthly',
        }
        r = self.client.post('/api/contracts/', payload, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(r.data['success'])
        data = r.data['data']
        self.assertEqual(data['tenant']['full_name'], 'API Tenant')
        self.assertEqual(data['tenant']['national_id'], '1122334455')
        self.assertRegex(data['tenant']['tenant_reference'], r'^T-\d{6}$')
        self.assertEqual(data['tenant_name'], 'API Tenant')
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.rental_status, 'occupied')
        self.assertEqual(Tenant.objects.filter(national_id='1122334455').count(), 1)

    def test_create_contract_reuses_existing_tenant_by_national_id(self):
        self.client.force_authenticate(user=self.pm)
        existing = Tenant.objects.create(
            full_name='Existing Tenant',
            national_id='5566778899',
            phone='+966500111222',
        )

        payload = {
            'unit': self.unit.id,
            'tenant_data': {
                'full_name': 'Updated Existing Tenant',
                'national_id': '5566778899',
                'phone': '+966500333444',
                'email': 'existing.tenant@example.com',
                'nationality': 'SA',
            },
            'monthly_rent': '4000.00',
            'start_date': '2026-06-01',
            'duration_months': 12,
        }
        r = self.client.post('/api/contracts/', payload, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(Tenant.objects.filter(national_id='5566778899').count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.full_name, 'Updated Existing Tenant')
        self.assertEqual(existing.phone, '+966500333444')

    def test_create_contract_400_when_tenant_data_missing(self):
        self.client.force_authenticate(user=self.pm)
        payload = {
            'unit': self.unit.id,
            'monthly_rent': '4000.00',
            'start_date': '2026-06-01',
            'duration_months': 12,
        }
        r = self.client.post('/api/contracts/', payload, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.data.get('success', True))

    def test_create_contract_403_for_accountant(self):
        accountant = User.objects.create_user(
            username='api_acct',
            password='testpass123',
            role='accountant',
        )
        self.client.force_authenticate(user=accountant)
        payload = {
            'unit': self.unit.id,
            'tenant_data': {
                'full_name': 'Should Fail',
                'national_id': '9988776655',
            },
            'monthly_rent': '4000.00',
            'start_date': '2026-06-01',
            'duration_months': 12,
        }
        r = self.client.post('/api/contracts/', payload, format='json')
        self.assertEqual(r.status_code, 403)

    def test_create_contract_401_when_unauthenticated(self):
        payload = {
            'unit': self.unit.id,
            'tenant_data': {'full_name': 'X', 'national_id': '1'},
            'monthly_rent': '4000.00',
            'start_date': '2026-06-01',
            'duration_months': 12,
        }
        r = self.client.post('/api/contracts/', payload, format='json')
        self.assertEqual(r.status_code, 401)


class TenantReadAPITests(APITestCase):
    def setUp(self):
        self.pm = User.objects.create_user(
            username='tenant_api_pm',
            password='testpass123',
            role='property_manager',
        )
        Tenant.objects.create(full_name='Ali Hassan', national_id='1000000001', phone='+966500000001')
        Tenant.objects.create(full_name='Noura Salem', national_id='1000000002', phone='+966500000002')

    def test_list_tenants_with_search(self):
        self.client.force_authenticate(user=self.pm)
        r = self.client.get('/api/tenants/?search=Noura')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertGreaterEqual(r.data.get('count', 0), 1)
        names = [item['full_name'] for item in r.data.get('results', [])]
        self.assertIn('Noura Salem', names)


class ContractCreateDuplicateTenantTests(APITestCase):
    """Regression: duplicate national_id rows must not crash contract creation."""

    def setUp(self):
        self.pm = User.objects.create_user(
            username='dup_pm',
            password='testpass123',
            role='property_manager',
        )
        _, self.unit = _property_and_vacant_unit()
        Tenant.objects.create(full_name='Dup A', national_id='DUPDUP001')
        Tenant.objects.create(full_name='Dup B', national_id='DUPDUP001')

    def test_create_contract_survives_duplicate_national_id(self):
        self.client.force_authenticate(user=self.pm)
        payload = {
            'unit': self.unit.id,
            'tenant_data': {
                'full_name': 'Dup A Updated',
                'national_id': 'DUPDUP001',
            },
            'monthly_rent': '3000.00',
            'start_date': '2026-06-01',
            'duration_months': 12,
        }
        r = self.client.post('/api/contracts/', payload, format='json')
        self.assertIn(r.status_code, (200, 201), r.content)
        self.assertEqual(Tenant.objects.filter(national_id='DUPDUP001').count(), 2)
