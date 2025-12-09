from django.contrib import messages
from django.contrib.auth import logout  # we're using session auth, so logout is fine
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from datetime import date, datetime
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .models import User, Profile,RoomAvailability, ActionLog
from .forms import LoginForm, BookingForm, AdminBookingForm, UserForm, RoomTypeForm, RoomForm, \
    UserCreateForm  # ✅ import BookingForm
from .models import User, Room, Booking, Notification, RoomType


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


def log_action(request, action_description: str):
    user_id = request.session.get("user_id")
    if not user_id:
        return  # ignore logs when not logged in

    ActionLog.objects.create(
        user_id=user_id,
        action=action_description
    )


# ------------------ HOME ------------------


@method_decorator(never_cache, name='dispatch')
class HomeView(View):
    template_name = 'booking_app/home_admin.html'

    def get(self, request):
        if not request.session.get('user_id'):
            return redirect('login')

        today_date = date.today()

        # Get all rooms and their availability
        rooms = Room.objects.all()
        rooms_with_availability = []

        for room in rooms:
            availability = RoomAvailability.objects.filter(room=room).order_by('day_of_week', 'start_time')

            for avail in availability:
                # Ensure start_time and end_time are valid datetime objects
                if not isinstance(avail.start_time, datetime) or not isinstance(avail.end_time, datetime):
                    avail.is_available = False
                    continue

                overlapping_bookings = Booking.objects.filter(
                    room=room,
                    start_time__lt=avail.end_time,
                    end_time__gt=avail.start_time,
                    status='approved'
                )
                avail.is_available = not overlapping_bookings.exists()

            rooms_with_availability.append({
                'room': room,
                'availability': availability
            })

        context = {
            'rooms_with_availability': rooms_with_availability,
            'today': today_date,
        }

        return render(request, self.template_name, context)



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

            log_action(request, f"Created booking #{booking.id}")
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

            log_action(request, f"Admin created booking #{booking.id}")
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

        today = date.today()

        # Admin sees all bookings, users see their own
        if request.session.get('role_name') != 'Admin':
            all_bookings = Booking.objects.filter(user_id=request.session['user_id'])
        else:
            all_bookings = Booking.objects.all()

        all_bookings = all_bookings.order_by('start_time')

        # Filter out bookings with missing start or end times
        all_bookings = all_bookings.exclude(start_time__isnull=True).exclude(end_time__isnull=True)

        # Categorize bookings safely
        past_bookings = all_bookings.filter(end_time__date__lt=today)
        today_bookings = all_bookings.filter(start_time__date__lte=today, end_time__date__gte=today)
        future_bookings = all_bookings.filter(start_time__date__gt=today)

        context = {
            "past_bookings": past_bookings,
            "today_bookings": today_bookings,
            "future_bookings": future_bookings,
            "today": today
        }

        return render(request, self.template_name, context)



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

            log_action(request, f"Updated booking #{booking.id} status to {new_status}")
            messages.success(request, f"Booking {booking.id} status updated to {new_status}.")
            create_notifications_for_booking(f"updated to {new_status}", booking)
        else:
            messages.info(request, "No status change detected.")

        return redirect('admin_dashboard')

class DeleteBookingView(View):
    def post(self, request, booking_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')

        booking = get_object_or_404(Booking, id=booking_id)
        messages.success(request, f"Booking {booking.id} deleted successfully.")
        log_action(request, f"Deleted booking #{booking.id}")
        booking.delete()
        return redirect('admin_dashboard')

@method_decorator(never_cache, name='dispatch')
class RoomListView(View):
    template_name = 'booking_app/room_list.html'

    def get(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        rooms = Room.objects.all()
        return render(request, self.template_name, {'rooms': rooms})


@method_decorator(never_cache, name='dispatch')
class RoomCreateView(View):
    template_name = 'booking_app/room_form.html'

    def get(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        form = RoomForm()
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Create New Room',
            'submit_text': 'Create Room',
            'delete_url': None
        })

    def post(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()

            log_action(request, f"Created room {room.room_number}")
            messages.success(request, "Room created successfully.")
            return redirect('room_list')
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Create New Room',
            'submit_text': 'Create Room',
            'delete_url': None
        })


@method_decorator(never_cache, name='dispatch')
class RoomUpdateView(View):
    template_name = 'booking_app/room_form.html'

    def get(self, request, room_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        room = get_object_or_404(Room, id=room_id)
        form = RoomForm(instance=room)
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit Room: {room.room_number}',
            'submit_text': 'Update Room',
            'delete_url': f'/rooms/{room.id}/delete/'
        })

    def post(self, request, room_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        room = get_object_or_404(Room, id=room_id)
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            updated = form.save()

            log_action(request, f"Updated room {updated.room_number}")
            messages.success(request, "Room updated successfully.")
            return redirect('room_list')
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit Room: {room.room_number}',
            'submit_text': 'Update Room',
        })


@method_decorator(never_cache, name='dispatch')
class RoomDeleteView(View):
    def get(self, request, room_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        room = get_object_or_404(Room, id=room_id)
        room_number = room.room_number
        room.delete()

        log_action(request, f"Deleted room {room_number}")
        messages.success(request, "Room deleted successfully.")
        return redirect('room_list')

@method_decorator(never_cache, name='dispatch')
class RoomTypeListView(View):
    template_name = 'booking_app/room_type_list.html'

    def get(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        types = RoomType.objects.all()
        return render(request, self.template_name, {'types': types})


@method_decorator(never_cache, name='dispatch')
class RoomTypeCreateView(View):
    template_name = 'booking_app/room_type_form.html'

    def get(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        form = RoomTypeForm()
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Create New Room Type',
            'submit_text': 'Create Room Type',
            'delete_url': None
        })

    def post(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        form = RoomTypeForm(request.POST)
        if form.is_valid():
            room_type = form.save()

            log_action(request, f"Created room type {room_type.room_type_name}")
            messages.success(request, "Room type created successfully.")
            return redirect('room_type_list')
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Create New Room Type',
            'submit_text': 'Create Room Type',
            'delete_url': None
        })


