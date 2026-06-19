# models/__init__.py
from .users import User
from .patientProfile import PatientProfile
from .dctorProfile import DoctorProfile
from .specialty import Specialty

__all__ = [
    'User',
    'patientProfile',
    'dctorProfile',
    'Specialty',
]