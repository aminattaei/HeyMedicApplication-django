from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash

from .models import User


class LoginView(View):
    """Login page using phone number and password."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('website:home_page')
        return render(request, 'website/auth/login.html')

    def post(self, request):
        phone_number = request.POST.get('phone_number', '')
        password = request.POST.get('password', '')
        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None:
            login(request, user)
            return redirect('website:home_page')
        return render(request, 'website/auth/login.html', {
            'error': 'شماره موبایل یا رمز عبور اشتباه است.'
        })


class RegisterView(View):
    """Register page for new users."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('website:home_page')
        return render(request, 'website/auth/register.html')

    def post(self, request):
        phone_number = request.POST.get('phone_number', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        role = request.POST.get('role', 'patient')

        if User.objects.filter(phone_number=phone_number).exists():
            return render(request, 'website/auth/register.html', {
                'error': 'این شماره موبایل قبلاً ثبت شده است.'
            })

        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            email=email if email else None,
            role=role,
        ) # type: ignore

        if role == 'patient':
            from .models import PatientProfile
            PatientProfile.objects.create(
                user=user,
                full_name='',
                national_id='0000000000',
                birth_date='2000-01-01',
                gender='other',
            )
        elif role == 'doctor':
            from .models import DoctorProfile, Specialty
            default_specialty, _ = Specialty.objects.get_or_create(
                title='عمومی',
                defaults={'slug': 'general'}
            )
            DoctorProfile.objects.create(
                user=user,
                specialty=default_specialty,
                full_name='',
                medical_license_no=f'NEW-{user.pk}',
                clinic_address='',
                price=0,
            )

        login(request, user)
        return redirect('website:home_page')


class LogoutView(View):
    """Logout and redirect to home."""

    def get(self, request):
        logout(request)
        return redirect('website:home_page')


class ChangePasswordView(LoginRequiredMixin, View):
    """Change user password with old password verification."""

    template_name = "website/auth/change_password.html"
    login_url = "/accounts/login/"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        user = request.user
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password1', '')
        new_password_confirm = request.POST.get('new_password2', '')

        if not user.check_password(old_password):
            messages.error(request, "رمز عبور فعلی اشتباه است.")
            return render(request, self.template_name)

        if new_password != new_password_confirm:
            messages.error(request, "رمز عبور جدید و تکرار آن مطابقت ندارند.")
            return render(request, self.template_name)

        if len(new_password) < 8:
            messages.error(request, "رمز عبور باید حداقل ۸ کاراکتر باشد.")
            return render(request, self.template_name)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "رمز عبور با موفقیت تغییر کرد.")
        return render(request, self.template_name)