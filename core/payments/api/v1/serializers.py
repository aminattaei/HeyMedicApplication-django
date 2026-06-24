from rest_framework import serializers
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """
    Read serializer for payment records.
    Includes denormalized patient and doctor names.
    """

    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.full_name', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'appointment', 'patient', 'patient_name', 'doctor_name',
            'amount', 'status', 'gateway_ref', 'paid_at', 'created_at'
        ]
        read_only_fields = ['status', 'gateway_ref', 'paid_at', 'created_at']


class PaymentInitSerializer(serializers.Serializer):
    """
    Input serializer for initiating a payment.
    Validates that the appointment exists, is pending, and has no prior payment.
    """

    appointment_id = serializers.IntegerField()

    def validate_appointment_id(self, value):
        from appointments.models import Appointment
        try:
            appointment = Appointment.objects.get(id=value, status='pending')
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("Valid appointment not found.")
        if hasattr(appointment, 'payment'):
            raise serializers.ValidationError("This appointment already has a payment.")
        return value


class PaymentVerifySerializer(serializers.Serializer):
    """
    Input serializer for payment verification callback from the gateway.
    """

    gateway_ref = serializers.CharField()
    status = serializers.ChoiceField(choices=['successful', 'failed'])
