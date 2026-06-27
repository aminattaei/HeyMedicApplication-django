from rest_framework import serializers
from reviews.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for patient reviews.
    Enforces:
        - Rating must be between 1 and 5.
        - Appointment must be completed.
        - Each appointment can only be reviewed once.
    """

    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'appointment', 'patient', 'patient_name',
            'doctor', 'doctor_name', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['created_at', 'patient', 'doctor']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_appointment(self, value):
        if Review.objects.filter(appointment=value).exists():
            raise serializers.ValidationError("This appointment has already been reviewed.")
        if value.status != 'completed':
            raise serializers.ValidationError("Only completed appointments can be reviewed.")
        return value

    def validate_appointment(self, value):
        if hasattr(value, 'review'):
            raise serializers.ValidationError("This appointment has already been reviewed.")
        if value.status != 'completed':
            raise serializers.ValidationError("Only completed appointments can be reviewed.")
        return value
