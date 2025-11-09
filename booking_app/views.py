from django.contrib import messages
from django.contrib.auth import logout  # we're using session auth, so logout is fine
from django.shortcuts import render, redirect
from django.views import View
from datetime import date

from .forms import LoginForm, BookingForm  # ✅ import BookingForm
from .models import User, Room, Booking


# ------------------ HOME ------------------

class HomeView(View):
    template_name = 'booking_app/home.html'

    def get(self, request):
        # Require login for home
        if not request.session.get('user_id'):
            return redirect('login')

        today = date.today()
        rooms = Room.objects.all()
        bookings = Booking.objects.filter(start_time__date=today)
        return render(request, self.template_name, {
            'rooms': rooms,
            'bookings': bookings,
            'today': today,
        })


# ------------------ BOOKINGS ------------------

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


class BookingListView(View):
    template_name = 'booking_app/booking_list.html'

    def get(self, request):
        if not request.session.get('user_id'):
            return redirect('login')

        bookings = Booking.objects.all().order_by('-start_time')
        return render(request, self.template_name, {'bookings': bookings})


# ------------------ ADMIN DASHBOARD ------------------

class AdminDashboardView(View):
    template_name = 'booking_app/admin_dashboard.html'

    def get(self, request):
        if not request.session.get('user_id'):
            return redirect('login')

        rooms = Room.objects.all()
        bookings = Booking.objects.all().order_by('start_time')
        return render(request, self.template_name, {'rooms': rooms, 'bookings': bookings})


# ------------------ LOGIN / LOGOUT ------------------

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


class LogoutViewCustom(View):
    def get(self, request):
        logout(request)
        request.session.flush()  # clears session
        storage = messages.get_messages(request)
        list(storage)  # consume/clear old messages
        messages.info(request, "You have been logged out.")
        return redirect('login')