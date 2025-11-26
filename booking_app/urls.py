from django.urls import path
from .views import (
    HomeView,
    BookingCreateView,
    BookingListView,
    AdminDashboardView,
    LoginViewCustom,
    LogoutViewCustom,
    BookingStatusUpdateView,
    AdminBookingCreateView,
    UpdateBookingStatusView,
    EditProfileView
)


# ⚠️ NOTE: no app_name here, so you can use {% url 'booking_list' %} directly
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('bookings/', BookingListView.as_view(), name='booking_list'),   # ← this name must exist
    path('bookings/create/', BookingCreateView.as_view(), name='create_booking'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-bookings/create/', AdminBookingCreateView.as_view(), name='admin_create_booking'),
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('login/', LoginViewCustom.as_view(), name='login'),
    path('logout/', LogoutViewCustom.as_view(), name='logout'),
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),
    path(
        'booking/<int:booking_id>/update_status/',
        BookingStatusUpdateView.as_view(),
        name='update_booking_status'
    ),
]
