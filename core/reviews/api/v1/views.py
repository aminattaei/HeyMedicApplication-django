from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from reviews.models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing doctor reviews.

    - Patients can create reviews for their completed appointments.
    - Anyone can filter reviews by doctor_id query param.
    - Patients see only their own reviews; doctors see reviews about them.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Review.objects.select_related(
            'patient', 'doctor', 'doctor__specialty', 'appointment'
        ).all()

        doctor_id = self.request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)

        if user.role == 'patient':
            queryset = queryset.filter(patient__user=user)
        elif user.role == 'doctor':
            queryset = queryset.filter(doctor__user=user)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        appointment = serializer.validated_data['appointment']
        serializer.save(
            patient=user.patient_profile,
            doctor=appointment.doctor
        )
