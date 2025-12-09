from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from booking_app.models import Booking, Room, Role
from booking_app.models import Room, RoomType, User

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'room_type', 'capacity']


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['room_type_name', 'room_type_description']


class UserForm(forms.ModelForm):


    class Meta:
        model = User
        fields = ['name', 'email', 'password_hash', 'role']


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['room', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if room and start and end:
            # Prevent past bookings
            if start and timezone.is_naive(start):
                start = timezone.make_aware(start)
            if end and timezone.is_naive(end):
                end = timezone.make_aware(end)
            if start < timezone.now():
                raise ValidationError("Start time cannot be in the past.")
            if end < timezone.now():
                raise ValidationError("End time cannot be in the past.")

            # Check for overlapping bookings
            conflicts = Booking.objects.filter(
                room=room,
                start_time__lt=end,
                end_time__gt=start,
                status__in=['pending', 'approved']  # only block active bookings
            )
            if conflicts.exists():
                raise ValidationError(f"{room} is already booked for this time range.")

            if start >= end:
                raise ValidationError("End time must be after start time.")

class AdminBookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['user', 'room', 'start_time', 'end_time', 'status']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get('room')
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        if room and start and end:
            # Prevent past bookings
            if start < timezone.now():
                raise ValidationError("Start time cannot be in the past.")
            if end < timezone.now():
                raise ValidationError("End time cannot be in the past.")

            conflicts = Booking.objects.filter(
                room=room,
                start_time__lt=end,
                end_time__gt=start,
                status__in=['pending', 'approved']
            )
            if conflicts.exists():
                raise ValidationError(f"{room} is already booked for this time range.")

            if start >= end:
                raise ValidationError("End time must be after start time.")



class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        # We do NOT expose password_hash or role directly in the form
        fields = ['name', 'email']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get("password")
        cpwd = cleaned_data.get("confirm_password")

        if pwd and cpwd and pwd != cpwd:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

    def save(self, commit=True):
        """
        Save the user with:
        - password_hash set to the provided password (to match your current login logic)
        - a default Role, e.g. role_name='User'
        """
        user = super().save(commit=False)

        # Store the raw password in password_hash (matches your current login check)
        user.password_hash = self.cleaned_data['password']

        # Assign a default role (create it if it doesn't exist)
        default_role, _ = Role.objects.get_or_create(role_name="User")
        user.role = default_role

        if commit:
            user.save()
        return user