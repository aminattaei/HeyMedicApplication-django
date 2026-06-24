from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.html import format_html

from .models import User, PatientProfile, Specialty, DoctorProfile


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class PatientProfileInline(admin.StackedInline):
    model = PatientProfile
    can_delete = False
    verbose_name_plural = 'Patient Profile'
    fields = ('full_name', 'national_id', 'birth_date', 'gender')


class DoctorProfileInline(admin.StackedInline):
    model = DoctorProfile
    can_delete = False
    verbose_name_plural = 'Doctor Profile'
    fields = ('full_name', 'specialty', 'medical_license_no', 'bio', 'clinic_address', 'price')


class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm

    list_display = ('phone_number', 'email', 'role', 'is_verified', 'is_staff', 'get_created_at')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active', 'created_at')
    search_fields = ('phone_number', 'email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'last_login')

    fieldsets = (
        (None, {'fields': ('phone_number', 'email', 'password')}),
        ('Role & Verification', {'fields': ('role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )

    def has_add_permission(self, request):
        return False

    def get_created_at(self, obj):
        return obj.created_at

    get_created_at.short_description = 'Created At'

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        if obj.role == 'patient':
            return [PatientProfileInline]
        elif obj.role == 'doctor':
            return [DoctorProfileInline]
        return []


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'national_id', 'gender', 'birth_date')
    list_filter = ('gender',)
    search_fields = ('full_name', 'national_id', 'user__phone_number')
    raw_id_fields = ('user',)
    readonly_fields = ('user',)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'doctor_count')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)

    def doctor_count(self, obj):
        return obj.doctors.count()

    doctor_count.short_description = 'Doctors'


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialty', 'medical_license_no', 'price', 'rating_display', 'user')
    list_filter = ('specialty', 'rating_avg')
    search_fields = ('full_name', 'medical_license_no', 'user__phone_number')
    raw_id_fields = ('user', 'specialty')
    readonly_fields = ('rating_avg',)
    fieldsets = (
        ('Personal Info', {'fields': ('user', 'full_name', 'specialty', 'medical_license_no')}),
        ('Professional Info', {'fields': ('bio', 'clinic_address', 'price')}),
        ('Rating', {'fields': ('rating_avg',)}),
    )

    def rating_display(self, obj):
        if obj.rating_avg >= 4.0:
            color = 'green'
        elif obj.rating_avg >= 3.0:
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color:{};">{:.1f} / 5.0</span>', color, obj.rating_avg)

    rating_display.short_description = 'Rating'


admin.site.register(User, CustomUserAdmin)
