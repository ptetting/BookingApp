from django.contrib import messages
from django.contrib.auth import logout  # we're using session auth, so logout is fine
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from datetime import date

from .forms import LoginForm, BookingForm, AdminBookingForm  # ✅ import BookingForm
from .models import User, Room, Booking, Notification


# ----------------- HELPER -----------------
def create_notifications_for_booking(action: str, booking):
    """
    Persist notifications for the booking's user and all admins.
    action examples: 'created', 'approved', 'cancelled', 'completed', 'removed', 'updated to approved'
    """
    # Message content
    user_msg = f"Your booking for Room {booking.room.room_number} at {booking.start_time} was {action}."
    admin_msg = f"Booking for Room {booking.room.room_number} with user {booking.user.name} was {action}."

    # Notify booking owner
    Notification.objects.create(
        user=booking.user,
        booking=booking,
        notification_message=user_msg,
        notification_status='unread'
    )

    # Notify admins
    admins = User.objects.filter(role__role_name="Admin")
    Notification.objects.bulk_create([
        Notification(
            user=admin,
            booking=booking,
            notification_message=admin_msg,
            notification_status='unread'
        )
        for admin in admins
    ])


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
            create_notifications_for_booking("created", booking)
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
            booking = form.save()
            messages.success(request, "Booking created by admin.")
            create_notifications_for_booking("created by admin", booking)
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

        booking = get_object_or_404(Booking, id=booking_id)
        new_status = request.POST.get('status')
        if new_status and new_status != booking.status:
            booking.status = new_status
            booking.save()
            messages.success(request, f"Booking {booking.id} status updated to {new_status}.")
            create_notifications_for_booking(f"updated to {new_status}", booking)
        else:
            messages.info(request, "No status change detected.")

        return redirect('admin_dashboard')


# ------------------ NOTIFICATIONS -------------------
@method_decorator(never_cache, name='dispatch')
class NotificationsView(View):
    template_name = 'booking_app/notifications.html'

    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('login')

        notifications = Notification.objects.filter(user_id=user_id).order_by('-notification_timestamp')
        return render(request, self.template_name, {'notifications': notifications})


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