from django.db import models

# --- Roles and Users ---
class Role(models.Model):
    role_name = models.CharField(max_length=50)

    class Meta:
        db_table = 'Role'

    def __str__(self):
        return self.role_name


class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'User'

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'Profile'

    def __str__(self):
        return f"Profile of {self.user.name}"


# --- Room Tables ---
class RoomType(models.Model):
    room_type_name = models.CharField(max_length=50)
    room_type_description = models.TextField(blank=True)

    class Meta:
        db_table = 'RoomType'

    def __str__(self):
        return self.room_type_name


class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField()

    class Meta:
        db_table = 'Room'

    def __str__(self):
        return f"{self.room_number} ({self.room_type})"


class Facility(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    facility_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'Facility'

    def __str__(self):
        return f"{self.facility_name} - {self.room.room_number}"


class RoomFeature(models.Model):
    feature_name = models.CharField(max_length=100)
    feature_description = models.TextField(blank=True)

    class Meta:
        db_table = 'RoomFeature'

    def __str__(self):
        return self.feature_name


class RoomRoomFeature(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    feature = models.ForeignKey(RoomFeature, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('room', 'feature')
        db_table = 'RoomRoomFeature'


# --- Booking System ---
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'Booking'

    def __str__(self):
        return f"{self.room} - {self.user.name} ({self.status})"


# --- Notifications and Logs ---
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    notification_message = models.TextField()
    notification_status = models.CharField(max_length=20, default='unread')
    notification_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Notification'

    def __str__(self):
        return f"Notification for {self.user.name}"


class ActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    action_timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ActionLog'

    def __str__(self):
        return f"{self.user.name}: {self.action}"


class RoomAvailability(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=10)
    start_time = models.DateTimeField()   # changed from TimeField
    end_time = models.DateTimeField()     # changed from TimeField
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = 'RoomAvailability'

    def __str__(self):
        return f"{self.room.room_number} - {self.day_of_week}"


# --- Optional Product Table ---
class Product(models.Model):
    product_name = models.CharField(max_length=100)
    product_description = models.TextField(blank=True)
    product_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = 'Product'

    def __str__(self):
        return self.product_name
