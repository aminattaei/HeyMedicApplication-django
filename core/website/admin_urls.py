from django.urls import path
from . import admin_views

urlpatterns = [
    path('login/', admin_views.AdminLoginView.as_view(), name='admin_login'),
    path('', admin_views.AdminDashboardView.as_view(), name='admin_dashboard'),

    # Users
    path('users/', admin_views.AdminUserListView.as_view(), name='admin_user_list'),
    path('users/add/', admin_views.AdminUserCreateView.as_view(), name='admin_user_add'),
    path('users/<int:pk>/edit/', admin_views.AdminUserEditView.as_view(), name='admin_user_edit'),
    path('users/<int:pk>/delete/', admin_views.AdminUserDeleteView.as_view(), name='admin_user_delete'),

    # Doctors
    path('doctors/', admin_views.AdminDoctorListView.as_view(), name='admin_doctor_list'),
    path('doctors/add/', admin_views.AdminDoctorCreateView.as_view(), name='admin_doctor_add'),
    path('doctors/<int:pk>/edit/', admin_views.AdminDoctorEditView.as_view(), name='admin_doctor_edit'),
    path('doctors/<int:pk>/delete/', admin_views.AdminDoctorDeleteView.as_view(), name='admin_doctor_delete'),

    # Patients
    path('patients/', admin_views.AdminPatientListView.as_view(), name='admin_patient_list'),
    path('patients/add/', admin_views.AdminPatientCreateView.as_view(), name='admin_patient_add'),
    path('patients/<int:pk>/edit/', admin_views.AdminPatientEditView.as_view(), name='admin_patient_edit'),
    path('patients/<int:pk>/delete/', admin_views.AdminPatientDeleteView.as_view(), name='admin_patient_delete'),

    # Specialties
    path('specialties/', admin_views.AdminSpecialtyListView.as_view(), name='admin_specialty_list'),
    path('specialties/add/', admin_views.AdminSpecialtyCreateView.as_view(), name='admin_specialty_add'),
    path('specialties/<int:pk>/edit/', admin_views.AdminSpecialtyEditView.as_view(), name='admin_specialty_edit'),
    path('specialties/<int:pk>/delete/', admin_views.AdminSpecialtyDeleteView.as_view(), name='admin_specialty_delete'),

    # Time Slots
    path('timeslots/', admin_views.AdminTimeSlotListView.as_view(), name='admin_timeslot_list'),
    path('timeslots/add/', admin_views.AdminTimeSlotCreateView.as_view(), name='admin_timeslot_add'),
    path('timeslots/<int:pk>/edit/', admin_views.AdminTimeSlotEditView.as_view(), name='admin_timeslot_edit'),
    path('timeslots/<int:pk>/delete/', admin_views.AdminTimeSlotDeleteView.as_view(), name='admin_timeslot_delete'),

    # Appointments
    path('appointments/', admin_views.AdminAppointmentListView.as_view(), name='admin_appointment_list'),
    path('appointments/<int:pk>/edit/', admin_views.AdminAppointmentEditView.as_view(), name='admin_appointment_edit'),
    path('appointments/<int:pk>/delete/', admin_views.AdminAppointmentDeleteView.as_view(), name='admin_appointment_delete'),

    # Payments
    path('payments/', admin_views.AdminPaymentListView.as_view(), name='admin_payment_list'),
    path('payments/<int:pk>/edit/', admin_views.AdminPaymentEditView.as_view(), name='admin_payment_edit'),
    path('payments/<int:pk>/delete/', admin_views.AdminPaymentDeleteView.as_view(), name='admin_payment_delete'),

    # Reviews
    path('reviews/', admin_views.AdminReviewListView.as_view(), name='admin_review_list'),
    path('reviews/<int:pk>/edit/', admin_views.AdminReviewEditView.as_view(), name='admin_review_edit'),
    path('reviews/<int:pk>/delete/', admin_views.AdminReviewDeleteView.as_view(), name='admin_review_delete'),
]
