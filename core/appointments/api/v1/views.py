from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from appointments.models import TimeSlot, Appointment
from .serializers import (
    TimeSlotSerializer,
    TimeSlotCreateSerializer,
    AppointmentSerializer,
    AppointmentBookSerializer,
)


class TimeSlotViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing doctor time slots.

    Supports filtering by doctor_id, date, and available_only query params.
    Doctors can create/update their own slots; patients can only list them.
    """

    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = TimeSlot.objects.select_related('doctor', 'doctor__specialty').all()
        doctor_id = self.request.query_params.get('doctor_id')
        date = self.request.query_params.get('date')
        available_only = self.request.query_params.get('available_only')

        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if date:
            queryset = queryset.filter(date=date)
        if available_only == 'true':
            queryset = queryset.filter(is_available=True)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return TimeSlotCreateSerializer
        return TimeSlotSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing appointments.

    - Doctors see their own scheduled appointments.
    - Patients see their own booked appointments.
    - Patients can book via POST /api/v1/appointments/book/
    - Either party can cancel via PATCH /api/v1/appointments/{id}/cancel/
    """

    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base_qs = Appointment.objects.select_related(
            'patient', 'doctor', 'doctor__specialty', 'time_slot'
        )
        if user.role == 'doctor':
            return base_qs.filter(doctor__user=user)
        elif user.role == 'patient':
            return base_qs.filter(patient__user=user)
        return Appointment.objects.none()

    @action(detail=False, methods=['post'], url_path='book')
    def book(self, request):
        """
        Book an available time slot for the authenticated patient.
        Uses select_for_update to prevent race conditions (double booking).
        """
        serializer = AppointmentBookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        time_slot_id = serializer.validated_data['time_slot_id']

        with transaction.atomic():
            slot = TimeSlot.objects.select_for_update().get(id=time_slot_id)

            if not slot.is_available:
                return Response(
                    {"detail": "This time slot has already been booked."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                patient_profile = request.user.patient_profile
            except Exception:
                return Response(
                    {"detail": "Patient profile not found."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            appointment = Appointment.objects.create(
                patient=patient_profile,
                doctor=slot.doctor,
                time_slot=slot,
                status='pending'
            )
            slot.is_available = False
            slot.save()

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        Cancel an appointment. Only pending or confirmed appointments can be cancelled.
        The associated time slot is released back to available.
        """
        appointment = self.get_object()

        if appointment.status not in ('pending', 'confirmed'):
            return Response(
                {"detail": "This appointment cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            appointment.status = 'cancelled'
            appointment.save()
            appointment.time_slot.is_available = True
            appointment.time_slot.save()

        return Response(AppointmentSerializer(appointment).data)
