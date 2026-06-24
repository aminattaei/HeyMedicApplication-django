from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import TimeSlot, Appointment


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'status_display', 'is_available')
    list_filter = ('date', 'is_available', 'doctor__specialty')
    search_fields = ('doctor__full_name', 'doctor__user__phone_number')
    raw_id_fields = ('doctor',)
    date_hierarchy = 'date'
    list_editable = ('is_available',)
    actions = ['make_available', 'make_unavailable', 'delete_past_slots']

    def status_display(self, obj):
        if obj.is_available:
            return format_html('<span style="color:green;">Available</span>')
        return format_html('<span style="color:red;">Booked</span>')

    status_display.short_description = 'Status'

    @admin.action(description='Mark selected slots as available')
    def make_available(self, request, queryset):
        count = queryset.update(is_available=True)
        self.message_user(request, f'{count} slot(s) marked as available.')

    @admin.action(description='Mark selected slots as unavailable')
    def make_unavailable(self, request, queryset):
        count = queryset.update(is_available=False)
        self.message_user(request, f'{count} slot(s) marked as unavailable.')

    @admin.action(description='Delete past time slots')
    def delete_past_slots(self, request, queryset):
        today = timezone.now().date()
        past_slots = queryset.filter(date__lt=today)
        count = past_slots.count()
        past_slots.delete()
        self.message_user(request, f'{count} past slot(s) deleted.')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'slot_info', 'status_display', 'created_at')
    list_filter = ('status', 'doctor__specialty', 'created_at')
    search_fields = ('patient__full_name', 'doctor__full_name', 'patient__user__phone_number')
    raw_id_fields = ('patient', 'doctor', 'time_slot')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    actions = ['confirm_appointments', 'cancel_appointments', 'complete_appointments']

    def slot_info(self, obj):
        return f"{obj.time_slot.date} {obj.time_slot.start_time}-{obj.time_slot.end_time}"

    slot_info.short_description = 'Time Slot'

    def status_display(self, obj):
        colors = {
            'pending': 'orange',
            'confirmed': 'blue',
            'completed': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html('<span style="color:{};">{}</span>', color, obj.get_status_display())

    status_display.short_description = 'Status'

    @admin.action(description='Confirm selected appointments')
    def confirm_appointments(self, request, queryset):
        count = queryset.filter(status='pending').update(status='confirmed')
        self.message_user(request, f'{count} appointment(s) confirmed.')

    @admin.action(description='Cancel selected appointments')
    def cancel_appointments(self, request, queryset):
        count = queryset.filter(status__in=['pending', 'confirmed']).update(status='cancelled')
        self.message_user(request, f'{count} appointment(s) cancelled.')

    @admin.action(description='Complete selected appointments')
    def complete_appointments(self, request, queryset):
        count = queryset.filter(status='confirmed').update(status='completed')
        self.message_user(request, f'{count} appointment(s) marked as completed.')
