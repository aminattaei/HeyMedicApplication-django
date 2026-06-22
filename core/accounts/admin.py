# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User,PatientProfile,Specialty,DoctorProfile

#TODO: admin.py will should  complete

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('phone_number', 'email', 'role')

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = ('phone_number', 'email', 'role', 'is_verified', 'is_staff', 'get_created_at')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('phone_number', 'email')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('phone_number', 'email', 'password')}),
        ('Role & Verification', {'fields': ('role', 'is_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'email', 'role', 'password1', 'password2'),
        }),
    )
    
    def get_created_at(self, obj):
        return obj.created_at


admin.site.register(User, CustomUserAdmin)
admin.site.register(PatientProfile)
admin.site.register(Specialty)
admin.site.register(DoctorProfile)