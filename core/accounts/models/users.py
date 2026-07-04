from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField # type: ignore
from django.utils.text import slugify


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        if len(phone_number) != 11:
            raise ValueError('Phone number must have 11 character!')


        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
            
        return self.create_user(phone_number, password, **extra_fields)

class User(AbstractBaseUser,PermissionsMixin):
    USER_TYPE = [
        ('admin', 'Admin'),
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    ]
    
    
    email = models.EmailField(blank=True, null=True, unique=True)
    phone_number = PhoneNumberField(unique=True, max_length=20)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(
        max_length=7,
        choices=USER_TYPE,
        default='patient'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return str(self.phone_number)
        
    