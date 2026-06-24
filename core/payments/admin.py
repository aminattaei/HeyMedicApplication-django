from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'appointment_info', 'amount_display', 'status_display', 'gateway_ref', 'paid_at', 'created_at')
    list_filter = ('status', 'created_at', 'paid_at')
    search_fields = ('patient__full_name', 'gateway_ref', 'patient__user__phone_number')
    raw_id_fields = ('patient', 'appointment')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_successful', 'mark_failed', 'mark_refunded']

    def appointment_info(self, obj):
        return f"{obj.appointment.doctor.full_name} - {obj.appointment.time_slot.date}"

    appointment_info.short_description = 'Appointment'

    def amount_display(self, obj):
        return f"{obj.amount:,} Toman"

    amount_display.short_description = 'Amount'

    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'successful': 'green',
            'failed': 'red',
            'refunded': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color:{};">{}</span>', color, obj.get_status_display())

    status_display.short_description = 'Status'

    @admin.action(description='Mark selected payments as successful')
    def mark_successful(self, request, queryset):
        from django.utils import timezone
        count = queryset.filter(status='pending').update(status='successful', paid_at=timezone.now())
        self.message_user(request, f'{count} payment(s) marked as successful.')

    @admin.action(description='Mark selected payments as failed')
    def mark_failed(self, request, queryset):
        count = queryset.filter(status='pending').update(status='failed')
        self.message_user(request, f'{count} payment(s) marked as failed.')

    @admin.action(description='Mark selected payments as refunded')
    def mark_refunded(self, request, queryset):
        count = queryset.filter(status='successful').update(status='refunded')
        self.message_user(request, f'{count} payment(s) marked as refunded.')
