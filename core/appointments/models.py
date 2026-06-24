from django.db import models
from django.core.exceptions import ValidationError


class TimeSlot(models.Model):
    """
    Represents an available time slot that a doctor defines for booking.

    Each slot is tied to a specific doctor, date, and start/end time.
    Patients can only book slots where is_available is True.
    The unique_together constraint prevents a doctor from having
    overlapping slots at the same start time on the same date.
    """

    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name="پزشک"
    )
    date = models.DateField(verbose_name="تاریخ")
    start_time = models.TimeField(verbose_name="ساعت شروع")
    end_time = models.TimeField(verbose_name="ساعت پایان")
    is_available = models.BooleanField(default=True, verbose_name="قابل رزرو")

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name = "Time Slot"
        verbose_name_plural = "Time Slots"
        unique_together = ['doctor', 'date', 'start_time']

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    def __str__(self):
        return f"{self.doctor.full_name} - {self.date} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """
    Represents a booked appointment between a patient and a doctor.

    Status flow:
        pending   → confirmed → completed
        pending   → cancelled
        confirmed → cancelled

    Each appointment is linked to exactly one TimeSlot (OneToOne),
    and the slot's is_available flag is set to False upon booking.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    patient = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="بیمار"
    )
    doctor = models.ForeignKey(
        'accounts.DoctorProfile',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name="پزشک"
    )
    time_slot = models.OneToOneField(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='appointment',
        verbose_name="ساعت نوبت"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت"
    )
    notes = models.TextField(blank=True, verbose_name="یادداشت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"

    def __str__(self):
        return f"{self.patient.full_name} -> {self.doctor.full_name} ({self.get_status_display()})"
