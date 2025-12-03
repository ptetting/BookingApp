from datetime import date, datetime
from django.contrib import messages
from django.contrib.auth import logout  # we're using session auth, so logout is fine
from django.shortcuts import render, redirect
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from .forms import LoginForm, BookingForm, AdminBookingForm  # ✅ import BookingForm
from .models import User, Room, Booking, RoomAvailability, Profile


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
            # Optional: you can mark unavailable slots based on existing bookings here
            for avail in availability:
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
            booking.user_id = request.session['user_id']  # assign logged-in user

            if request.session.get('role_name') == 'Admin':
                # Admin can select status manually
                new_status = form.cleaned_data.get('status', 'Pending')
                if new_status in ['Pending', 'Approved', 'Cancelled', 'Completed']:
                    booking.status = new_status
                else:
                    booking.status = 'Pending'
            else:
                # Students always get pending
                booking.status = 'Pending'

            booking.save()
            messages.success(request, "Booking submitted successfully!")
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

        today = date.today()

        # Admin sees all bookings, users see their own
        if request.session.get('role_name') != 'Admin':
            all_bookings = Booking.objects.filter(user_id=request.session['user_id'])
        else:
            all_bookings = Booking.objects.all()

        all_bookings = all_bookings.order_by('start_time')

        # Categorize based on start_time & end_time
        past_bookings = all_bookings.filter(
            end_time__date__lt=today
        )

        today_bookings = all_bookings.filter(
            start_time__date__lte=today,
            end_time__date__gte=today
        )

        future_bookings = all_bookings.filter(
            start_time__date__gt=today
        )

        context = {
            "past_bookings": past_bookings,
            "today_bookings": today_bookings,
            "future_bookings": future_bookings,
            "today": today
        }

        return render(request, self.template_name, context)


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
            booking = Booking.objects.get(booking_id=booking_id)
            booking.status = new_status
            booking.save()
            messages.success(request, f"Booking {booking.booking_id} status updated to {new_status}.")
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")

        return redirect('admin_dashboard')


# ------------------ BOOKING STATUS UPDATE (ADMIN ONLY) ------------------
@method_decorator(never_cache, name='dispatch')
class BookingStatusUpdateView(View):
    def post(self, request, booking_id):
        # Require login
        if not request.session.get('user_id'):
            return redirect('login')

        try:
            user = User.objects.get(user_id=request.session['user_id'])
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('login')

        # Check if user is admin
        if user.role.role_name != 'Admin':
            messages.error(request, "You are not authorized to update bookings.")
            return redirect('home')

        # Get new status from POST
        new_status = request.POST.get('status')  # e.g., 'approved', 'cancelled'

        # Validate against model choices
        valid_statuses = [choice[0] for choice in Booking.STATUS_CHOICES]

        try:
            booking = Booking.objects.get(booking_id=booking_id)
            if new_status in valid_statuses:
                booking.status = new_status
                booking.save()
                messages.success(request, f"Booking {booking.booking_id} status updated to {new_status}.")
            else:
                messages.error(request, "Invalid status.")
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
                request.session['user_id'] = user.user_id
                request.session['user_name'] = user.name
                request.session['role_name'] = user.role.role_name  # <-- store role

                if user.password_hash == password:
                    # Clear any existing messages first
                    storage = messages.get_messages(request)
                    list(storage)

                    # Log in user
                    request.session['user_id'] = user.user_id
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
class EditProfileView(View):
    template_name = 'booking_app/edit_profile.html'

    def get(self, request):
        if not request.session.get("user_id"):
            return redirect("login")

        user = User.objects.get(user_id=request.session["user_id"])
        # Get or create the profile linked to this user
        profile, created = Profile.objects.get_or_create(user=user)
        return render(request, self.template_name, {"user": user, "profile": profile})

    def post(self, request):
        if not request.session.get("user_id"):
            return redirect("login")

        user = User.objects.get(user_id=request.session["user_id"])
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
