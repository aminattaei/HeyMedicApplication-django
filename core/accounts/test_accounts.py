import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from accounts.models import PatientProfile, DoctorProfile, Specialty

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self, patient_user):
        assert patient_user.pk is not None
        assert patient_user.role == 'patient'

    def test_create_superuser(self, admin_user):
        assert admin_user.is_superuser is True
        assert admin_user.is_staff is True
        assert admin_user.role == 'admin'

    def test_user_str(self, patient_user):
        assert str(patient_user) == str(patient_user.phone_number)

    def test_user_phone_number_unique(self, patient_user):
        with pytest.raises(Exception):
            User.objects.create_user(
                phone_number='+989000000003',
                password='test1234',
                role='patient',
            )


@pytest.mark.django_db
class TestPatientProfile:
    def test_create_patient_profile(self, patient_profile):
        assert patient_profile.pk is not None
        assert patient_profile.full_name == 'John Doe'

    def test_patient_profile_str(self, patient_profile):
        assert str(patient_profile) == 'John Doe'

    def test_national_id_unique(self, patient_profile):
        with pytest.raises(Exception):
            PatientProfile.objects.create(
                user=User.objects.create_user(
                    phone_number='+989000000099',
                    password='test1234',
                    role='patient',
                ),
                full_name='Jane Doe',
                national_id='1234567890',
                birth_date='1995-01-01',
                gender='female',
            )


@pytest.mark.django_db
class TestDoctorProfile:
    def test_create_doctor_profile(self, doctor_profile):
        assert doctor_profile.pk is not None
        assert doctor_profile.full_name == 'Dr. Smith'

    def test_doctor_profile_str(self, doctor_profile):
        expected = f"{doctor_profile.full_name} - {doctor_profile.specialty.title}"
        assert str(doctor_profile) == expected

    def test_medical_license_unique(self, doctor_profile):
        with pytest.raises(Exception):
            DoctorProfile.objects.create(
                user=User.objects.create_user(
                    phone_number='+989000000098',
                    password='test1234',
                    role='doctor',
                ),
                specialty=doctor_profile.specialty,
                full_name='Dr. Jones',
                medical_license_no='MD12345',
                clinic_address='456 Medical Center',
                price=600000,
            )


@pytest.mark.django_db
class TestSpecialty:
    def test_create_specialty(self, specialty):
        assert specialty.pk is not None
        assert specialty.title == 'Cardiology'

    def test_specialty_str(self, specialty):
        assert str(specialty) == 'Cardiology'

    def test_specialty_slug_auto(self, specialty):
        assert specialty.slug == 'cardiology'

    def test_specialty_ordering(self, specialty):
        Specialty.objects.create(title='Dermatology')
        Specialty.objects.create(title='Neurology')
        specialties = list(Specialty.objects.all())
        assert specialties[0].title == 'Cardiology'
        assert specialties[1].title == 'Dermatology'
        assert specialties[2].title == 'Neurology'


@pytest.mark.django_db
class TestAccountsAPI:
    def test_user_registration(self, api_client):
        data = {
            'phone_number': '+989000000050',
            'email': 'newuser@test.com',
            'password': 'testpass123',
            're_password': 'testpass123',
        }
        response = api_client.post('/api/auth/users/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_user_login(self, api_client, patient_user):
        data = {
            'phone_number': '+989000000003',
            'password': 'patient1234',
        }
        response = api_client.post('/api/auth/jwt/create/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_user_login_invalid_credentials(self, api_client, patient_user):
        data = {
            'phone_number': '+989000000003',
            'password': 'wrongpassword',
        }
        response = api_client.post('/api/auth/jwt/create/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
