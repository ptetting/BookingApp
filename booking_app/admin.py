
# Register your models here.

from django.contrib import admin
from .models import *

models_list = [
    Role, User, Profile, RoomType, Room,
    Facility, RoomFeature, RoomRoomFeature,
    Booking, RoomAvailability, Notification,
    ActionLog, Product
]

for model in models_list:
    admin.site.register(model)
