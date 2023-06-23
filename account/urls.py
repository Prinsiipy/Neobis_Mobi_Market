from django.urls import path

from .views import (
    RegistrationAPIView,
    LoginView,
    RegisterUpdateView,
    SendCodeView,
    PhoneVerifyView,
    ProductListCreateView,
    ProductRetrieveUpdateDestroyView,
    ProductLikeAPIView,
    ProductUnlikeAPIView,
    FavoriteListCreateView,
    FavoriteRetrieveDestroyView
)

from rest_framework_simplejwt.views import TokenObtainPairView


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', RegisterUpdateView.as_view(), name='profile'),
    path('send_verification_code/', SendCodeView.as_view(), name='send_verification_code'),
    path('verify_phone/', PhoneVerifyView.as_view(), name='verify_phone'),
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('products/<int:product_id>/like/', ProductLikeAPIView.as_view(), name='product-likes'),
    path('products/<int:product_id>/unlike/', ProductUnlikeAPIView.as_view(), name='product-unlike'),
    path('favorites/', FavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('favorites/<int:pk>/', FavoriteRetrieveDestroyView.as_view(), name='favorite-retrieve-destroy')
]