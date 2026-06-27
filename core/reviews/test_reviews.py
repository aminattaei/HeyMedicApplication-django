import pytest
from rest_framework import status

from reviews.models import Review


@pytest.mark.django_db
class TestReviewModel:
    def test_create_review(self, review):
        assert review.pk is not None
        assert review.rating == 5

    def test_review_str(self, review):
        expected = f"{review.patient.full_name} -> {review.doctor.full_name} (5/5)"
        assert str(review) == expected

    def test_review_updates_doctor_rating(self, review, doctor_profile):
        doctor_profile.refresh_from_db()
        assert doctor_profile.rating_avg == 5.0

    def test_review_rating_average(self, patient_profile, doctor_profile, completed_appointment):
        review1 = Review.objects.create(
            appointment=completed_appointment,
            patient=patient_profile,
            doctor=doctor_profile,
            rating=4,
            comment='Good doctor',
        )
        doctor_profile.refresh_from_db()
        assert doctor_profile.rating_avg == 4.0

    def test_multiple_reviews_average(self, patient_profile, doctor_profile, completed_appointment):
        from datetime import date, time, timedelta
        from appointments.models import TimeSlot, Appointment

        slot1 = TimeSlot.objects.create(
            doctor=doctor_profile,
            date=date.today() + timedelta(days=10),
            start_time=time(9, 0),
            end_time=time(9, 30),
        )
        appt2 = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            time_slot=slot1,
            status='completed',
        )
        Review.objects.create(
            appointment=completed_appointment,
            patient=patient_profile,
            doctor=doctor_profile,
            rating=5,
            comment='Excellent',
        )
        Review.objects.create(
            appointment=appt2,
            patient=patient_profile,
            doctor=doctor_profile,
            rating=3,
            comment='Okay',
        )
        doctor_profile.refresh_from_db()
        assert doctor_profile.rating_avg == 4.0

    def test_comment_blank_by_default(self, patient_profile, doctor_profile, completed_appointment):
        review = Review.objects.create(
            appointment=completed_appointment,
            patient=patient_profile,
            doctor=doctor_profile,
            rating=4,
        )
        assert review.comment == ''

    def test_created_at_set(self, review):
        assert review.created_at is not None


@pytest.mark.django_db
class TestReviewAPI:
    def test_list_reviews(self, api_client, review):
        api_client.force_authenticate(user=review.patient.user)
        response = api_client.get('/api/v1/reviews/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_filter_by_doctor_id(self, api_client, doctor_user, review):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get(f'/api/v1/reviews/?doctor_id={review.doctor.pk}')
        assert response.status_code == status.HTTP_200_OK
        for r in response.data:
            assert r['doctor'] == review.doctor.pk

    def test_create_review(self, api_client, patient_user, patient_profile, completed_appointment, doctor_profile):
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': completed_appointment.pk,
            'rating': 4,
            'comment': 'Great experience',
        }
        response = api_client.post('/api/v1/reviews/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rating'] == 4

    def test_create_review_invalid_rating(self, api_client, patient_user, completed_appointment, doctor_profile):
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': completed_appointment.pk,
            'doctor': doctor_profile.pk,
            'rating': 6,
            'comment': 'Invalid rating',
        }
        response = api_client.post('/api/v1/reviews/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_review_low_rating_valid(self, api_client, patient_user, completed_appointment):
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': completed_appointment.pk,
            'rating': 1,
            'comment': 'Terrible',
        }
        response = api_client.post('/api/v1/reviews/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['rating'] == 1

    def test_create_review_rating_below_minimum(self, api_client, patient_user, completed_appointment, doctor_profile):
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': completed_appointment.pk,
            'doctor': doctor_profile.pk,
            'rating': 0,
            'comment': 'Invalid',
        }
        response = api_client.post('/api/v1/reviews/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_review_non_completed_appointment(self, api_client, patient_user, appointment):
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': appointment.pk,
            'rating': 5,
            'comment': 'Should fail',
        }
        response = api_client.post('/api/v1/reviews/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_review_twice_same_appointment(self, api_client, patient_user, completed_appointment, patient_profile, doctor_profile):
        Review.objects.create(
            appointment=completed_appointment,
            patient=patient_profile,
            doctor=doctor_profile,
            rating=5,
            comment='First review',
        )
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': completed_appointment.pk,
            'rating': 3,
            'comment': 'Second review',
        }
        response = api_client.post('/api/v1/reviews/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_review_unauthorized(self, api_client):
        response = api_client.get('/api/v1/reviews/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
