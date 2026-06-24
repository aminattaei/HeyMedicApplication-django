from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class HeyMedicAdminSite(admin.AdminSite):
    site_header = _("HeyMedic Administration")
    site_title = _("HeyMedic Admin")
    index_title = _("Platform Management")
    site_url = "/"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        from accounts.models import User, DoctorProfile, PatientProfile
        from appointments.models import Appointment, TimeSlot
        from payments.models import Payment
        from reviews.models import Review

        extra_context['stats'] = {
            'total_users': User.objects.count(),
            'total_doctors': DoctorProfile.objects.count(),
            'total_patients': PatientProfile.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'pending_appointments': Appointment.objects.filter(status='pending').count(),
            'completed_appointments': Appointment.objects.filter(status='completed').count(),
            'cancelled_appointments': Appointment.objects.filter(status='cancelled').count(),
            'total_payments': Payment.objects.count(),
            'successful_payments': Payment.objects.filter(status='successful').count(),
            'total_reviews': Review.objects.count(),
            'available_slots': TimeSlot.objects.filter(is_available=True).count(),
        }
        return super().index(request, extra_context=extra_context)


admin_site = HeyMedicAdminSite(name='heymedic_admin')
