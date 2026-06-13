from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField # type: ignore
from django.utils.text import slugify




class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        
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

class User(AbstractUser):
    USER_TYPE = [
        ('admin', 'Admin'),
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    ]
    
    username = None
    email = models.EmailField(
        "Email Address",
        blank=True,
        null=True,
        unique=True
    )
    phone_number = PhoneNumberField(unique=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(
        max_length=10,
        choices=USER_TYPE,
        default='patient'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return str(self.phone_number)
    

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
        verbose_name = "پروفایل بیمار"
        verbose_name_plural = "پروفایل بیماران"
    
    def __str__(self):
        return self.full_name


class Specialty(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان تخصص")
    slug = models.SlugField(unique=True, blank=True, verbose_name="متن جایگزین")

    class Meta:
        ordering = ['title']
        verbose_name = "تخصص"
        verbose_name_plural = "تخصص‌ها"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class DoctorProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile'
    )
    specialty = models.ForeignKey(
        'Specialty', 
        on_delete=models.PROTECT, 
        related_name='doctors',
        verbose_name="تخصص"
    )
    full_name = models.CharField(max_length=255, verbose_name="نام کامل")
    medical_license_no = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="شماره نظام پزشکی"
    )
    bio = models.TextField(blank=True, verbose_name="بیوگرافی")
    clinic_address = models.TextField(verbose_name="آدرس کلینیک")
    price = models.PositiveIntegerField(verbose_name="هزینه نوبت (تومان)")
    rating_avg = models.FloatField(default=0.0, verbose_name="میانگین امتیاز")
    
    class Meta:
        verbose_name = "پروفایل پزشک"
        verbose_name_plural = "پروفایل پزشکان"
    
    def __str__(self):
        return f"{self.full_name} - {self.specialty.title}"