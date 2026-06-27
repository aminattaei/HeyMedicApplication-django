import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from django.test import Client

from accounts.models import PatientProfile, DoctorProfile, Specialty

User = get_user_model()


@pytest.mark.django_db
class TestUserManager:
    def test_create_user_with_phone(self):
        user = User.objects.create_user(
            phone_number='+989000000100',
            password='test1234',
            role='patient',
        )
        assert user.pk is not None
        assert user.phone_number == '+989000000100'
        assert user.role == 'patient'
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_create_user_requires_phone(self):
        with pytest.raises(ValueError, match='Phone number is required'):
            User.objects.create_user(phone_number='', password='test1234')

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            phone_number='+989000000101',
            password='admin1234',
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == 'admin'
        assert admin.is_verified is True

    def test_create_superuser_forces_staff(self):
        with pytest.raises(ValueError, match='Superuser must have is_staff=True'):
            User.objects.create_superuser(
                phone_number='+989000000102',
                password='admin1234',
                is_staff=False,
            )


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

    def test_user_email_unique(self, patient_user):
        patient_user.email = 'test@example.com'
        patient_user.save()
        with pytest.raises(Exception):
            User.objects.create_user(
                phone_number='+989000000099',
                password='test1234',
                role='patient',
                email='test@example.com',
            )

    def test_user_default_role_is_patient(self):
        user = User.objects.create_user(
            phone_number='+989000000200',
            password='test1234',
        )
        assert user.role == 'patient'

    def test_user_created_at_set(self, patient_user):
        assert patient_user.created_at is not None


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

    def test_profile_related_to_user(self, patient_user, patient_profile):
        assert hasattr(patient_user, 'patient_profile')
        assert patient_user.patient_profile == patient_profile


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

    def test_profile_related_to_user(self, doctor_user, doctor_profile):
        assert hasattr(doctor_user, 'doctor_profile')
        assert doctor_user.doctor_profile == doctor_profile

    def test_rating_avg_default(self, doctor_profile):
        assert doctor_profile.rating_avg == 0.0

    def test_price_default(self, doctor_profile):
        assert doctor_profile.price == 500000


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

    def test_specialty_slug_unique(self):
        Specialty.objects.create(title='General', slug='general')
        with pytest.raises(Exception):
            Specialty.objects.create(title='General Medicine', slug='general')


@pytest.mark.django_db
class TestAccountsAPI:
    def test_list_users(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/accounts/api/v1/users/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_list_patient_profiles(self, api_client, admin_user, patient_profile):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/accounts/api/v1/PatientProfile/')
        assert response.status_code == status.HTTP_200_OK

    def test_list_specialties(self, api_client, admin_user, specialty):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/accounts/api/v1/specialty/')
        assert response.status_code == status.HTTP_200_OK

    def test_user_api_unauthenticated_read_allowed(self, api_client):
        response = api_client.get('/accounts/api/v1/users/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAccountsViews:
    def test_login_get(self, client):
        response = client.get('/accounts/login/')
        assert response.status_code == 200

    def test_login_post_success(self, client, patient_user):
        response = client.post('/accounts/login/', {
            'phone_number': '+989000000003',
            'password': 'patient1234',
        })
        assert response.status_code == 302

    def test_login_post_invalid(self, client):
        response = client.post('/accounts/login/', {
            'phone_number': '+989000000099',
            'password': 'wrongpass',
        })
        assert response.status_code == 200
        assert 'شماره موبایل یا رمز عبور اشتباه است' in response.content.decode()

    def test_register_get(self, client):
        response = client.get('/accounts/register/')
        assert response.status_code == 200

    def test_register_post_patient(self, client):
        response = client.post('/accounts/register/', {
            'phone_number': '+989000000300',
            'password': 'testpass1234',
            'role': 'patient',
        })
        assert response.status_code == 302
        assert User.objects.filter(phone_number='+989000000300').exists()

    def test_register_post_duplicate_phone(self, client, patient_user):
        response = client.post('/accounts/register/', {
            'phone_number': '+989000000003',
            'password': 'test1234',
            'role': 'patient',
        })
        assert response.status_code == 200
        assert 'این شماره موبایل قبلاً ثبت شده است' in response.content.decode()

    def test_register_doctor_creates_default_specialty(self, client):
        response = client.post('/accounts/register/', {
            'phone_number': '+989000000301',
            'password': 'testpass1234',
            'role': 'doctor',
        })
        assert response.status_code == 302
        assert Specialty.objects.filter(title='عمومی').exists()

    def test_logout(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/accounts/logout/')
        assert response.status_code == 302

    def test_change_password_get(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/accounts/profile/change-password/')
        assert response.status_code == 200

    def test_change_password_wrong_old(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/accounts/profile/change-password/', {
            'old_password': 'wrongold',
            'new_password1': 'newpass1234',
            'new_password2': 'newpass1234',
        })
        assert response.status_code == 200
        assert 'رمز عبور فعلی اشتباه است' in response.content.decode()

    def test_change_password_success(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/accounts/profile/change-password/', {
            'old_password': 'patient1234',
            'new_password1': 'newpass1234',
            'new_password2': 'newpass1234',
        })
        assert response.status_code == 200
        assert 'رمز عبور با موفقیت تغییر کرد' in response.content.decode()

    def test_change_password_mismatch(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/accounts/profile/change-password/', {
            'old_password': 'patient1234',
            'new_password1': 'newpass1234',
            'new_password2': 'diffpass1234',
        })
        assert response.status_code == 200
        assert 'مطابقت ندارند' in response.content.decode()

    def test_change_password_too_short(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/accounts/profile/change-password/', {
            'old_password': 'patient1234',
            'new_password1': 'short',
            'new_password2': 'short',
        })
        assert response.status_code == 200
        assert 'حداقل ۸ کاراکتر' in response.content.decode()
