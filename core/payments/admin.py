from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'appointment', 'amount', 'status', 'paid_at', 'created_at']
    list_filter = ['status']
    search_fields = ['patient__full_name', 'gateway_ref']
