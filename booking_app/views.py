from django.views import View
from django.shortcuts import render
from .models import Room, Booking
from datetime import date

class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        today = date.today()
        bookings = Booking.objects.filter(start_time__date=today)
        rooms = Room.objects.all()
        context = {
            'today': today,
            'rooms': rooms,
            'bookings': bookings,
        }
        return render(request, self.template_name, context)