@method_decorator(never_cache, name='dispatch')
class RoomTypeUpdateView(View):
    template_name = 'booking_app/room_type_form.html'

    def get(self, request, type_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        room_type = get_object_or_404(RoomType, id=type_id)
        form = RoomTypeForm(instance=room_type)
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit Room Type: {room_type.room_type_name}',
            'submit_text': 'Update Room Type',
            'delete_url': f'/room_types/{room_type.id}/delete/'
        })

    def post(self, request, type_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        room_type = get_object_or_404(RoomType, id=type_id)
        form = RoomTypeForm(request.POST, instance=room_type)
        if form.is_valid():
            updated = form.save()

            log_action(request, f"Updated room type {updated.room_type_name}")
            messages.success(request, "Room type updated successfully.")
            return redirect('room_type_list')
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit Room Type: {room_type.room_type_name}',
            'submit_text': 'Update Room Type',
            'delete_url': f'/room_types/{room_type.id}/delete/'
        })


@method_decorator(never_cache, name='dispatch')
class RoomTypeDeleteView(View):
    def get(self, request, type_id):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        room_type = get_object_or_404(RoomType, id=type_id)
        room_type_name = room_type.room_type_name
        room_type.delete()

        log_action(request, f"Deleted room type {room_type_name}")
        messages.success(request, "Room type deleted successfully.")
        return redirect('room_type_list')


@method_decorator(never_cache, name='dispatch')
class UserListView(View):
    template_name = 'booking_app/user_list.html'

    def get(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')
        users = User.objects.all()
        return render(request, self.template_name, {'users': users})


@method_decorator(never_cache, name='dispatch')
class UserCreateView(View):
    template_name = 'booking_app/user_form.html'

    def get(self, request):
        form = UserForm()
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Create New User',
            'submit_text': 'Create User',
            'delete_url': None
        })

    def post(self, request):
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = form.save()

            log_action(request, f"Created user {new_user.name}")
            messages.success(request, "User created successfully.")
            return redirect('user_list')
        return render(request, self.template_name, {
            'form': form,
            'form_title': 'Create New User',
            'submit_text': 'Create User',
            'delete_url': None
        })
@method_decorator(never_cache, name='dispatch')
class UserUpdateView(View):
    template_name = 'booking_app/user_form.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        form = UserForm(instance=user)
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit User: {user.name}',
            'submit_text': 'Update User',
            'delete_url': f'/users/{user.id}/delete/'  # see next step
        })

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save()

            log_action(request, f"Updated user {updated_user.name}")
            messages.success(request, "User updated successfully.")
            return redirect('user_list')
        return render(request, self.template_name, {
            'form': form,
            'form_title': f'Edit User: {user.name}',
            'submit_text': 'Update User',
            'delete_url': f'/users/{user.id}/delete/'
        })

@method_decorator(never_cache, name='dispatch')
class UserDeleteView(View):
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        name = user.name
        user.delete()
        log_action(request, f"Deleted user {name}")
        messages.success(request, "User deleted successfully.")
        return redirect('user_list')

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



@method_decorator(never_cache, name='dispatch')
class RegisterView(View):
    template_name = 'booking_app/register.html'  # matches your register.html

    def get(self, request):
        if request.session.get('user_id'):
            return redirect('home')

        form = UserCreateForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        if request.session.get('user_id'):
            return redirect('home')

        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully. You can now log in.")
            return redirect('login')

        # If invalid, render again with errors
        return render(request, self.template_name, {'form': form})



@method_decorator(never_cache, name='dispatch')
class EditProfileView(View):
    template_name = 'booking_app/edit_profile.html'

    def get(self, request):
        if not request.session.get("user_id"):
            return redirect("login")

        user = User.objects.get(id=request.session["user_id"])
        # Get or create the profile linked to this user
        profile, created = Profile.objects.get_or_create(user=user)
        return render(request, self.template_name, {"user": user, "profile": profile})

    def post(self, request):
        if not request.session.get("user_id"):
            return redirect("login")

        user = User.objects.get(id=request.session["user_id"])
        profile, created = Profile.objects.get_or_create(user=user)

        # Update User fields
        name = request.POST.get("name")
        if name:
            user.name = name

        email = request.POST.get("email")
        if email:
            user.email = email

        new_password = request.POST.get("password")
        if new_password:
            user.password_hash = new_password  # hash if needed

        user.save()

        # Update Profile fields
        address = request.POST.get("address")
        if address:
            profile.address = address

        phone_number = request.POST.get("phone_number")
        if phone_number:
            profile.phone_number = phone_number

        profile.save()

        messages.success(request, "Profile updated successfully!")

        # Update session name in navbar
        request.session["user_name"] = user.name

        return redirect("home")


# ------------------ AUDIT LOG ------------------
@method_decorator(never_cache, name='dispatch')
class AuditLogView(View):
    template_name = 'booking_app/audit_log.html'

    def get(self, request):
        if request.session.get('role_name') != 'Admin':
            return redirect('home')

        logs = ActionLog.objects.select_related('user').order_by('-action_timestamp')

        return render(request, self.template_name, {'logs': logs})
