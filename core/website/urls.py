from django.urls import path

from . import views


app_name = "website"

urlpatterns = [
    path("", views.HomePageTemplateView.as_view(), name="home_page"),
]
