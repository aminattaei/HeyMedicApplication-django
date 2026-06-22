from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from accounts.models import User, DoctorProfile, PatientProfile, Specialty
from appointments.models import TimeSlot, Appointment
from payments.models import Payment
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


class PatientDashboardView(LoginRequiredMixin, TemplateView):
    """Patient dashboard showing stats, upcoming appointments, payments, and reviews."""
    template_name = "website/dashboard/patient.html"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'patient':
            return redirect('website:home_page')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient = self.request.user.patient_profile
        status_filter = self.request.GET.get('status')

        all_appts = Appointment.objects.filter(patient=patient)
        ctx['stats'] = {
            'total': all_appts.count(),
            'pending': all_appts.filter(status='pending').count(),
            'confirmed': all_appts.filter(status='confirmed').count(),
            'completed': all_appts.filter(status='completed').count(),
            'cancelled': all_appts.filter(status='cancelled').count(),
        }

        upcoming = all_appts.filter(status__in=['pending', 'confirmed'])
        if status_filter in ('pending', 'confirmed'):
            upcoming = upcoming.filter(status=status_filter)
        ctx['upcoming_appointments'] = upcoming.select_related(
            'doctor', 'doctor__specialty', 'time_slot'
        )[:10]

        ctx['recent_payments'] = Payment.objects.filter(
            patient=patient
        ).select_related('appointment', 'appointment__doctor')[:5]

        ctx['recent_reviews'] = Review.objects.filter(
            patient=patient
        ).select_related('doctor')[:5]

        return ctx


class DoctorDashboardView(LoginRequiredMixin, TemplateView):
    """Doctor dashboard with stats, revenue chart, weekly calendar, and appointment management."""
    template_name = "website/dashboard/doctor.html"
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'doctor':
            return redirect('website:home_page')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.utils import timezone
        from django.db.models import Sum, Count
        from datetime import timedelta

        today = timezone.now().date()
        doctor_profile = self.request.user.doctor_profile
        status_filter = self.request.GET.get('status')
        search = self.request.GET.get('search')

        all_appts = Appointment.objects.filter(doctor=doctor_profile)

        ctx['doctor_profile'] = doctor_profile

        ctx['stats'] = {
            'total_appointments': all_appts.count(),
            'today_count': all_appts.filter(time_slot__date=today).count(),
            'total_patients': all_appts.values('patient').distinct().count(),
            'total_revenue': Payment.objects.filter(
                appointment__doctor=doctor_profile, status='successful'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }

        ctx['today_appointments'] = all_appts.filter(
            time_slot__date=today
        ).select_related('patient', 'time_slot')

        filtered_appts = all_appts.select_related('patient', 'time_slot')
        if status_filter:
            filtered_appts = filtered_appts.filter(status=status_filter)
        if search:
            filtered_appts = filtered_appts.filter(patient__full_name__icontains=search)
        ctx['all_appointments'] = filtered_appts[:30]

        ctx['time_slots'] = TimeSlot.objects.filter(
            doctor=doctor_profile
        ).order_by('-date', 'start_time')[:20]

        ctx['recent_reviews'] = Review.objects.filter(
            doctor=doctor_profile
        ).select_related('patient')[:5]

        # Weekly calendar data
        start_of_week = today - timedelta(days=today.weekday())
        weekly_days = []
        day_labels = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
        for i in range(7):
            d = start_of_week + timedelta(days=i)
            weekly_days.append({'label': day_labels[i], 'date': d.strftime('%m/%d'), 'raw': d})
        ctx['weekly_days'] = weekly_days

        ctx['weekly_slots'] = TimeSlot.objects.filter(
            doctor=doctor_profile,
            date__gte=start_of_week,
            date__lt=start_of_week + timedelta(days=7),
        ).order_by('date', 'start_time')

        weekly_hours = []
        for h in range(7, 21):
            weekly_hours.append(f'{h:02d}:00')
        ctx['weekly_hours'] = weekly_hours

        # Monthly revenue for chart (last 6 months)
        monthly_revenue = []
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            if i > 0:
                next_month_start = (month_start + timedelta(days=32)).replace(day=1)
            else:
                next_month_start = today + timedelta(days=1)
            total = Payment.objects.filter(
                appointment__doctor=doctor_profile,
                status='successful',
                paid_at__gte=month_start,
                paid_at__lt=next_month_start,
            ).aggregate(total=Sum('amount'))['total'] or 0
            monthly_revenue.append({
                'month': month_start.strftime('%Y/%m'),
                'total': total,
            })
        ctx['monthly_revenue'] = monthly_revenue

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


class UserProfileView(LoginRequiredMixin, View):
    """
    User profile page with view and edit functionality.
    Displays user info and profile-specific fields based on role.
    """

    template_name = "website/profile.html"
    login_url = "/accounts/login/"

    def get(self, request):
        user = request.user
        context = {'user': user}

        if user.role == 'patient':
            try:
                context['patient_profile'] = user.patient_profile
                context['profile'] = user.patient_profile
            except PatientProfile.DoesNotExist:
                context['patient_profile'] = None
                context['profile'] = None

        elif user.role == 'doctor':
            try:
                context['doctor_profile'] = user.doctor_profile
                context['profile'] = user.doctor_profile
                context['specialties'] = Specialty.objects.all()
            except DoctorProfile.DoesNotExist:
                context['doctor_profile'] = None
                context['profile'] = None

        return render(request, self.template_name, context)

    def post(self, request):
        user = request.user
        context = {'user': user}

        if request.POST.get('form_type') == 'change_password':
            return redirect('website:change_password')

        user.email = request.POST.get('email', user.email)
        user.save()

        if user.role == 'patient':
            profile, _ = PatientProfile.objects.get_or_create(user=user)
            profile.full_name = request.POST.get('full_name', profile.full_name)
            profile.national_id = request.POST.get('national_id', profile.national_id)
            birth_date = request.POST.get('birth_date')
            if birth_date:
                profile.birth_date = birth_date
            profile.gender = request.POST.get('gender', profile.gender)
            profile.save()
            context['patient_profile'] = profile
            context['profile'] = profile

        elif user.role == 'doctor':
            profile, _ = DoctorProfile.objects.get_or_create(user=user)
            profile.full_name = request.POST.get('full_name', profile.full_name)
            profile.medical_license_no = request.POST.get('medical_license_no', profile.medical_license_no)
            profile.bio = request.POST.get('bio', profile.bio)
            profile.clinic_address = request.POST.get('clinic_address', profile.clinic_address)
            price = request.POST.get('price')
            if price:
                profile.price = int(price)
            specialty_id = request.POST.get('specialty')
            if specialty_id:
                profile.specialty_id = specialty_id
            profile.save()
            context['doctor_profile'] = profile
            context['profile'] = profile
            context['specialties'] = Specialty.objects.all()

        messages.success(request, "پروفایل با موفقیت به‌روزرسانی شد.")
        return render(request, self.template_name, context)


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
