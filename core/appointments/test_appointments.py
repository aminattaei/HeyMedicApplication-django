import pytest
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from datetime import date, time, timedelta

from appointments.models import TimeSlot, Appointment


@pytest.mark.django_db
class TestTimeSlotModel:
    def test_create_time_slot(self, time_slot):
        assert time_slot.pk is not None
        assert time_slot.is_available is True

    def test_time_slot_str(self, time_slot):
        expected = f"{time_slot.doctor.full_name} - {time_slot.date} {time_slot.start_time}-{time_slot.end_time}"
        assert str(time_slot) == expected

    def test_time_slot_unique_together(self, doctor_profile):
        tomorrow = date.today() + timedelta(days=1)
        TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(9, 0),
            end_time=time(9, 30),
        )
        with pytest.raises(Exception):
            TimeSlot.objects.create(
                doctor=doctor_profile,
                date=tomorrow,
                start_time=time(9, 0),
                end_time=time(9, 30),
            )

    def test_time_slot_ordering(self, doctor_profile):
        tomorrow = date.today() + timedelta(days=1)
        slot1 = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        slot2 = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(9, 0),
            end_time=time(9, 30),
        )
        slots = list(TimeSlot.objects.all())
        assert slots[0] == slot2
        assert slots[1] == slot1


@pytest.mark.django_db
class TestAppointmentModel:
    def test_create_appointment(self, appointment):
        assert appointment.pk is not None
        assert appointment.status == 'pending'

    def test_appointment_str(self, appointment):
        expected = f"{appointment.patient.full_name} -> {appointment.doctor.full_name} (Pending)"
        assert str(appointment) == expected

    def test_appointment_status_choices(self, appointment):
        for status_choice in ['pending', 'confirmed', 'cancelled', 'completed']:
            appointment.status = status_choice
            appointment.save()
            appointment.refresh_from_db()
            assert appointment.status == status_choice

    def test_appointment_ordering(self, patient_profile, doctor_profile, booked_time_slot):
        tomorrow = date.today() + timedelta(days=2)
        slot1 = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(11, 0),
            end_time=time(11, 30),
        )
        slot2 = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=tomorrow,
            start_time=time(12, 0),
            end_time=time(12, 30),
        )
        appt1 = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            time_slot=slot1,
            status='pending',
        )
        appt2 = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            time_slot=slot2,
            status='pending',
        )
        appointments = list(Appointment.objects.all())
        assert appointments[0] == appt2
        assert appointments[1] == appt1


@pytest.mark.django_db
class TestTimeSlotAPI:
    def test_list_time_slots(self, api_client, doctor_user, time_slot):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get('/api/v1/slots/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_time_slot_authenticated(self, api_client, doctor_user, doctor_profile):
        api_client.force_authenticate(user=doctor_user)
        tomorrow = date.today() + timedelta(days=1)
        data = {
            'doctor': doctor_profile.pk,
            'date': tomorrow.isoformat(),
            'start_time': '14:00:00',
            'end_time': '14:30:00',
        }
        response = api_client.post('/api/v1/slots/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_by_doctor(self, api_client, doctor_user, time_slot):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get(f'/api/v1/slots/?doctor_id={time_slot.doctor.pk}')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_by_date(self, api_client, doctor_user, time_slot):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get(f'/api/v1/slots/?date={time_slot.date}')
        assert response.status_code == status.HTTP_200_OK

    def test_filter_available_only(self, api_client, doctor_user, time_slot, booked_time_slot):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get('/api/v1/slots/?available_only=true')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAppointmentAPI:
    def test_list_appointments_as_patient(self, api_client, patient_user, appointment):
        api_client.force_authenticate(user=patient_user)
        response = api_client.get('/api/v1/appointments/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_appointments_as_doctor(self, api_client, doctor_user, appointment):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get('/api/v1/appointments/')
        assert response.status_code == status.HTTP_200_OK

    def test_book_appointment(self, api_client, patient_user, patient_profile, time_slot):
        api_client.force_authenticate(user=patient_user)
        data = {'time_slot_id': time_slot.pk}
        response = api_client.post('/api/v1/appointments/book/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        time_slot.refresh_from_db()
        assert time_slot.is_available is False

    def test_book_already_booked_slot(self, api_client, patient_user, booked_time_slot):
        api_client.force_authenticate(user=patient_user)
        data = {'time_slot_id': booked_time_slot.pk}
        response = api_client.post('/api/v1/appointments/book/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cancel_appointment(self, api_client, patient_user, appointment):
        api_client.force_authenticate(user=patient_user)
        response = api_client.patch(f'/api/v1/appointments/{appointment.pk}/cancel/')
        assert response.status_code == status.HTTP_200_OK
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'

    def test_cancel_completed_appointment(self, api_client, patient_user, completed_appointment):
        api_client.force_authenticate(user=patient_user)
        response = api_client.patch(f'/api/v1/appointments/{completed_appointment.pk}/cancel/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
