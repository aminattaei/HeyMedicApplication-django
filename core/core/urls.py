"""
URL configuration for HeyMedic project.

Main URL patterns:
    /                  - Landing page
    /admin/            - Django admin panel
    /api/v1/           - REST API endpoints (appointments, payments, reviews)
    /accounts/api/v1/  - Account management API (users, profiles)
    /api/schema/       - OpenAPI schema (JSON/YAML)
    /api/docs/         - Swagger UI (interactive API documentation)
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("", include("website.urls")),
    path("admin/", admin.site.urls),

    # DRF browsable auth
    path("api-auth/", include("rest_framework.urls")),

    # Accounts API
    path("accounts/api/v1/", include("accounts.api.v1.urls")),

    # Appointments, Payments, Reviews API
    path("api/v1/", include("appointments.api.v1.urls")),
    path("api/v1/", include("payments.api.v1.urls")),
    path("api/v1/", include("reviews.api.v1.urls")),

    # OpenAPI schema & Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
