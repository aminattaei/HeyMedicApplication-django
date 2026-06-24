from rest_framework import serializers
from appointments.models import TimeSlot, Appointment


class TimeSlotSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for time slots.
    Includes denormalized doctor name and specialty for convenience.
    """

    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    specialty = serializers.CharField(source='doctor.specialty.title', read_only=True)

    class Meta:
        model = TimeSlot
        fields = ['id', 'doctor', 'doctor_name', 'specialty', 'date', 'start_time', 'end_time', 'is_available']


class TimeSlotCreateSerializer(serializers.ModelSerializer):
    """Serializer used when doctors create new time slots."""

    class Meta:
        model = TimeSlot
        fields = ['id', 'doctor', 'date', 'start_time', 'end_time']


class AppointmentSerializer(serializers.ModelSerializer):
    """
    Full appointment serializer with denormalized patient/doctor names
    and time slot details for read operations.
    """

    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    doctor_specialty = serializers.CharField(source='doctor.specialty.title', read_only=True)
    slot_date = serializers.DateField(source='time_slot.date', read_only=True)
    slot_start = serializers.TimeField(source='time_slot.start_time', read_only=True)
    slot_end = serializers.TimeField(source='time_slot.end_time', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'doctor_specialty', 'time_slot', 'slot_date', 'slot_start',
            'slot_end', 'status', 'notes', 'created_at'
        ]
        read_only_fields = ['status', 'created_at']


class AppointmentBookSerializer(serializers.Serializer):
    """
    Input serializer for the book action.
    Validates that the requested time slot exists and is available.
    """

    time_slot_id = serializers.IntegerField()

    def validate_time_slot_id(self, value):
        try:
            slot = TimeSlot.objects.get(id=value, is_available=True)
        except TimeSlot.DoesNotExist:
            raise serializers.ValidationError("This time slot is not available.")
        return value
