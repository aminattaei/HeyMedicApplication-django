from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.urls import reverse_lazy
from datetime import timedelta
import json

from accounts.models import User, DoctorProfile, PatientProfile, Specialty
from appointments.models import TimeSlot, Appointment
from payments.models import Payment
from reviews.models import Review


class AdminRequiredMixin(LoginRequiredMixin):
    login_url = "/panel/login/"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        if request.user.role != 'admin':
            messages.error(request, "Access denied. Admin only.")
            return redirect('website:home_page')
        return super().dispatch(request, *args, **kwargs)


class AdminLoginView(View):
    def get(self, request):
        if request.user.is_authenticated and request.user.role == 'admin':
            return redirect('website:admin_dashboard')
        return render(request, 'website/admin/login.html')

    def post(self, request):
        phone_number = request.POST.get('phone_number', '')
        password = request.POST.get('password', '')
        user = authenticate(request, phone_number=phone_number, password=password)
        if user is not None and user.role == 'admin':
            login(request, user)
            return redirect('website:admin_dashboard')
        return render(request, 'website/admin/login.html', {
            'error': 'Phone number or password is incorrect.'
        })


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'website/admin/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()

        ctx['stats'] = {
            'total_users': User.objects.count(),
            'total_doctors': DoctorProfile.objects.count(),
            'total_patients': PatientProfile.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'pending_appointments': Appointment.objects.filter(status='pending').count(),
            'confirmed_appointments': Appointment.objects.filter(status='confirmed').count(),
            'completed_appointments': Appointment.objects.filter(status='completed').count(),
            'cancelled_appointments': Appointment.objects.filter(status='cancelled').count(),
            'total_payments': Payment.objects.count(),
            'successful_payments': Payment.objects.filter(status='successful').count(),
            'total_revenue': Payment.objects.filter(status='successful').aggregate(
                total=Sum('amount'))['total'] or 0,
            'total_reviews': Review.objects.count(),
            'available_slots': TimeSlot.objects.filter(is_available=True).count(),
        }

        ctx['recent_appointments'] = Appointment.objects.select_related(
            'patient', 'doctor', 'doctor__specialty', 'time_slot'
        ).order_by('-created_at')[:10]

        ctx['recent_payments'] = Payment.objects.select_related(
            'patient', 'appointment', 'appointment__doctor'
        ).order_by('-created_at')[:10]

        ctx['recent_reviews'] = Review.objects.select_related(
            'patient', 'doctor', 'doctor__specialty'
        ).order_by('-created_at')[:10]

        return ctx


class AdminUserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.all().order_by('-created_at')
        search = self.request.GET.get('search')
        role = self.request.GET.get('role')
        if search:
            qs = qs.filter(Q(phone_number__icontains=search) | Q(email__icontains=search))
        if role:
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Users'
        ctx['model_name'] = 'user'
        ctx['headers'] = ['Phone', 'Email', 'Role', 'Verified', 'Staff', 'Created']
        ctx['add_url'] = 'website:admin_user_add'
        ctx['search_placeholder'] = 'Search by phone or email...'
        return ctx


class AdminUserCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add User',
            'model_name': 'user',
            'fields': [
                {'name': 'phone_number', 'label': 'Phone Number', 'type': 'tel', 'required': True},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': False},
                {'name': 'password', 'label': 'Password', 'type': 'password', 'required': True},
                {'name': 'role', 'label': 'Role', 'type': 'select', 'required': True,
                 'options': [('admin', 'Admin'), ('patient', 'Patient'), ('doctor', 'Doctor')]},
                {'name': 'is_verified', 'label': 'Verified', 'type': 'checkbox', 'required': False},
                {'name': 'is_staff', 'label': 'Staff', 'type': 'checkbox', 'required': False},
            ],
            'back_url': 'website:admin_user_list',
        })

    def post(self, request):
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email') or None
        password = request.POST.get('password')
        role = request.POST.get('role', 'patient')
        is_verified = request.POST.get('is_verified') == 'on'
        is_staff = request.POST.get('is_staff') == 'on'

        if User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'This phone number already exists.')
            return redirect('website:admin_user_add')

        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            email=email,
            role=role,
            is_verified=is_verified,
            is_staff=is_staff,
        )

        if role == 'patient':
            PatientProfile.objects.create(
                user=user, full_name='', national_id=f'000000000{user.pk}',
                birth_date='2000-01-01', gender='other'
            )
        elif role == 'doctor':
            default_spec, _ = Specialty.objects.get_or_create(
                title='General', defaults={'slug': 'general'}
            )
            DoctorProfile.objects.create(
                user=user, specialty=default_spec, full_name='',
                medical_license_no=f'MD-{user.pk}', clinic_address='', price=0
            )

        messages.success(request, f'User {phone_number} created successfully.')
        return redirect('website:admin_user_list')


class AdminUserEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit User - {user.phone_number}',
            'model_name': 'user',
            'instance': user,
            'fields': [
                {'name': 'phone_number', 'label': 'Phone Number', 'type': 'tel', 'required': True, 'value': user.phone_number},
                {'name': 'email', 'label': 'Email', 'type': 'email', 'required': False, 'value': user.email or ''},
                {'name': 'role', 'label': 'Role', 'type': 'select', 'required': True,
                 'options': [('admin', 'Admin'), ('patient', 'Patient'), ('doctor', 'Doctor')],
                 'value': user.role},
                {'name': 'is_verified', 'label': 'Verified', 'type': 'checkbox', 'required': False,
                 'checked': user.is_verified},
                {'name': 'is_staff', 'label': 'Staff', 'type': 'checkbox', 'required': False,
                 'checked': user.is_staff},
                {'name': 'is_active', 'label': 'Active', 'type': 'checkbox', 'required': False,
                 'checked': user.is_active},
            ],
            'back_url': 'website:admin_user_list',
        })

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        user.email = request.POST.get('email') or None
        user.role = request.POST.get('role', user.role)
        user.is_verified = request.POST.get('is_verified') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_active = request.POST.get('is_active') == 'on'

        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)

        user.save()
        messages.success(request, f'User {user.phone_number} updated successfully.')
        return redirect('website:admin_user_list')


class AdminUserDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('website:admin_user_list')


class AdminDoctorListView(AdminRequiredMixin, ListView):
    model = DoctorProfile
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = DoctorProfile.objects.select_related('user', 'specialty').all()
        search = self.request.GET.get('search')
        specialty = self.request.GET.get('specialty')
        if search:
            qs = qs.filter(Q(full_name__icontains=search) | Q(medical_license_no__icontains=search))
        if specialty:
            qs = qs.filter(specialty__id=specialty)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Doctors'
        ctx['model_name'] = 'doctor'
        ctx['headers'] = ['Name', 'Specialty', 'License No', 'Price', 'Rating', 'Phone']
        ctx['add_url'] = 'website:admin_doctor_add'
        ctx['specialties'] = Specialty.objects.all()
        ctx['search_placeholder'] = 'Search by name or license...'
        return ctx


class AdminDoctorCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add Doctor',
            'model_name': 'doctor',
            'fields': [
                {'name': 'user_phone', 'label': 'User Phone', 'type': 'tel', 'required': True},
                {'name': 'user_password', 'label': 'User Password', 'type': 'password', 'required': True},
                {'name': 'user_email', 'label': 'User Email', 'type': 'email', 'required': False},
                {'name': 'full_name', 'label': 'Full Name', 'type': 'text', 'required': True},
                {'name': 'specialty', 'label': 'Specialty', 'type': 'select', 'required': True,
                 'options': [(s.pk, s.title) for s in Specialty.objects.all()]},
                {'name': 'medical_license_no', 'label': 'Medical License No', 'type': 'text', 'required': True},
                {'name': 'bio', 'label': 'Bio', 'type': 'textarea', 'required': False},
                {'name': 'clinic_address', 'label': 'Clinic Address', 'type': 'textarea', 'required': True},
                {'name': 'price', 'label': 'Price (Toman)', 'type': 'number', 'required': True},
            ],
            'back_url': 'website:admin_doctor_list',
        })

    def post(self, request):
        phone = request.POST.get('user_phone')
        password = request.POST.get('user_password')
        email = request.POST.get('user_email') or None

        if User.objects.filter(phone_number=phone).exists():
            messages.error(request, 'This phone number already exists.')
            return redirect('website:admin_doctor_add')

        user = User.objects.create_user(
            phone_number=phone, password=password, email=email, role='doctor', is_verified=True
        )

        DoctorProfile.objects.create(
            user=user,
            full_name=request.POST.get('full_name'),
            specialty_id=request.POST.get('specialty'),
            medical_license_no=request.POST.get('medical_license_no'),
            bio=request.POST.get('bio', ''),
            clinic_address=request.POST.get('clinic_address'),
            price=int(request.POST.get('price', 0)),
        )

        messages.success(request, 'Doctor created successfully.')
        return redirect('website:admin_doctor_list')


class AdminDoctorEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        doctor = get_object_or_404(DoctorProfile, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit Doctor - {doctor.full_name}',
            'model_name': 'doctor',
            'instance': doctor,
            'fields': [
                {'name': 'full_name', 'label': 'Full Name', 'type': 'text', 'required': True, 'value': doctor.full_name},
                {'name': 'specialty', 'label': 'Specialty', 'type': 'select', 'required': True,
                 'options': [(s.pk, s.title) for s in Specialty.objects.all()],
                 'value': doctor.specialty_id},
                {'name': 'medical_license_no', 'label': 'Medical License No', 'type': 'text', 'required': True,
                 'value': doctor.medical_license_no},
                {'name': 'bio', 'label': 'Bio', 'type': 'textarea', 'required': False, 'value': doctor.bio},
                {'name': 'clinic_address', 'label': 'Clinic Address', 'type': 'textarea', 'required': True,
                 'value': doctor.clinic_address},
                {'name': 'price', 'label': 'Price (Toman)', 'type': 'number', 'required': True, 'value': doctor.price},
                {'name': 'rating_avg', 'label': 'Rating Avg', 'type': 'number', 'required': False,
                 'value': doctor.rating_avg, 'readonly': True},
            ],
            'back_url': 'website:admin_doctor_list',
        })

    def post(self, request, pk):
        doctor = get_object_or_404(DoctorProfile, pk=pk)
        doctor.full_name = request.POST.get('full_name', doctor.full_name)
        doctor.specialty_id = request.POST.get('specialty', doctor.specialty_id)
        doctor.medical_license_no = request.POST.get('medical_license_no', doctor.medical_license_no)
        doctor.bio = request.POST.get('bio', doctor.bio)
        doctor.clinic_address = request.POST.get('clinic_address', doctor.clinic_address)
        price = request.POST.get('price')
        if price:
            doctor.price = int(price)
        doctor.save()
        messages.success(request, 'Doctor updated successfully.')
        return redirect('website:admin_doctor_list')


class AdminDoctorDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        doctor = get_object_or_404(DoctorProfile, pk=pk)
        doctor.delete()
        messages.success(request, 'Doctor deleted successfully.')
        return redirect('website:admin_doctor_list')


class AdminPatientListView(AdminRequiredMixin, ListView):
    model = PatientProfile
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = PatientProfile.objects.select_related('user').all()
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(Q(full_name__icontains=search) | Q(national_id__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Patients'
        ctx['model_name'] = 'patient'
        ctx['headers'] = ['Name', 'National ID', 'Gender', 'Birth Date', 'Phone']
        ctx['add_url'] = 'website:admin_patient_add'
        ctx['search_placeholder'] = 'Search by name or national ID...'
        return ctx


class AdminPatientCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add Patient',
            'model_name': 'patient',
            'fields': [
                {'name': 'user_phone', 'label': 'User Phone', 'type': 'tel', 'required': True},
                {'name': 'user_password', 'label': 'User Password', 'type': 'password', 'required': True},
                {'name': 'user_email', 'label': 'User Email', 'type': 'email', 'required': False},
                {'name': 'full_name', 'label': 'Full Name', 'type': 'text', 'required': True},
                {'name': 'national_id', 'label': 'National ID', 'type': 'text', 'required': True},
                {'name': 'birth_date', 'label': 'Birth Date', 'type': 'date', 'required': True},
                {'name': 'gender', 'label': 'Gender', 'type': 'select', 'required': True,
                 'options': [('male', 'Male'), ('female', 'Female'), ('other', 'Other')]},
            ],
            'back_url': 'website:admin_patient_list',
        })

    def post(self, request):
        phone = request.POST.get('user_phone')
        password = request.POST.get('user_password')
        email = request.POST.get('user_email') or None

        if User.objects.filter(phone_number=phone).exists():
            messages.error(request, 'This phone number already exists.')
            return redirect('website:admin_patient_add')

        user = User.objects.create_user(
            phone_number=phone, password=password, email=email, role='patient', is_verified=True
        )

        PatientProfile.objects.create(
            user=user,
            full_name=request.POST.get('full_name'),
            national_id=request.POST.get('national_id'),
            birth_date=request.POST.get('birth_date'),
            gender=request.POST.get('gender', 'other'),
        )

        messages.success(request, 'Patient created successfully.')
        return redirect('website:admin_patient_list')


class AdminPatientEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        patient = get_object_or_404(PatientProfile, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit Patient - {patient.full_name}',
            'model_name': 'patient',
            'instance': patient,
            'fields': [
                {'name': 'full_name', 'label': 'Full Name', 'type': 'text', 'required': True, 'value': patient.full_name},
                {'name': 'national_id', 'label': 'National ID', 'type': 'text', 'required': True, 'value': patient.national_id},
                {'name': 'birth_date', 'label': 'Birth Date', 'type': 'date', 'required': True, 'value': patient.birth_date},
                {'name': 'gender', 'label': 'Gender', 'type': 'select', 'required': True,
                 'options': [('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
                 'value': patient.gender},
            ],
            'back_url': 'website:admin_patient_list',
        })

    def post(self, request, pk):
        patient = get_object_or_404(PatientProfile, pk=pk)
        patient.full_name = request.POST.get('full_name', patient.full_name)
        patient.national_id = request.POST.get('national_id', patient.national_id)
        birth_date = request.POST.get('birth_date')
        if birth_date:
            patient.birth_date = birth_date
        patient.gender = request.POST.get('gender', patient.gender)
        patient.save()
        messages.success(request, 'Patient updated successfully.')
        return redirect('website:admin_patient_list')


class AdminPatientDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        patient = get_object_or_404(PatientProfile, pk=pk)
        patient.delete()
        messages.success(request, 'Patient deleted successfully.')
        return redirect('website:admin_patient_list')


class AdminSpecialtyListView(AdminRequiredMixin, ListView):
    model = Specialty
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = Specialty.objects.all()
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Specialties'
        ctx['model_name'] = 'specialty'
        ctx['headers'] = ['Title', 'Slug', 'Doctors Count']
        ctx['add_url'] = 'website:admin_specialty_add'
        ctx['search_placeholder'] = 'Search by title...'
        return ctx


class AdminSpecialtyCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add Specialty',
            'model_name': 'specialty',
            'fields': [
                {'name': 'title', 'label': 'Title', 'type': 'text', 'required': True},
                {'name': 'slug', 'label': 'Slug', 'type': 'text', 'required': False},
            ],
            'back_url': 'website:admin_specialty_list',
        })

    def post(self, request):
        title = request.POST.get('title')
        slug = request.POST.get('slug') or None
        Specialty.objects.create(title=title, slug=slug)
        messages.success(request, 'Specialty created successfully.')
        return redirect('website:admin_specialty_list')


class AdminSpecialtyEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        specialty = get_object_or_404(Specialty, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit Specialty - {specialty.title}',
            'model_name': 'specialty',
            'instance': specialty,
            'fields': [
                {'name': 'title', 'label': 'Title', 'type': 'text', 'required': True, 'value': specialty.title},
                {'name': 'slug', 'label': 'Slug', 'type': 'text', 'required': False, 'value': specialty.slug},
            ],
            'back_url': 'website:admin_specialty_list',
        })

    def post(self, request, pk):
        specialty = get_object_or_404(Specialty, pk=pk)
        specialty.title = request.POST.get('title', specialty.title)
        specialty.slug = request.POST.get('slug') or specialty.slug
        specialty.save()
        messages.success(request, 'Specialty updated successfully.')
        return redirect('website:admin_specialty_list')


class AdminSpecialtyDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        specialty = get_object_or_404(Specialty, pk=pk)
        specialty.delete()
        messages.success(request, 'Specialty deleted successfully.')
        return redirect('website:admin_specialty_list')


class AdminTimeSlotListView(AdminRequiredMixin, ListView):
    model = TimeSlot
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = TimeSlot.objects.select_related('doctor', 'doctor__specialty').all()
        search = self.request.GET.get('search')
        available = self.request.GET.get('available')
        if search:
            qs = qs.filter(doctor__full_name__icontains=search)
        if available == 'true':
            qs = qs.filter(is_available=True)
        elif available == 'false':
            qs = qs.filter(is_available=False)
        return qs.order_by('-date', 'start_time')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Time Slots'
        ctx['model_name'] = 'timeslot'
        ctx['headers'] = ['Doctor', 'Specialty', 'Date', 'Start', 'End', 'Available']
        ctx['add_url'] = 'website:admin_timeslot_add'
        ctx['search_placeholder'] = 'Search by doctor name...'
        return ctx


class AdminTimeSlotCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add Time Slot',
            'model_name': 'timeslot',
            'fields': [
                {'name': 'doctor', 'label': 'Doctor', 'type': 'select', 'required': True,
                 'options': [(d.pk, f"{d.full_name} - {d.specialty.title}") for d in DoctorProfile.objects.all()]},
                {'name': 'date', 'label': 'Date', 'type': 'date', 'required': True},
                {'name': 'start_time', 'label': 'Start Time', 'type': 'time', 'required': True},
                {'name': 'end_time', 'label': 'End Time', 'type': 'time', 'required': True},
            ],
            'back_url': 'website:admin_timeslot_list',
        })

    def post(self, request):
        TimeSlot.objects.create(
            doctor_id=request.POST.get('doctor'),
            date=request.POST.get('date'),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
        )
        messages.success(request, 'Time slot created successfully.')
        return redirect('website:admin_timeslot_list')


class AdminTimeSlotEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit Time Slot',
            'model_name': 'timeslot',
            'instance': slot,
            'fields': [
                {'name': 'doctor', 'label': 'Doctor', 'type': 'select', 'required': True,
                 'options': [(d.pk, f"{d.full_name} - {d.specialty.title}") for d in DoctorProfile.objects.all()],
                 'value': slot.doctor_id},
                {'name': 'date', 'label': 'Date', 'type': 'date', 'required': True, 'value': slot.date},
                {'name': 'start_time', 'label': 'Start Time', 'type': 'time', 'required': True, 'value': slot.start_time},
                {'name': 'end_time', 'label': 'End Time', 'type': 'time', 'required': True, 'value': slot.end_time},
                {'name': 'is_available', 'label': 'Available', 'type': 'checkbox', 'required': False,
                 'checked': slot.is_available},
            ],
            'back_url': 'website:admin_timeslot_list',
        })

    def post(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)
        slot.doctor_id = request.POST.get('doctor', slot.doctor_id)
        slot.date = request.POST.get('date', slot.date)
        slot.start_time = request.POST.get('start_time', slot.start_time)
        slot.end_time = request.POST.get('end_time', slot.end_time)
        slot.is_available = request.POST.get('is_available') == 'on'
        slot.save()
        messages.success(request, 'Time slot updated successfully.')
        return redirect('website:admin_timeslot_list')


class AdminTimeSlotDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)
        slot.delete()
        messages.success(request, 'Time slot deleted successfully.')
        return redirect('website:admin_timeslot_list')


class AdminAppointmentListView(AdminRequiredMixin, ListView):
    model = Appointment
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = Appointment.objects.select_related(
            'patient', 'doctor', 'doctor__specialty', 'time_slot'
        ).all()
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        if search:
            qs = qs.filter(
                Q(patient__full_name__icontains=search) | Q(doctor__full_name__icontains=search)
            )
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Appointments'
        ctx['model_name'] = 'appointment'
        ctx['headers'] = ['Patient', 'Doctor', 'Date', 'Time', 'Status', 'Created']
        ctx['add_url'] = 'website:admin_appointment_add'
        ctx['search_placeholder'] = 'Search by patient or doctor name...'
        return ctx


class AdminAppointmentCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add Appointment',
            'model_name': 'appointment',
            'fields': [
                {'name': 'patient', 'label': 'Patient', 'type': 'select', 'required': True,
                 'options': [(p.pk, f"{p.full_name} - {p.user.phone_number}") for p in PatientProfile.objects.select_related('user').all()]},
                {'name': 'doctor', 'label': 'Doctor', 'type': 'select', 'required': True,
                 'options': [(d.pk, f"{d.full_name} - {d.specialty.title}") for d in DoctorProfile.objects.select_related('specialty').all()]},
                {'name': 'time_slot', 'label': 'Time Slot', 'type': 'select', 'required': True,
                 'options': [(ts.pk, f"{ts.doctor.full_name} - {ts.date} {ts.start_time}-{ts.end_time}")
                             for ts in TimeSlot.objects.filter(is_available=True).select_related('doctor')]},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'required': True,
                 'options': [('pending', 'Pending'), ('confirmed', 'Confirmed'),
                             ('cancelled', 'Cancelled'), ('completed', 'Completed')]},
                {'name': 'notes', 'label': 'Notes', 'type': 'textarea', 'required': False},
            ],
            'back_url': 'website:admin_appointment_list',
        })

    def post(self, request):
        time_slot = get_object_or_404(TimeSlot, pk=request.POST.get('time_slot'))
        patient = get_object_or_404(PatientProfile, pk=request.POST.get('patient'))
        doctor = get_object_or_404(DoctorProfile, pk=request.POST.get('doctor'))

        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            time_slot=time_slot,
            status=request.POST.get('status', 'pending'),
            notes=request.POST.get('notes', ''),
        )
        time_slot.is_available = False
        time_slot.save()
        messages.success(request, 'Appointment created successfully.')
        return redirect('website:admin_appointment_list')


class AdminAppointmentEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit Appointment #{appt.pk}',
            'model_name': 'appointment',
            'instance': appt,
            'fields': [
                {'name': 'status', 'label': 'Status', 'type': 'select', 'required': True,
                 'options': [('pending', 'Pending'), ('confirmed', 'Confirmed'),
                             ('cancelled', 'Cancelled'), ('completed', 'Completed')],
                 'value': appt.status},
                {'name': 'notes', 'label': 'Notes', 'type': 'textarea', 'required': False, 'value': appt.notes},
            ],
            'back_url': 'website:admin_appointment_list',
        })

    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk)
        appt.status = request.POST.get('status', appt.status)
        appt.notes = request.POST.get('notes', appt.notes)
        appt.save()
        messages.success(request, 'Appointment updated successfully.')
        return redirect('website:admin_appointment_list')


class AdminAppointmentDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        appt = get_object_or_404(Appointment, pk=pk)
        appt.delete()
        messages.success(request, 'Appointment deleted successfully.')
        return redirect('website:admin_appointment_list')


class AdminPaymentListView(AdminRequiredMixin, ListView):
    model = Payment
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = Payment.objects.select_related(
            'patient', 'appointment', 'appointment__doctor'
        ).all()
        search = self.request.GET.get('search')
        status_filter = self.request.GET.get('status')
        if search:
            qs = qs.filter(
                Q(patient__full_name__icontains=search) | Q(gateway_ref__icontains=search)
            )
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Payments'
        ctx['model_name'] = 'payment'
        ctx['headers'] = ['Patient', 'Doctor', 'Amount', 'Status', 'Gateway Ref', 'Paid At']
        ctx['add_url'] = 'website:admin_payment_add'
        ctx['search_placeholder'] = 'Search by patient name or gateway ref...'
        return ctx


class AdminPaymentCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add Payment',
            'model_name': 'payment',
            'fields': [
                {'name': 'patient', 'label': 'Patient', 'type': 'select', 'required': True,
                 'options': [(p.pk, f"{p.full_name} - {p.user.phone_number}") for p in PatientProfile.objects.select_related('user').all()]},
                {'name': 'appointment', 'label': 'Appointment', 'type': 'select', 'required': True,
                 'options': [(a.pk, f"#{a.pk} - {a.patient.full_name} → {a.doctor.full_name}")
                             for a in Appointment.objects.select_related('patient', 'doctor').all()]},
                {'name': 'amount', 'label': 'Amount (Toman)', 'type': 'number', 'required': True},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'required': True,
                 'options': [('pending', 'Pending'), ('successful', 'Successful'),
                             ('failed', 'Failed'), ('refunded', 'Refunded')]},
                {'name': 'gateway_ref', 'label': 'Gateway Ref', 'type': 'text', 'required': False},
            ],
            'back_url': 'website:admin_payment_list',
        })

    def post(self, request):
        payment = Payment.objects.create(
            patient_id=request.POST.get('patient'),
            appointment_id=request.POST.get('appointment'),
            amount=int(request.POST.get('amount', 0)),
            status=request.POST.get('status', 'pending'),
            gateway_ref=request.POST.get('gateway_ref', ''),
        )
        messages.success(request, 'Payment created successfully.')
        return redirect('website:admin_payment_list')


class AdminPaymentEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit Payment #{payment.pk}',
            'model_name': 'payment',
            'instance': payment,
            'fields': [
                {'name': 'status', 'label': 'Status', 'type': 'select', 'required': True,
                 'options': [('pending', 'Pending'), ('successful', 'Successful'),
                             ('failed', 'Failed'), ('refunded', 'Refunded')],
                 'value': payment.status},
                {'name': 'gateway_ref', 'label': 'Gateway Ref', 'type': 'text', 'required': False,
                 'value': payment.gateway_ref},
                {'name': 'amount', 'label': 'Amount (Toman)', 'type': 'number', 'required': True,
                 'value': payment.amount},
            ],
            'back_url': 'website:admin_payment_list',
        })

    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        old_status = payment.status
        payment.status = request.POST.get('status', payment.status)
        payment.gateway_ref = request.POST.get('gateway_ref', payment.gateway_ref)
        amount = request.POST.get('amount')
        if amount:
            payment.amount = int(amount)
        if payment.status == 'successful' and old_status != 'successful':
            payment.paid_at = timezone.now()
        payment.save()
        messages.success(request, 'Payment updated successfully.')
        return redirect('website:admin_payment_list')


class AdminPaymentDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        payment.delete()
        messages.success(request, 'Payment deleted successfully.')
        return redirect('website:admin_payment_list')


class AdminReviewListView(AdminRequiredMixin, ListView):
    model = Review
    template_name = 'website/admin/list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = Review.objects.select_related(
            'patient', 'doctor', 'doctor__specialty', 'appointment'
        ).all()
        search = self.request.GET.get('search')
        rating = self.request.GET.get('rating')
        if search:
            qs = qs.filter(
                Q(patient__full_name__icontains=search) | Q(doctor__full_name__icontains=search)
            )
        if rating:
            qs = qs.filter(rating=rating)
        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Reviews'
        ctx['model_name'] = 'review'
        ctx['headers'] = ['Patient', 'Doctor', 'Rating', 'Comment', 'Created']
        ctx['add_url'] = 'website:admin_review_add'
        ctx['search_placeholder'] = 'Search by patient or doctor name...'
        return ctx


class AdminReviewCreateView(AdminRequiredMixin, View):
    def get(self, request):
        return render(request, 'website/admin/form.html', {
            'title': 'Add Review',
            'model_name': 'review',
            'fields': [
                {'name': 'patient', 'label': 'Patient', 'type': 'select', 'required': True,
                 'options': [(p.pk, f"{p.full_name} - {p.user.phone_number}") for p in PatientProfile.objects.select_related('user').all()]},
                {'name': 'doctor', 'label': 'Doctor', 'type': 'select', 'required': True,
                 'options': [(d.pk, f"{d.full_name} - {d.specialty.title}") for d in DoctorProfile.objects.select_related('specialty').all()]},
                {'name': 'appointment', 'label': 'Appointment', 'type': 'select', 'required': True,
                 'options': [(a.pk, f"#{a.pk} - {a.patient.full_name} → {a.doctor.full_name}")
                             for a in Appointment.objects.filter(status='completed').select_related('patient', 'doctor')]},
                {'name': 'rating', 'label': 'Rating (1-5)', 'type': 'number', 'required': True},
                {'name': 'comment', 'label': 'Comment', 'type': 'textarea', 'required': False},
            ],
            'back_url': 'website:admin_review_list',
        })

    def post(self, request):
        review = Review.objects.create(
            patient_id=request.POST.get('patient'),
            doctor_id=request.POST.get('doctor'),
            appointment_id=request.POST.get('appointment'),
            rating=int(request.POST.get('rating', 5)),
            comment=request.POST.get('comment', ''),
        )
        messages.success(request, 'Review created successfully.')
        return redirect('website:admin_review_list')


class AdminReviewEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        return render(request, 'website/admin/form.html', {
            'title': f'Edit Review #{review.pk}',
            'model_name': 'review',
            'instance': review,
            'fields': [
                {'name': 'rating', 'label': 'Rating (1-5)', 'type': 'number', 'required': True,
                 'value': review.rating},
                {'name': 'comment', 'label': 'Comment', 'type': 'textarea', 'required': False,
                 'value': review.comment},
            ],
            'back_url': 'website:admin_review_list',
        })

    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.rating = int(request.POST.get('rating', review.rating))
        review.comment = request.POST.get('comment', review.comment)
        review.save()
        messages.success(request, 'Review updated successfully.')
        return redirect('website:admin_review_list')


class AdminReviewDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        review = get_object_or_404(Review, pk=pk)
        review.delete()
        messages.success(request, 'Review deleted successfully.')
        return redirect('website:admin_review_list')
