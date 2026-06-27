from django.urls import path, include
from . import views


app_name = "accounts"

urlpatterns = [
    path("profile/change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
]