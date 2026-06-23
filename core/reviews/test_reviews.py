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


@pytest.mark.django_db
class TestReviewAPI:
    def test_list_reviews(self, api_client, review):
        api_client.force_authenticate(user=review.patient.user)
        response = api_client.get('/api/v1/reviews/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_review(self, api_client, patient_user, patient_profile, completed_appointment, doctor_profile):
        api_client.force_authenticate(user=patient_user)
        data = {
            'appointment': completed_appointment.pk,
            'patient': patient_profile.pk,
            'doctor': doctor_profile.pk,
            'rating': 4,
            'comment': 'Great experience',
        }
        response = api_client.post('/api/v1/reviews/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

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

    def test_review_unauthorized(self, api_client):
        response = api_client.get('/api/v1/reviews/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
