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