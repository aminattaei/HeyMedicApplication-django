from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .serializers import (
    UserSerializer,
    PatientProfileSerializer,
    SpecialtySerializer
)

from accounts.models import User,PatientProfile,Specialty


class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    permission_classes= [IsAuthenticatedOrReadOnly]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    

class PatientProfileViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing PatientProfile instance
    """
    permission_classes= [IsAuthenticatedOrReadOnly]
    serializer_class = PatientProfileSerializer
    queryset = PatientProfile.objects.all()

class SpecialtyViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Specialty instance
    """
    permission_classes= [IsAuthenticatedOrReadOnly]
    serializer_class = SpecialtySerializer
    queryset = Specialty.objects.all()