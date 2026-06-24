import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from accounts.models import PatientProfile, DoctorProfile, Specialty
from appointments.models import TimeSlot, Appointment
from payments.models import Payment
from reviews.models import Review
from datetime import date, time, timedelta
from decimal import Decimal

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        phone_number='+989000000001',
        password='admin1234',
        email='admin@heymedic.com',
        role='admin',
        is_verified=True,
    )


@pytest.fixture
def doctor_user(db):
    return User.objects.create_user(
        phone_number='+989000000002',
        password='doctor1234',
        email='doctor@heymedic.com',
        role='doctor',
        is_verified=True,
    )


@pytest.fixture
def patient_user(db):
    return User.objects.create_user(
        phone_number='+989000000003',
        password='patient1234',
        email='patient@heymedic.com',
        role='patient',
        is_verified=True,
    )


@pytest.fixture
def specialty(db):
    return Specialty.objects.create(title='Cardiology', slug='cardiology')


@pytest.fixture
def doctor_profile(doctor_user, specialty):
    return DoctorProfile.objects.create(
        user=doctor_user,
        specialty=specialty,
        full_name='Dr. Smith',
        medical_license_no='MD12345',
        bio='Experienced cardiologist',
        clinic_address='123 Medical Center',
        price=500000,
    )


@pytest.fixture
def patient_profile(patient_user):
    return PatientProfile.objects.create(
        user=patient_user,
        full_name='John Doe',
        national_id='1234567890',
        birth_date='1990-01-01',
        gender='male',
    )


@pytest.fixture
def time_slot(doctor_profile):
    tomorrow = date.today() + timedelta(days=1)
    return TimeSlot.objects.create(
        doctor=doctor_profile,
        date=tomorrow,
        start_time=time(9, 0),
        end_time=time(9, 30),
        is_available=True,
    )


@pytest.fixture
def booked_time_slot(doctor_profile):
    tomorrow = date.today() + timedelta(days=1)
    return TimeSlot.objects.create(
        doctor=doctor_profile,
        date=tomorrow,
        start_time=time(10, 0),
        end_time=time(10, 30),
        is_available=False,
    )


@pytest.fixture
def appointment(patient_profile, doctor_profile, booked_time_slot):
    return Appointment.objects.create(
        patient=patient_profile,
        doctor=doctor_profile,
        time_slot=booked_time_slot,
        status='pending',
    )


@pytest.fixture
def confirmed_appointment(patient_profile, doctor_profile, booked_time_slot):
    return Appointment.objects.create(
        patient=patient_profile,
        doctor=doctor_profile,
        time_slot=booked_time_slot,
        status='confirmed',
    )


@pytest.fixture
def completed_appointment(patient_profile, doctor_profile, booked_time_slot):
    return Appointment.objects.create(
        patient=patient_profile,
        doctor=doctor_profile,
        time_slot=booked_time_slot,
        status='completed',
    )


@pytest.fixture
def payment(appointment, patient_profile):
    return Payment.objects.create(
        appointment=appointment,
        patient=patient_profile,
        amount=Decimal('500000'),
        status='pending',
    )


@pytest.fixture
def successful_payment(appointment, patient_profile):
    return Payment.objects.create(
        appointment=appointment,
        patient=patient_profile,
        amount=Decimal('500000'),
        status='successful',
        gateway_ref='GW123456',
    )


@pytest.fixture
def review(completed_appointment, patient_profile, doctor_profile):
    return Review.objects.create(
        appointment=completed_appointment,
        patient=patient_profile,
        doctor=doctor_profile,
        rating=5,
        comment='Excellent doctor!',
    )
