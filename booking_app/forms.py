from django import forms
from django.core.exceptions import ValidationError
from booking_app.models import Booking, Room


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