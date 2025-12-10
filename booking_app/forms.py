from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.forms import modelformset_factory
from booking_app.models import Booking, Room, Role, RoomAvailability
from booking_app.models import Room, RoomType, User


from django.forms import modelformset_factory
from .models import RoomAvailability

# booking_app/forms.py
from django import forms
from django.forms import modelformset_factory
from .models import RoomAvailability

class RoomAvailabilityForm(forms.ModelForm):
    class Meta:
        model = RoomAvailability
        fields = ('day_of_week', 'start_time', 'end_time')  # no is_available
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        # If both times are empty, treat as unavailable (skip saving later)
        if not start and not end:
            raise forms.ValidationError("Empty row — will be treated as unavailable.")

        # Optional: enforce end > start
        if start and end and end <= start:
            raise forms.ValidationError("End time must be later than start time.")

        return cleaned_data


RoomAvailabilityFormSet = modelformset_factory(
    RoomAvailability,
    form=RoomAvailabilityForm,
    extra=7,          # one blank row by default
    can_delete=False   # allow removing rows
)


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

        if not room or not start or not end:
            return cleaned_data

        # Get weekday code from start_time (Mon, Tue, etc.)
        weekday_code = start.strftime("%A")  # e.g. "Mon"

        # Find availability slots for that room/day
        availabilities = RoomAvailability.objects.filter(room=room, day_of_week=weekday_code)

        if not availabilities.exists():
            raise forms.ValidationError("This room has no availability on that day.")

        # Check if booking fits inside ANY availability slot
        valid_slot = False
        for avail in availabilities:
            if start.time() >= avail.start_time and end.time() <= avail.end_time:
                valid_slot = True
                break

        if not valid_slot:
            raise forms.ValidationError("Booking must be within the room’s available time periods.")

        return cleaned_data

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

        if not room or not start or not end:
            return cleaned_data

        # Get weekday code from start_time (Mon, Tue, etc.)
        weekday_code = start.strftime("%A")  # e.g. "Mon"

        # Find availability slots for that room/day
        availabilities = RoomAvailability.objects.filter(room=room, day_of_week=weekday_code)

        if not availabilities.exists():
            raise forms.ValidationError("This room has no availability on that day.")

        # Check if booking fits inside ANY availability slot
        valid_slot = False
        for avail in availabilities:
            if start.time() >= avail.start_time and end.time() <= avail.end_time:
                valid_slot = True
                break

        if not valid_slot:
            raise forms.ValidationError("Booking must be within the room’s available time periods.")

        return cleaned_data



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