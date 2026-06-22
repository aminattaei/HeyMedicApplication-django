from django.db import models


class Payment(models.Model):
    """
    Tracks payment transactions for appointments.

    Status flow:
        pending   → successful (after gateway callback confirms)
        pending   → failed     (after gateway reports failure)
        successful → refunded  (if a refund is processed)

    After a successful payment, the linked appointment's status
    should be updated to 'confirmed'.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name="نوبت"
    )
    patient = models.ForeignKey(
        'accounts.PatientProfile',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="بیمار"
    )
    amount = models.PositiveIntegerField(verbose_name="مبلغ (تومان)")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت"
    )
    gateway_ref = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="شماره مرجع درگاه"
    )
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پرداخت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"{self.patient.full_name} - {self.amount} Toman ({self.get_status_display()})"
