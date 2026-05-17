from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, VerifyEmailView, ResendOTPView,
    LoginView, LogoutView, ProfileView,
    ClassmatesView, UserListView, UserDetailView,
)

urlpatterns = [
    path('register/',            RegisterView.as_view()),
    path('verify-email/',        VerifyEmailView.as_view()),
    path('resend-otp/',          ResendOTPView.as_view()),
    path('login/',               LoginView.as_view()),
    path('logout/',              LogoutView.as_view()),
    path('token/refresh/',       TokenRefreshView.as_view()),
    path('profile/',             ProfileView.as_view()),
    path('classmates/',          ClassmatesView.as_view()),
    path('users/',               UserListView.as_view()),
    path('users/<int:user_id>/', UserDetailView.as_view()),
]
