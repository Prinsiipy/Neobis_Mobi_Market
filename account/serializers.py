from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError

from .models import User, VerifyPhone


def validate_password_characters(value):
    if not any(char.isalpha() and char.isupper() for char in value):
        raise ValidationError(
            "Пароль должен содержать как минимум одну заглавную букву.",
            code='password_no_uppercase'
        )
    if not any(char.isalpha() and not char.isupper() for char in value):
        raise ValidationError(
            "Пароль должен содержать как минимум одну строчную букву.",
            code='password_no_lowercase'
        )
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.",
                                          code='password-length-lower-8')
    if len(value) > 15:
        raise serializers.ValidationError("Password must not exceed 15 characters.",
                                          code='password-length-higher-15')

    if not any(char.isdigit() for char in value):
        raise serializers.ValidationError("Password must contain at least one digit.")

    if not any(char.isalnum() for char in value):
        raise serializers.ValidationError("Password must contain at least one special character.")


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password_characters])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        confirm_password = validated_data.pop('confirm_password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')


class RegisterUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ('photo', 'first_name', 'last_name', 'username', 'date_of_birth', 'email')

    def update(self, instance, validated_data):
        instance.photo = validated_data.get('photo', instance.photo)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)

        instance.save()

        return instance


class SendCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number']

    def update(self, instance, validated_data):
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)

        instance.save()

        return instance