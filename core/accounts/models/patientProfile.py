from django.db import models
from .users import User

class PatientProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'مرد'),
        ('female', 'زن'),
        ('other', 'سایر'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='patient_profile'
    )
    full_name = models.CharField(max_length=255, verbose_name="نام کامل")
    national_id = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="کد ملی"
    )
    birth_date = models.DateField(verbose_name="تاریخ تولد")
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        verbose_name="جنسیت"
    )
    
    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patients Profile"
    
    def __str__(self):
        return self.full_name
