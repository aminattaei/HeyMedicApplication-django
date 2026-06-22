from django.urls import path
from . import views

app_name = "website"

urlpatterns = [
    path("", views.HomePageTemplateView.as_view(), name="home_page"),
    path("doctors/", views.DoctorListView.as_view(), name="doctor_list"),
    path("doctors/<int:pk>/", views.DoctorProfileView.as_view(), name="doctor_profile"),
    path("my-appointments/", views.MyAppointmentsView.as_view(), name="my_appointments"),
    path("dashboard/doctor/", views.DoctorDashboardView.as_view(), name="doctor_dashboard"),
    path("accounts/login/", views.LoginView.as_view(), name="login"),
    path("accounts/register/", views.RegisterView.as_view(), name="register"),
    path("accounts/logout/", views.LogoutView.as_view(), name="logout"),
]
