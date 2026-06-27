import pytest
from datetime import date, time, timedelta
from decimal import Decimal

from django.test import Client
from django.contrib.auth import get_user_model

from accounts.models import Specialty, DoctorProfile, PatientProfile
from appointments.models import TimeSlot, Appointment
from payments.models import Payment
from reviews.models import Review

User = get_user_model()


@pytest.mark.django_db
class TestHomePage:
    def test_home_page_status(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_home_page_uses_correct_template(self, client):
        response = client.get('/')
        assert 'website/index.html' in [t.name for t in response.templates]


@pytest.mark.django_db
class TestDoctorListView:
    def test_doctor_list_status(self, client, doctor_profile):
        response = client.get('/doctors/')
        assert response.status_code == 200
        assert doctor_profile.full_name in response.content.decode()

    def test_doctor_list_search(self, client, doctor_profile):
        response = client.get('/doctors/?search=Dr.')
        assert response.status_code == 200

    def test_doctor_list_filter_by_specialty(self, client, specialty, doctor_profile):
        response = client.get(f'/doctors/?specialty={specialty.slug}')
        assert response.status_code == 200

    def test_doctor_list_pagination(self, client, doctor_profile):
        response = client.get('/doctors/')
        assert response.status_code == 200

    def test_doctor_list_specialties_in_context(self, client, specialty):
        response = client.get('/doctors/')
        assert 'specialties' in response.context


@pytest.mark.django_db
class TestDoctorProfileView:
    def test_doctor_profile_status(self, client, doctor_profile):
        response = client.get(f'/doctors/{doctor_profile.pk}/')
        assert response.status_code == 200

    def test_doctor_profile_404(self, client):
        response = client.get('/doctors/99999/')
        assert response.status_code == 404

    def test_doctor_profile_shows_reviews_in_context(self, client, doctor_profile, review):
        response = client.get(f'/doctors/{doctor_profile.pk}/')
        assert 'reviews' in response.context

    def test_doctor_profile_context_has_doctor_object(self, client, doctor_profile):
        response = client.get(f'/doctors/{doctor_profile.pk}/')
        assert response.context['doctor'] == doctor_profile


@pytest.mark.django_db
class TestMyAppointmentsView:
    def test_requires_login(self, client):
        response = client.get('/my-appointments/')
        assert response.status_code == 302

    def test_patient_can_access(self, client, patient_user, patient_profile, appointment):
        client.force_login(patient_user)
        response = client.get('/my-appointments/')
        assert response.status_code == 200

    def test_shows_patient_appointments(self, client, patient_user, patient_profile, appointment):
        client.force_login(patient_user)
        response = client.get('/my-appointments/')
        assert appointment in response.context['appointments']

    def test_does_not_show_other_patient_appointments(self, client, appointment):
        other_user = User.objects.create_user(
            phone_number='+989000000900',
            password='test1234',
            role='patient',
        )
        PatientProfile.objects.create(
            user=other_user,
            full_name='Other Patient',
            national_id='9999999999',
            birth_date='1990-01-01',
            gender='female',
        )
        client.force_login(other_user)
        response = client.get('/my-appointments/')
        assert appointment not in response.context['appointments']

    def test_login_redirect_url(self, client):
        response = client.get('/my-appointments/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url


@pytest.mark.django_db
class TestPatientDashboard:
    def test_patient_dashboard_requires_login(self, client):
        response = client.get('/dashboard/patient/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_patient_dashboard_access(self, client, patient_user, patient_profile):
        client.force_login(patient_user)
        response = client.get('/dashboard/patient/')
        assert response.status_code == 200

    def test_doctor_cannot_access_patient_dashboard(self, client, doctor_user, doctor_profile):
        client.force_login(doctor_user)
        response = client.get('/dashboard/patient/')
        assert response.status_code == 302

    def test_dashboard_shows_stats(self, client, patient_user, patient_profile, appointment):
        client.force_login(patient_user)
        response = client.get('/dashboard/patient/')
        assert 'stats' in response.context
        assert response.context['stats']['total'] >= 1

    def test_dashboard_with_upcoming_appointments(self, client, patient_user, patient_profile, appointment):
        client.force_login(patient_user)
        response = client.get('/dashboard/patient/')
        assert 'upcoming_appointments' in response.context

    def test_dashboard_with_status_filter(self, client, patient_user, patient_profile, appointment):
        client.force_login(patient_user)
        response = client.get('/dashboard/patient/?status=pending')
        assert response.status_code == 200
        assert 'upcoming_appointments' in response.context


@pytest.mark.django_db
class TestDoctorDashboard:
    def test_doctor_dashboard_requires_login(self, client):
        response = client.get('/dashboard/doctor/')
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_doctor_dashboard_access(self, client, doctor_user, doctor_profile):
        client.force_login(doctor_user)
        response = client.get('/dashboard/doctor/')
        assert response.status_code == 200

    def test_patient_cannot_access_doctor_dashboard(self, client, patient_user, patient_profile):
        client.force_login(patient_user)
        response = client.get('/dashboard/doctor/')
        assert response.status_code == 302

    def test_dashboard_shows_stats(self, client, doctor_user, doctor_profile):
        client.force_login(doctor_user)
        response = client.get('/dashboard/doctor/')
        assert 'stats' in response.context
        assert 'total_appointments' in response.context['stats']

    def test_dashboard_shows_weekly_calendar(self, client, doctor_user, doctor_profile):
        client.force_login(doctor_user)
        response = client.get('/dashboard/doctor/')
        assert 'weekly_days' in response.context
        assert len(response.context['weekly_days']) == 7

    def test_dashboard_shows_monthly_revenue(self, client, doctor_user, doctor_profile):
        client.force_login(doctor_user)
        response = client.get('/dashboard/doctor/')
        assert 'monthly_revenue' in response.context
        assert len(response.context['monthly_revenue']) == 6

    def test_dashboard_with_status_filter(self, client, doctor_user, doctor_profile, appointment):
        client.force_login(doctor_user)
        response = client.get('/dashboard/doctor/?status=pending')
        assert response.status_code == 200
        assert 'all_appointments' in response.context

    def test_dashboard_with_search(self, client, doctor_user, doctor_profile, appointment):
        client.force_login(doctor_user)
        response = client.get('/dashboard/doctor/?search=John')
        assert response.status_code == 200


@pytest.mark.django_db
class TestUserProfileView:
    def test_profile_requires_login(self, client):
        response = client.get('/profile/')
        assert response.status_code == 302

    def test_profile_access_patient(self, client, patient_user, patient_profile):
        client.force_login(patient_user)
        response = client.get('/profile/')
        assert response.status_code == 200

    def test_profile_access_doctor(self, client, doctor_user, doctor_profile):
        client.force_login(doctor_user)
        response = client.get('/profile/')
        assert response.status_code == 200

    def test_profile_post_update_patient(self, client, patient_user, patient_profile):
        client.force_login(patient_user)
        response = client.post('/profile/', {
            'email': 'newemail@test.com',
            'full_name': 'Updated Name',
            'national_id': '1234567890',
            'birth_date': '1990-01-01',
            'gender': 'male',
        })
        assert response.status_code == 200
        patient_profile.refresh_from_db()
        assert patient_profile.full_name == 'Updated Name'

    def test_profile_post_update_doctor(self, client, doctor_user, doctor_profile, specialty):
        client.force_login(doctor_user)
        response = client.post('/profile/', {
            'email': 'doctor_new@test.com',
            'full_name': 'Dr. Updated',
            'medical_license_no': 'MD99999',
            'bio': 'Updated bio',
            'clinic_address': 'New Clinic',
            'price': '600000',
            'specialty': specialty.pk,
        })
        assert response.status_code == 200
        doctor_profile.refresh_from_db()
        assert doctor_profile.full_name == 'Dr. Updated'
        assert doctor_profile.price == 600000

    def test_profile_updates_email(self, client, patient_user, patient_profile):
        client.force_login(patient_user)
        client.post('/profile/', {
            'email': 'updated@test.com',
            'full_name': 'John Doe',
            'national_id': '1234567890',
            'birth_date': '1990-01-01',
            'gender': 'male',
        })
        patient_user.refresh_from_db()
        assert patient_user.email == 'updated@test.com'


@pytest.mark.django_db
class TestWebsiteChangePasswordView:
    def test_get_requires_login(self, client):
        response = client.get('/profile/change-password/')
        assert response.status_code == 302

    def test_get_renders_form(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/profile/change-password/')
        assert response.status_code == 200

    def test_change_password_wrong_old(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/profile/change-password/', {
            'old_password': 'wrongold',
            'new_password1': 'newpass1234',
            'new_password2': 'newpass1234',
        })
        assert response.status_code == 200
        assert 'رمز عبور فعلی اشتباه است' in response.content.decode()

    def test_change_password_mismatch(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/profile/change-password/', {
            'old_password': 'patient1234',
            'new_password1': 'newpass1234',
            'new_password2': 'diffpass1234',
        })
        assert response.status_code == 200
        assert 'مطابقت ندارند' in response.content.decode()

    def test_change_password_too_short(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/profile/change-password/', {
            'old_password': 'patient1234',
            'new_password1': 'short',
            'new_password2': 'short',
        })
        assert response.status_code == 200
        assert 'حداقل ۸ کاراکتر' in response.content.decode()

    def test_change_password_success(self, client, patient_user):
        client.force_login(patient_user)
        response = client.post('/profile/change-password/', {
            'old_password': 'patient1234',
            'new_password1': 'newpass1234',
            'new_password2': 'newpass1234',
        })
        assert response.status_code == 200
        assert 'رمز عبور با موفقیت تغییر کرد' in response.content.decode()


@pytest.mark.django_db
class TestWebsiteLoginView:
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

    def test_login_redirect_if_already_authenticated(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/accounts/login/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestWebsiteRegisterView:
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

    def test_register_patient_creates_profile(self, client):
        client.post('/accounts/register/', {
            'phone_number': '+989000000302',
            'password': 'testpass1234',
            'role': 'patient',
        })
        user = User.objects.get(phone_number='+989000000302')
        assert hasattr(user, 'patient_profile')

    def test_register_redirect_if_already_authenticated(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/accounts/register/')
        assert response.status_code == 302


@pytest.mark.django_db
class TestWebsiteLogoutView:
    def test_logout(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/accounts/logout/')
        assert response.status_code == 302

    def test_logout_redirects_to_home(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/accounts/logout/')
        assert response.status_code == 302


# ===========================
# ADMIN PANEL TESTS
# ===========================

@pytest.mark.django_db
class TestAdminLoginView:
    def test_admin_login_get(self, client):
        response = client.get('/panel/login/')
        assert response.status_code == 200

    def test_admin_login_post_success(self, client, admin_user):
        response = client.post('/panel/login/', {
            'phone_number': '+989000000001',
            'password': 'admin1234',
        })
        assert response.status_code == 302

    def test_admin_login_post_invalid(self, client):
        response = client.post('/panel/login/', {
            'phone_number': '+989000000099',
            'password': 'wrongpass',
        })
        assert response.status_code == 200

    def test_admin_login_redirects_if_already_admin(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/panel/login/')
        assert response.status_code == 302

    def test_non_admin_login_fails(self, client, patient_user):
        response = client.post('/panel/login/', {
            'phone_number': '+989000000003',
            'password': 'patient1234',
        })
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminDashboardView:
    def test_requires_login(self, client):
        response = client.get('/panel/')
        assert response.status_code == 302

    def test_requires_admin_role(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/')
        assert response.status_code == 302

    def test_admin_can_access(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/panel/')
        assert response.status_code == 200

    def test_dashboard_shows_stats(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/panel/')
        assert 'stats' in response.context

    def test_dashboard_shows_recent_data(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/panel/')
        assert 'recent_appointments' in response.context
        assert 'recent_payments' in response.context
        assert 'recent_reviews' in response.context


@pytest.mark.django_db
class TestAdminUserCRUD:
    def test_user_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/users/')
        assert response.status_code == 302

    def test_user_list(self, client, admin_user, patient_user):
        client.force_login(admin_user)
        response = client.get('/panel/users/')
        assert response.status_code == 200

    def test_user_list_search(self, client, admin_user, patient_user):
        client.force_login(admin_user)
        response = client.get('/panel/users/?search=+989000000003')
        assert response.status_code == 200

    def test_user_list_filter_by_role(self, client, admin_user, patient_user):
        client.force_login(admin_user)
        response = client.get('/panel/users/?role=patient')
        assert response.status_code == 200

    def test_user_add_get(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/panel/users/add/')
        assert response.status_code == 200

    def test_user_add_post(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post('/panel/users/add/', {
            'phone_number': '+989000000500',
            'password': 'testpass1234',
            'email': 'new@test.com',
            'role': 'patient',
        })
        assert response.status_code == 302
        assert User.objects.filter(phone_number='+989000000500').exists()

    def test_user_edit_get(self, client, admin_user, patient_user):
        client.force_login(admin_user)
        response = client.get(f'/panel/users/{patient_user.pk}/edit/')
        assert response.status_code == 200

    def test_user_edit_post(self, client, admin_user, patient_user):
        client.force_login(admin_user)
        response = client.post(f'/panel/users/{patient_user.pk}/edit/', {
            'phone_number': str(patient_user.phone_number),
            'email': 'updated@test.com',
            'role': 'patient',
            'is_verified': 'on',
            'is_staff': 'on',
            'is_active': 'on',
        })
        assert response.status_code == 302
        patient_user.refresh_from_db()
        assert patient_user.email == 'updated@test.com'

    def test_user_delete(self, client, admin_user):
        client.force_login(admin_user)
        user_to_delete = User.objects.create_user(
            phone_number='+989000000600',
            password='testpass1234',
            role='patient',
        )
        response = client.post(f'/panel/users/{user_to_delete.pk}/delete/')
        assert response.status_code == 302
        assert not User.objects.filter(pk=user_to_delete.pk).exists()


@pytest.mark.django_db
class TestAdminDoctorCRUD:
    def test_doctor_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/doctors/')
        assert response.status_code == 302

    def test_doctor_list(self, client, admin_user, doctor_profile):
        client.force_login(admin_user)
        response = client.get('/panel/doctors/')
        assert response.status_code == 200

    def test_doctor_list_search(self, client, admin_user, doctor_profile):
        client.force_login(admin_user)
        response = client.get('/panel/doctors/?search=Smith')
        assert response.status_code == 200

    def test_doctor_add_get(self, client, admin_user, specialty):
        client.force_login(admin_user)
        response = client.get('/panel/doctors/add/')
        assert response.status_code == 200

    def test_doctor_edit_get(self, client, admin_user, doctor_profile):
        client.force_login(admin_user)
        response = client.get(f'/panel/doctors/{doctor_profile.pk}/edit/')
        assert response.status_code == 200

    def test_doctor_edit_post(self, client, admin_user, doctor_profile, specialty):
        client.force_login(admin_user)
        response = client.post(f'/panel/doctors/{doctor_profile.pk}/edit/', {
            'full_name': 'Dr. Updated',
            'specialty': specialty.pk,
            'medical_license_no': doctor_profile.medical_license_no,
            'bio': 'Updated bio',
            'clinic_address': 'New Address',
            'price': '700000',
        })
        assert response.status_code == 302
        doctor_profile.refresh_from_db()
        assert doctor_profile.full_name == 'Dr. Updated'

    def test_doctor_delete(self, client, admin_user, doctor_profile):
        client.force_login(admin_user)
        response = client.post(f'/panel/doctors/{doctor_profile.pk}/delete/')
        assert response.status_code == 302
        assert not DoctorProfile.objects.filter(pk=doctor_profile.pk).exists()


@pytest.mark.django_db
class TestAdminPatientCRUD:
    def test_patient_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/patients/')
        assert response.status_code == 302

    def test_patient_list(self, client, admin_user, patient_profile):
        client.force_login(admin_user)
        response = client.get('/panel/patients/')
        assert response.status_code == 200

    def test_patient_list_search(self, client, admin_user, patient_profile):
        client.force_login(admin_user)
        response = client.get('/panel/patients/?search=Doe')
        assert response.status_code == 200

    def test_patient_add_get(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/panel/patients/add/')
        assert response.status_code == 200

    def test_patient_edit_get(self, client, admin_user, patient_profile):
        client.force_login(admin_user)
        response = client.get(f'/panel/patients/{patient_profile.pk}/edit/')
        assert response.status_code == 200

    def test_patient_edit_post(self, client, admin_user, patient_profile):
        client.force_login(admin_user)
        response = client.post(f'/panel/patients/{patient_profile.pk}/edit/', {
            'full_name': 'Updated Patient',
            'national_id': patient_profile.national_id,
            'birth_date': '1990-01-01',
            'gender': 'male',
        })
        assert response.status_code == 302
        patient_profile.refresh_from_db()
        assert patient_profile.full_name == 'Updated Patient'

    def test_patient_delete(self, client, admin_user, patient_profile):
        client.force_login(admin_user)
        response = client.post(f'/panel/patients/{patient_profile.pk}/delete/')
        assert response.status_code == 302
        assert not PatientProfile.objects.filter(pk=patient_profile.pk).exists()


@pytest.mark.django_db
class TestAdminSpecialtyCRUD:
    def test_specialty_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/specialties/')
        assert response.status_code == 302

    def test_specialty_list(self, client, admin_user, specialty):
        client.force_login(admin_user)
        response = client.get('/panel/specialties/')
        assert response.status_code == 200

    def test_specialty_list_search(self, client, admin_user, specialty):
        client.force_login(admin_user)
        response = client.get('/panel/specialties/?search=Cardio')
        assert response.status_code == 200

    def test_specialty_add_get(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get('/panel/specialties/add/')
        assert response.status_code == 200

    def test_specialty_add_post(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post('/panel/specialties/add/', {
            'title': 'Neurology',
            'slug': 'neurology',
        })
        assert response.status_code == 302
        assert Specialty.objects.filter(title='Neurology').exists()

    def test_specialty_edit_get(self, client, admin_user, specialty):
        client.force_login(admin_user)
        response = client.get(f'/panel/specialties/{specialty.pk}/edit/')
        assert response.status_code == 200

    def test_specialty_edit_post(self, client, admin_user, specialty):
        client.force_login(admin_user)
        response = client.post(f'/panel/specialties/{specialty.pk}/edit/', {
            'title': 'Updated Specialty',
            'slug': 'updated-specialty',
        })
        assert response.status_code == 302
        specialty.refresh_from_db()
        assert specialty.title == 'Updated Specialty'

    def test_specialty_delete(self, client, admin_user, specialty):
        client.force_login(admin_user)
        response = client.post(f'/panel/specialties/{specialty.pk}/delete/')
        assert response.status_code == 302
        assert not Specialty.objects.filter(pk=specialty.pk).exists()


@pytest.mark.django_db
class TestAdminTimeSlotCRUD:
    def test_timeslot_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/timeslots/')
        assert response.status_code == 302

    def test_timeslot_list(self, client, admin_user, time_slot):
        client.force_login(admin_user)
        response = client.get('/panel/timeslots/')
        assert response.status_code == 200

    def test_timeslot_list_filter_available(self, client, admin_user, time_slot, booked_time_slot):
        client.force_login(admin_user)
        response = client.get('/panel/timeslots/?available=true')
        assert response.status_code == 200

    def test_timeslot_add_get(self, client, admin_user, doctor_profile):
        client.force_login(admin_user)
        response = client.get('/panel/timeslots/add/')
        assert response.status_code == 200

    def test_timeslot_edit_get(self, client, admin_user, time_slot):
        client.force_login(admin_user)
        response = client.get(f'/panel/timeslots/{time_slot.pk}/edit/')
        assert response.status_code == 200

    def test_timeslot_edit_post(self, client, admin_user, time_slot):
        client.force_login(admin_user)
        response = client.post(f'/panel/timeslots/{time_slot.pk}/edit/', {
            'doctor': time_slot.doctor.pk,
            'date': time_slot.date.isoformat(),
            'start_time': '15:00',
            'end_time': '15:30',
            'is_available': 'on',
        })
        assert response.status_code == 302
        time_slot.refresh_from_db()
        assert time_slot.start_time == time(15, 0)

    def test_timeslot_delete(self, client, admin_user, time_slot):
        client.force_login(admin_user)
        response = client.post(f'/panel/timeslots/{time_slot.pk}/delete/')
        assert response.status_code == 302
        assert not TimeSlot.objects.filter(pk=time_slot.pk).exists()


@pytest.mark.django_db
class TestAdminAppointmentCRUD:
    def test_appointment_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/appointments/')
        assert response.status_code == 302

    def test_appointment_list(self, client, admin_user, appointment):
        client.force_login(admin_user)
        response = client.get('/panel/appointments/')
        assert response.status_code == 200

    def test_appointment_list_filter_status(self, client, admin_user, appointment):
        client.force_login(admin_user)
        response = client.get('/panel/appointments/?status=pending')
        assert response.status_code == 200

    def test_appointment_list_search(self, client, admin_user, appointment):
        client.force_login(admin_user)
        response = client.get('/panel/appointments/?search=Doe')
        assert response.status_code == 200

    def test_appointment_edit_get(self, client, admin_user, appointment):
        client.force_login(admin_user)
        response = client.get(f'/panel/appointments/{appointment.pk}/edit/')
        assert response.status_code == 200

    def test_appointment_edit_post(self, client, admin_user, appointment):
        client.force_login(admin_user)
        response = client.post(f'/panel/appointments/{appointment.pk}/edit/', {
            'status': 'confirmed',
            'notes': 'Updated by admin',
        })
        assert response.status_code == 302
        appointment.refresh_from_db()
        assert appointment.status == 'confirmed'

    def test_appointment_delete(self, client, admin_user, appointment):
        client.force_login(admin_user)
        response = client.post(f'/panel/appointments/{appointment.pk}/delete/')
        assert response.status_code == 302
        assert not Appointment.objects.filter(pk=appointment.pk).exists()


@pytest.mark.django_db
class TestAdminPaymentCRUD:
    def test_payment_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/payments/')
        assert response.status_code == 302

    def test_payment_list(self, client, admin_user, payment):
        client.force_login(admin_user)
        response = client.get('/panel/payments/')
        assert response.status_code == 200

    def test_payment_list_filter_status(self, client, admin_user, payment):
        client.force_login(admin_user)
        response = client.get('/panel/payments/?status=pending')
        assert response.status_code == 200

    def test_payment_edit_get(self, client, admin_user, payment):
        client.force_login(admin_user)
        response = client.get(f'/panel/payments/{payment.pk}/edit/')
        assert response.status_code == 200

    def test_payment_edit_post(self, client, admin_user, payment):
        client.force_login(admin_user)
        response = client.post(f'/panel/payments/{payment.pk}/edit/', {
            'status': 'successful',
            'gateway_ref': 'GW_ADMIN_TEST',
            'amount': str(payment.amount),
        })
        assert response.status_code == 302
        payment.refresh_from_db()
        assert payment.status == 'successful'
        assert payment.paid_at is not None

    def test_payment_delete(self, client, admin_user, payment):
        client.force_login(admin_user)
        response = client.post(f'/panel/payments/{payment.pk}/delete/')
        assert response.status_code == 302
        assert not Payment.objects.filter(pk=payment.pk).exists()


@pytest.mark.django_db
class TestAdminReviewCRUD:
    def test_review_list_requires_admin(self, client, patient_user):
        client.force_login(patient_user)
        response = client.get('/panel/reviews/')
        assert response.status_code == 302

    def test_review_list(self, client, admin_user, review):
        client.force_login(admin_user)
        response = client.get('/panel/reviews/')
        assert response.status_code == 200

    def test_review_list_search(self, client, admin_user, review):
        client.force_login(admin_user)
        response = client.get('/panel/reviews/?search=Doe')
        assert response.status_code == 200

    def test_review_list_filter_rating(self, client, admin_user, review):
        client.force_login(admin_user)
        response = client.get('/panel/reviews/?rating=5')
        assert response.status_code == 200

    def test_review_edit_get(self, client, admin_user, review):
        client.force_login(admin_user)
        response = client.get(f'/panel/reviews/{review.pk}/edit/')
        assert response.status_code == 200

    def test_review_edit_post(self, client, admin_user, review):
        client.force_login(admin_user)
        response = client.post(f'/panel/reviews/{review.pk}/edit/', {
            'rating': '3',
            'comment': 'Updated comment by admin',
        })
        assert response.status_code == 302
        review.refresh_from_db()
        assert review.rating == 3

    def test_review_delete(self, client, admin_user, review):
        client.force_login(admin_user)
        response = client.post(f'/panel/reviews/{review.pk}/delete/')
        assert response.status_code == 302
        assert not Review.objects.filter(pk=review.pk).exists()


@pytest.mark.django_db
class TestAdminDoctorCreate:
    def test_doctor_create_post(self, client, admin_user, specialty):
        client.force_login(admin_user)
        response = client.post('/panel/doctors/add/', {
            'user_phone': '+989000000700',
            'user_password': 'testpass1234',
            'user_email': 'newdoc@test.com',
            'full_name': 'Dr. New',
            'specialty': specialty.pk,
            'medical_license_no': 'MD-NEW-001',
            'bio': 'New doctor',
            'clinic_address': 'New Clinic',
            'price': '400000',
        })
        assert response.status_code == 302
        assert User.objects.filter(phone_number='+989000000700').exists()
        user = User.objects.get(phone_number='+989000000700')
        assert DoctorProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestAdminPatientCreate:
    def test_patient_create_post(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post('/panel/patients/add/', {
            'user_phone': '+989000000800',
            'user_password': 'testpass1234',
            'user_email': 'newpatient@test.com',
            'full_name': 'New Patient',
            'national_id': '1111111111',
            'birth_date': '1995-05-15',
            'gender': 'female',
        })
        assert response.status_code == 302
        assert User.objects.filter(phone_number='+989000000800').exists()
        user = User.objects.get(phone_number='+989000000800')
        assert PatientProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
class TestAdminAppointmentCreate:
    def test_appointment_create_post(self, client, admin_user, patient_profile, doctor_profile, time_slot):
        client.force_login(admin_user)
        response = client.post('/panel/appointments/add/', {
            'patient': patient_profile.pk,
            'doctor': doctor_profile.pk,
            'time_slot': time_slot.pk,
            'status': 'pending',
            'notes': 'Admin created',
        })
        assert response.status_code == 302
        assert Appointment.objects.filter(time_slot=time_slot).exists()
        time_slot.refresh_from_db()
        assert time_slot.is_available is False


@pytest.mark.django_db
class TestAdminPaymentCreate:
    def test_payment_create_post(self, client, admin_user, patient_profile, appointment):
        client.force_login(admin_user)
        response = client.post('/panel/payments/add/', {
            'patient': patient_profile.pk,
            'appointment': appointment.pk,
            'amount': '500000',
            'status': 'pending',
        })
        assert response.status_code == 302
        assert Payment.objects.filter(appointment=appointment).exists()


@pytest.mark.django_db
class TestAdminReviewCreate:
    def test_review_create_post(self, client, admin_user, patient_profile, doctor_profile, completed_appointment):
        client.force_login(admin_user)
        response = client.post('/panel/reviews/add/', {
            'patient': patient_profile.pk,
            'doctor': doctor_profile.pk,
            'appointment': completed_appointment.pk,
            'rating': '4',
            'comment': 'Admin created review',
        })
        assert response.status_code == 302
        assert Review.objects.filter(appointment=completed_appointment).exists()


@pytest.mark.django_db
class TestAdminUserCreateEdgeCases:
    def test_user_add_duplicate_phone(self, client, admin_user, patient_user):
        client.force_login(admin_user)
        response = client.post('/panel/users/add/', {
            'phone_number': '+989000000003',
            'password': 'testpass1234',
            'role': 'patient',
        })
        assert response.status_code == 302
        assert User.objects.filter(phone_number='+989000000003').count() == 1


@pytest.mark.django_db
class TestAdminAccessDenied:
    def test_doctor_redirected_from_admin_panel(self, client, doctor_user, doctor_profile):
        client.force_login(doctor_user)
        response = client.get('/panel/')
        assert response.status_code == 302

    def test_patient_redirected_from_admin_panel(self, client, patient_user, patient_profile):
        client.force_login(patient_user)
        response = client.get('/panel/')
        assert response.status_code == 302

    def test_unauthenticated_redirected_from_admin_panel(self, client):
        response = client.get('/panel/')
        assert response.status_code == 302
