from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'rating_display', 'comment_preview', 'created_at')
    list_filter = ('rating', 'created_at', 'doctor__specialty')
    search_fields = ('patient__full_name', 'doctor__full_name', 'comment')
    raw_id_fields = ('patient', 'doctor', 'appointment')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    def rating_display(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        if obj.rating >= 4:
            color = 'green'
        elif obj.rating >= 3:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color:{};">{} ({}/5)</span>', color, stars, obj.rating)

    rating_display.short_description = 'Rating'

    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'

    comment_preview.short_description = 'Comment'
