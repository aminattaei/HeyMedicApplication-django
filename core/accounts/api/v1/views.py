from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .serializers import (
    UserSerializer,
    PatientProfileSerializer,
    SpecialtySerializer
)

from accounts.models import User, PatientProfile, Specialty


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin-only endpoint for viewing user instances.
    """
    permission_classes = [IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.all()


class IsOwnerOrAdmin(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user or request.user.role == 'admin'


class PatientProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing PatientProfile instances.
    Patients can only access their own profile; admins can access all.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PatientProfileSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return PatientProfile.objects.all()
        return PatientProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SpecialtyViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Specialty instance
    """
    permission_classes= [IsAuthenticatedOrReadOnly]
    serializer_class = SpecialtySerializer
    queryset = Specialty.objects.all()