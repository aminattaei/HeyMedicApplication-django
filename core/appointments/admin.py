from django.contrib import admin
from .models import TimeSlot, Appointment


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'is_available']
    list_filter = ['date', 'is_available', 'doctor__specialty']
    search_fields = ['doctor__full_name']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'status', 'created_at']
    list_filter = ['status', 'doctor__specialty']
    search_fields = ['patient__full_name', 'doctor__full_name']
