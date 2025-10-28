from django.shortcuts import render
from .models import Room, Booking
from datetime import date

def home(request):
    today = date.today()
    bookings = Booking.objects.filter(start_time__date=today)
    rooms = Room.objects.all()
    return render(request, 'booking_app/home.html', {'rooms': rooms, 'bookings': bookings})
