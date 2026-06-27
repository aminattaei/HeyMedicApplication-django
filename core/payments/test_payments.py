import pytest
from rest_framework import status
from decimal import Decimal

from payments.models import Payment


@pytest.mark.django_db
class TestPaymentModel:
    def test_create_payment(self, payment):
        assert payment.pk is not None
        assert payment.status == 'pending'

    def test_payment_str(self, payment):
        expected = f"{payment.patient.full_name} - {payment.amount} Toman (Pending)"
        assert str(payment) == expected

    def test_payment_status_choices(self, payment):
        for status_choice in ['pending', 'successful', 'failed', 'refunded']:
            payment.status = status_choice
            payment.save()
            payment.refresh_from_db()
            assert payment.status == status_choice

    def test_payment_ordering(self, patient_profile, appointment):
        payment1 = Payment.objects.create(
            appointment=appointment,
            patient=patient_profile,
            amount=Decimal('500000'),
            status='pending',
        )
        assert payment1.pk is not None

    def test_gateway_ref_blank_by_default(self, payment):
        assert payment.gateway_ref == ''

    def test_paid_at_null_by_default(self, payment):
        assert payment.paid_at is None

    def test_payment_created_at_set(self, payment):
        assert payment.created_at is not None

    def test_patient_sees_own_payments(self, patient_user, payment):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assert payment.patient.user == patient_user


@pytest.mark.django_db
class TestPaymentAPI:
    def test_list_payments(self, api_client, patient_user, payment):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_payments_empty_for_doctor(self, api_client, doctor_user, payment):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_init_payment(self, api_client, patient_user, appointment):
        api_client.force_authenticate(user=patient_user)
        data = {'appointment_id': appointment.pk}
        response = api_client.post('/api/v1/payments/init/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'payment_id' in response.data
        assert 'amount' in response.data
        assert 'gateway_url' in response.data

    def test_init_payment_nonexistent_appointment(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        data = {'appointment_id': 99999}
        response = api_client.post('/api/v1/payments/init/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_payment_successful(self, api_client, patient_user, payment):
        api_client.force_authenticate(user=patient_user)
        payment.gateway_ref = 'GW_TEST_123'
        payment.save()
        data = {'gateway_ref': 'GW_TEST_123', 'status': 'successful'}
        response = api_client.post('/api/v1/payments/verify/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        assert payment.status == 'successful'
        assert payment.paid_at is not None

    def test_verify_payment_failed(self, api_client, patient_user, payment):
        api_client.force_authenticate(user=patient_user)
        payment.gateway_ref = 'GW_TEST_456'
        payment.save()
        data = {'gateway_ref': 'GW_TEST_456', 'status': 'failed'}
        response = api_client.post('/api/v1/payments/verify/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        payment.refresh_from_db()
        assert payment.status == 'failed'
        assert payment.paid_at is None

    def test_verify_nonexistent_gateway_ref(self, api_client, patient_user):
        api_client.force_authenticate(user=patient_user)
        data = {'gateway_ref': 'NONEXISTENT', 'status': 'successful'}
        response = api_client.post('/api/v1/payments/verify/', data, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_successful_payment_confirms_appointment(self, api_client, patient_user, payment):
        api_client.force_authenticate(user=patient_user)
        payment.gateway_ref = 'GW_CONFIRM_TEST'
        payment.save()
        data = {'gateway_ref': 'GW_CONFIRM_TEST', 'status': 'successful'}
        api_client.post('/api/v1/payments/verify/', data, format='json')
        payment.refresh_from_db()
        assert payment.appointment.status == 'confirmed'

    def test_payment_unauthorized(self, api_client):
        response = api_client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_init_payment_unauthorized(self, api_client):
        response = api_client.post('/api/v1/payments/init/', {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
