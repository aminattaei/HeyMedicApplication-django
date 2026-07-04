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
    
    national_id = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name="کد ملی"
    )
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        verbose_name="جنسیت"
    )

    full_name = models.CharField(max_length=255, verbose_name="نام کامل")
    email = models.EmailField(
        "Email Address",
        blank=True,
        null=True,
        unique=True
    )
    birth_date = models.DateField(verbose_name="تاریخ تولد")


    class Meta:
        verbose_name = "Patient Profile"
        verbose_name_plural = "Patients Profile"
    
    def __str__(self):
        return self.full_name
