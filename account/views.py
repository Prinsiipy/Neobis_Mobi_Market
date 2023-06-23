import random
import string

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.exceptions import AuthenticationFailed, NotAcceptable
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, exceptions, permissions, serializers
from rest_framework_simplejwt.tokens import RefreshToken

from twilio.rest import Client

from drf_yasg.utils import swagger_auto_schema

from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    RegisterUpdateSerializer,
    SendCodeSerializer,
    ProductSerializer,
    FavoriteSerializer
)
from .models import (
    User,
    VerifyPhone,
    Product,
    ProductLike,
    Favorite
)

from .permissions import IsVerifiedOrReadOnly, IsOwnerOrReadOnly


class RegistrationAPIView(APIView):
    @swagger_auto_schema(request_body=RegistrationSerializer)
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        username = request.data['username']
        password = request.data['password']

        user = User.objects.filter(username=username).first()

        if user is None:
            raise AuthenticationFailed('User not found')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password')

        refresh = RefreshToken.for_user(user)

        return Response({
            'status': 'success',
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })


class RegisterUpdateView(generics.GenericAPIView):
    serializer_class = RegisterUpdateSerializer

    @swagger_auto_schema(request_body=RegisterUpdateSerializer,
                         responses={200: 'User updated successfully', 400: 'Bad Request'})
    def put(self, request):
        user = request.user

        serializer = RegisterUpdateSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User updated successfully'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendCodeView(APIView):
    serializer_class = SendCodeSerializer

    @swagger_auto_schema(request_body=SendCodeSerializer,
                         responses={200: 'User updated successfully', 400: 'Bad Request'})
    def put(self, request):
        user = request.user

        serializer = SendCodeSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            user_data = serializer.data
            try:
                user = User.objects.get(phone_number=user_data["phone_number"])
            except User.DoesNotExist:
                raise NotAcceptable("Please enter a valid phone.")

            code = ''.join(random.choice(string.digits) for _ in range(4))
            VerifyPhone.objects.create(phone=user.phone_number, code=code)
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                message = client.messages.create(
                    body=f"Your verification code pin is {code}",
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=user.phone_number
                )
                return Response({'status': 'success', 'message': 'SMS sent successfully.'})
            except Exception as e:
                return Response({'status': 'error', 'message': str(e)})
            return Response({'message': 'User updated successfully'})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PhoneVerifyView(APIView):
    def post(self, request):
        data = request.data

        verify_phone = VerifyPhone.objects.filter(code=data['code']).first()

        if data['code'] != int(verify_phone.code):
            raise exceptions.APIException('Code is incorrect!')

        user = User.objects.filter(phone_number=verify_phone.phone).first()

        if not user:
            raise exceptions.NotFound('User not found!')

        user.is_verified = True
        user.save()
        return Response({
            'message': 'You successfully verified your phone number'
        })


class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVerifiedOrReadOnly]

    def get_queryset(self):
        # Only return products of the authenticated user
        return Product.objects.all()

    def perform_create(self, serializer):
        # Set the owner of the product as the authenticated user
        serializer.save(owner=self.request.user)


class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVerifiedOrReadOnly]


class ProductLikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerifiedOrReadOnly]

    def post(self, request, product_id):  # Modify parameter name from pk to product_id
        user = request.user
        try:
            product = Product.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return Response({'message': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has already liked the product
        if product.likes.filter(id=user.id).exists():
            return Response({'message': 'You have already liked this product'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new ProductLike instance
        ProductLike.objects.create(product=product, user=user)

        return Response({'message': 'Product liked successfully'}, status=status.HTTP_201_CREATED)


class ProductUnlikeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVerifiedOrReadOnly]

    def delete(self, request, product_id):  # Modify parameter name from pk to product_id
        user = request.user
        try:
            product = Product.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return Response({'message': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user has liked the product
        if not product.likes.filter(id=user.id).exists():
            return Response({'message': 'You have not liked this product'}, status=status.HTTP_400_BAD_REQUEST)

        # Delete the ProductLike instance
        ProductLike.objects.filter(product=product, user=user).delete()

        return Response({'message': 'Product unliked successfully'}, status=status.HTTP_204_NO_CONTENT)


class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsVerifiedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        return Favorite.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        product_id = self.request.data.get('product')

        if Favorite.objects.filter(user=user, product_id=product_id).exists():
            raise serializers.ValidationError('This product is already in your favorites')

        serializer.save(user=user)


class FavoriteRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]