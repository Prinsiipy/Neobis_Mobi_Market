from django.urls import path
from .views import RegistrationAPIView, LoginView, RegisterUpdateView, SendCodeView, PhoneVerifyView
from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', RegisterUpdateView.as_view(), name='profile'),
    path('send_verification_code/', SendCodeView.as_view(), name='send_verification_code'),
    path('verify_phone/', PhoneVerifyView.as_view(), name='verify_phone')
]