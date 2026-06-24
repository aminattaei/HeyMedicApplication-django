from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from payments.models import Payment
from .serializers import (
    PaymentSerializer,
    PaymentInitSerializer,
    PaymentVerifySerializer,
)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for payment operations.

    - Patients can list their payment history.
    - POST /api/v1/payments/init/ to start a payment (returns gateway URL).
    - POST /api/v1/payments/verify/ to handle the gateway callback.
    """

    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            return Payment.objects.select_related(
                'patient', 'appointment', 'appointment__doctor'
            ).filter(patient__user=user)
        return Payment.objects.none()

    @action(detail=False, methods=['post'], url_path='init')
    def init_payment(self, request):
        """
        Initialize a payment for an appointment.
        Returns the payment ID, amount, and a gateway redirect URL.
        TODO: Replace mock gateway with real provider (Zibal / IDPay / Mellat).
        """
        serializer = PaymentInitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from appointments.models import Appointment
        appointment = Appointment.objects.get(id=serializer.validated_data['appointment_id'])
        patient_profile = request.user.patient_profile

        payment = Payment.objects.create(
            appointment=appointment,
            patient=patient_profile,
            amount=appointment.doctor.price,
            status='pending'
        )

        gateway_url = f"/payments/mock-gateway/{payment.id}/"

        return Response({
            "payment_id": payment.id,
            "amount": payment.amount,
            "gateway_url": gateway_url,
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='verify')
    def verify_payment(self, request):
        """
        Verify a payment after the gateway callback.
        On success: marks payment as successful and confirms the appointment.
        """
        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gateway_ref = serializer.validated_data['gateway_ref']
        result_status = serializer.validated_data['status']

        try:
            payment = Payment.objects.select_related('appointment').get(gateway_ref=gateway_ref)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Transaction not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        payment.status = result_status
        if result_status == 'successful':
            payment.paid_at = timezone.now()
            payment.appointment.status = 'confirmed'
            payment.appointment.save()
        payment.save()

        return Response(PaymentSerializer(payment).data)
