import pytest
from django.utils import timezone
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


@pytest.mark.django_db
class TestPaymentAPI:
    def test_list_payments(self, api_client, patient_user, payment):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_payment(self, api_client, patient_user, patient_profile, appointment):
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': appointment.pk,
            'patient': patient_profile.pk,
            'amount': 500000,
        }
        response = api_client.post('/api/v1/payments/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_init_payment(self, api_client, patient_user, appointment):
        api_client.force_authenticate(user=patient_user)
        data = {'appointment_id': appointment.pk}
        response = api_client.post('/api/v1/payments/init/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_verify_payment(self, api_client, patient_user, payment):
        api_client.force_authenticate(user=patient_user)
        payment.gateway_ref = 'GW_TEST_123'
        payment.save()
        data = {'gateway_ref': 'GW_TEST_123', 'status': 'successful'}
        response = api_client.post('/api/v1/payments/verify/', data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_payment_unauthorized(self, api_client):
        response = api_client.get('/api/v1/payments/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
