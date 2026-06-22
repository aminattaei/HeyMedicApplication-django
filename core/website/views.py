from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.models import User, DoctorProfile, Specialty
from appointments.models import TimeSlot, Appointment
from reviews.models import Review


class HomePageTemplateView(TemplateView):
    template_name = "website/index.html"


class DoctorListView(ListView):
    """List all doctors with optional search and specialty filter."""
    model = DoctorProfile
    template_name = "website/doctors/list.html"
    context_object_name = "doctors"
    paginate_by = 12

    def get_queryset(self):
        qs = DoctorProfile.objects.select_related('specialty', 'user').all()
        search = self.request.GET.get('search')
        specialty = self.request.GET.get('specialty')
        if search:
            qs = qs.filter(full_name__icontains=search)
        if specialty:
            qs = qs.filter(specialty__slug=specialty)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['specialties'] = Specialty.objects.all()
        return ctx


class DoctorProfileView(DetailView):
    """Doctor profile page with reviews and available slots."""
    model = DoctorProfile
    template_name = "website/doctors/profile.html"
    context_object_name = "doctor"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['reviews'] = Review.objects.filter(
            doctor=self.object
        ).select_related('patient')[:10]
        return ctx


class MyAppointmentsView(LoginRequiredMixin, ListView):
    """Patient's appointment list."""
    template_name = "website/appointments/my.html"
    context_object_name = "appointments"
    login_url = "/accounts/login/"

    def get_queryset(self):
        return Appointment.objects.filter(
            patient__user=self.request.user
        ).select_related(
            'doctor', 'doctor__specialty', 'time_slot', 'review'
        )


class DoctorDashboardView(LoginRequiredMixin, TemplateView):
    """Doctor dashboard showing today's appointments and time slots."""
    template_name = "website/dashboard/doctor.html"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'doctor':
            return redirect('website:home_page')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.utils import timezone
        today = timezone.now().date()
        doctor_profile = self.request.user.doctor_profile

        ctx['doctor_profile'] = doctor_profile
        ctx['today_appointments'] = Appointment.objects.filter(
            doctor=doctor_profile,
            time_slot__date=today
        ).select_related('patient', 'time_slot')
        ctx['all_appointments'] = Appointment.objects.filter(
            doctor=doctor_profile
        ).select_related('patient', 'time_slot')[:20]
        ctx['time_slots'] = TimeSlot.objects.filter(
            doctor=doctor_profile
        ).order_by('-date', 'start_time')[:20]
        return ctx


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
        )

        if role == 'patient':
            from accounts.models import PatientProfile
            PatientProfile.objects.create(
                user=user,
                full_name='',
                national_id='0000000000',
                birth_date='2000-01-01',
                gender='other',
            )
        elif role == 'doctor':
            from accounts.models import DoctorProfile, Specialty
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
