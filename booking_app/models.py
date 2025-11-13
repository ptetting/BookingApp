from django.db import models

# --- Roles and Users ---
class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50)

    def __str__(self):
        return self.role_name


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, db_column='role_id')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='user_id')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Profile of {self.user.name}"


# --- Room Tables ---
class RoomType(models.Model):
    room_type_id = models.AutoField(primary_key=True)
    room_type_name = models.CharField(max_length=50)
    room_type_description = models.TextField(blank=True)

    def __str__(self):
        return self.room_type_name


class Room(models.Model):
    room_id = models.AutoField(primary_key=True)
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, db_column='room_type_id')
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.room_number} ({self.room_type})"


class Facility(models.Model):
    facility_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, db_column='room_id')
    facility_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.facility_name} - {self.room.room_number}"


class RoomFeature(models.Model):
    room_feature_id = models.AutoField(primary_key=True)
    feature_name = models.CharField(max_length=100)
    feature_description = models.TextField(blank=True)

    def __str__(self):
        return self.feature_name


class RoomFeatureLink(models.Model):
    room_feature_link_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, db_column='room_id')
    feature = models.ForeignKey(RoomFeature, on_delete=models.CASCADE, db_column='room_feature_id')

    class Meta:
     
        unique_together = ('room', 'feature')

    def __str__(self):
        return f"{self.room.room_number} - {self.feature.feature_name}"

# --- Booking System ---
class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, db_column='room_id')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.room} - {self.user.name} ({self.status})"


# --- Notifications and Logs ---
class Notification(models.Model):
    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, db_column='booking_id')
    notification_message = models.TextField()
    notification_status = models.CharField(max_length=20, default='unread')
    notification_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.name}"


class ActionLog(models.Model):
    action_log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    action = models.CharField(max_length=255)
    action_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name}: {self.action}"


class RoomAvailability(models.Model):
    room_availability_id = models.AutoField(primary_key=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, db_column='room_id')
    day_of_week = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.room.room_number} - {self.day_of_week}"


# --- Optional Product Table ---
class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=100)
    product_description = models.TextField(blank=True)
    product_price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.product_name
