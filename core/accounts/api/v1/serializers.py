from rest_framework import serializers

from accounts.models import User
from accounts.models import PatientProfile
from accounts.models import Specialty



class UserSerializer(serializers.ModelSerializer):
    role = serializers.ReadOnlyField()
    """
    This serializer get an instance of User model and serializing it
    """
    class Meta:
        model = User
        fields = ('email',"phone_number",'role',"created_at")



class PatientProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="user.role", read_only=True)
    """
    This serializer get an instance of PatientProfile model and serializing it
    """
    class Meta:
        model = PatientProfile
        fields = ("user","full_name","role","national_id","birth_date","gender")




class SpecialtySerializer(serializers.ModelSerializer):
    
    """
    This serializer get an instance of Specialty model and serializing it
    """
    class Meta:
        model = Specialty
        fields = ("title","slug")




class UserSerializer(serializers.ModelSerializer):
    role = serializers.ReadOnlyField()
    """
    This serializer get an instance of User model and serializing it
    """
    class Meta:
        model = User
        fields = ('email',"phone_number",'role',"created_at")
