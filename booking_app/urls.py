from django.urls import path
from .views import HomeView, BookingCreateView, BookingListView, AdminDashboardView, LoginViewCustom, LogoutViewCustom, \
    AdminBookingCreateView, UpdateBookingStatusView, NotificationsView, RoomCreateView, RoomListView, RoomUpdateView, \
    RoomTypeListView, RoomTypeCreateView, UserListView, UserCreateView, UserUpdateView, UserDeleteView, \
    RoomTypeUpdateView, RoomDeleteView, RoomTypeDeleteView, RegisterView,EditProfileView

# ⚠️ NOTE: no app_name here, so you can use {% url 'booking_list' %} directly
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('bookings/', BookingListView.as_view(), name='booking_list'),   # ← this name must exist
    path('bookings/create/', BookingCreateView.as_view(), name='create_booking'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-bookings/create/', AdminBookingCreateView.as_view(), name='admin_create_booking'),
    path('admin-bookings/<int:booking_id>/update-status/', UpdateBookingStatusView.as_view(), name='update_booking_status'),
    path('notifications/', NotificationsView.as_view(), name='notifications'),
    path('login/', LoginViewCustom.as_view(), name='login'),
    path('logout/', LogoutViewCustom.as_view(), name='logout'),
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('rooms/create/', RoomCreateView.as_view(), name='room_create'),
    path('rooms/<int:room_id>/edit/', RoomUpdateView.as_view(), name='room_edit'),
    path('rooms/<int:room_id>/delete/', RoomDeleteView.as_view(), name='room_delete'),

    path('room_types/', RoomTypeListView.as_view(), name='room_type_list'),
    path('room_types/create/', RoomTypeCreateView.as_view(), name='room_type_create'),
    path('room_types/<int:type_id>/edit/', RoomTypeUpdateView.as_view(), name='room_type_edit'),
    path('room_types/<int:type_id>/delete/', RoomTypeDeleteView.as_view(), name='room_type_delete'),

    path('users/', UserListView.as_view(), name='user_list'),
    path('users/new/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/edit/', UserUpdateView.as_view(), name='user_edit'),
    path('users/<int:user_id>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('register/', RegisterView.as_view(), name='register'),
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),
]

