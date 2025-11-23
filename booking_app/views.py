from django.contrib import messages
from django.contrib.auth import logout  # we're using session auth, so logout is fine
from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from datetime import date

from .forms import LoginForm, BookingForm, AdminBookingForm  # ✅ import BookingForm
from .models import User, Room, Booking


# ------------------ HOME ------------------

@method_decorator(never_cache, name='dispatch')
class HomeView(View):
    def get(self, request):
        if not request.session.get('user_id'):
            return redirect('login')

        today = date.today()
        role = request.session.get('role_name')

        if role == 'Admin':
            rooms = Room.objects.all()
            bookings = Booking.objects.all().order_by('start_time')
            return render(request, 'booking_app/home_admin.html', {
                'rooms': rooms,
                'bookings': bookings,
                'today': today,
            })
        else:
            rooms = Room.objects.all()
            bookings = Booking.objects.filter(
                user_id=request.session['user_id']
            ).order_by('-start_time')
            return render(request, 'booking_app/home_user.html', {
                'rooms': rooms,
                'bookings': bookings,
                'today': today,
            })



# ------------------ BOOKINGS ------------------

@method_decorator(never_cache, name='dispatch')
class BookingCreateView(View):
    template_name = 'booking_app/create_booking.html'

    def get(self, request):
        if not request.session.get('user_id'):
            return redirect('login')

        form = BookingForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if not request.session.get('user_id'):
            return redirect('login')

        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user_id = request.session['user_id']  # auto-assign logged-in user
            booking.status = 'pending'
            booking.save()
            messages.success(request, "Booking submitted (pending).")
            return redirect('booking_list')

        return render(request, self.template_name, {'form': form})

@method_decorator(never_cache, name='dispatch')
class AdminBookingCreateView(View):
    template_name = 'booking_app/admin_create_booking.html'

    def get(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        form = AdminBookingForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        form = AdminBookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Booking created by admin.")
            return redirect('admin_dashboard')
        return render(request, self.template_name, {'form': form})

@method_decorator(never_cache, name='dispatch')
class BookingListView(View):
    template_name = 'booking_app/booking_list.html'

    def get(self, request):
        if not request.session.get('user_id'):
            return redirect('login')

        if request.session.get('role_name') != 'Admin':
            bookings = Booking.objects.filter(user_id=request.session['user_id'])
        else:
            bookings = Booking.objects.all().order_by('-start_time')

        return render(request, self.template_name, {'bookings': bookings})


# ------------------ ADMIN DASHBOARD ------------------
@method_decorator(never_cache, name='dispatch')
class AdminDashboardView(View):
    template_name = 'booking_app/admin_dashboard.html'

    def get(self, request):
        if not request.session.get('user_id'):
            return redirect('login')
        if request.session.get('role_name') != 'Admin':
            return redirect('home')

        rooms = Room.objects.all()
        bookings = Booking.objects.all().order_by('start_time')
        return render(request, self.template_name, {'rooms': rooms, 'bookings': bookings})

@method_decorator(never_cache, name='dispatch')
class UpdateBookingStatusView(View):
    def post(self, request, booking_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')

        new_status = request.POST.get('status')
        try:
            booking = Booking.objects.get(id=booking_id)
            booking.status = new_status
            booking.save()
            messages.success(request, f"Booking {booking.id} status updated to {new_status}.")
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")

        return redirect('admin_dashboard')



# ------------------ LOGIN / LOGOUT ------------------
@method_decorator(never_cache, name='dispatch')
class LoginViewCustom(View):
    template_name = 'booking_app/login.html'

    def get(self, request):
        # Clear any messages from previous sessions
        list(messages.get_messages(request))
        if request.session.get('user_id'):
            return redirect('home')
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email=email)
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                request.session['role_name'] = user.role.role_name  # <-- store role

                if user.password_hash == password:
                    # Clear any existing messages first
                    storage = messages.get_messages(request)
                    list(storage)

                    # Log in user
                    request.session['user_id'] = user.id
                    request.session['user_name'] = user.name

                    # Add welcome message
                    messages.success(request, f"Welcome, {user.name}!")
                    return redirect('home')
                else:
                    messages.error(request, "Invalid password.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        return render(request, self.template_name, {'form': form})

@method_decorator(never_cache, name='dispatch')
class LogoutViewCustom(View):
    def get(self, request):
        logout(request)
        request.session.flush()  # clears session
        storage = messages.get_messages(request)
        list(storage)  # consume/clear old messages
        messages.info(request, "You have been logged out.")
        return redirect('login')