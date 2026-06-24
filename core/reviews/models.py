from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """
    Represents a patient's review and rating for a doctor after an appointment.

    Rules:
        - Only completed appointments can be reviewed.
        - Each appointment can have at most one review (OneToOne).
        - On save, the doctor's rating_avg is recalculated automatically.
    """

    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name="نوبت"
    )
    patient = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="بیمار"
    )
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="پزشک"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="امتیاز"
    )
    comment = models.TextField(blank=True, verbose_name="نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f"{self.patient.full_name} -> {self.doctor.full_name} ({self.rating}/5)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._update_doctor_rating()

    def _update_doctor_rating(self):
        from django.db.models import Avg
        avg = Review.objects.filter(doctor=self.doctor).aggregate(Avg('rating'))['rating__avg']
        self.doctor.rating_avg = round(avg, 1) if avg else 0.0
        self.doctor.save(update_fields=['rating_avg'])
